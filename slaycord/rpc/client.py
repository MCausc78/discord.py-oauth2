from __future__ import annotations

import asyncio
from typing import Literal

from ..dispatcher import _loop, Dispatcher
from .enums import Opcode
from .transport import IPCTransport

TransportType = Literal[
    'ipc',
]


class Client(Dispatcher):
    def __init__(
        self,
        *,
        transport: TransportType = 'ipc',
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = _loop
        self.transport_type: TransportType = transport

    async def _async_setup_hook(self) -> None:
        # Called whenever the client needs to initialise asyncio objects with a running loop
        loop = asyncio.get_running_loop()
        self.loop = loop

    async def setup_hook(self) -> None:
        """|coro|

        A coroutine to be called to setup the bot, by default this is blank.

        To perform asynchronous setup after the bot is logged in but before
        it has connected to the Websocket, overwrite this coroutine.

        This is only called once, in :meth:`login`, and will be called before
        any events are dispatched, making it a better solution than doing such
        setup in the :func:`~slaycord.on_ready` event.

        .. warning::

            Since this is called *before* the websocket connection is made therefore
            anything that waits for the websocket will deadlock, this includes things
            like :meth:`wait_for` and :meth:`wait_until_ready`.

        .. versionadded:: 2.0
        """
        pass

    async def start(self, *, client_id: int) -> None:
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
        while True:
            await transport.poll_event()
