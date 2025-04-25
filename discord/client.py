"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from __future__ import annotations

import asyncio
import datetime
import logging
from typing import (
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Dict,
    Generator,
    List,
    Literal,
    Optional,
    Sequence,
    Tuple,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
    overload,
)

import aiohttp

from .activity import BaseActivity, Spotify, ActivityTypes, Session, HeadlessSession, create_activity
from .appinfo import AppInfo
from .backoff import ExponentialBackoff
from .channel import PartialMessageable
from .client_properties import ClientProperties, DefaultClientProperties
from .connections import Connection
from .emoji import Emoji
from .enums import ChannelType, Status, RelationshipType, ClientType
from .errors import *
from .flags import ApplicationFlags, Intents
from .gateway import *
from .guild import UserGuild, Guild
from .http import HTTPClient
from .invite import Invite
from .lobby import Lobby
from .mentions import AllowedMentions
from .object import Object
from .sku import Entitlement
from .soundboard import SoundboardSound
from .stage_instance import StageInstance
from .state import ConnectionState
from .sticker import GuildSticker
from .threads import Thread
from .template import Template
from .user import _UserTag, User, ClientUser
from .utils import (
    MISSING,
    SequenceProxy,
    resolve_invite,
    resolve_template,
    setup_logging,
    time_snowflake,
)
from .voice_client import VoiceClient
from .widget import Widget


if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self

    from .abc import Messageable, PrivateChannel, Snowflake, SnowflakeTime
    from .automod import AutoModAction, AutoModRule
    from .channel import DMChannel, GroupChannel, EphemeralDMChannel
    from .ext.commands import Bot, Context, CommandError
    from .game_relationship import GameRelationship
    from .guild import GuildChannel
    from .integrations import Integration
    from .member import Member, VoiceState
    from .message import Message, LobbyMessage
    from .poll import PollAnswer
    from .raw_models import (
        RawAppCommandPermissionsUpdateEvent,
        RawBulkMessageDeleteEvent,
        RawIntegrationDeleteEvent,
        RawMemberRemoveEvent,
        RawMessageDeleteEvent,
        RawMessageUpdateEvent,
        RawReactionActionEvent,
        RawReactionClearEmojiEvent,
        RawReactionClearEvent,
        RawThreadDeleteEvent,
        RawThreadMembersUpdate,
        RawThreadUpdateEvent,
        RawTypingEvent,
        RawPollVoteActionEvent,
    )
    from .reaction import Reaction
    from .relationship import Relationship
    from .role import Role
    from .settings import UserSettings, AudioSettingsManager
    from .scheduled_event import ScheduledEvent
    from .subscription import Subscription
    from .threads import ThreadMember
    from .types.guild import Guild as GuildPayload
    from .voice_client import VoiceProtocol


# fmt: off
__all__ = (
    'Client',
)
# fmt: on

T = TypeVar('T')
Coro = Coroutine[Any, Any, T]
CoroT = TypeVar('CoroT', bound=Callable[..., Coro[Any]])

_log = logging.getLogger(__name__)


class _LoopSentinel:
    __slots__ = ()

    def __getattr__(self, attr: str) -> None:
        msg = (
            'loop attribute cannot be accessed in non-async contexts. '
            'Consider using either an asynchronous main function and passing it to asyncio.run or '
            'using asynchronous initialisation hooks such as Client.setup_hook'
        )
        raise AttributeError(msg)


_loop: Any = _LoopSentinel()


class Client:
    r"""Represents a client connection that connects to Discord.
    This class is used to interact with the Discord WebSocket and API.

    .. container:: operations

        .. describe:: async with x

            Asynchronously initialises the client and automatically cleans up.

            .. versionadded:: 2.0

    A number of options can be passed to the :class:`Client`.

    Parameters
    ----------
    max_messages: Optional[:class:`int`]
        The maximum number of messages to store in the internal message cache.
        This defaults to ``1000``. Passing in ``None`` disables the message cache.

        .. versionchanged:: 1.3
            Allow disabling the message cache and change the default size to ``1000``.
    max_lobby_messages: Optional[:class:`int`]
        The maximum number of lobby messages to store in the internal lobby message cache.
        This defaults to ``1000``. Passing in ``None`` disables the lobby message cache.
    proxy: Optional[:class:`str`]
        Proxy URL.
    proxy_auth: Optional[:class:`aiohttp.BasicAuth`]
        An object that represents proxy HTTP Basic Authorization.
    application_id: :class:`int`
        The client's application ID.
    intents: Optional[:class:`Intents`]
        The intents that you want to enable for the session. This is a way of
        disabling and enabling certain Gateway events from triggering and being sent.

        .. versionadded:: 1.5

        .. versionchanged:: 2.0
            Parameter is now required.
    member_cache_flags: :class:`MemberCacheFlags`
        Allows for finer control over how the library caches members.
        If not given, defaults to cache as much as possible with the
        currently selected intents.

        .. versionadded:: 1.5
    chunk_guilds_at_startup: :class:`bool`
        Indicates if :func:`.on_ready` should be delayed to chunk all guilds
        at start-up if necessary. This operation is incredibly slow for large
        amounts of guilds. The default is ``True`` if :attr:`Intents.members`
        is ``True``.

        .. versionadded:: 1.5
    status: Optional[:class:`.Status`]
        A status to start your presence with upon logging on to Discord.
    activity: Optional[:class:`.BaseActivity`]
        An activity to start your presence with upon logging on to Discord.
    allowed_mentions: Optional[:class:`AllowedMentions`]
        Control how the client handles mentions by default on every message sent.

        .. versionadded:: 1.4
    heartbeat_timeout: :class:`float`
        The maximum numbers of seconds before timing out and restarting the
        WebSocket in the case of not receiving a HEARTBEAT_ACK. Useful if
        processing the initial packets take too long to the point of disconnecting
        you. The default timeout is 60 seconds.
    assume_unsync_clock: :class:`bool`
        Whether to assume the system clock is unsynced. This applies to the ratelimit handling
        code. If this is set to ``True``, the default, then the library uses the time to reset
        a rate limit bucket given by Discord. If this is ``False`` then your system clock is
        used to calculate how long to sleep for. If this is set to ``False`` it is recommended to
        sync your system clock to Google's NTP server.

        .. versionadded:: 1.3
    enable_debug_events: :class:`bool`
        Whether to enable events that are useful only for debugging gateway related information.

        Right now this involves :func:`on_socket_raw_receive` and :func:`on_socket_raw_send`. If
        this is ``False`` then those events will not be dispatched (due to performance considerations).
        To enable these events, this must be set to ``True``. Defaults to ``False``.

        .. versionadded:: 2.0
    enable_raw_presences: :class:`bool`
        Whether to manually enable or disable the :func:`on_raw_presence_update` event.

        Setting this flag to ``True`` requires :attr:`Intents.presences` to be enabled.

        By default, this flag is set to ``True`` only when :attr:`Intents.presences` is enabled and :attr:`Intents.members`
        is disabled, otherwise it's set to ``False``.

        .. versionadded:: 2.5
    http_trace: :class:`aiohttp.TraceConfig`
        The trace configuration to use for tracking HTTP requests the library does using ``aiohttp``.
        This allows you to check requests the library is using. For more information, check the
        `aiohttp documentation <https://docs.aiohttp.org/en/stable/client_advanced.html#client-tracing>`_.

        .. versionadded:: 2.0
    max_ratelimit_timeout: Optional[:class:`float`]
        The maximum number of seconds to wait when a non-global rate limit is encountered.
        If a request requires sleeping for more than the seconds passed in, then
        :exc:`~discord.RateLimited` will be raised. By default, there is no timeout limit.
        In order to prevent misuse and unnecessary bans, the minimum value this can be
        set to is ``30.0`` seconds.

        .. versionadded:: 2.0
    connector: Optional[:class:`aiohttp.BaseConnector`]
        The aiohttp connector to use for this client. This can be used to control underlying aiohttp
        behavior, such as setting a dns resolver or sslcontext.

        .. versionadded:: 2.5

    Attributes
    ----------
    ws
        The websocket gateway the client is currently connected to. Could be ``None``.
    """

    def __init__(self, *, intents: Optional[Intents] = None, **options: Any) -> None:
        self.loop: asyncio.AbstractEventLoop = _loop
        # self.ws is set in the connect method
        self.ws: DiscordWebSocket = None  # type: ignore
        self._listeners: Dict[str, List[Tuple[asyncio.Future, Callable[..., bool]]]] = {}

        properties = options.get('client_properties')
        if properties is None:
            properties = DefaultClientProperties()

        connector: Optional[aiohttp.BaseConnector] = options.get('connector', None)
        proxy: Optional[str] = options.pop('proxy', None)
        proxy_auth: Optional[aiohttp.BasicAuth] = options.pop('proxy_auth', None)
        unsync_clock: bool = options.pop('assume_unsync_clock', True)
        http_trace: Optional[aiohttp.TraceConfig] = options.pop('http_trace', None)
        max_ratelimit_timeout: Optional[float] = options.pop('max_ratelimit_timeout', None)

        self.http: HTTPClient = HTTPClient(
            self.loop,
            connector,
            client_properties=properties,
            proxy=proxy,
            proxy_auth=proxy_auth,
            unsync_clock=unsync_clock,
            http_trace=http_trace,
            max_ratelimit_timeout=max_ratelimit_timeout,
        )
        self.properties: ClientProperties = properties

        self._handlers: Dict[str, Callable[..., None]] = {
            'ready': self._handle_ready,
        }

        self._hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = {
            'before_identify': self._call_before_identify_hook,
        }

        self._enable_debug_events: bool = options.pop('enable_debug_events', False)
        self._connection: ConnectionState[Self] = self._get_state(intents=intents, **options)
        self._closing_task: Optional[asyncio.Task[None]] = None
        self._ready: asyncio.Event = MISSING
        self._application: Optional[AppInfo] = None
        self._connection._get_websocket = self._get_websocket
        self._connection._get_client = lambda: self

        if VoiceClient.warn_nacl:
            VoiceClient.warn_nacl = False
            _log.warning("PyNaCl is not installed, voice will NOT be supported")

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

    # internals

    def _get_websocket(self, guild_id: Optional[int] = None) -> DiscordWebSocket:
        return self.ws

    def _get_state(self, **options: Any) -> ConnectionState[Self]:
        return ConnectionState(dispatch=self.dispatch, handlers=self._handlers, hooks=self._hooks, http=self.http, **options)

    def _handle_ready(self) -> None:
        self._ready.set()

    @property
    def latency(self) -> float:
        """:class:`float`: Measures latency between a HEARTBEAT and a HEARTBEAT_ACK in seconds.

        This could be referred to as the Discord WebSocket protocol latency.
        """
        ws = self.ws
        return float('nan') if not ws else ws.latency

    def is_ws_ratelimited(self) -> bool:
        """:class:`bool`: Whether the websocket is currently rate limited.

        This can be useful to know when deciding whether you should query members
        using HTTP or via the gateway.

        .. versionadded:: 1.6
        """
        if self.ws:
            return self.ws.is_ratelimited()
        return False

    @property
    def user(self) -> Optional[ClientUser]:
        """Optional[:class:`.ClientUser`]: Represents the connected client. ``None`` if not logged in."""
        return self._connection.user

    @property
    def guilds(self) -> Sequence[Guild]:
        """Sequence[:class:`.Guild`]: The guilds that the connected client is a member of."""
        return self._connection.guilds

    @property
    def lobbies(self) -> Sequence[Lobby]:
        """Sequence[:class:`.Lobby`]: The lobbies that the connected client is a member of."""
        return self._connection.lobbies

    @property
    def emojis(self) -> Sequence[Emoji]:
        """Sequence[:class:`.Emoji`]: The emojis that the connected client has.

        .. note::

            This not include the emojis that are owned by the application.
            Use :meth:`.fetch_application_emoji` to get those.
        """
        return self._connection.emojis

    @property
    def stickers(self) -> Sequence[GuildSticker]:
        """Sequence[:class:`.GuildSticker`]: The stickers that the connected client has.

        .. versionadded:: 2.0
        """
        return self._connection.stickers

    @property
    def sessions(self) -> Sequence[Session]:
        """Sequence[:class:`.Session`]: The gateway sessions that the current user is connected in with.

        When connected, this includes a representation of the library's session and an "all" session representing the user's overall presence.
        """
        return SequenceProxy(self._connection._sessions.values())

    @property
    def soundboard_sounds(self) -> List[SoundboardSound]:
        """List[:class:`.SoundboardSound`]: The soundboard sounds that the connected client has.

        .. versionadded:: 2.5
        """
        return self._connection.soundboard_sounds

    @property
    def cached_messages(self) -> Sequence[Message]:
        """Sequence[:class:`.Message`]: Read-only list of messages the connected client has cached.

        .. versionadded:: 1.1
        """
        return SequenceProxy(self._connection._messages or [])

    @property
    def cached_lobby_messages(self) -> Sequence[LobbyMessage]:
        """Sequence[:class:`.LobbyMessage`]: Read-only list of lobby messages the connected client has cached."""
        return SequenceProxy(self._connection._lobby_messages or [])

    @property
    def private_channels(self) -> Sequence[PrivateChannel]:
        """Sequence[:class:`.abc.PrivateChannel`]: The private channels that the connected client is participating on.

        .. note::

            This returns only up to 128 most recent private channels due to an internal working
            on how Discord deals with private channels.
        """
        return self._connection.private_channels

    @property
    def relationships(self) -> Sequence[Relationship]:
        """Sequence[:class:`.Relationship`]: Returns all the relationships that the connected client has."""
        return SequenceProxy(self._connection._relationships.values())

    @property
    def game_relationships(self) -> Sequence[GameRelationship]:
        """Sequence[:class:`.GameRelationship`]: Returns all the game relationships that the connected client has."""
        return SequenceProxy(self._connection._game_relationships.values())

    @property
    def friends(self) -> List[Relationship]:
        """List[:class:`.Relationship`]: Returns all the users that the connected client is friends with."""
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.friend]

    @property
    def incoming_friend_requests(self) -> List[Relationship]:
        """List[:class:`.Relationship`]: Returns all the users that the connected client has friend request from."""
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.incoming_request]

    @property
    def outgoing_friend_requests(self) -> List[Relationship]:
        """List[:class:`.Relationship`]: Returns all the users that the connected client has sent friend request to."""
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.outgoing_request]

    @property
    def game_friends(self) -> List[GameRelationship]:
        """List[:class:`.GameRelationship`]: Returns all the users that the connected client is friends with in-game."""
        return [r for r in self._connection._game_relationships.values() if r.type is RelationshipType.friend]

    @property
    def incoming_game_friend_requests(self) -> List[GameRelationship]:
        """List[:class:`.GameRelationship`]: Returns all the users that the connected client has game friend request from."""
        return [r for r in self._connection._game_relationships.values() if r.type is RelationshipType.incoming_request]

    @property
    def outgoing_game_friend_requests(self) -> List[GameRelationship]:
        """List[:class:`.GameRelationship`]: Returns all the users that the connected client has sent game friend request."""
        return [r for r in self._connection._game_relationships.values() if r.type is RelationshipType.outgoing_request]

    @property
    def blocked(self) -> List[Relationship]:
        """List[:class:`.Relationship`]: Returns all the users that the connected client has blocked."""
        return [r for r in self._connection._relationships.values() if r.type is RelationshipType.blocked]

    def get_game_relationship(self, user_id: int, /) -> Optional[GameRelationship]:
        """Retrieves the :class:`.GameRelationship`, if applicable.

        Parameters
        ----------
        user_id: :class:`int`
            The user ID to check if we have a game relationship with them.

        Returns
        -------
        Optional[:class:`.GameRelationship`]
            The game relationship, if available.
        """
        return self._connection._game_relationships.get(user_id)

    def get_relationship(self, user_id: int, /) -> Optional[Relationship]:
        """Retrieves the :class:`.Relationship`, if applicable.

        Parameters
        ----------
        user_id: :class:`int`
            The user ID to check if we have a relationship with them.

        Returns
        -------
        Optional[:class:`.Relationship`]
            The relationship, if available.
        """
        return self._connection._relationships.get(user_id)

    @property
    def settings(self) -> UserSettings:
        """:class:`.UserSettings`: Returns the user's settings."""
        return self._connection.settings

    @property
    def audio_settings(self) -> AudioSettingsManager:
        """:class:`.AudioSettingsManager`: Returns the manager for user's audio settings."""
        return self._connection._audio_settings

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        """List[:class:`.VoiceProtocol`]: Represents a list of voice connections.

        These are usually :class:`.VoiceClient` instances.
        """
        return self._connection.voice_clients

    @property
    def application_id(self) -> Optional[int]:
        """Optional[:class:`int`]: The client's application ID.

        If this is not passed via ``__init__`` then this is retrieved
        through the gateway when an event contains the data or after a call
        to :meth:`~discord.Client.login`. Usually after :func:`~discord.on_connect`
        is called.

        .. versionadded:: 2.0
        """
        return self._connection.application_id or 0

    @property
    def application_name(self) -> str:
        """:class:`str`: The client's application name."""
        return self._connection.application_name or ''

    @property
    def application_flags(self) -> ApplicationFlags:
        """:class:`~discord.ApplicationFlags`: The client's application flags.

        .. versionadded:: 2.0
        """
        return self._connection.application_flags or ApplicationFlags()

    @property
    def application(self) -> Optional[AppInfo]:
        """Optional[:class:`~discord.AppInfo`]: The client's application info.

        This is retrieved on :meth:`~discord.Client.login` and is not updated
        afterwards. This allows populating the application_id without requiring a
        gateway connection.

        This is ``None`` if accessed before :meth:`~discord.Client.login` is called.

        .. seealso:: The :meth:`~discord.Client.application_info` API call

        .. versionadded:: 2.0
        """
        return self._application

    @property
    def disclose(self) -> Sequence[str]:
        """Sequence[:class:`str`]: Upcoming changes to the user's account."""
        return SequenceProxy(self._connection.disclose)

    @property
    def av_sf_protocol_floor(self) -> int:
        """:class:`int`: The minimum DAVE version. Currently ``-1``."""
        return self._connection.av_sf_protocol_floor

    @property
    def scopes(self) -> Tuple[str, ...]:
        """Tuple[:class:`str`, ...]: The OAuth2 scopes the connected client has."""
        return self._connection.scopes

    def is_ready(self) -> bool:
        """:class:`bool`: Specifies if the client's internal cache is ready for use."""
        return self._ready is not MISSING and self._ready.is_set()

    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # Schedules the task
        return self.loop.create_task(wrapped, name=f'discord.py: {event_name}')

    def dispatch(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        _log.debug('Dispatching event %s', event)
        method = 'on_' + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        """|coro|

        The default error handler provided by the client.

        By default this logs to the library logger however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.

        .. versionchanged:: 2.0

            ``event_method`` parameter is now positional-only
            and instead of writing to ``sys.stderr`` it logs instead.
        """
        _log.exception('Ignoring exception in %s', event_method)

    # hooks

    async def _call_before_identify_hook(self, *, initial: bool = False) -> None:
        # This hook is an internal hook that actually calls the public one.
        # It allows the library to have its own hook without stepping on the
        # toes of those who need to override their own hook.
        await self.before_identify_hook(initial=initial)

    async def before_identify_hook(self, *, initial: bool = False) -> None:
        """|coro|

        A hook that is called before IDENTIFYing a session. This is useful
        if you wish to have more control over the synchronization of multiple
        IDENTIFYing clients.

        The default implementation sleeps for 5 seconds.

        .. versionadded:: 1.4

        Parameters
        ----------
        initial: :class:`bool`
            Whether this IDENTIFY is the first initial IDENTIFY.
        """

        if not initial:
            await asyncio.sleep(5.0)

    async def _async_setup_hook(self) -> None:
        # Called whenever the client needs to initialise asyncio objects with a running loop
        loop = asyncio.get_running_loop()
        self.loop = loop
        self.http.loop = loop
        self._connection.loop = loop
        self._ready = asyncio.Event()
        await self.properties.setup()

    async def setup_hook(self) -> None:
        """|coro|

        A coroutine to be called to setup the bot, by default this is blank.

        To perform asynchronous setup after the bot is logged in but before
        it has connected to the Websocket, overwrite this coroutine.

        This is only called once, in :meth:`login`, and will be called before
        any events are dispatched, making it a better solution than doing such
        setup in the :func:`~discord.on_ready` event.

        .. warning::

            Since this is called *before* the websocket connection is made therefore
            anything that waits for the websocket will deadlock, this includes things
            like :meth:`wait_for` and :meth:`wait_until_ready`.

        .. versionadded:: 2.0
        """
        pass

    # login state management

    async def login(self, token: str) -> None:
        """|coro|

        Logs in the client with the specified credentials and
        calls the :meth:`setup_hook`.


        Parameters
        ----------
        token: :class:`str`
            The authentication token. Do not prefix this token with
            anything as the library will do it for you.

        Raises
        ------
        LoginFailure
            The wrong credentials are passed.
        HTTPException
            An unknown HTTP related error occurred,
            usually when it isn't 200 or the known incorrect credentials
            passing status code.
        """

        _log.info('logging in using static token')

        if self.loop is _loop:
            await self._async_setup_hook()

        if not isinstance(token, str):
            raise TypeError(f'expected token to be a str, received {token.__class__.__name__} instead')
        token = token.strip()

        data = await self.http.static_login(token)
        self._connection.user = ClientUser(state=self._connection, data=data)
        await self.setup_hook()

    async def connect(self, *, reconnect: bool = True) -> None:
        """|coro|

        Creates a websocket connection and lets the websocket listen
        to messages from Discord. This is a loop that runs the entire
        event system and miscellaneous aspects of the library. Control
        is not resumed until the WebSocket connection is terminated.

        Parameters
        ----------
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid intents or bad tokens).

        Raises
        ------
        GatewayNotFound
            If the gateway to connect to Discord is not found. Usually if this
            is thrown then there is a Discord API outage.
        ConnectionClosed
            The websocket connection has been terminated.
        """

        backoff = ExponentialBackoff()
        ws_params: Dict[str, Any] = {
            'initial': True,
        }
        while not self.is_closed():
            try:
                coro = DiscordWebSocket.from_client(self, **ws_params)
                self.ws = await asyncio.wait_for(coro, timeout=60.0)
                ws_params['initial'] = False
                while True:
                    await self.ws.poll_event()
            except ReconnectWebSocket as e:
                _log.debug('Got a request to %s the websocket.', e.op)
                self.dispatch('disconnect')
                ws_params.update(sequence=self.ws.sequence, resume=e.resume, session=self.ws.session_id)
                if e.resume:
                    ws_params['gateway'] = self.ws.gateway
                continue
            except (
                OSError,
                HTTPException,
                GatewayNotFound,
                ConnectionClosed,
                aiohttp.ClientError,
                asyncio.TimeoutError,
            ) as exc:
                self.dispatch('disconnect')
                if not reconnect:
                    await self.close()
                    if isinstance(exc, ConnectionClosed) and exc.code == 1000:
                        # clean close, don't re-raise this
                        return
                    raise

                if self.is_closed():
                    return

                # If we get connection reset by peer then try to RESUME
                if isinstance(exc, OSError) and exc.errno in (54, 10054):
                    ws_params.update(
                        sequence=self.ws.sequence,
                        gateway=self.ws.gateway,
                        initial=False,
                        resume=True,
                        session=self.ws.session_id,
                    )
                    continue

                # We should only get this when an unhandled close code happens,
                # such as a clean disconnect (1000) or a bad state (bad token, bad intents, etc)
                # sometimes, discord sends us 1000 for unknown reasons so we should reconnect
                # regardless and rely on is_closed instead
                if isinstance(exc, ConnectionClosed):
                    if exc.code == 4014:
                        raise PrivilegedIntentsRequired() from None
                    if exc.code != 1000:
                        await self.close()
                        raise

                retry = backoff.delay()
                _log.exception("Attempting a reconnect in %.2fs", retry)
                await asyncio.sleep(retry)
                # Always try to RESUME the connection
                # If the connection is not RESUME-able then the gateway will invalidate the session.
                # This is apparently what the official Discord client does.
                ws_params.update(
                    sequence=self.ws.sequence,
                    gateway=self.ws.gateway,
                    resume=True,
                    session=self.ws.session_id,
                )

    async def close(self) -> None:
        """|coro|

        Closes the connection to Discord.
        """
        if self._closing_task:
            return await self._closing_task

        async def _close():
            await self._connection.close()

            if self.ws is not None and self.ws.open:
                await self.ws.close(code=1000)

            await self.http.close()

            if self._ready is not MISSING:
                self._ready.clear()

            self.loop = MISSING

        self._closing_task = asyncio.create_task(_close())
        await self._closing_task

    def clear(self) -> None:
        """Clears the internal state of the bot.

        After this, the bot can be considered "re-opened", i.e. :meth:`is_closed`
        and :meth:`is_ready` both return ``False`` along with the bot's internal
        cache cleared.
        """
        self._closing_task = None
        self._ready.clear()
        self._connection.clear()
        self.http.clear()

    async def start(self, token: str, *, reconnect: bool = True) -> None:
        """|coro|

        A shorthand coroutine for :meth:`login` + :meth:`connect`.

        Parameters
        ----------
        token: :class:`str`
            The authentication token. Do not prefix this token with
            anything as the library will do it for you.
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid intents or bad tokens).

        Raises
        ------
        TypeError
            An unexpected keyword argument was received.
        """
        await self.login(token)
        await self.connect(reconnect=reconnect)

    def run(
        self,
        token: str,
        *,
        reconnect: bool = True,
        log_handler: Optional[logging.Handler] = MISSING,
        log_formatter: logging.Formatter = MISSING,
        log_level: int = MISSING,
        root_logger: bool = False,
    ) -> None:
        """A blocking call that abstracts away the event loop
        initialisation from you.

        If you want more control over the event loop then this
        function should not be used. Use :meth:`start` coroutine
        or :meth:`connect` + :meth:`login`.

        This function also sets up the logging library to make it easier
        for beginners to know what is going on with the library. For more
        advanced users, this can be disabled by passing ``None`` to
        the ``log_handler`` parameter.

        .. warning::

            This function must be the last function to call due to the fact that it
            is blocking. That means that registration of events or anything being
            called after this function call will not execute until it returns.

        Parameters
        ----------
        token: :class:`str`
            The authentication token. Do not prefix this token with
            anything as the library will do it for you.
        reconnect: :class:`bool`
            If we should attempt reconnecting, either due to internet
            failure or a specific failure on Discord's part. Certain
            disconnects that lead to bad state will not be handled (such as
            invalid intents or bad tokens).
        log_handler: Optional[:class:`logging.Handler`]
            The log handler to use for the library's logger. If this is ``None``
            then the library will not set up anything logging related. Logging
            will still work if ``None`` is passed, though it is your responsibility
            to set it up.

            The default log handler if not provided is :class:`logging.StreamHandler`.

            .. versionadded:: 2.0
        log_formatter: :class:`logging.Formatter`
            The formatter to use with the given log handler. If not provided then it
            defaults to a colour based logging formatter (if available).

            .. versionadded:: 2.0
        log_level: :class:`int`
            The default log level for the library's logger. This is only applied if the
            ``log_handler`` parameter is not ``None``. Defaults to ``logging.INFO``.

            .. versionadded:: 2.0
        root_logger: :class:`bool`
            Whether to set up the root logger rather than the library logger.
            By default, only the library logger (``'discord'``) is set up. If this
            is set to ``True`` then the root logger is set up as well.

            Defaults to ``False``.

            .. versionadded:: 2.0
        """

        async def runner():
            async with self:
                await self.start(token, reconnect=reconnect)

        if log_handler is not None:
            setup_logging(
                handler=log_handler,
                formatter=log_formatter,
                level=log_level,
                root=root_logger,
            )

        try:
            asyncio.run(runner())
        except KeyboardInterrupt:
            # nothing to do here
            # `asyncio.run` handles the loop cleanup
            # and `self.start` closes all sockets and the HTTPClient instance.
            return

    # properties

    def is_closed(self) -> bool:
        """:class:`bool`: Indicates if the websocket connection is closed."""
        return self._closing_task is not None

    @property
    def initial_activity(self) -> Optional[ActivityTypes]:
        """Optional[:class:`.BaseActivity`]: The primary activity set upon logging in.

        .. note::

            The client may be setting multiple activities, these can be accessed under :attr:`initial_activities`.
        """
        state = self._connection
        return create_activity(state._activities[0], state) if state._activities else None

    @initial_activity.setter
    def initial_activity(self, value: Optional[ActivityTypes]) -> None:
        if value is None:
            self._connection._activities = []
        elif isinstance(value, BaseActivity):
            self._connection._activities = [value.to_dict()]
        else:
            raise TypeError('activity must derive from BaseActivity')

    @property
    def initial_activities(self) -> List[ActivityTypes]:
        """List[:class:`.BaseActivity`]: The activities set upon logging in."""
        state = self._connection
        return [create_activity(activity, state) for activity in state._activities]

    @initial_activities.setter
    def initial_activities(self, values: Sequence[ActivityTypes]) -> None:
        if not values:
            self._connection._activities = []
        elif all(isinstance(value, (BaseActivity, Spotify)) for value in values):
            self._connection._activities = [value.to_dict() for value in values]
        else:
            raise TypeError('activity must derive from BaseActivity')

    @property
    def initial_status(self) -> Optional[Status]:
        """Optional[:class:`.Status`]: The status set upon logging in."""
        if self._connection._status in {state.value for state in Status}:
            return Status(self._connection._status)

    @initial_status.setter
    def initial_status(self, value: Status):
        if value is Status.offline:
            self._connection._status = 'invisible'
        elif isinstance(value, Status):
            self._connection._status = str(value)
        else:
            raise TypeError('status must derive from Status')

    @property
    def status(self) -> Status:
        """:class:`.Status`: The user's overall status."""
        status = getattr(self._connection.all_session, 'status', None)
        if status is None and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status or Status.offline

    @property
    def raw_status(self) -> str:
        """:class:`str`: The user's overall status as a string value."""
        return str(self.status)

    @property
    def client_status(self) -> Status:
        """:class:`.Status`: The library's status."""
        status = getattr(self._connection.current_session, 'status', None)
        if status is None and not self.is_closed():
            status = getattr(self._connection.settings, 'status', status)
        return status or Status.offline

    def is_on_mobile(self) -> bool:
        """:class:`bool`: A helper function that determines if the user is active on a mobile device."""
        return any(session.client == ClientType.mobile for session in self._connection._sessions.values())

    @property
    def activities(self) -> Tuple[ActivityTypes, ...]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`], ...]: Returns the activities
        the client is currently doing.

        .. note::

            Due to a Discord API limitation, this may be ``None`` if
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :issue:`1738` for more information.
        """
        state = self._connection
        activities = state.all_session.activities if state.all_session else None
        if activities is None and not self.is_closed():
            activity = getattr(state.settings, 'custom_activity', None)
            activities = (activity,) if activity else activities
        return activities or ()

    @property
    def activity(self) -> Optional[ActivityTypes]:
        """Optional[Union[:class:`.BaseActivity`, :class:`.Spotify`]]: Returns the primary
        activity the client is currently doing. Could be ``None`` if no activity is being done.

        .. note::

            Due to a Discord API limitation, this may be ``None`` if
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :issue:`1738` for more information.

        .. note::

            The client may have multiple activities, these can be accessed under :attr:`activities`.
        """
        if activities := self.activities:
            return activities[0]

    @property
    def client_activities(self) -> Tuple[ActivityTypes, ...]:
        """Tuple[Union[:class:`.BaseActivity`, :class:`.Spotify`], ...]: Returns the activities
        the client is currently doing through this library, if applicable.
        """

        state = self._connection
        activities = state.current_session.activities if state.current_session else None
        if activities is None and not self.is_closed():
            activity = getattr(state.settings, 'custom_activity', None)
            activities = (activity,) if activity else activities
        return activities or ()

    @property
    def allowed_mentions(self) -> Optional[AllowedMentions]:
        """Optional[:class:`~discord.AllowedMentions`]: The allowed mention configuration.

        .. versionadded:: 1.4
        """
        return self._connection.allowed_mentions

    @allowed_mentions.setter
    def allowed_mentions(self, value: Optional[AllowedMentions]) -> None:
        if value is None or isinstance(value, AllowedMentions):
            self._connection.allowed_mentions = value
        else:
            raise TypeError(f'allowed_mentions must be AllowedMentions not {value.__class__.__name__}')

    @property
    def intents(self) -> Intents:
        """:class:`~discord.Intents`: The intents configured for this connection.

        .. versionadded:: 1.5
        """
        return self._connection.intents

    # helpers/getters

    @property
    def users(self) -> List[User]:
        """List[:class:`~discord.User`]: Returns a list of all the users the bot can see."""
        return list(self._connection._users.values())

    def get_channel(self, id: int, /) -> Optional[Union[GuildChannel, Thread, PrivateChannel]]:
        """Returns a channel or thread with the given ID.

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[Union[:class:`.abc.GuildChannel`, :class:`.Thread`, :class:`.abc.PrivateChannel`]]
            The returned channel or ``None`` if not found.
        """
        return self._connection.get_channel(id)  # type: ignore # The cache contains all channel types

    def get_partial_messageable(
        self, id: int, *, guild_id: Optional[int] = None, type: Optional[ChannelType] = None
    ) -> PartialMessageable:
        """Returns a partial messageable with the given destination ID.

        This is useful if you have a destination ID but don't want to do an API call
        to send messages to it.

        .. versionadded:: 2.0

        Parameters
        ----------
        id: :class:`int`
            The destination ID to create a partial messageable for.

            Depending on ``type``, ID of specific entity must be passed instead.

            +-----------------------------------+----------------+
            | Channel Type                      | Entity Type    |
            +-----------------------------------+----------------+
            | :attr:`~ChannelType.private`      | :class:`User`  |
            +-----------------------------------+----------------+
            | :attr:`~ChannelType.lobby`        | :class:`Lobby` |
            +-----------------------------------+----------------+
            | :attr:`~ChannelType.ephemeral_dm` | :class:`User`  |
            +-----------------------------------+----------------+
            | Other                             | A channel      |
            +-----------------------------------+----------------+
        guild_id: Optional[:class:`int`]
            The optional guild ID to create a partial messageable for.

            This is not required to actually send messages, but it does allow the
            :meth:`~discord.PartialMessageable.jump_url` and
            :attr:`~discord.PartialMessageable.guild` properties to function properly.
        type: Optional[:class:`.ChannelType`]
            The underlying channel type for the partial messageable.

        Returns
        -------
        :class:`.PartialMessageable`
            The partial messageable.
        """
        return PartialMessageable(state=self._connection, id=id, guild_id=guild_id, type=type)

    def get_stage_instance(self, id: int, /) -> Optional[StageInstance]:
        """Returns a stage instance with the given stage channel ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.StageInstance`]
            The stage instance or ``None`` if not found.
        """
        from .channel import StageChannel

        channel = self._connection.get_channel(id)

        if isinstance(channel, StageChannel):
            return channel.instance

    def get_guild(self, id: int, /) -> Optional[Guild]:
        """Returns a guild with the given ID.

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.Guild`]
            The guild or ``None`` if not found.
        """
        return self._connection._get_guild(id)

    def get_user(self, id: int, /) -> Optional[User]:
        """Returns a user with the given ID.

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`~discord.User`]
            The user or ``None`` if not found.
        """
        return self._connection.get_user(id)

    def get_emoji(self, id: int, /) -> Optional[Emoji]:
        """Returns an emoji with the given ID.

        .. versionchanged:: 2.0

            ``id`` parameter is now positional-only.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.Emoji`]
            The custom emoji or ``None`` if not found.
        """
        return self._connection.get_emoji(id)

    def get_sticker(self, id: int, /) -> Optional[GuildSticker]:
        """Returns a guild sticker with the given ID.

        .. versionadded:: 2.0

        .. note::

            To retrieve standard stickers, use :meth:`.fetch_sticker`.
            or :meth:`.fetch_premium_sticker_packs`.

        Returns
        -------
        Optional[:class:`.GuildSticker`]
            The sticker or ``None`` if not found.
        """
        return self._connection.get_sticker(id)

    def get_soundboard_sound(self, id: int, /) -> Optional[SoundboardSound]:
        """Returns a soundboard sound with the given ID.

        .. versionadded:: 2.5

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.SoundboardSound`]
            The soundboard sound or ``None`` if not found.
        """
        return self._connection.get_soundboard_sound(id)

    def get_lobby(self, id: int, /) -> Optional[Lobby]:
        """Returns a lobby with the given ID.

        Parameters
        ----------
        id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.Lobby`]
            The lobby or ``None`` if not found.
        """
        return self._connection._get_lobby(id)

    def get_all_channels(self) -> Generator[GuildChannel, None, None]:
        """A generator that retrieves every :class:`.abc.GuildChannel` the client can 'access'.

        This is equivalent to: ::

            for guild in client.guilds:
                for channel in guild.channels:
                    yield channel

        .. note::

            Just because you receive a :class:`.abc.GuildChannel` does not mean that
            you can communicate in said channel. :meth:`.abc.GuildChannel.permissions_for` should
            be used for that.

        Yields
        ------
        :class:`.abc.GuildChannel`
            A channel the client can 'access'.
        """

        for guild in self.guilds:
            yield from guild.channels

    def get_all_members(self) -> Generator[Member, None, None]:
        """Returns a generator with every :class:`.Member` the client can see.

        This is equivalent to: ::

            for guild in client.guilds:
                for member in guild.members:
                    yield member

        Yields
        ------
        :class:`.Member`
            A member the client can see.
        """
        for guild in self.guilds:
            yield from guild.members

    # listeners/waiters

    async def wait_until_ready(self) -> None:
        """|coro|

        Waits until the client's internal cache is all ready.

        .. warning::

            Calling this inside :meth:`setup_hook` can lead to a deadlock.
        """
        if self._ready is not MISSING:
            await self._ready.wait()
        else:
            raise RuntimeError(
                'Client has not been properly initialised. '
                'Please use the login method or asynchronous context manager before calling this method'
            )

    # App Commands

    @overload
    async def wait_for(
        self,
        event: Literal['raw_app_command_permissions_update'],
        /,
        *,
        check: Optional[Callable[[RawAppCommandPermissionsUpdateEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawAppCommandPermissionsUpdateEvent:
        ...

    # AutoMod

    @overload
    async def wait_for(
        self,
        event: Literal['automod_rule_create', 'automod_rule_update', 'automod_rule_delete'],
        /,
        *,
        check: Optional[Callable[[AutoModRule], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> AutoModRule:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['automod_action'],
        /,
        *,
        check: Optional[Callable[[AutoModAction], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> AutoModAction:
        ...

    # Channels

    @overload
    async def wait_for(
        self,
        event: Literal['private_channel_update'],
        /,
        *,
        check: Optional[Callable[[GroupChannel, GroupChannel], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[GroupChannel, GroupChannel]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['private_channel_pins_update'],
        /,
        *,
        check: Optional[Callable[[PrivateChannel, datetime.datetime], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[PrivateChannel, datetime.datetime]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_channel_delete', 'guild_channel_create'],
        /,
        *,
        check: Optional[Callable[[GuildChannel], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> GuildChannel:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_channel_update'],
        /,
        *,
        check: Optional[Callable[[GuildChannel, GuildChannel], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[GuildChannel, GuildChannel]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_channel_pins_update'],
        /,
        *,
        check: Optional[
            Callable[
                [Union[GuildChannel, Thread], Optional[datetime.datetime]],
                bool,
            ]
        ],
        timeout: Optional[float] = ...,
    ) -> Tuple[Union[GuildChannel, Thread], Optional[datetime.datetime]]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['typing'],
        /,
        *,
        check: Optional[Callable[[Messageable, Union[User, Member], datetime.datetime], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Messageable, Union[User, Member], datetime.datetime]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_typing'],
        /,
        *,
        check: Optional[Callable[[RawTypingEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawTypingEvent:
        ...

    # Debug & Gateway events

    @overload
    async def wait_for(
        self,
        event: Literal['connect', 'disconnect', 'ready', 'resumed'],
        /,
        *,
        check: Optional[Callable[[], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> None:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['socket_event_type', 'socket_raw_receive'],
        /,
        *,
        check: Optional[Callable[[str], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> str:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['socket_raw_send'],
        /,
        *,
        check: Optional[Callable[[Union[str, bytes]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Union[str, bytes]:
        ...

    # Entitlements
    @overload
    async def wait_for(
        self,
        event: Literal['entitlement_create', 'entitlement_update', 'entitlement_delete'],
        /,
        *,
        check: Optional[Callable[[Entitlement], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Entitlement:
        ...

    # Guilds

    @overload
    async def wait_for(
        self,
        event: Literal[
            'guild_available',
            'guild_unavailable',
            'guild_join',
            'guild_remove',
        ],
        /,
        *,
        check: Optional[Callable[[Guild], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Guild:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_update'],
        /,
        *,
        check: Optional[Callable[[Guild, Guild], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Guild, Guild]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_emojis_update'],
        /,
        *,
        check: Optional[Callable[[Guild, Sequence[Emoji], Sequence[Emoji]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Guild, Sequence[Emoji], Sequence[Emoji]]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_stickers_update'],
        /,
        *,
        check: Optional[Callable[[Guild, Sequence[GuildSticker], Sequence[GuildSticker]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Guild, Sequence[GuildSticker], Sequence[GuildSticker]]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['invite_create', 'invite_delete'],
        /,
        *,
        check: Optional[Callable[[Invite], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Invite:
        ...

    # Integrations

    @overload
    async def wait_for(
        self,
        event: Literal['integration_create', 'integration_update'],
        /,
        *,
        check: Optional[Callable[[Integration], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Integration:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_integrations_update'],
        /,
        *,
        check: Optional[Callable[[Guild], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Guild:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['webhooks_update'],
        /,
        *,
        check: Optional[Callable[[GuildChannel], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> GuildChannel:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_integration_delete'],
        /,
        *,
        check: Optional[Callable[[RawIntegrationDeleteEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawIntegrationDeleteEvent:
        ...

    # Members

    @overload
    async def wait_for(
        self,
        event: Literal['member_join', 'member_remove'],
        /,
        *,
        check: Optional[Callable[[Member], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Member:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_member_remove'],
        /,
        *,
        check: Optional[Callable[[RawMemberRemoveEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawMemberRemoveEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['member_update', 'presence_update'],
        /,
        *,
        check: Optional[Callable[[Member, Member], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Member, Member]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['user_update'],
        /,
        *,
        check: Optional[Callable[[User, User], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[User, User]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['member_ban'],
        /,
        *,
        check: Optional[Callable[[Guild, Union[User, Member]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Guild, Union[User, Member]]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['member_unban'],
        /,
        *,
        check: Optional[Callable[[Guild, User], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Guild, User]:
        ...

    # Messages

    @overload
    async def wait_for(
        self,
        event: Literal['message', 'message_delete'],
        /,
        *,
        check: Optional[Callable[[Message], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Message:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['message_edit'],
        /,
        *,
        check: Optional[Callable[[Message, Message], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Message, Message]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['bulk_message_delete'],
        /,
        *,
        check: Optional[Callable[[List[Message]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> List[Message]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_message_edit'],
        /,
        *,
        check: Optional[Callable[[RawMessageUpdateEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawMessageUpdateEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_message_delete'],
        /,
        *,
        check: Optional[Callable[[RawMessageDeleteEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawMessageDeleteEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_bulk_message_delete'],
        /,
        *,
        check: Optional[Callable[[RawBulkMessageDeleteEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawBulkMessageDeleteEvent:
        ...

    # Reactions

    @overload
    async def wait_for(
        self,
        event: Literal['reaction_add', 'reaction_remove'],
        /,
        *,
        check: Optional[Callable[[Reaction, Union[Member, User]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Reaction, Union[Member, User]]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['reaction_clear'],
        /,
        *,
        check: Optional[Callable[[Message, List[Reaction]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Message, List[Reaction]]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['reaction_clear_emoji'],
        /,
        *,
        check: Optional[Callable[[Reaction], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Reaction:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_reaction_add', 'raw_reaction_remove'],
        /,
        *,
        check: Optional[Callable[[RawReactionActionEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawReactionActionEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_reaction_clear'],
        /,
        *,
        check: Optional[Callable[[RawReactionClearEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawReactionClearEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_reaction_clear_emoji'],
        /,
        *,
        check: Optional[Callable[[RawReactionClearEmojiEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawReactionClearEmojiEvent:
        ...

    # Roles

    @overload
    async def wait_for(
        self,
        event: Literal['guild_role_create', 'guild_role_delete'],
        /,
        *,
        check: Optional[Callable[[Role], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Role:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['guild_role_update'],
        /,
        *,
        check: Optional[Callable[[Role, Role], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Role, Role]:
        ...

    # Scheduled Events

    @overload
    async def wait_for(
        self,
        event: Literal['scheduled_event_create', 'scheduled_event_delete'],
        /,
        *,
        check: Optional[Callable[[ScheduledEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> ScheduledEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['scheduled_event_user_add', 'scheduled_event_user_remove'],
        /,
        *,
        check: Optional[Callable[[ScheduledEvent, User], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[ScheduledEvent, User]:
        ...

    # Stages

    @overload
    async def wait_for(
        self,
        event: Literal['stage_instance_create', 'stage_instance_delete'],
        /,
        *,
        check: Optional[Callable[[StageInstance], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> StageInstance:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['stage_instance_update'],
        /,
        *,
        check: Optional[Callable[[StageInstance, StageInstance], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Coroutine[Any, Any, Tuple[StageInstance, StageInstance]]:
        ...

    # Subscriptions
    @overload
    async def wait_for(
        self,
        event: Literal['subscription_create', 'subscription_update', 'subscription_delete'],
        /,
        *,
        check: Optional[Callable[[Subscription], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Subscription:
        ...

    # Threads
    @overload
    async def wait_for(
        self,
        event: Literal['thread_create', 'thread_join', 'thread_remove', 'thread_delete'],
        /,
        *,
        check: Optional[Callable[[Thread], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Thread:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['thread_update'],
        /,
        *,
        check: Optional[Callable[[Thread, Thread], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Thread, Thread]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_thread_update'],
        /,
        *,
        check: Optional[Callable[[RawThreadUpdateEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawThreadUpdateEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_thread_delete'],
        /,
        *,
        check: Optional[Callable[[RawThreadDeleteEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawThreadDeleteEvent:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['thread_member_join', 'thread_member_remove'],
        /,
        *,
        check: Optional[Callable[[ThreadMember], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> ThreadMember:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_thread_member_remove'],
        /,
        *,
        check: Optional[Callable[[RawThreadMembersUpdate], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawThreadMembersUpdate:
        ...

    # Voice

    @overload
    async def wait_for(
        self,
        event: Literal['voice_state_update'],
        /,
        *,
        check: Optional[Callable[[Member, VoiceState, VoiceState], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Member, VoiceState, VoiceState]:
        ...

    # Polls

    @overload
    async def wait_for(
        self,
        event: Literal['poll_vote_add', 'poll_vote_remove'],
        /,
        *,
        check: Optional[Callable[[Union[User, Member], PollAnswer], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Union[User, Member], PollAnswer]:
        ...

    @overload
    async def wait_for(
        self,
        event: Literal['raw_poll_vote_add', 'raw_poll_vote_remove'],
        /,
        *,
        check: Optional[Callable[[RawPollVoteActionEvent], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> RawPollVoteActionEvent:
        ...

    # Commands

    @overload
    async def wait_for(
        self: Bot,
        event: Literal["command", "command_completion"],
        /,
        *,
        check: Optional[Callable[[Context[Any]], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Context[Any]:
        ...

    @overload
    async def wait_for(
        self: Bot,
        event: Literal["command_error"],
        /,
        *,
        check: Optional[Callable[[Context[Any], CommandError], bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Tuple[Context[Any], CommandError]:
        ...

    @overload
    async def wait_for(
        self,
        event: str,
        /,
        *,
        check: Optional[Callable[..., bool]] = ...,
        timeout: Optional[float] = ...,
    ) -> Any:
        ...

    def wait_for(
        self,
        event: str,
        /,
        *,
        check: Optional[Callable[..., bool]] = None,
        timeout: Optional[float] = None,
    ) -> Coro[Any]:
        """|coro|

        Waits for a WebSocket event to be dispatched.

        This could be used to wait for a user to reply to a message,
        or to react to a message, or to edit a message in a self-contained
        way.

        The ``timeout`` parameter is passed onto :func:`asyncio.wait_for`. By default,
        it does not timeout. Note that this does propagate the
        :exc:`asyncio.TimeoutError` for you in case of timeout and is provided for
        ease of use.

        In case the event returns multiple arguments, a :class:`tuple` containing those
        arguments is returned instead. Please check the
        :ref:`documentation <discord-api-events>` for a list of events and their
        parameters.

        This function returns the **first event that meets the requirements**.

        Examples
        --------

        Waiting for a user reply: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$greet'):
                    channel = message.channel
                    await channel.send('Say hello!')

                    def check(m):
                        return m.content == 'hello' and m.channel == channel

                    msg = await client.wait_for('message', check=check)
                    await channel.send(f'Hello {msg.author}!')

        Waiting for a thumbs up reaction from the message author: ::

            @client.event
            async def on_message(message):
                if message.content.startswith('$thumb'):
                    channel = message.channel
                    await channel.send('Send me that \N{THUMBS UP SIGN} reaction, mate')

                    def check(reaction, user):
                        return user == message.author and str(reaction.emoji) == '\N{THUMBS UP SIGN}'

                    try:
                        reaction, user = await client.wait_for('reaction_add', timeout=60.0, check=check)
                    except asyncio.TimeoutError:
                        await channel.send('\N{THUMBS DOWN SIGN}')
                    else:
                        await channel.send('\N{THUMBS UP SIGN}')

        .. versionchanged:: 2.0

            ``event`` parameter is now positional-only.


        Parameters
        ----------
        event: :class:`str`
            The event name, similar to the :ref:`event reference <discord-api-events>`,
            but without the ``on_`` prefix, to wait for.
        check: Optional[Callable[..., :class:`bool`]]
            A predicate to check what to wait for. The arguments must meet the
            parameters of the event being waited for.
        timeout: Optional[:class:`float`]
            The number of seconds to wait before timing out and raising
            :exc:`asyncio.TimeoutError`.

        Raises
        ------
        asyncio.TimeoutError
            If a timeout is provided and it was reached.

        Returns
        -------
        Any
            Returns no arguments, a single argument, or a :class:`tuple` of multiple
            arguments that mirrors the parameters passed in the
            :ref:`event reference <discord-api-events>`.
        """

        future = self.loop.create_future()
        if check is None:

            def _check(*args):
                return True

            check = _check

        ev = event.lower()
        try:
            listeners = self._listeners[ev]
        except KeyError:
            listeners = []
            self._listeners[ev] = listeners

        listeners.append((future, check))
        return asyncio.wait_for(future, timeout)

    # event registration

    def event(self, coro: CoroT, /) -> CoroT:
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        -------

        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')

        .. versionchanged:: 2.0

            ``coro`` parameter is now positional-only.

        Raises
        ------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        _log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro

    async def change_presence(
        self,
        *,
        activity: Optional[BaseActivity] = None,
        status: Optional[Status] = None,
    ) -> None:
        """|coro|

        Changes the client's presence.

        Example
        -------

        .. code-block:: python3

            game = discord.Game("with the API")
            await client.change_presence(status=discord.Status.idle, activity=game)

        .. versionchanged:: 2.0
            Removed the ``afk`` keyword-only parameter.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` instead of
            ``InvalidArgument``.

        Parameters
        ----------
        activity: Optional[:class:`.BaseActivity`]
            The activity being done. ``None`` if no currently active activity is done.
        status: Optional[:class:`.Status`]
            Indicates what status to change to. If ``None``, then
            :attr:`.Status.online` is used.

        Raises
        ------
        TypeError
            If the ``activity`` parameter is not the proper type.
        """

        if status is None:
            status_str = 'online'
            status = Status.online
        elif status is Status.offline:
            status_str = 'invisible'
            status = Status.offline
        else:
            status_str = str(status)

        await self.ws.change_presence(activity=activity, status=status_str)

        for guild in self._connection.guilds:
            me = guild.me
            if me is None:
                continue

            if activity is not None:
                me.activities = (activity,)  # type: ignore
            else:
                me.activities = ()

            me.status = status

    async def create_headless_session(
        self, *, activities: List[ActivityTypes], token: Optional[str] = None
    ) -> HeadlessSession:
        """|coro|

        Creates, or updates a headless session.

        Parameters
        ----------
        activities: List[Union[:class:`BaseActivity`, :class:`Spotify`], ...]
            The activities. This must contain exactly single activity.
        token: Optional[:class:`str`]
            The ID of the headless session to update. ``None`` denotes creating a new headless session.

        Raises
        ------
        HTTPException
            The session token is invalid, or creating or editing the headless session failed.

        Returns
        -------
        :class:`HeadlessSession`
            The created headless session.
        """

        state = self._connection
        data = await state.http.create_headless_session(
            activities=[a.to_dict() for a in activities],
            token=token,
        )
        return HeadlessSession(
            token=data['token'],
            activities=tuple(create_activity(d, state) for d in data['activities']),
            state=state,
        )

    # Connections

    async def fetch_connections(self) -> List[Connection]:
        r"""|coro|

        Retrieves :class:`list` of your :class:`Connection`\s.

        Raises
        ------
        Forbidden
            You do not have proper permissions to retrieve your connections.
        HTTPException
            Retrieving connections failed.

        Returns
        -------
        List[:class:`Connection`]
            The retrieved connections.
        """
        state = self._connection
        data = await state.http.get_connections()
        return [Connection(data=d, state=state) for d in data]

    async def change_voice_state(
        self,
        *,
        channel: Optional[Snowflake],
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
    ) -> None:
        """|coro|

        Changes client's private channel voice state.

        Parameters
        ----------
        channel: Optional[:class:`~discord.abc.Snowflake`]
            Channel the client wants to join (must be a private channel). Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        self_video: :class:`bool`
            Indicates if the client should show camera.
        """
        state = self._connection
        ws = self.ws
        channel_id = channel.id if channel else None

        await ws.voice_state(None, channel_id, self_mute, self_deaf, self_video)

    # Guild stuff

    async def fetch_guilds(
        self,
        *,
        limit: Optional[int] = 200,
        before: Optional[SnowflakeTime] = None,
        after: Optional[SnowflakeTime] = None,
        with_counts: bool = True,
    ) -> AsyncIterator[UserGuild]:
        """Retrieves an :term:`asynchronous iterator` that enables receiving your guilds.

        .. note::

            Using this, you will only receive :attr:`.UserGuild.is_owner`, :attr:`.UserGuild.icon`,
            :attr:`.UserGuild.id`, :attr:`.UserGuild.name`, :attr:`.UserGuild.approximate_member_count`,
            and :attr:`.UserGuild.approximate_presence_count` per :class:`.UserGuild`.

        .. note::

            This method is an API call. For general usage, consider :attr:`guilds` instead.

        Examples
        --------

        Usage ::

            async for guild in client.fetch_guilds(limit=150):
                print(guild.name)

        Flattening into a list ::

            guilds = [guild async for guild in client.fetch_guilds(limit=150)]
            # guilds is now a list of UserGuild...

        All parameters are optional.

        Parameters
        ----------
        limit: Optional[:class:`int`]
            The number of guilds to retrieve.
            If ``None``, it retrieves every guild you have access to. Note, however,
            that this would make it a slow operation.
            Defaults to ``200``.

            .. versionchanged:: 2.0

                The default has been changed to 200.

        before: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieves guilds before this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        after: Union[:class:`.abc.Snowflake`, :class:`datetime.datetime`]
            Retrieve guilds after this date or object.
            If a datetime is provided, it is recommended to use a UTC aware datetime.
            If the datetime is naive, it is assumed to be local time.
        with_counts: :class:`bool`
            Whether to include count information in the guilds. This fills the
            :attr:`.UserGuild.approximate_member_count` and :attr:`.UserGuild.approximate_presence_count`
            attributes without needing any privileged intents. Defaults to ``True``.

            .. versionadded:: 2.3

        Raises
        ------
        HTTPException
            Getting the guilds failed.

        Yields
        ------
        :class:`.UserGuild`
            The guild with the guild data parsed.
        """

        async def _before_strategy(retrieve: int, before: Optional[Snowflake], limit: Optional[int]):
            before_id = before.id if before else None
            data = await self.http.get_guilds(retrieve, before=before_id, with_counts=with_counts)

            if data:
                if limit is not None:
                    limit -= len(data)

                before = Object(id=int(data[0]['id']))

            return data, before, limit

        async def _after_strategy(retrieve: int, after: Optional[Snowflake], limit: Optional[int]):
            after_id = after.id if after else None
            data = await self.http.get_guilds(retrieve, after=after_id, with_counts=with_counts)

            if data:
                if limit is not None:
                    limit -= len(data)

                after = Object(id=int(data[-1]['id']))

            return data, after, limit

        if isinstance(before, datetime.datetime):
            before = Object(id=time_snowflake(before, high=False))
        if isinstance(after, datetime.datetime):
            after = Object(id=time_snowflake(after, high=True))

        predicate: Optional[Callable[[GuildPayload], bool]] = None
        strategy, state = _after_strategy, after

        if before:
            strategy, state = _before_strategy, before

        if before and after:
            predicate = lambda m: int(m['id']) > after.id

        while True:
            retrieve = 200 if limit is None else min(limit, 200)
            if retrieve < 1:
                return

            data, state, limit = await strategy(retrieve, state, limit)

            if predicate:
                data = filter(predicate, data)

            count = 0

            for count, raw_guild in enumerate(data, 1):
                yield UserGuild(state=self._connection, data=raw_guild)

            if count < 200:
                # There's no data left after this
                break

    async def fetch_template(self, code: Union[Template, str]) -> Template:
        """|coro|

        Gets a :class:`.Template` from a discord.new URL or code.

        Parameters
        ----------
        code: Union[:class:`.Template`, :class:`str`]
            The Discord Template Code or URL (must be a discord.new URL).

        Raises
        ------
        NotFound
            The template is invalid.
        HTTPException
            Getting the template failed.

        Returns
        -------
        :class:`.Template`
            The template from the URL/code.
        """
        code = resolve_template(code)
        data = await self.http.get_template(code)
        return Template(data=data, state=self._connection)

    # Invite management

    async def fetch_invite(
        self,
        url: Union[Invite, str],
        *,
        with_counts: bool = True,
        with_expiration: bool = True,
        scheduled_event_id: Optional[int] = None,
    ) -> Invite:
        """|coro|

        Gets an :class:`.Invite` from a discord.gg URL or ID.

        .. note::

            If the invite is for a guild you have not joined, the guild and channel
            attributes of the returned :class:`.Invite` will be :class:`.PartialInviteGuild` and
            :class:`.PartialInviteChannel` respectively.

        Parameters
        ----------
        url: Union[:class:`.Invite`, :class:`str`]
            The Discord invite ID or URL (must be a discord.gg URL).
        with_counts: :class:`bool`
            Whether to include count information in the invite. This fills the
            :attr:`.Invite.approximate_member_count` and :attr:`.Invite.approximate_presence_count`
            fields.
        scheduled_event_id: Optional[:class:`int`]
            The ID of the scheduled event this invite is for.

            .. note::

                It is not possible to provide a url that contains an ``event_id`` parameter
                when using this parameter.

            .. versionadded:: 2.0

        Raises
        ------
        ValueError
            The url contains an ``event_id``, but ``scheduled_event_id`` has also been provided.
        NotFound
            The invite has expired or is invalid.
        HTTPException
            Getting the invite failed.

        Returns
        -------
        :class:`.Invite`
            The invite from the URL/ID.
        """

        resolved = resolve_invite(url)

        if scheduled_event_id and resolved.event:
            raise ValueError('Cannot specify scheduled_event_id and contain an event_id in the url.')

        scheduled_event_id = scheduled_event_id or resolved.event

        data = await self.http.get_invite(
            resolved.code,
            with_counts=with_counts,
            guild_scheduled_event_id=scheduled_event_id,
        )
        return Invite.from_incomplete(state=self._connection, data=data)

    # Miscellaneous stuff

    async def fetch_widget(self, guild_id: int, /) -> Widget:
        """|coro|

        Gets a :class:`.Widget` from a guild ID.

        .. note::

            The guild must have the widget enabled to get this information.

        .. versionchanged:: 2.0

            ``guild_id`` parameter is now positional-only.

        Parameters
        ----------
        guild_id: :class:`int`
            The ID of the guild.

        Raises
        ------
        Forbidden
            The widget for this guild is disabled.
        HTTPException
            Retrieving the widget failed.

        Returns
        -------
        :class:`.Widget`
            The guild's widget.
        """
        data = await self.http.get_widget(guild_id)

        return Widget(state=self._connection, data=data)

    async def fetch_game_relationships(self) -> List[GameRelationship]:
        """|coro|

        Retrieves all your game relationships.

        .. note::

            This method is an API call. For general usage, consider :attr:`game_relationships` instead.

        Raises
        ------
        HTTPException
            Retrieving your game relationships failed.

        Returns
        -------
        List[:class:`.GameRelationship`]
            All your game relationships.
        """
        state = self._connection
        data = await state.http.get_game_relationships()
        return [GameRelationship(state=state, data=d) for d in data]

    async def fetch_relationships(self, *, with_implicit: Optional[bool] = None) -> List[Relationship]:
        """|coro|

        Retrieves all your relationships.

        .. note::

            This method is an API call. For general usage, consider :attr:`relationships` instead.

        Parameters
        ----------
        with_implicit: Optional[:class:`bool`]
            Whether to include :attr:`~RelationshipType.implicit` relationships as well. Defaults to ``False``.

        Raises
        ------
        HTTPException
            Retrieving your relationships failed.

        Returns
        -------
        List[:class:`.Relationship`]
            All your relationships.
        """
        state = self._connection
        data = await state.http.get_relationships(with_implicit=with_implicit)
        return [Relationship(state=state, data=d) for d in data]

    async def create_dm(self, user: Snowflake) -> Union[DMChannel, EphemeralDMChannel]:
        """|coro|

        Creates a :class:`.DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        .. versionadded:: 2.0

        Parameters
        ----------
        user: :class:`~discord.abc.Snowflake`
            The user to create a DM with.

        Returns
        -------
        Union[:class:`.DMChannel`, :class:`.EphemeralDMChannel`]
            The channel that was created.
        """
        state = self._connection
        found = state._get_private_channel_by_user(user.id)
        if found:
            return found

        data = await state.http.start_private_message(user.id)
        return state.add_dm_channel(data)

    async def create_or_join_lobby(
        self,
        secret: str,
        *,
        lobby_metadata: Optional[Dict[str, str]] = None,
        member_metadata: Optional[Dict[str, str]] = None,
        idle_timeout: Optional[int] = None,
    ) -> Lobby:
        """|coro|

        Creates or joins an existing lobby by secret.

        Parameters
        ----------
        secret: :class:`str`
            The secret for joining/creating a lobby.
        lobby_metadata: Optional[Dict[:class:`str`, :class:`str`]]
            The lobby's metadata. Must be 1000 characters in total (length of keys + values).
        member_metadata: Optional[Dict[:class:`str`, :class:`str`]]
            The member's metadata to assign to yourself. Must be 1000 characters in total (length of keys + values).
        idle_timeout: Optional[:class:`int`]
            The seconds to wait before shutting down a lobby after it becomes idle. Must be between 5 seconds and 1 week.

            Defaults to 5 minutes if not provided.

        Raises
        ------
        Forbidden
            You do not have proper permissions to join lobby.
        HTTPException
            Creating/joining the lobby failed.

        Returns
        -------
        :class:`Lobby`
            The joined or created lobby.
        """

        state = self._connection
        data = await state.http.create_or_join_lobby(
            secret=secret,
            lobby_metadata=lobby_metadata,
            member_metadata=member_metadata,
            idle_timeout_seconds=idle_timeout,
        )

        return Lobby(data=data, state=state)

    @overload
    async def send_friend_request(self, user: _UserTag, /) -> None:
        ...

    @overload
    async def send_friend_request(self, user: str, /) -> None:
        ...

    @overload
    async def send_friend_request(self, username: str, discriminator: str, /) -> None:
        ...

    async def send_friend_request(self, *args: Union[_UserTag, str, int]) -> None:
        """|coro|

        Sends a friend request to another user.

        This function can be used in multiple ways.

        .. code-block:: python

            # Passing a user object:
            await client.send_friend_request(user)

            # Passing a username
            await client.send_friend_request('dolfies')

            # Passing a legacy user:
            await client.send_friend_request('Dolfies#0040')

            # Passing a legacy username and discriminator:
            await client.send_friend_request('Dolfies', '0040')

        Parameters
        ----------
        user: Union[:class:`discord.User`, :class:`str`, :class:`int`]
            The user to send the friend request to.
        username: :class:`str`
            The username of the user to send the friend request to.
        discriminator: :class:`str`
            The discriminator of the user to send the friend request to.

        Raises
        ------
        Forbidden
            Not allowed to send a friend request to this user.
        HTTPException
            Sending the friend request failed.
        TypeError
            More than 2 parameters or less than 1 parameter was passed.
        """
        username: str
        discrim: str
        if len(args) == 1:
            user = args[0]
            if isinstance(user, int):
                await self._connection.http.add_relationship(user)
                return

            if isinstance(user, _UserTag):
                user = str(user)
            username, _, discrim = user.partition('#')
        elif len(args) == 2:
            username, discrim = args  # type: ignore
        else:
            raise TypeError(f'send_friend_request() takes 1 or 2 arguments but {len(args)} were given')

        state = self._connection
        await state.http.send_friend_request(username, discrim or 0)

    async def send_game_friend_request(self, user: Union[_UserTag, int, str]) -> None:
        """|coro|

        Sends a game friend request to another user.

        This function can be used in multiple ways.

        .. code-block:: python

            # Passing a user object:
            await client.send_game_friend_request(user)

            # Passing a username
            await client.send_game_friend_request('dolfies')

            # Passing a ID
            await client.send_game_friend_request(852892297661906993)


        Parameters
        ----------
        user: Union[:class:`discord.User`, :class:`str`, :class:`int`]
            The user to send the game friend request to.

        Raises
        ------
        Forbidden
            Not allowed to send a game friend request to this user.
        HTTPException
            Sending the game friend request failed.
        TypeError
            More than 2 parameters or less than 1 parameter was passed.
        """
        state = self._connection

        if isinstance(user, _UserTag):
            username = str(user)
        elif isinstance(user, str):
            username = user
        elif isinstance(user, int):
            await state.http.add_game_relationship(user)
            return

        await state.http.send_game_friend_request(username)
