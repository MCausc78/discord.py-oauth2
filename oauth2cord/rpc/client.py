from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, List, Literal, Optional, TYPE_CHECKING, Tuple, Type, Union

from ..activity import create_activity_from_rpc
from ..dispatcher import _loop, Dispatcher
from ..enums import (
    InstallationType,
    OAuth2CodeChallengeMethod,
    OAuth2ResponseType,
)
from ..http import HTTPClient
from ..impersonate import DefaultImpersonate
from ..oauth2 import OAuth2Authorization
from ..utils import MISSING
from .config import EmbeddedActivityConfig
from .enums import Opcode, PromptBehavior
from .state import RPCConnectionState
from .transport import IPCTransport

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self

    import aiohttp

    from ..abc import Snowflake
    from ..activity import BaseActivity, Spotify, ActivityTypes
    from ..client import Client as NormalClient
    from ..flags import Intents
    from ..permissions import Permissions
    from .types.commands import (
        SetConfigRequest as SetConfigRequestPayload,
        SetConfigResponse as SetConfigResponsePayload,
        AuthorizeRequest as AuthorizeRequestPayload,
        AuthorizeResponse as AuthorizeResponsePayload,
        AuthenticateRequest as AuthenticateRequestPayload,
        AuthenticateResponse as AuthenticateResponsePayload,
        SetActivityRequest as SetActivityRequestPayload,
        SetActivityResponse as SetActivityResponsePayload,
        SendActivityJoinInviteRequest as SendActivityJoinInviteRequestPayload,
        CloseActivityJoinRequest as CloseActivityJoinRequestPayload,
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

    def upgrade(self, *, intents: Optional[Intents] = None) -> NormalClient:
        from ..client import Client as NormalClient

        return NormalClient(intents=intents, _rpc_client=self)

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

    async def start(
        self,
        client_id: int,
        *,
        background: bool,
        pipe: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> Optional[asyncio.Task[None]]:
        if self.loop is _loop:
            await self._async_setup_hook()

        transport = await IPCTransport.from_client(self, pipe=pipe, timeout=timeout)
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

    async def edit_embedded_activity_config(self, *, use_interactive_pip: bool) -> EmbeddedActivityConfig:
        """|coro|

        Edits the configuration for current embedded activity.

        Parameters
        ----------
        use_interactive_pip: :class:`bool`
            Whether the picture-in-picture should be interactive.

        Raises
        ------
        RPCException
            Editing the embedded activity configuration failed.

        Returns
        -------
        :class:`EmbeddedActivityConfig`
            The newly updated embedded activity config.
        """
        payload: SetConfigRequestPayload = {
            'use_interactive_pip': use_interactive_pip,
        }

        data: SetConfigResponsePayload = await self._transport.send_command('SET_CONFIG', payload)
        return EmbeddedActivityConfig(data)

    async def authorize(
        self,
        client_id: int,
        *,
        response_type: Optional[OAuth2ResponseType] = OAuth2ResponseType.code,
        scopes: Optional[List[str]] = None,
        code_challenge: Optional[str] = None,
        code_challenge_method: Optional[OAuth2CodeChallengeMethod] = None,
        state: Optional[str] = None,
        nonce: Optional[str] = None,
        permissions: Optional[Permissions] = None,
        guild: Optional[Snowflake] = None,
        channel: Optional[Snowflake] = None,
        prompt: Optional[PromptBehavior] = None,
        disable_guild_select: Optional[bool] = None,
        install_type: Optional[InstallationType] = None,
        pid: Optional[int] = MISSING,
    ) -> str:
        """|coro|

        Opens OAuth2 authorization modal in the Discord client.

        Parameters
        ----------
        client_id: :class:`int`
            The ID of the application being authorized.
        response_type: Optional[:class:`OAuth2ResponseType`]
            The type of response to return. Defaults to :attr:`~OAuth2ResponseType.code`.
        scopes: Optional[List[:class:`str`]]
            The scopes to authorize the application with.
        code_challenge: Optional[:class:`str`]
            A code challenge for the PKCE extension to the authorization code grant. Must be provided if using ``code_challenge_method``.
        code_challenge_method: Optional[:class:`OAuth2CodeChallengeMethod`]
            The method used to generate the code challenge.
        state: Optional[:class:`str`]
            An unique string to bind the user's request to their authenticated state.
        nonce: Optional[:class:`str`]
            An unique string to bind the user's request to their authenticated state.
            Only applicable if requesting ``openid`` scope.
        permissions: Optional[:class:`~oauth2cord.Permissions`]
            The permissions to grant to the bot.
        guild: Optional[:class:`~oauth2cord.abc.Snowflake`]
            The guild to pre-fill the dropdown picker with.

            Only applicable if requesting ``bot`` / ``applications.commands`` / ``webhook.incoming`` scope and ``install_type` is :attr:`~oauth2cord.InstallationType.guild`.
        channel: Optional[:class:`~oauth2cord.abc.Snowflake`]
            The channel to pre-fill the dropdown picker with.

            Only applicable if requesting ``webhook.incoming`` scope.
        prompt: Optional[:class:`PromptBehavior`]
            The prompt behavior to use for the authorization flow (default consent)

        disable_guild_select: Optional[:class:`bool`]
            Disallows the user from changing the guild dropdown.
            Only applicable when requesting ``bot`` / ``applications.commands`` / ``webhook.incoming`` scope and ``install_type` is :attr:`~oauth2cord.InstallationType.guild`.
            Defaults to ``False``.
        install_type: Optional[:class:`InstallationType`]
            The installation context for the authorization.
            Only applicable when requesting ``application.commands`` scope.
            Defaults to :attr:`~oauth2cord.InstallationType.guild`.
        pid: Optional[:class:`int`]
            The ID of the process to open the authorization modal in. If ``None`` wasn't explicitly passed, this defaults to result of :func:`os.getpid`.

            If ``None`` is explicitly passed, then the modal will be open in existing Discord client instead.

        Raises
        ------
        RPCException
            Authorizing the application failed.

        Returns
        -------
        :class:`str`
            The code that can be exchanged.
        """
        if pid is MISSING:
            pid = self.pid

        payload: AuthorizeRequestPayload = {
            'client_id': str(client_id),
        }

        if response_type is not None:
            payload['response_type'] = response_type.value
        if scopes is not None:
            payload['scopes'] = scopes
        if code_challenge is not None:
            payload['code_challenge'] = code_challenge
        if code_challenge_method is not None:
            payload['code_challenge_method'] = code_challenge_method.value
        if state is not None:
            payload['state'] = state
        if nonce is not None:
            payload['nonce'] = nonce
        if permissions is not None:
            payload['permissions'] = str(permissions.value)
        if guild is not None:
            payload['guild_id'] = str(guild.id)
        if channel is not None:
            payload['channel_id'] = str(channel.id)
        if prompt is not None:
            payload['prompt'] = prompt.value
        if disable_guild_select is not None:
            payload['disable_guild_select'] = disable_guild_select
        if install_type is not None:
            payload['integration_type'] = install_type.value
        if pid is not None:
            payload['pid'] = pid

        data: AuthorizeResponsePayload = await self._transport.send_command('AUTHORIZE', payload)
        return data['code']

    async def authenticate(self, token: str) -> Tuple[OAuth2Authorization, str]:
        """|coro|

        Authenticates with the provided access token.

        Note that you need to connect to IPC socket first using :meth:`start`.

        Parameters
        ----------
        token: :class:`str`
            The authentication token.

        Parameters
        ----------
        RPCException
            Authenticating failed.

        Returns
        -------
        Tuple[:class:`~oauth2cord.OAuth2Authorization`, :class:`str`]
            The current OAuth2 authorization and sanitized access token.
        """
        payload: AuthenticateRequestPayload = {'access_token': token}
        data: AuthenticateResponsePayload = await self._transport.send_command('AUTHENTICATE', payload)
        return (OAuth2Authorization(data=data, state=self._connection), data['access_token'])

    # Remaining:
    # - GET_GUILD
    # - GET_GUILDS
    # - GET_CHANNEL
    # - GET_CHAHNNELS
    # - GET_CHANNEL_PERMISSIONS
    # - CREATE_CHANNEL_INVITE
    # - GET_RELATIONSHIPS
    # - GET_USER
    # - SUBSCRIBE
    # - UNSUBSCRIBE
    # - SET_USER_VOICE_SETTINGS
    # - SET_USER_VOICE_SETTINGS_2
    # - PUSH_TO_TALK
    # - SELECT_VOICE_CHANNEL
    # - GET_SELECTED_VOICE_CHANNEL
    # - SELECT_TEXT_CHANNEL
    # - GET_VOICE_SETTINGS
    # - SET_VOICE_SETTINGS_2
    # - SET_VOICE_SETTINGS
    # - SET_ACTIVITY (implemented already)

    async def change_presence(
        self,
        *,
        activity: Optional[Union[BaseActivity, Spotify]] = MISSING,
    ) -> Optional[ActivityTypes]:
        """|coro|

        Updates the current activity.

        All parameters are optional.

        Parameters
        ----------
        activity: Optional[Union[:class:`~oauth2cord.BaseActivity`, :class:`~oauth2cord.Spotify`]]
            The activity. Passing ``None`` denotes the activity will be removed.

        Raises
        ------
        RPCException
            Changing the presence failed.
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
        data: SetActivityResponsePayload = await self._transport.send_command('SET_ACTIVITY', payload)
        return create_activity_from_rpc(data, self._connection)

    async def send_activity_join_invite(self, to: Snowflake) -> None:
        """|coro|

        Sends an activity join invite to target user.

        Parameters
        ----------
        to: :class:`~oauth2cord.abc.Snowflake`
            The user to send invite to.

        Raises
        ------
        RPCException
            Sending the invite failed.
        """
        payload: SendActivityJoinInviteRequestPayload = {
            'pid': self.pid,
            'user_id': str(to.id),
        }
        await self._transport.send_command('ACTIVITY_JOIN_INVITE', payload)

    async def close_activity_join_request(self, from_: Snowflake) -> None:
        payload: CloseActivityJoinRequestPayload = {'user_id': str(from_.id)}
        await self._transport.send_command('CLOSE_ACTIVITY_JOIN_REQUEST', payload)
