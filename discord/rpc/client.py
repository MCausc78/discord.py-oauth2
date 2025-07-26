from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict, List, Literal, Optional, TYPE_CHECKING, Tuple, Type, TypeVar, Union, overload

from ..activity import create_activity_from_rpc
from ..client import Client as NormalClient
from ..dispatcher import _loop, Dispatcher
from ..entitlements import Gift
from ..enums import (
    ConnectionType,
    InstallationType,
    OAuth2CodeChallengeMethod,
    OAuth2ResponseType,
    PaymentSourceType,
)
from ..http import HTTPClient
from ..impersonate import DefaultImpersonate
from ..invite import Invite
from ..oauth2 import OAuth2Authorization
from ..relationship import Relationship
from ..user import User, ClientUser
from ..utils import MISSING
from .channel import PartialGuildChannel, GuildChannel
from .config import EmbeddedActivityConfig
from .enums import DeepLinkLocation, Opcode, PromptBehavior, VoiceSettingsModeType
from .guild import PartialGuild, Guild
from .settings import (
    UserVoiceSettings,
    VoiceIOSettings,
    PartialVoiceSettingsMode,
    VoiceSettings,
)
from .state import RPCConnectionState
from .transport import IPCTransport

if TYPE_CHECKING:
    from types import TracebackType
    from typing_extensions import Self

    import aiohttp

    from ..abc import Snowflake
    from ..activity import BaseActivity, Spotify, ActivityTypes
    from ..flags import Intents
    from ..permissions import Permissions
    from .subscriptions import EventSubscription
    from .types.commands import (
        SetConfigRequest as SetConfigRequestPayload,
        SetConfigResponse as SetConfigResponsePayload,
        AuthorizeRequest as AuthorizeRequestPayload,
        AuthorizeResponse as AuthorizeResponsePayload,
        AuthenticateRequest as AuthenticateRequestPayload,
        AuthenticateResponse as AuthenticateResponsePayload,
        GetGuildRequest as GetGuildRequestPayload,
        GetGuildResponse as GetGuildResponsePayload,
        GetGuildsResponse as GetGuildsResponsePayload,
        GetChannelRequest as GetChannelRequestPayload,
        GetChannelResponse as GetChannelResponsePayload,
        GetChannelsRequest as GetChannelsRequestPayload,
        GetChannelsResponse as GetChannelsResponsePayload,
        GetChannelPermissionsRequest as GetChannelPermissionsRequestPayload,
        GetChannelPermissionsResponse as GetChannelPermissionsResponsePayload,
        CreateChannelInviteRequest as CreateChannelInviteRequestPayload,
        CreateChannelInviteResponse as CreateChannelInviteResponsePayload,
        GetRelationshipsRequest as GetRelationshipsRequestPayload,
        GetRelationshipsResponse as GetRelationshipsResponsePayload,
        GetUserRequest as GetUserRequestPayload,
        GetUserResponse as GetUserResponsePayload,
        SubscribeRequest as SubscribeRequestPayload,
        SubscribeResponse as SubscribeResponsePayload,
        UnsubscribeRequest as UnsubscribeRequestPayload,
        UnsubscribeResponse as UnsubscribeResponsePayload,
        SetUserVoiceSettingsRequest as SetUserVoiceSettingsRequestPayload,
        SetUserVoiceSettingsResponse as SetUserVoiceSettingsResponsePayload,
        SetUserVoiceSettings2Request as SetUserVoiceSettings2RequestPayload,
        # SetUserVoiceSettings2Response as SetUserVoiceSettings2ResponsePayload,
        PushToTalkRequest as PushToTalkRequestPayload,
        # PushToTalkResponse as PushToTalkResponsePayload,
        SelectVoiceChannelRequest as SelectVoiceChannelRequestPayload,
        SelectVoiceChannelResponse as SelectVoiceChannelResponsePayload,
        GetSelectedVoiceChannelRequest as GetSelectedVoiceChannelRequestPayload,
        GetSelectedVoiceChannelResponse as GetSelectedVoiceChannelResponsePayload,
        SelectTextChannelRequest as SelectTextChannelRequestPayload,
        SelectTextChannelResponse as SelectTextChannelResponsePayload,
        GetVoiceSettingsRequest as GetVoiceSettingsRequestPayload,
        GetVoiceSettingsResponse as GetVoiceSettingsResponsePayload,
        SetVoiceSettings2Request as SetVoiceSettings2RequestPayload,
        # SetVoiceSettings2Response as SetVoiceSettings2ResponsePayload,
        SetVoiceSettingsRequest as SetVoiceSettingsRequestPayload,
        SetVoiceSettingsResponse as SetVoiceSettingsResponsePayload,
        SetActivityRequest as SetActivityRequestPayload,
        SetActivityResponse as SetActivityResponsePayload,
        SendActivityJoinInviteRequest as SendActivityJoinInviteRequestPayload,
        CloseActivityJoinRequest as CloseActivityJoinRequestPayload,
        ActivityInviteUserRequest as ActivityInviteUserRequestPayload,
        # ActivityInviteUserResponse as ActivityInviteUserResponsePayload,
        AcceptActivityInviteRequest as AcceptActivityInviteRequestPayload,
        # AcceptActivityInviteResponse as AcceptActivityInviteResponsePayload,
        OpenInviteDialogRequest as OpenInviteDialogRequestPayload,
        # OpenInviteDialogResponse as OpenInviteDialogResponsePayload,
        OpenShareMomentDialogRequest as OpenShareMomentDialogRequestPayload,
        # OpenShareMomentDialogResponse as OpenShareMomentDialogResponsePayload,
        ShareInteractionRequestPreviewImage as ShareInteractionRequestPreviewImagePayload,
        ShareInteractionRequestComponent as ShareInteractionRequestComponentPayload,
        ShareInteractionRequest as ShareInteractionRequestPayload,
        ShareInteractionResponse as ShareInteractionResponsePayload,
        InitiateImageUploadRequest as InitiateImageUploadRequestPayload,
        InitiateImageUploadResponse as InitiateImageUploadResponsePayload,
        ShareLinkRequest as ShareLinkRequestPayload,
        ShareLinkResponse as ShareLinkResponsePayload,
        InviteBrowserRequest as InviteBrowserRequestPayload,
        InviteBrowserResponse as InviteBrowserResponsePayload,
        DeepLinkRequest as DeepLinkRequestPayload,
        DeepLinkResponse as DeepLinkResponsePayload,
        ConnectionsCallbackRequest as ConnectionsCallbackRequestPayload,
        # ConnectionsCallbackResponse as ConnectionsCallbackResponsePayload,
        BillingPopupBridgeCallbackRequest as BillingPopupBridgeCallbackRequestPayload,
        BillingPopupBridgeCallbackResponse as BillingPopupBridgeCallbackResponsePayload,
        BraintreePopupBridgeCallbackRequest as BraintreePopupBridgeCallbackRequestPayload,
        BraintreePopupBridgeCallbackResponse as BraintreePopupBridgeCallbackResponsePayload,
        GiftCodeBrowserRequest as GiftCodeBrowserRequestPayload,
        GiftCodeBrowserResponse as GiftCodeBrowserResponsePayload,
    )
    from .types.http import Response as ResponsePayload
    from .ui import Button
    from .voice_state import Pan

    C = TypeVar('C', bound='NormalClient')

TransportType = Literal[
    'ipc',
]

_log = logging.getLogger(__name__)

# Unsure where to place this
class PreviewImage:
    __slots__ = (
        'height',
        'url',
        'width',
    )

    def __init__(self, url: str, *, height: int, width: int) -> None:
        self.url: str = url
        self.height: int = height
        self.width: int = width

    def to_dict(self) -> ShareInteractionRequestPreviewImagePayload:
        return {
            'height': self.height,
            'url': self.url,
            'width': self.width,
        }


class SharedLink:
    __slots__ = (
        'success',
        'did_copy_link',
        'did_send_message',
    )

    def __init__(self, data: ShareLinkResponsePayload) -> None:
        self.success: bool = data['success']
        self.did_copy_link: bool = data.get('didCopyLink', False)
        self.did_send_message: bool = data.get('didSendMessage', False)


class Client(Dispatcher):
    """Represents a RPC client.

    Note that to perform any operations with the Discord client you must call :meth:`start` first.
    """

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
        """|coro|

        Upgrades the RPC client to regular client.

        Parameters
        ----------
        intents: Optional[:class:`~discord.Intents`]
            The intents that you want to enable for the session.
            This is a way of disabling and enabling certain Gateway events from triggering and being sent.

        Returns
        -------
        :class:`discord.Client`
            The client.
        """
        return NormalClient(intents=intents, rpc=self)

    async def setup_hook(self) -> None:
        """|coro|

        A coroutine to be called to setup the client, by default this is blank.

        To perform asynchronous setup after the client is logged in but before
        it has connected to the IPC socket, overwrite this coroutine.

        This is only called once, in :meth:`login`, and will be called before
        any events are dispatched, making it a better solution than doing such
        setup in the :func:`~discord.on_ready` event.

        .. warning::

            Since this is called *before* the IPC connection is made therefore
            anything that waits for the IPC will deadlock, this includes things
            like :meth:`wait_for` and :meth:`wait_until_ready`.
        """
        pass

    @overload
    async def start(
        self,
        client_id: int,
        *,
        background: Literal[False],
        pipe: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> None:
        ...

    @overload
    async def start(
        self,
        client_id: int,
        *,
        background: Literal[True],
        pipe: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> asyncio.Task[None]:
        ...

    async def start(
        self,
        client_id: int,
        *,
        background: bool = False,
        pipe: Optional[int] = None,
        timeout: Optional[float] = 30.0,
    ) -> Optional[asyncio.Task[None]]:
        """|coro|

        Connects to the IPC socket.

        Parameters
        ----------
        client_id: :class:`int`
            The ID of the application.
        background: :class:`bool`
            Whether to connect to IPC socket and return task that will handle the socket flow.
        pipe: Optional[:class:`int`]
            The pipe to connect to.
        timeout: Optional[:class:`float`]
            The connection timeout in seconds.

        Returns
        -------
        Optional[:class:`asyncio.Task`]
            The task that handles the flow.
        """
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

    @property
    def user(self) -> Optional[ClientUser]:
        """Optional[:class:`~discord.ClientUser`]: The currently connected user. ``None`` if not connected yet."""
        return self._connection.user

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
        permissions: Optional[:class:`~discord.Permissions`]
            The permissions to grant to the bot.
        guild: Optional[:class:`~discord.abc.Snowflake`]
            The guild to pre-fill the dropdown picker with.

            Only applicable if requesting ``bot`` / ``applications.commands`` / ``webhook.incoming`` scope and ``install_type` is :attr:`~discord.InstallationType.guild`.
        channel: Optional[:class:`~discord.abc.Snowflake`]
            The channel to pre-fill the dropdown picker with.

            Only applicable if requesting ``webhook.incoming`` scope.
        prompt: Optional[:class:`PromptBehavior`]
            The prompt behavior to use for the authorization flow (default consent)

        disable_guild_select: Optional[:class:`bool`]
            Disallows the user from changing the guild dropdown.
            Only applicable when requesting ``bot`` / ``applications.commands`` / ``webhook.incoming`` scope and ``install_type` is :attr:`~discord.InstallationType.guild`.
            Defaults to ``False``.
        install_type: Optional[:class:`InstallationType`]
            The installation context for the authorization.
            Only applicable when requesting ``application.commands`` scope.
            Defaults to :attr:`~discord.InstallationType.guild`.
        pid: Optional[:class:`int`]
            The ID of the process to open the authorization modal in. If ``None`` wasn't explicitly passed, this defaults to result of :attr:`pid`.

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
        Tuple[:class:`~discord.OAuth2Authorization`, :class:`str`]
            The current OAuth2 authorization and sanitized access token.
        """
        payload: AuthenticateRequestPayload = {'access_token': token}
        data: AuthenticateResponsePayload = await self._transport.send_command('AUTHENTICATE', payload)
        return (OAuth2Authorization(data=data, state=self._connection), data['access_token'])

    async def fetch_guild(self, guild_id: int, *, timeout: Optional[int] = None) -> Guild:
        """|coro|

        Retrieves a :class:`Guild` with specified ID.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild's ID to request.

        Parameters
        ----------
        RPCException
            Retrieving the guild failed.

        Returns
        -------
        :class:`Guild`
            The guild you requested.
        """

        if timeout is None:
            timeout = 30

        payload: GetGuildRequestPayload = {
            'guild_id': str(guild_id),
            'timeout': timeout,
        }
        data: GetGuildResponsePayload = await self._transport.send_command('GET_GUILD', payload)

        return Guild(data=data, state=self._connection)

    async def fetch_guilds(self) -> List[PartialGuild]:
        """|coro|

        Retrieves a list of guilds you're in.

        Raises
        ------
        RPCException
            Retrieving the guild list failed.

        Returns
        -------
        List[:class:`PartialGuild`]
            The guilds.
        """

        data: GetGuildsResponsePayload = await self._transport.send_command('GET_GUILDS', None)
        state = self._connection
        return [PartialGuild(data=d, state=state) for d in data['guilds']]

    async def fetch_channel(self, channel_id: int) -> GuildChannel:
        """|coro|

        Retrieves a :class:`GuildChannel` from specified ID.

        Parameters
        ----------
        channel_id: :class:`int`
            The channel's ID to request.

        Raises
        ------
        RPCException
            Retrieving the channel failed.

        Returns
        -------
        :class:`GuildChanenl`
            The guild channel you requested.
        """

        payload: GetChannelRequestPayload = {'channel_id': str(channel_id)}
        data: GetChannelResponsePayload = await self._transport.send_command('GET_CHANNEL', payload)
        return GuildChannel(data=data, state=self._connection)

    async def fetch_guild_channels(self, guild_id: int) -> List[PartialGuildChannel]:
        """|coro|

        Retrieves a list of channels the guild has.

        Parameters
        ----------
        guild_id: :class:`int`
            The guild's ID to request channels of.

        Raises
        ------
        RPCException
            Retrieving the guild channel list failed.

        Returns
        -------
        List[:class:`PartialGuildChannel`]
            The guild channels.
        """
        payload: GetChannelsRequestPayload = {'guild_id': str(guild_id)}
        data: GetChannelsResponsePayload = await self._transport.send_command('GET_CHANNELS', payload)
        state = self._connection
        return [PartialGuildChannel(data=d, guild_id=guild_id, state=state) for d in data['channels']]

    async def fetch_current_channel_permissions(self) -> Permissions:
        """|coro|

        Compute your permissions in the selected guild channel.

        Raises
        ------
        RPCException
            Computing permissions failed.

        Returns
        -------
        :class:`~discord.Permissions`
            The computed permissions.
        """
        payload: GetChannelPermissionsRequestPayload = {}
        data: GetChannelPermissionsResponsePayload = await self._transport.send_command('GET_CHANNEL_PERMISSIONS', payload)
        return Permissions._from_value(int(data['permissions']))

    async def create_channel_invite(self, channel_id: int) -> Invite:
        """|coro|

        Creates a invite in the specified channel.

        Parameters
        ----------
        channel_id: :class:`int`
            The channel's ID to create the invite for.

        Raises
        ------
        RPCException
            Creating the invite failed.

        Returns
        -------
        :class:`~discord.Invite`
            The created invite.
        """

        payload: CreateChannelInviteRequestPayload = {'channel_id': str(channel_id)}
        data: CreateChannelInviteResponsePayload = await self._transport.send_command('CREATE_CHANNEL_INVITE', payload)
        return Invite.from_incomplete(data=data, state=self._connection)

    async def fetch_relationships(self) -> List[Relationship]:
        """|coro|

        Retrieve all of your relationships and their presence.

        Note that you will receive only overall status
        and :attr:`discord.Relationship.activity` will be not ``None``
        if activity application is same as the authenticated application.

        Raises
        ------
        RPCException
            Retrieving relationships failed.

        Returns
        -------
        List[:class:`~discord.Relationship`]
            The relationships.
        """

        payload: GetRelationshipsRequestPayload = {}
        data: GetRelationshipsResponsePayload = await self._transport.send_command('GET_RELATIONSHIPS', payload)
        state = self._connection
        return [Relationship._from_rpc(d, state) for d in data['relationships']]

    async def fetch_user(self, user_id: int) -> Optional[User]:
        """|coro|

        Retrieve the specified user.

        Parameters
        ----------
        user_id: :class:`int`
            The user's ID to request.

        Raises
        ------
        RPCException
            Retrieving the user failed.

        Returns
        -------
        Optional[:class:`~discord.User`]
            The user, if any.
        """
        payload: GetUserRequestPayload = {'id': str(user_id)}
        data: GetUserResponsePayload = await self._transport.send_command('GET_USER', payload)
        if data is None:
            return None
        return User._from_rpc(data, self._connection)

    async def add_subscription(self, subscription: EventSubscription) -> str:
        """|coro|

        Adds an event subscription.

        Parameters
        ----------
        subscription: :class:`EventSubscription`
            The subscription to add.

        Raises
        ------
        RPCException
            Adding an event subscription failed.

        Returns
        -------
        :class:`str`
            The event that the subscription just added.
        """
        payload: SubscribeRequestPayload = subscription.get_data()
        data: SubscribeResponsePayload = await self._transport.send_command(
            'SUBSCRIBE', payload, event=subscription.get_type()
        )
        return data['evt']

    async def remove_subscription(self, subscription: EventSubscription) -> str:
        """|coro|

        Removes an event subscription.

        Parameters
        ----------
        subscription: :class:`EventSubscription`
            The subscription to remove.

        Raises
        ------
        RPCException
            Removing an event subscription failed.

        Returns
        -------
        :class:`str`
            The event that the subscription just removed.
        """
        payload: UnsubscribeRequestPayload = subscription.get_data()
        data: UnsubscribeResponsePayload = await self._transport.send_command(
            'UNSUBSCRIBE', payload, event=subscription.get_type()
        )
        return data['evt']

    async def edit_user_voice_settings(
        self,
        user_id: int,
        *,
        pan: Pan = MISSING,
        volume: float = MISSING,
        mute: bool = MISSING,
    ) -> UserVoiceSettings:
        """|coro|

        Edits the voice settings for specified user.

        You must have ``rpc`` or ``rpc.voice.write`` OAuth2 scope.

        All parameters are optional.

        Parameters
        ----------
        user_id: :class:`int`
            The target user's ID.
        pan: :class:`Pan`
            The new pan values for the target user.
        volume: :class:`float`
            The new local volume. Must be between 0 and 200.
        mute: :class:`bool`
            Whether the user should be muted.

        Raises
        ------
        RPCException
            Editing the user voice settings failed.

        Returns
        -------
        :class:`UserVoiceSettings`
            The newly updated user voice settings.
        """
        payload: SetUserVoiceSettingsRequestPayload = {
            'user_id': str(user_id),
        }
        if pan is not MISSING:
            payload['pan'] = pan.to_dict()
        if volume is not MISSING:
            payload['volume'] = volume
        if mute is not MISSING:
            payload['mute'] = mute

        data: SetUserVoiceSettingsResponsePayload = await self._transport.send_command('SET_USER_VOICE_SETTINGS', payload)
        return UserVoiceSettings(data=data, state=self._connection)

    async def edit_user_voice_settings_2(
        self,
        user_id: int,
        *,
        volume: float = MISSING,
        mute: bool = MISSING,
    ) -> None:
        """|coro|

        Edits the voice settings for specified user.

        All parameters are optional.

        Parameters
        ----------
        user_id: :class:`int`
            The target user's ID.
        volume: :class:`float`
            The new local volume. Must be between 0 and 200.
        mute: :class:`bool`
            Whether the user should be muted.

        Raises
        ------
        RPCException
            Editing the user voice settings failed.
        """
        payload: SetUserVoiceSettings2RequestPayload = {
            'user_id': str(user_id),
        }
        if volume is not MISSING:
            payload['volume'] = volume
        if mute is not MISSING:
            payload['mute'] = mute

        # Needs RPC_LOCAL_SCOPE (?)
        await self._transport.send_command('SET_USER_VOICE_SETTINGS_2', payload)

    async def push_to_talk(self, *, active: Optional[bool] = None) -> None:
        """|coro|

        Sets whether Push-To-Talk feature should be active.

        Parameters
        ----------
        active: Optional[:class:`bool`]
            Whether the Push-To-Talk feature should be active.

        Raises
        ------
        RPCException
            Setting Push-To-Talk feature failed.
        """
        payload: PushToTalkRequestPayload = {}
        if active not in (MISSING, None):
            payload['active'] = active
        await self._transport.send_command('PUSH_TO_TALK', payload)

    async def select_voice_channel(
        self,
        channel_id: Optional[int],
        *,
        timeout: Optional[float] = None,
        force: Optional[bool] = None,
        navigate: Optional[bool] = None,
    ) -> Optional[GuildChannel]:
        """|coro|

        Joins or leaves a voice channel.

        Parameters
        ----------
        channel_id: Optional[:class:`int`]
            The ID of the channel to join.
            Pass ``None`` to leave the current voice channel.
        timeout: Optional[:class:`float`]
            A timeout for joining/leaving voice channel in milliseconds.
        force: Optional[:class:`bool`]
            Whether to forcefully join/leave voice channel. Defaults to ``False``.
        navigate: Optional[:class:`bool`]
            Whether to navigate to the voice channel after joining. Defaults to ``False``.

        Raises
        ------
        RPCException
            Joining/leaving the voice channel failed.

        Returns
        -------
        Optional[:class:`GuildChannel`]
            The voice channel that you joined.
        """

        payload: SelectVoiceChannelRequestPayload = {'channel_id': None if channel_id is None else str(channel_id)}
        if timeout is not None:
            payload['timeout'] = timeout
        if force is not None:
            payload['force'] = force
        if navigate is not None:
            payload['navigate'] = navigate

        data: SelectVoiceChannelResponsePayload = await self._transport.send_command('SELECT_VOICE_CHANNEL', payload)
        if data is None:
            return None

        return GuildChannel(data=data, state=self._connection)

    async def fetch_selected_voice_channel(self) -> Optional[GuildChannel]:
        """|coro|

        Retrieve the voice channel you're currently in.

        Raises
        ------
        RPCException
            Retrieving the current voice channel failed.

        Returns
        -------
        Optional[:class:`GuildChannel`]
            The voice channel you're currently in, if any.
        """
        payload: GetSelectedVoiceChannelRequestPayload = {}
        data: GetSelectedVoiceChannelResponsePayload = await self._transport.send_command(
            'GET_SELECTED_VOICE_CHANNEL', payload
        )
        if data is None:
            return None

        return GuildChannel(data=data, state=self._connection)

    async def select_text_channel(
        self, channel_id: Optional[int], *, timeout: Optional[int] = None
    ) -> Optional[GuildChannel]:
        """|coro|

        Navigates to a text channel.

        Parameters
        ----------
        channel_id: Optional[:class:`int`]
            The ID of the channel to navigate to.
            Pass ``None`` to leave the current text channel.
        timeout: Optional[:class:`float`]
            A timeout for navigating text channel in milliseconds.

        Raises
        ------
        RPCException
            Navigating to text channel failed.

        Returns
        -------
        Optional[:class:`GuildChannel`]
            The text channel that you navigated to.
        """
        payload: SelectTextChannelRequestPayload = {'channel_id': None if channel_id is None else str(channel_id)}
        if timeout is not None:
            payload['timeout'] = timeout

        data: SelectTextChannelResponsePayload = await self._transport.send_command('SELECT_TEXT_CHANNEL', payload)
        if data is None:
            return None

        return GuildChannel(data=data, state=self._connection)

    async def fetch_voice_settings(self) -> VoiceSettings:
        """|coro|

        Retrieve your voice settings.

        Raises
        ------
        RPCException
            Retrieving voice settings failed.

        Returns
        -------
        :class:`VoiceSettings`
            The voice settings.
        """
        payload: GetVoiceSettingsRequestPayload = {}

        data: GetVoiceSettingsResponsePayload = await self._transport.send_command('GET_VOICE_SETTINGS', payload)
        return VoiceSettings(data=data, state=self._connection)

    async def edit_voice_settings_2(
        self,
        *,
        input_mode_type: VoiceSettingsModeType = MISSING,
        input_mode_shortcut: str = MISSING,
        self_mute: bool = MISSING,
        self_deaf: bool = MISSING,
    ) -> None:
        """|coro|

        Edits the voice settings.

        All parameters are optional.

        Parameters
        ----------
        input_mode_type: :class:`VoiceSettingsModeType`
            The new type of input mode.
        input_mode_shortcut: :class:`str`
            The new shortcut of input mode.
        deaf: :class:`bool`
            Indicates if you should be deafened by your accord.
        mute: :class:`bool`
            Indicates if you should be muted by your accord.

        Raises
        ------
        RPCException
            Editing the voice settings failed.
        """
        payload: SetVoiceSettings2RequestPayload = {}

        input_mode: Dict[str, Any] = {}

        if input_mode_type is not MISSING:
            input_mode['type'] = input_mode_type.value

        if input_mode_shortcut is not MISSING:
            input_mode['shortcut'] = input_mode_shortcut

        if input_mode:
            payload['input_mode'] = input_mode  # type: ignore

        if self_mute is not MISSING:
            payload['self_mute'] = self_mute

        if self_deaf is not MISSING:
            payload['self_deaf'] = self_deaf

        await self._transport.send_command('SET_VOICE_SETTINGS_2', payload)

    async def edit_voice_settings(
        self,
        *,
        input: VoiceIOSettings = MISSING,
        output: VoiceIOSettings = MISSING,
        mode: PartialVoiceSettingsMode = MISSING,
        automatic_gain_control: bool = MISSING,
        echo_cancellation: bool = MISSING,
        noise_suppression: bool = MISSING,
        qos: bool = MISSING,
        silence_warning: bool = MISSING,
        deaf: bool = MISSING,
        mute: bool = MISSING,
    ) -> VoiceSettings:
        """|coro|

        Edits the voice settings.

        All parameters are optional.

        Parameters
        ----------
        input: :class:`VoiceIOSettings`
            The new input settings.
        output: :class:`VoiceIOSettings`
            The new output settings.
        mode: :class:`VoiceSettingsMode`
            The new voice mode settings.
        automatic_gain_control: :class:`bool`
            Indicates if automatic gain control is enabled.
        echo_cancellation: :class:`bool`
            Indicates if echo cancellation is enabled.
        noise_suppression: :class:`bool`
            Indicates if the background noise is being suppressed.
        qos: :class:`bool`
            Indicates if Voice Quality of Service (QoS) is enabled.
        silence_warning: :class:`bool`
            Indicates if the silence warning notice is disabled.
        deaf: :class:`bool`
            Indicates if the user is deafened by their accord.
        mute: :class:`bool`
            Indicates if the user is muted by their accord.

        Raises
        ------
        RPCException
            Editing the voice settings failed.

        Returns
        -------
        :class:`VoiceSettings`
            The newly updated voice settings.
        """

        payload: SetVoiceSettingsRequestPayload = {}

        if input is not MISSING:
            payload['input'] = input.to_partial_dict()
        if output is not MISSING:
            payload['output'] = output.to_partial_dict()
        if mode is not MISSING:
            payload['mode'] = mode.to_dict()
        if automatic_gain_control is not MISSING:
            payload['automatic_gain_control'] = automatic_gain_control
        if echo_cancellation is not MISSING:
            payload['echo_cancellation'] = echo_cancellation
        if noise_suppression is not MISSING:
            payload['noise_suppression'] = noise_suppression
        if qos is not MISSING:
            payload['qos'] = qos
        if silence_warning is not MISSING:
            payload['silence_warning'] = silence_warning
        if deaf is not MISSING:
            payload['deaf'] = deaf
        if mute is not MISSING:
            payload['mute'] = mute

        data: SetVoiceSettingsResponsePayload = await self._transport.send_command('SET_VOICE_SETTINGS', payload)
        return VoiceSettings(data=data, state=self._connection)

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
        activity: Optional[Union[:class:`~discord.BaseActivity`, :class:`~discord.Spotify`]]
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
        to: :class:`~discord.abc.Snowflake`
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
        await self._transport.send_command('SEND_ACTIVITY_JOIN_INVITE', payload)

    async def reject_activity_join_request(self, from_: Snowflake) -> None:
        """|coro|

        Rejects an activity join request from the target user.

        Parameters
        ----------
        from_: :class:`~discord.abc.Snowflake`
            The user to reject the join request from.

        """
        payload: CloseActivityJoinRequestPayload = {'user_id': str(from_.id)}
        await self._transport.send_command('CLOSE_ACTIVITY_JOIN_REQUEST', payload)

    async def send_activity_invite(self, to: Snowflake, *, content: Optional[str] = None) -> None:
        """|coro|

        Sends an activity invite to target user.

        Parameters
        ----------
        to: :class:`~discord.abc.Snowflake`
            The user to send invite to.
        content: Optional[:class:`str`]
            The content to send with the invite.

        Raises
        ------
        RPCException
            Sending the invite failed.
        """
        payload: ActivityInviteUserRequestPayload = {
            'user_id': str(to.id),
            'type': 1,
            'pid': self.pid,
        }
        if content is not None:
            payload['content'] = content

        await self._transport.send_command('ACTIVITY_INVITE_USER', payload)

    async def accept_activity_invite(
        self,
        from_: Snowflake,
        *,
        session_id: str,
        channel_id: int,
        message_id: int,
        application_id: Optional[int] = None,
    ) -> None:
        """|coro|

        Sends an activity invite to target user.

        Parameters
        ----------
        to: :class:`~discord.abc.Snowflake`
            The user to send invite to.
        content: Optional[:class:`str`]
            The content to send with the invite.

        Raises
        ------
        RPCException
            Sending the invite failed.
        """
        payload: AcceptActivityInviteRequestPayload = {
            'type': 1,
            'user_id': str(from_.id),
            'session_id': session_id,
            'channel_id': str(channel_id),
            'message_id': str(message_id),
        }
        if application_id is not None:
            payload['application_id'] = str(application_id)

        await self._transport.send_command('ACCEPT_ACTIVITY_INVITE', payload)

    async def open_invite_dialog(self) -> None:
        """|coro|

        Opens a modal to invite someone to the current voice channel.

        Raises
        ------
        RPCException
            Opening the modal failed.
        """
        payload: OpenInviteDialogRequestPayload = {}
        await self._transport.send_command('OPEN_INVITE_DIALOG', payload)

    async def open_share_moment_dialog(self, *, media_url: str) -> None:
        """|coro|

        Opens a modal to share media to a channel.

        Parameters
        ----------
        media_url: :class:`str`
            The URL to the media.

        Raises
        ------
        RPCException
            Opening the modal failed.
        """
        payload: OpenShareMomentDialogRequestPayload = {
            'mediaUrl': media_url,
        }
        await self._transport.send_command('OPEN_SHARE_MOMENT_DIALOG', payload)

    async def share_interaction(
        self,
        command: str,
        *,
        options: Optional[Dict[str, str]] = None,
        content: Optional[str] = None,
        require_launch_channel: Optional[bool] = None,
        preview_image: Optional[PreviewImage] = None,
        components: Optional[List[Optional[List[Button]]]] = None,
        pid: Optional[int] = MISSING,
    ) -> bool:
        """|coro|

        Shares an interaction.

        Parameters
        ----------
        command: :class:`str`
            The name of the command to share.
        options: Optional[Dict[:class:`str`, :class:`str`]]
            The options for the command.
        content: Optional[:class:`str`]
            The content. Can be only up to 2000 characters.
        require_launch_channel: Optional[:class:`bool`]
            Whether to require launching in channel.
        preview_image: Optional[:class:`PreviewImage`]
            The preview image.
        components: Optional[List[Optional[List[:class:`Button`]]]]
            The components. Rows can hold only up to 5 components.
        pid: Optional[:class:`int`]
            The ID of the process. If not provided, this defaults to :attr:`pid`.

        Raises
        ------
        RPCException
            Sharing the interaction failed.

        Returns
        -------
        :class:`bool`
            Whether the interaction was shared successfully.
        """
        if pid is MISSING:
            pid = self.pid

        payload: ShareInteractionRequestPayload = {
            'command': command,
        }
        if options is not None:
            payload['options'] = [{'name': k, 'value': v} for k, v in options.items()]
        if content is not None:
            payload['content'] = content
        if require_launch_channel is not None:
            payload['require_launch_channel'] = require_launch_channel
        if preview_image is not None:
            payload['preview_image'] = preview_image.to_dict()
        if components is not None:
            transformed_components: List[ShareInteractionRequestComponentPayload] = []
            for row in components:
                if row is None:
                    transformed_components.append({'type': 1})
                else:
                    transformed_components.append(
                        {
                            'type': 1,
                            'components': [inner.to_dict() for inner in row],
                        }
                    )
            payload['components'] = transformed_components
        if pid is not None:
            payload['pid'] = pid

        data: ShareInteractionResponsePayload = await self._transport.send_command('SHARE_INTERACTION', payload)
        return data['success']

    async def initiate_image_upload(self) -> str:
        """|coro|

        Initiates the image upload flow.

        Raises
        ------
        RPCException
            Initiating the image upload failed.

        Returns
        -------
        :class:`str`
            The URL to the image that was uploaded.
        """
        payload: InitiateImageUploadRequestPayload = {}
        data: InitiateImageUploadResponsePayload = await self._transport.send_command('INITIATE_IMAGE_UPLOAD', payload)
        return data['image_url']

    async def share_link(
        self,
        message: str,
        *,
        custom_id: Optional[str] = None,
        link_id: Optional[str] = None,
    ) -> SharedLink:
        """|coro|

        Shares a link.

        Parameters
        ----------
        message: :class:`str`
            The message. Can be only up to 1000 characters.
        custom_id: Optional[:class:`str`]
            The developer-defined ID for the link. Can be only up to 64 characters.
        link_id: Optional[:class:`str`]
            The developer-defined ID for the link. Can be only up to 64 characters.

        Raises
        ------
        RPCException
            Sharing the link failed.

        Returns
        -------
        :class:`SharedLink`
            The result of sharing link.
        """

        payload: ShareLinkRequestPayload = {'message': message}
        if custom_id is not None:
            payload['custom_id'] = custom_id
        if link_id is not None:
            payload['link_id'] = link_id

        data: ShareLinkResponsePayload = await self._transport.send_command('SHARE_LINK', payload)
        return SharedLink(data)

    async def open_invite_modal(self, code: str) -> Tuple[str, Invite]:
        """|coro|

        Opens a invite modal in the Discord client.

        Parameters
        ----------
        code: :class:`str`
            The code.

        Raises
        ------
        RPCException
            Opening the invite modal failed.

        Returns
        -------
        Tuple[:class:`str`, :class:`~discord.Invite`]
            The invite.
        """
        payload: InviteBrowserRequestPayload = {'code': code}
        data: InviteBrowserResponsePayload = await self._transport.send_command('INVITE_BROWSER', payload)

        return data['code'], Invite.from_incomplete(data=data['invite'], state=self._connection)

    async def deep_link(self, location: DeepLinkLocation, *, params: Any = MISSING) -> Optional[bool]:
        """|coro|

        Opens a deep link.

        Parameters
        ----------
        location: :class:`DeepLinkLocation`
            The location.
        params: Any
            The parameters for the deep link.

        Raises
        ------
        RPCException
            Opening the deep link failed.

        Returns
        -------
        Optional[:class:`bool`]
            Unknown.
        """

        payload: DeepLinkRequestPayload = {
            'type': location.value,
        }
        if params is not MISSING:
            payload['params'] = params

        data: DeepLinkResponsePayload = await self._transport.send_command('DEEP_LINK', payload)
        return data

    async def trigger_connections_callback(
        self,
        code: str,
        *,
        type: ConnectionType,
        openid_params: Optional[str] = None,
        issuer: Optional[str] = None,
        state: str,
    ) -> None:
        """|coro|

        Triggers the connections callback.

        Parameters
        ----------
        code: :class:`str`
            The code.
        type: :class:`~discord.ConnectionType`
            The connection type.
        openid_params: Optional[:class:`str`]
            The OpenID parameters.
        issuer: Optional[:class:`str`]
            The issuer.
        state: :class:`str`
            The state.

        Raises
        ------
        RPCException
            Triggering the connections callback failed.
        """
        payload: ConnectionsCallbackRequestPayload = {
            'providerType': type.value,
            'code': code,
            'state': state,
        }
        if openid_params is not None:
            payload['openid_params'] = openid_params
        if issuer is not None:
            payload['iss'] = issuer

        await self._transport.send_command('CONNECTIONS_CALLBACK', payload)

    async def trigger_billing_popup_bridge_callback(
        self,
        path: str,
        *,
        payment_source_type: PaymentSourceType,
        query: Optional[Dict[str, str]] = None,
        state: str,
    ) -> ResponsePayload:
        """|coro|

        Triggers the billing popup bridge callback.

        Parameters
        ----------
        path: :class:`str`
            The path.
        payment_source_type: :class:`~discord.PaymentSourceType`
            The payment source type.
        query: Optional[Dict[:class:`str`, :class:`str`]]
            The parameters.
        state: :class:`str`
            The state.

        Raises
        ------
        RPCException
            Triggering the billing popup bridge callback failed.
        """
        payload: BillingPopupBridgeCallbackRequestPayload = {
            'state': state,
            'path': path,
            'payment_source_type': payment_source_type.value,
        }
        if query is not None:
            payload['query'] = query

        data: BillingPopupBridgeCallbackResponsePayload = await self._transport.send_command(
            'BILLING_POPUP_BRIDGE_CALLBACK', payload
        )
        return data

    async def trigger_braintree_popup_bridge_callback(
        self,
        path: str,
        *,
        payment_source_type: PaymentSourceType,
        query: Optional[Dict[str, str]] = None,
        state: str,
    ) -> ResponsePayload:
        """|coro|

        Triggers the Braintree popup bridge callback.

        Parameters
        ----------
        path: :class:`str`
            The path.
        query: Optional[Dict[:class:`str`, :class:`str`]]
            The parameters.
        state: :class:`str`
            The state.

        Raises
        ------
        RPCException
            Triggering the Braintree popup bridge callback failed.
        """
        payload: BraintreePopupBridgeCallbackRequestPayload = {
            'state': state,
            'path': path,
        }
        if query is not None:
            payload['query'] = query

        data: BraintreePopupBridgeCallbackResponsePayload = await self._transport.send_command(
            'BRAINTREE_POPUP_BRIDGE_CALLBACK', payload
        )
        return data

    async def fetch_gift(self, code: str) -> Gift:
        """|coro|

        Retrieves a gift.

        Parameters
        ----------
        code: :class:`str`
            The code of the gift.

        Raises
        ------
        RPCException
            Retrieving the gift failed.

        Returns
        -------
        :class:`~discord.Gift`
            The gift.
        """
        payload: GiftCodeBrowserRequestPayload = {'code': code}
        data: GiftCodeBrowserResponsePayload = await self._transport.send_command('GIFT_CODE_BROWSER', payload)

        return Gift(data=data['giftCode'], state=self._connection)
