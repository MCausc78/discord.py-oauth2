from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Literal, Optional, TYPE_CHECKING, Type, Union

from ..dispatcher import _loop, Dispatcher
from ..http import HTTPClient
from ..impersonate import DefaultImpersonate
from ..utils import MISSING
from .enums import Opcode
from .state import RPCConnectionState
from .transport import IPCTransport

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self

    import aiohttp

    from ..activity import BaseActivity, Spotify
    from .types.commands import (
        SetActivityRequest as SetActivityRequestPayload,
    )

TransportType = Literal[
    'ipc',
]

_log = logging.getLogger(__name__)


class Client(Dispatcher):
    def __init__(
        self,
        *,
        transport: TransportType = 'ipc',
        **options: Any,
    ) -> None:
        super().__init__(logger=_log)

        impersonate = options.get('impersonate')
        if impersonate is None:
            impersonate = DefaultImpersonate()

        connector: Optional[aiohttp.BaseConnector] = options.get('connector', None)
        proxy: Optional[str] = options.pop('proxy', None)
        proxy_auth: Optional[aiohttp.BasicAuth] = options.pop('proxy_auth', None)
        unsync_clock: bool = options.pop('assume_unsync_clock', True)
        http_trace: Optional[aiohttp.TraceConfig] = options.pop('http_trace', None)
        max_ratelimit_timeout: Optional[float] = options.pop('max_ratelimit_timeout', None)

        self.http: HTTPClient = HTTPClient(
            self.loop,
            connector,
            impersonate=impersonate,
            proxy=proxy,
            proxy_auth=proxy_auth,
            unsync_clock=unsync_clock,
            http_trace=http_trace,
            max_ratelimit_timeout=max_ratelimit_timeout,
        )
        self.pid: int = options.pop('pid', os.getpid())
        self.transport_type: TransportType = transport
        self._closing_task: Optional[asyncio.Task[None]] = None
        self._connection: RPCConnectionState = self._get_state()
        self._transport: IPCTransport = None  # type: ignore # Set in start method

    async def __aenter__(self) -> Self:
        await self._async_setup_hook()
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        # This avoids double-calling a user-provided .close()
        if self._closing_task:
            await self._closing_task
        else:
            await self.close()

    def _get_state(self) -> RPCConnectionState:
        return RPCConnectionState(
            dispatch=self.dispatch,
            http=self.http,
        )

    async def _async_setup_hook(self) -> None:
        # Called whenever the client needs to initialise asyncio objects with a running loop
        loop = asyncio.get_running_loop()
        self.loop = loop
        self.http.loop = loop
        await self.http.impersonate.setup()
        await self.http.startup()

    async def setup_hook(self) -> None:
        """|coro|

        A coroutine to be called to setup the client, by default this is blank.

        To perform asynchronous setup after the client is logged in but before
        it has connected to the IPC socket, overwrite this coroutine.

        This is only called once, in :meth:`login`, and will be called before
        any events are dispatched, making it a better solution than doing such
        setup in the :func:`~oauth2cord.on_ready` event.

        .. warning::

            Since this is called *before* the IPC connection is made therefore
            anything that waits for the IPC will deadlock, this includes things
            like :meth:`wait_for` and :meth:`wait_until_ready`.
        """
        pass

    async def start(self, client_id: int, *, background: bool) -> Optional[asyncio.Task[None]]:
        if self.loop is _loop:
            await self._async_setup_hook()

        transport = await IPCTransport.from_client(self)
        await transport.send(
            Opcode.handshake.value,
            {
                'v': 1,
                'client_id': str(client_id),
            },
        )

        self._transport = transport
        if background:
            return asyncio.create_task(self._handle_transport_flow())

        await self._handle_transport_flow()

    async def close(self) -> None:
        """|coro|

        Closes the connection to Discord client.
        """
        if self._closing_task:
            return await self._closing_task

        async def _close():
            await self._transport.close()
            await self._connection.close()
            await self.http.close()
            self.loop = MISSING

        self._closing_task = asyncio.create_task(_close())
        await self._closing_task

    def clear(self) -> None:
        """Clears the internal state of the client.

        After this, the client can be considered "re-opened", i.e. :meth:`is_closed`
        and :meth:`is_ready` both return ``False`` along with the client's internal
        cache cleared.
        """
        self._closing_task = None
        self._connection.clear()
        self.http.clear()

    def is_closed(self) -> bool:
        """:class:`bool`: Indicates if the IPC connection is closed."""
        return self._closing_task is not None

    async def _handle_transport_flow(self) -> None:
        cond = True
        while cond:
            try:
                cond = await self._transport.poll_event()
            except StopAsyncIteration:
                cond = False

    async def change_presence(
        self,
        *,
        activity: Optional[Union[BaseActivity, Spotify]] = MISSING,
    ) -> None:
        """|coro|

        Changes the current activity.

        All parameters are optional.

        Parameters
        ----------
        activity: Optional[Union[:class:`~oauth2cord.BaseActivity`, :class:`~oauth2cord.Spotify`]]
            The activity. Passing ``None`` denotes the activity will be removed.
        """

        if activity is MISSING:
            return

        self._activity = activity

        if self._activity is None:
            activity_data = None
        else:
            activity_data = self._activity.to_rpc_dict()

        payload: SetActivityRequestPayload = {
            'pid': self.pid,
            'activity': activity_data,
        }
        await self._transport.send_command('SET_ACTIVITY', payload)
