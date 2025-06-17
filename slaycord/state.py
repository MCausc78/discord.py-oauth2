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
from collections import deque, OrderedDict
from copy import copy
import inspect
import logging
from typing import (
    Any,
    Callable,
    Coroutine,
    Deque,
    Dict,
    Generic,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    TypeVar,
    Tuple,
    Union,
    cast,
    overload,
)

# import weakref

from ._types import ClientT
from .activity import BaseActivity, Session, ActivityInvite, create_activity
from .automod import AutoModRule, AutoModAction
from .channel import *
from .channel import _private_channel_factory, _channel_factory
from .emoji import Emoji
from .entitlements import Entitlement
from .enums import try_enum, AudioContext, ChannelType, Status, StreamDeletionReason
from .flags import ApplicationFlags, Intents, MemberCacheFlags
from .game_invite import GameInvite
from .game_relationship import GameRelationship
from .guild import Guild
from .integrations import _integration_factory
from .invite import Invite
from .lobby import LobbyMember, Lobby, _extract_user_id
from .member import VoiceState, Member
from .mentions import AllowedMentions
from .message import Message, LobbyMessage
from .object import Object
from .partial_emoji import PartialEmoji
from .presences import ClientStatus, RawPresenceUpdateEvent
from .raw_models import *
from .relationship import Relationship
from .role import Role
from .scheduled_event import ScheduledEvent
from .settings import UserSettings, AudioSettings, AudioSettingsManager
from .soundboard import SoundboardSound
from .stage_instance import StageInstance
from .sticker import GuildSticker
from .stream import PartialStream, Stream
from .subscription import Subscription
from .threads import Thread, ThreadMember
from .user import User, ClientUser
from .utils import MISSING, SequenceProxy, _get_as_snowflake, find, parse_time

if TYPE_CHECKING:
    from .abc import PrivateChannel
    from .calls import Call
    from .gateway import DiscordWebSocket
    from .guild import GuildChannel
    from .http import HTTPClient
    from .message import MessageableChannel
    from .poll import Poll
    from .voice_client import VoiceProtocol

    from .types import gateway as gw
    from .types.activity import (
        PartialPresenceUpdate as PartialPresenceUpdatePayload,
        Activity as ActivityPayload,
    )
    from .types.automod import AutoModerationRule, AutoModerationActionExecution
    from .types.channel import (
        DMChannel as DMChannelPayload,
        EphemeralDMChannel as EphemeralDMChannelPayload,
    )
    from .types.command import GuildApplicationCommandPermissions as GuildApplicationCommandPermissionsPayload
    from .types.emoji import Emoji as EmojiPayload, PartialEmoji as PartialEmojiPayload
    from .types.guild import Guild as GuildPayload
    from .types.member import MemberWithUser as MemberWithUserPayload
    from .types.message import Message as MessagePayload, PartialMessage as PartialMessagePayload
    from .types.sticker import GuildSticker as GuildStickerPayload
    from .types.user import User as UserPayload, PartialUser as PartialUserPayload
    from .types.voice import BaseVoiceState as VoiceStatePayload

    T = TypeVar('T')
    Channel = Union[GuildChannel, PrivateChannel, PartialMessageable]


_log = logging.getLogger(__name__)


async def logging_coroutine(coroutine: Coroutine[Any, Any, T], *, info: str) -> Optional[T]:
    try:
        await coroutine
    except Exception:
        _log.exception('Exception occurred during %s', info)


class ConnectionState(Generic[ClientT]):
    if TYPE_CHECKING:
        _get_websocket: Callable[[], DiscordWebSocket]
        _get_client: Callable[[], ClientT]
        _parsers: Dict[str, Callable[[Dict[str, Any]], None]]

    def __init__(
        self,
        *,
        dispatch: Callable[..., Any],
        handlers: Dict[str, Callable[..., Any]],
        hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]],
        http: HTTPClient,
        **options: Any,
    ) -> None:
        # Set later, after Client.login
        self.loop: asyncio.AbstractEventLoop = MISSING
        self.http: HTTPClient = http
        self.max_messages: Optional[int] = options.get('max_messages', 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.max_lobby_messages: Optional[int] = options.get('max_lobby_messages', 1000)
        if self.max_lobby_messages is not None and self.max_lobby_messages <= 0:
            self.max_lobby_messages = 1000

        self.dispatch: Callable[..., Any] = dispatch
        self.handlers: Dict[str, Callable[..., Any]] = handlers
        self.hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = hooks
        self.application_id: Optional[int] = _get_as_snowflake(options, 'application_id')
        self.application_name: str = MISSING
        self.application_flags: ApplicationFlags = MISSING
        self.heartbeat_timeout: float = options.get('heartbeat_timeout', 60.0)

        allowed_mentions = options.get('allowed_mentions')

        if allowed_mentions is not None and not isinstance(allowed_mentions, AllowedMentions):
            raise TypeError('allowed_mentions parameter must be AllowedMentions')

        self.allowed_mentions: Optional[AllowedMentions] = allowed_mentions

        activities = options.get('activities', [])
        if not activities:
            activity = options.get('activity')
            if activity is not None:
                activities = [activity]

        if not all(isinstance(activity, BaseActivity) for activity in activities):
            raise TypeError('All activities must derive from BaseActivity')

        activities = [activity.to_dict() for activity in activities]

        status = options.get('status', None)
        if status:
            if status is Status.offline:
                status = 'invisible'
            else:
                status = str(status)

        intents = options.get('intents')
        if intents is not None:
            if not isinstance(intents, Intents):
                raise TypeError(f'intents parameter must be Intent not {type(intents)!r}')

        if intents is not None and not intents.guilds:
            _log.warning('Guilds intent seems to be disabled. This may cause state related issues.')

        cache_flags = options.get('member_cache_flags')
        if cache_flags is None:
            if intents is None:
                cache_flags = MemberCacheFlags.none()
            else:
                cache_flags = MemberCacheFlags.from_intents(intents)
        elif not isinstance(cache_flags, MemberCacheFlags):
            raise TypeError(f'member_cache_flags parameter must be MemberCacheFlags not {type(cache_flags)!r}')
        # else: cache_flags._verify_intents(intents)

        self.member_cache_flags: MemberCacheFlags = cache_flags
        self._activities: List[ActivityPayload] = activities
        self._status: Optional[str] = status
        self._intents: Optional[Intents] = intents

        self.parsers: Dict[str, Callable[[Any], None]]
        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func

        self.clear()

    # For some reason Discord still sends emoji/sticker data in payloads
    # This makes it hard to actually swap out the appropriate store methods
    # So this is checked instead, it's a small penalty to pay
    @property
    def cache_guild_expressions(self) -> bool:
        intents = self._intents
        if intents is None:
            return True
        return intents.emojis_and_stickers

    async def close(self) -> None:
        for voice in self.voice_clients:
            try:
                await voice.disconnect(force=True)
            except Exception:
                # if an error happens during disconnects, disregard it.
                pass

        # Purposefully don't call `clear` because users rely on cache being available post-close

    def clear(self) -> None:
        self.user: Optional[ClientUser] = None
        # self._users: weakref.WeakValueDictionary[int, User] = weakref.WeakValueDictionary()
        self._users: Dict[int, User] = {}
        self._emojis: Dict[int, Emoji] = {}
        self._stickers: Dict[int, GuildSticker] = {}
        self._guilds: Dict[int, Guild] = {}

        self._lobbies: Dict[int, Lobby] = {}
        self._game_invites: Dict[int, GameInvite] = {}
        self._game_relationships: Dict[int, GameRelationship] = {}
        self._audio_settings: AudioSettingsManager = AudioSettingsManager(data={}, state=self)
        self._relationships: Dict[int, Relationship] = {}
        self._sessions: Dict[str, Session] = {}
        self._streams: Dict[str, Stream] = {}
        self._subscriptions: Dict[int, Subscription] = {}

        self.analytics_token: Optional[str] = None
        self.av_sf_protocol_floor: int = -1
        self.disabled_gateway_events: Tuple[str, ...] = ()
        self.disabled_functions: Tuple[str, ...] = ()
        self.disclose: List[str] = []
        self.scopes: Tuple[str, ...] = ()
        self.settings: UserSettings = UserSettings(data={}, state=self)

        self._calls: Dict[int, Call] = {}
        self._call_message_cache: Dict[int, Message] = {}
        self._voice_clients: Dict[int, VoiceProtocol] = {}
        self._voice_states: Dict[int, VoiceState] = {}

        # LRU of max size 128
        self._private_channels: OrderedDict[int, PrivateChannel] = OrderedDict()
        # extra dict to look up private channels by user id
        self._private_channels_by_user: Dict[int, Union[DMChannel, EphemeralDMChannel]] = {}

        if self.max_messages is not None:
            self._messages: Optional[Deque[Message]] = deque(maxlen=self.max_messages)
        else:
            self._messages: Optional[Deque[Message]] = None

        if self.max_lobby_messages is not None:
            self._lobby_messages: Optional[Deque[LobbyMessage]] = deque(maxlen=self.max_lobby_messages)
        else:
            self._lobby_messages: Optional[Deque[LobbyMessage]] = None

    def call_handlers(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            func = self.handlers[key]
        except KeyError:
            pass
        else:
            func(*args, **kwargs)

    async def call_hooks(self, key: str, *args: Any, **kwargs: Any) -> None:
        try:
            coro = self.hooks[key]
        except KeyError:
            pass
        else:
            await coro(*args, **kwargs)

    @property
    def self_id(self) -> Optional[int]:
        u = self.user
        return u.id if u else None

    @property
    def intents(self) -> Intents:
        ret = Intents.none()
        if self._intents is not None:
            ret.value = self._intents.value
        return ret

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        return list(self._voice_clients.values())

    def _update_voice_state(
        self, data: VoiceStatePayload, channel_id: Optional[int]
    ) -> Tuple[Optional[User], VoiceState, VoiceState]:
        user_id = int(data['user_id'])
        user = self.get_user(user_id)
        channel: Optional[Union[DMChannel, GroupChannel]] = self._get_private_channel(channel_id)  # type: ignore

        try:
            # Check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy(after)
            after._update(data, channel)
        except KeyError:
            # if we're here then add it into the cache
            after = VoiceState(data=data, channel=channel)
            before = VoiceState(data=data, channel=None)
            self._voice_states[user_id] = after

        return user, before, after

    def _voice_state_for(self, user_id: int) -> Optional[VoiceState]:
        return self._voice_states.get(user_id)

    def _get_voice_client(self, key_id: Optional[int]) -> Optional[VoiceProtocol]:
        # the keys of self._voice_clients are ints
        return self._voice_clients.get(key_id)  # type: ignore

    def _add_voice_client(self, key_id: int, voice: VoiceProtocol) -> None:
        self._voice_clients[key_id] = voice

    def _remove_voice_client(self, key_id: int) -> None:
        self._voice_clients.pop(key_id, None)

    def _update_references(self, ws: DiscordWebSocket) -> None:
        for vc in self.voice_clients:
            vc.main_ws = ws  # type: ignore # Silencing the unknown attribute (ok at runtime).

    def store_user(self, data: Union[UserPayload, PartialUserPayload], *, cache: bool = True, dispatch: bool = True) -> User:
        # this way is 300% faster than `dict.setdefault`.
        user_id = int(data['id'])
        try:
            user = self._users[user_id]
        except KeyError:
            user = User(state=self, data=data)
            if cache:
                self._users[user_id] = user
            return user
        else:
            if cache and 'username' in data and 'discriminator' in data:
                modified_avatar_decoration_data = data.get('avatar_decoration_data')

                original = (
                    user.name,
                    user.discriminator,
                    user._avatar,
                    user.global_name,
                    user._public_flags,
                    None if user._avatar_decoration_data is None else int(user._avatar_decoration_data['sku_id']),
                )
                modified = (
                    data['username'],
                    data['discriminator'],
                    data.get('avatar'),
                    data.get('global_name'),
                    data.get('public_flags') or 0,
                    None if modified_avatar_decoration_data is None else int(modified_avatar_decoration_data['sku_id']),
                )
                if original != modified:
                    before = copy(user)
                    user._update(data)
                    if dispatch:
                        self.dispatch('user_update', before, user)
            return user

    def create_user(self, data: Union[UserPayload, PartialUserPayload]) -> User:
        return User(state=self, data=data)

    def get_user(self, id: int) -> Optional[User]:
        return self._users.get(id)

    def store_emoji(self, guild: Guild, data: EmojiPayload) -> Emoji:
        # the id will be present here
        emoji_id = int(data['id'])  # type: ignore
        self._emojis[emoji_id] = emoji = Emoji(guild=guild, state=self, data=data)
        return emoji

    def store_sticker(self, guild: Guild, data: GuildStickerPayload) -> GuildSticker:
        sticker_id = int(data['id'])
        self._stickers[sticker_id] = sticker = GuildSticker(state=self, data=data)
        return sticker

    @property
    def guilds(self) -> Sequence[Guild]:
        return SequenceProxy(self._guilds.values())

    @property
    def lobbies(self) -> Sequence[Lobby]:
        return SequenceProxy(self._lobbies.values())

    def _get_guild(self, guild_id: Optional[int]) -> Optional[Guild]:
        # the keys of self._guilds are ints
        return self._guilds.get(guild_id)  # type: ignore

    def _get_lobby(self, lobby_id: Optional[int]) -> Optional[Lobby]:
        # the keys of self._lobbies are ints
        return self._lobbies.get(lobby_id)  # type: ignore

    def _get_or_create_unavailable_guild(self, guild_id: int, *, data: Optional[Dict[str, Any]] = None) -> Guild:
        return self._guilds.get(guild_id) or Guild._create_unavailable(state=self, guild_id=guild_id, data=data)

    def _add_guild(self, guild: Guild) -> None:
        self._guilds[guild.id] = guild

    def _remove_guild(self, guild: Guild) -> None:
        self._guilds.pop(guild.id, None)

        for emoji in guild.emojis:
            self._emojis.pop(emoji.id, None)

        for sticker in guild.stickers:
            self._stickers.pop(sticker.id, None)

        del guild

    @property
    def emojis(self) -> Sequence[Emoji]:
        return SequenceProxy(self._emojis.values())

    @property
    def stickers(self) -> Sequence[GuildSticker]:
        return SequenceProxy(self._stickers.values())

    @property
    def soundboard_sounds(self) -> List[SoundboardSound]:
        all_sounds = []
        for guild in self.guilds:
            all_sounds.extend(guild.soundboard_sounds)

        return all_sounds

    def get_emoji(self, emoji_id: Optional[int]) -> Optional[Emoji]:
        # the keys of self._emojis are ints
        return self._emojis.get(emoji_id)  # type: ignore

    def get_sticker(self, sticker_id: Optional[int]) -> Optional[GuildSticker]:
        # the keys of self._stickers are ints
        return self._stickers.get(sticker_id)  # type: ignore

    @property
    def private_channels(self) -> Sequence[PrivateChannel]:
        return SequenceProxy(self._private_channels.values())

    def _get_private_channel(self, channel_id: Optional[int]) -> Optional[PrivateChannel]:
        try:
            # the keys of self._private_channels are ints
            value = self._private_channels[channel_id]  # type: ignore
        except KeyError:
            return None
        else:
            # Type narrowing can't figure out that channel_id isn't None here
            self._private_channels.move_to_end(channel_id)  # type: ignore
            return value

    def _get_private_channel_by_user(self, user_id: Optional[int]) -> Optional[Union[DMChannel, EphemeralDMChannel]]:
        # the keys of self._private_channels are ints
        return self._private_channels_by_user.get(user_id)  # type: ignore

    def _add_private_channel(self, channel: PrivateChannel) -> None:
        channel_id = channel.id
        self._private_channels[channel_id] = channel

        if len(self._private_channels) > 128:
            _, to_remove = self._private_channels.popitem(last=False)
            if isinstance(to_remove, (DMChannel, EphemeralDMChannel)) and to_remove.recipient:
                self._private_channels_by_user.pop(to_remove.recipient.id, None)

        if isinstance(channel, (DMChannel, EphemeralDMChannel)) and channel.recipient:
            self._private_channels_by_user[channel.recipient.id] = channel

    @overload
    def add_dm_channel(self, data: DMChannelPayload) -> DMChannel:
        ...

    @overload
    def add_dm_channel(self, data: EphemeralDMChannelPayload) -> EphemeralDMChannel:
        ...

    def add_dm_channel(
        self, data: Union[DMChannelPayload, EphemeralDMChannelPayload]
    ) -> Union[DMChannel, EphemeralDMChannel]:
        # self.user is *always* cached when this is called
        if data['type'] == ChannelType.ephemeral_dm.value:
            cls = EphemeralDMChannel
        else:
            cls = DMChannel

        channel = cls(me=self.user, state=self, data=data)  # type: ignore
        self._add_private_channel(channel)
        return channel

    def _remove_private_channel(self, channel: PrivateChannel) -> None:
        self._private_channels.pop(channel.id, None)
        if isinstance(channel, (DMChannel, EphemeralDMChannel)):
            recipient = channel.recipient
            if recipient is not None:
                self._private_channels_by_user.pop(recipient.id, None)

    def _get_message(self, msg_id: Optional[int]) -> Optional[Message]:
        return find(lambda m: m.id == msg_id, reversed(self._messages)) if self._messages else None

    def _get_lobby_message(self, msg_id: Optional[int]) -> Optional[Message]:
        return find(lambda m: m.id == msg_id, reversed(self._lobby_messages)) if self._lobby_messages else None

    def _add_guild_from_data(self, data: GuildPayload) -> Guild:
        guild = Guild(data=data, state=self)
        self._add_guild(guild)
        return guild

    def _get_guild_channel(
        self, data: PartialMessagePayload, guild_id: Optional[int] = None
    ) -> Tuple[Union[Channel, Thread], Optional[Guild]]:
        if 'channel' in data:
            # We are probably in Ephemeral DM context
            channel_data = data['channel']
            factory, channel_type = _channel_factory(channel_data['type'])

            channel_id = int(channel_data['id'])
            guild_id = _get_as_snowflake(channel_data, 'guild_id')

            if factory is None:
                guild = self._get_guild(guild_id)
                return (
                    PartialMessageable(
                        state=self,
                        id=channel_id,
                        guild_id=guild_id,
                        type=channel_type,
                    ),
                    guild,
                )

            if guild_id is None:
                channel = self._get_private_channel(channel_id)
                if channel is None:
                    channel = factory(me=self.user, state=self, data=channel_data)  # type: ignore
                    self._add_private_channel(channel)  # type: ignore
                    if channel_type is ChannelType.ephemeral_dm:
                        self.dispatch('private_channel_create', channel)
                    return channel, None
                channel._update(channel_data)  # type: ignore
                return channel, None

            guild = self._get_guild(guild_id)
            if guild is None:
                guild = self._get_or_create_unavailable_guild(guild_id)

            channel = guild._resolve_channel(channel_id)
            if channel is None:
                return (
                    factory(state=self, guild=guild, data=channel_data),  # type: ignore
                    guild,
                )
            channel._update(guild, channel_data)  # type: ignore
            return (channel, guild)

        channel_id = int(data['channel_id'])
        try:
            guild_id = guild_id or int(data['guild_id'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
            guild = self._get_guild(guild_id)
        except KeyError:
            channel = self._get_private_channel(channel_id)
            if channel is None:
                if data.get('channel_type') == ChannelType.ephemeral_dm.value:
                    cls = EphemeralDMChannel
                else:
                    cls = DMChannel
                channel = cls._from_message(self, channel_id, _get_as_snowflake(data, 'id') or None)
            guild = None
        else:
            channel = guild and guild._resolve_channel(channel_id)

        return channel or PartialMessageable(state=self, guild_id=guild_id, id=channel_id), guild

    def _get_lobby_channel(
        self,
        channel_id: Optional[int],
        lobby_id: int,
    ) -> Tuple[Union[TextChannel, PartialMessageable], Optional[Guild]]:
        if channel_id is None:
            channel_id = lobby_id

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            channel = None
        else:
            channel = lobby.linked_channel

        if channel is None or not isinstance(channel, TextChannel):
            return (
                PartialMessageable(
                    state=self,
                    id=channel_id,
                    type=ChannelType.lobby,
                ),
                None,
            )
        return channel, channel.guild

    def _update_poll_counts(self, message: Message, answer_id: int, added: bool, self_voted: bool = False) -> Optional[Poll]:
        poll = message.poll
        if not poll:
            return
        poll._handle_vote(answer_id, added, self_voted)
        return poll

    def _update_poll_results(self, from_: Message, to: Union[Message, int]) -> None:
        if isinstance(to, Message):
            cached = self._get_message(to.id)
        elif isinstance(to, int):
            cached = self._get_message(to)

            if cached is None:
                return

            to = cached
        else:
            return

        if to.poll is None:
            return

        to.poll._update_results_from_message(from_)

        if cached is not None and cached.poll:
            cached.poll._update_results_from_message(from_)

    def _get_channel(
        self,
        channel_id: int,
        *,
        guild_id: Optional[int] = None,
        type: Optional[ChannelType] = None,
    ) -> Union[GuildChannel, PrivateChannel, Thread, PartialMessageable]:
        channel = self._get_private_channel(channel_id)
        if channel is not None:
            return channel

        for guild in self._guilds.values():
            channel = guild._resolve_channel(channel)
            if channel is not None:
                return channel

        return PartialMessageable(state=self, id=channel_id, guild_id=guild_id, type=type)

    def parse_ready(self, data: gw.ReadyEvent) -> None:
        self.clear()

        for user_data in data.get('users', ()):
            self.store_user(user_data)

        self.user = user = ClientUser(state=self, data=data['user'])
        self._users[user.id] = user  # type: ignore

        feature_flags = data.get('feature_flags') or {}  # ???

        self.analytics_token = data.get('analytics_token')
        self.av_sf_protocol_floor = data.get('av_sf_protocol_floor', -1)
        self.scopes = tuple(data.get('scopes', ()))

        # disabled_gateway_events is a list like ["LOBBY_CREATE", "LOBBY_UPDATE", "LOBBY_DELETE"] etc
        # disabled_functions is a list like ["CreateOrJoinLobby", "SendUserMessage"]. e.g. if u call
        # [`Client::CreateOrJoinLobby`](https://discord.com/developers/docs/social-sdk/classdiscordpp_1_1Client.html#a8b4e195555ecaa89ccdfc0acd28d3512)
        # and if disabled_functions contains CreateOrJoinLobby, the sdk will return an error.

        self.disabled_gateway_events = tuple(feature_flags.get('disabled_gateway_events', ()))
        self.disabled_functions = tuple(feature_flags.get('disabled_functions', ()))
        self.settings._update(data.get('user_settings') or {}, from_ready=True)

        application_data = data['application']
        self.application_id = int(application_data['id'])
        self.application_name: str = application_data['name']
        self.application_flags: ApplicationFlags = ApplicationFlags._from_value(application_data['flags'])

        for raw_guild_data, raw_guild_members_data in zip(
            data.get('guilds', ()),
            data.get('merged_members', ()),
        ):
            guild_data: GuildPayload = cast('GuildPayload', raw_guild_data)
            guild_members_data: List[MemberWithUserPayload] = cast('List[MemberWithUserPayload]', raw_guild_members_data)
            guild = self._add_guild_from_data(guild_data)

            for guild_member_data in guild_members_data:
                member = Member(data=guild_member_data, guild=guild, state=self)
                guild._add_member(member)

        for pm in data.get('private_channels', ()):
            factory, _ = _private_channel_factory(pm['type'])
            if factory is None:
                continue
            self._add_private_channel(factory(me=user, data=pm, state=self))  # type: ignore

        for relationship_data in data.get('relationships', ()):
            relationship = Relationship(data=relationship_data, state=self)
            self._relationships[relationship.user.id] = relationship

        for game_relationship_data in data.get('game_relationships', ()):
            game_relationship = GameRelationship(data=game_relationship_data, state=self)
            self._game_relationships[game_relationship.user.id] = game_relationship

        for lobby_data in data.get('lobbies', ()):
            lobby = Lobby(data=lobby_data, state=self)
            self._lobbies[lobby.id] = lobby

        self.parse_sessions_replace(data.get('sessions', ()), from_ready=True)

        self.dispatch('connect')

        # Before dispatching ready, we wait for READY_SUPPLEMENTAL
        # It has initial presence cache, as well omitted private channels

    def parse_ready_supplemental(self, data: gw.ReadySupplementalEvent) -> None:
        merged_presences = data.get('merged_presences') or {}

        guilds = []

        for (guild_index, (untyped_guild_data, untyped_guild_members_data, untyped_guild_presences_data),) in enumerate(
            zip(
                data.get('guilds', ()),
                data.get('merged_members', ()),
                merged_presences.get('guilds', ()),
            ),
        ):
            guild_data = cast('gw.SupplementalGuild', untyped_guild_data)
            guild_members_data = cast('List[MemberWithUserPayload]', untyped_guild_members_data)
            guild_presences_data = cast('List[PartialPresenceUpdatePayload]', untyped_guild_presences_data)

            guild_id = int(guild_data['id'])
            guild = self._get_guild(guild_id)

            if guild is None:
                _log.warning(
                    'READY_SUPPLEMENTAL referencing an unknown guild ID: %s at .guilds.%i. Discarding.',
                    guild_id,
                    guild_index,
                )
                continue

            members = [Member(data=guild_member_data, guild=guild, state=self) for guild_member_data in guild_members_data]
            for member in members:
                guild._add_member(member)

            guild_presences = []
            for guild_presence_data in guild_presences_data:
                event = RawPresenceUpdateEvent.__new__(RawPresenceUpdateEvent)
                if 'user' in guild_presence_data:
                    user_data = guild_presence_data['user']
                    user_id = int(user_data['id'])
                else:
                    raw_user_id = guild_presence_data['user_id']
                    user_data = {'id': raw_user_id}
                    user_id = int(raw_user_id)

                event.user_id = user_id
                event.client_status = ClientStatus(
                    status=guild_presence_data['status'], data=guild_presence_data['client_status']
                )
                event.activities = tuple(create_activity(d, self) for d in guild_presence_data['activities'])
                event.guild_id = guild_id
                event.guild = guild

                guild_presences.append(event)
                member = guild.get_member(event.user_id)
                if member is not None:
                    member._presence_update(event, user_data)  # type: ignore

            voice_states = []
            for voice_state_data in guild_data.get('voice_states', ()):
                voice_state_channel_id = _get_as_snowflake(voice_state_data, 'channel_id')
                member, _, voice_state = guild._update_voice_state(voice_state_data, voice_state_channel_id)
                if member is not None:
                    guild._add_member(member)
                voice_states.append(voice_state)

            guilds.append(
                SupplementalGuild(
                    id=guild_id,
                    members=members,
                    presences=guild_presences,
                    voice_states=voice_states,
                    underlying=guild,
                )
            )

        for pm in data.get('lazy_private_channels', ()):
            factory, _ = _private_channel_factory(pm['type'])
            if factory is None:
                continue
            self._add_private_channel(factory(me=self.user, data=pm, state=self))  # type: ignore

        friend_presences = []
        for friend_presence_data in merged_presences.get('friends', ()):
            if 'user' in friend_presence_data:
                user_data = friend_presence_data['user']
            else:
                user_data = {'id': friend_presence_data['user_id']}

            event = RawPresenceUpdateEvent.__new__(RawPresenceUpdateEvent)
            event.user_id = int(user_data['id'])
            event.client_status = ClientStatus(
                status=friend_presence_data['status'], data=friend_presence_data['client_status']
            )
            event.activities = tuple(create_activity(d, self) for d in friend_presence_data['activities'])
            event.guild_id = None
            event.guild = None

            relationship: Union[Relationship, GameRelationship]
            try:
                relationship = self._relationships[event.user_id]
            except KeyError:
                try:
                    relationship = self._game_relationships[event.user_id]
                except KeyError:
                    if len(user_data) > 1:
                        user = self.store_user(user_data, dispatch=True)  # type: ignore
                    else:
                        user = self.get_user(event.user_id) or Object(id=event.user_id)
                    relationship = Relationship._from_implicit(
                        state=self,
                        user=user,  # type: ignore
                    )
                    self._relationships[relationship.id] = relationship
            relationship._presence_update(event, user_data)  # type: ignore
            friend_presences.append(event)

        disclose = data.get('disclose', [])
        self.disclose = disclose

        game_invites = []
        for game_invite_data in data.get('game_invites', ()):
            game_invite = GameInvite(data=game_invite_data, state=self)
            self._game_invites[game_invite.id] = game_invite
            game_invites.append(game_invite)

        raw = RawReadyEvent(
            state=self,
            disclose=disclose,
            friend_presences=friend_presences,
            game_invites=game_invites,
            guilds=guilds,
        )

        self.call_handlers('ready')
        self.dispatch('raw_ready', raw)
        self.dispatch('ready')

    def parse_resumed(self, data: gw.ResumedEvent) -> None:
        self.dispatch('resumed')

    def parse_remote_command(self, data: Any) -> None:
        # This event can have anything as it's payload

        # class RemoteVoiceStateUpdateCommand(sckema.Struct):
        #     self_mute: bool = sckema.Boolean()
        #     self_deaf: bool = sckema.Boolean()
        #
        # class RemoteDisconnectCommand(sckema.Struct):
        #     pass
        #
        # class RemoteAudioSettingsUpdateCommand(sckema.Struct):
        #     context: Literal['user', 'stream'] = sckema.Choice(('user', 'stream'))
        #     id: int = sckema.Integer(coerce={str})
        #
        # remote_command_type = sckema.InternalTaggedEnumType('type', variants={
        #     'VOICE_STATE_UPDATE': RemoteVoiceStateUpdateCommand.finalize(),
        #     'DISCONNECT': RemoteDisconnectCommand.finalize(),
        #     'AUDIO_SETTINGS_UPDATE': RemoteAudioSettingsUpdateCommand.finalize(),
        # })

        self.dispatch('remote_command', data)

    def parse_activity_invite_create(self, data: gw.ActivityInviteCreateEvent) -> None:
        invite = ActivityInvite.from_event(data, state=self)

        self.dispatch('activity_invite', invite)

    def parse_message_create(self, data: gw.MessageCreateEvent) -> None:
        channel, _ = self._get_guild_channel(data)
        # channel would be the correct type here
        message = Message(channel=channel, data=data, state=self)  # type: ignore
        self.dispatch('message', message)
        if self._messages is not None:
            self._messages.append(message)

        # Should be correct:tm: (SDK does not do message.application_id == self.application_id check,
        # for some reason)
        if message.activity is not None:  # and message.application_id == self.application_id:
            activity_invite = ActivityInvite.from_message(message)

            self.dispatch('activity_invite', activity_invite)

        # We ensure that the channel is either a TextChannel, VoiceChannel, or Thread
        if channel and channel.__class__ in (TextChannel, VoiceChannel, Thread, StageChannel):
            channel.last_message_id = message.id  # type: ignore

    def parse_message_delete(self, data: gw.MessageDeleteEvent) -> None:
        raw = RawMessageDeleteEvent(data)
        found = self._get_message(raw.message_id)
        raw.cached_message = found
        if self._messages is not None and found is not None:
            self.dispatch('message_delete', found)
            self._messages.remove(found)
        self.dispatch('raw_message_delete', raw)

    def parse_message_delete_bulk(self, data: gw.MessageDeleteBulkEvent) -> None:
        raw = RawBulkMessageDeleteEvent(data)
        if self._messages:
            found_messages = [message for message in self._messages if message.id in raw.message_ids]
        else:
            found_messages = []
        raw.cached_messages = found_messages
        if found_messages:
            self.dispatch('bulk_message_delete', found_messages)
            for msg in found_messages:
                # self._messages won't be None here
                self._messages.remove(msg)  # type: ignore
        self.dispatch('raw_bulk_message_delete', raw)

    def parse_message_update(self, data: gw.MessageUpdateEvent) -> None:
        channel, _ = self._get_guild_channel(data)
        # channel would be the correct type here
        updated_message = Message(channel=channel, data=data, state=self)  # type: ignore

        raw = RawMessageUpdateEvent(data=data, message=updated_message)
        cached_message = self._get_message(updated_message.id)
        if cached_message is not None:
            older_message = copy(cached_message)
            raw.cached_message = older_message
            self.dispatch('raw_message_edit', raw)
            cached_message._update(data)

            # Coerce the `after` parameter to take the new updated Member
            # ref: #5999
            older_message.author = updated_message.author
            updated_message.metadata = older_message.metadata
            self.dispatch('message_edit', older_message, updated_message)
        else:
            self.dispatch('raw_message_edit', raw)

    def parse_message_reaction_add(self, data: gw.MessageReactionAddEvent) -> None:
        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = self
        raw = RawReactionActionEvent(data, emoji, 'REACTION_ADD')

        member_data = data.get('member')
        if member_data:
            guild = self._get_guild(raw.guild_id)
            if guild is not None:
                raw.member = Member(data=member_data, guild=guild, state=self)
            else:
                raw.member = None
        else:
            raw.member = None

        # Rich interface here
        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            user = raw.member or self._get_reaction_user(message.channel, raw.user_id)

            if user:
                self.dispatch('reaction_add', reaction, user)
        self.dispatch('raw_reaction_add', raw)

    def parse_message_reaction_remove_all(self, data: gw.MessageReactionRemoveAllEvent) -> None:
        raw = RawReactionClearEvent(data)

        message = self._get_message(raw.message_id)
        if message is not None:
            old_reactions = message.reactions.copy()
            message.reactions.clear()
            self.dispatch('reaction_clear', message, old_reactions)
        self.dispatch('raw_reaction_clear', raw)

    def parse_message_reaction_remove(self, data: gw.MessageReactionRemoveEvent) -> None:
        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = self
        raw = RawReactionActionEvent(data, emoji, 'REACTION_REMOVE')

        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            try:
                reaction = message._remove_reaction(data, emoji, raw.user_id)
            except (AttributeError, ValueError):  # Eventual consistency lol
                pass
            else:
                user = self._get_reaction_user(message.channel, raw.user_id)
                if user:
                    self.dispatch('reaction_remove', reaction, user)
        self.dispatch('raw_reaction_remove', raw)

    def parse_message_reaction_remove_emoji(self, data: gw.MessageReactionRemoveEmojiEvent) -> None:
        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = self
        raw = RawReactionClearEmojiEvent(data, emoji)

        message = self._get_message(raw.message_id)
        if message is not None:
            try:
                reaction = message._clear_emoji(emoji)
            except (AttributeError, ValueError):  # Eventual consistency lol
                pass
            else:
                if reaction:
                    self.dispatch('reaction_clear_emoji', reaction)
        self.dispatch('raw_reaction_clear_emoji', raw)

    def parse_presences_replace(self, data: List[gw.PresenceUpdateEvent]) -> None:
        for d in data:
            self.parse_presence_update(d)

    def parse_presence_update(self, data: gw.PresenceUpdateEvent) -> None:
        if data.get('__fake__'):
            _log.debug('Detected possibly fake PRESENCE_UPDATE. Discarding.')
            return

        raw = RawPresenceUpdateEvent(data=data, state=self)

        if raw.guild_id is None:
            old: Union[Relationship, GameRelationship]
            relationship: Union[Relationship, GameRelationship]
            user_update: Optional[Tuple[User, User]] = None

            try:
                relationship = self._relationships[raw.user_id]
            except KeyError:
                try:
                    relationship = self._game_relationships[raw.user_id]
                except KeyError:
                    user_data = data['user']
                    if len(user_data) > 1:
                        user = self.store_user(user_data)
                    else:
                        user = self.get_user(raw.user_id) or Object(id=raw.user_id)

                    relationship = Relationship._from_implicit(state=self, user=user)  # type: ignore
                    old = Relationship._copy(relationship, ClientStatus(), ())
                else:
                    old = copy(relationship)
                    user_update = relationship._presence_update(raw, data['user'])

            else:
                old = copy(relationship)
                user_update = relationship._presence_update(raw, data['user'])

            if user_update:
                self.dispatch('user_update', user_update[0], user_update[1])

            old.user = relationship.user
            raw.pair = (old, relationship)  # type: ignore
            self.dispatch('presence_update', old, relationship)
            self.dispatch('raw_presence_update', raw)
            return

        if raw.guild is None:
            _log.warning('PRESENCE_UPDATE referencing an unknown guild ID: %s. Discarding.', raw.guild_id)
            self.dispatch('raw_presence_update', raw)
            return

        member = raw.guild.get_member(raw.user_id)

        if member is None:
            _log.debug('PRESENCE_UPDATE referencing an unknown member ID: %s. Discarding.', raw.user_id)
            self.dispatch('raw_presence_update', raw)
            return

        old_member = Member._copy(member)
        user_update = member._presence_update(raw=raw, user=data['user'])

        if user_update:
            self.dispatch('user_update', user_update[0], user_update[1])

        raw.pair = (old_member, member)
        self.dispatch('presence_update', old_member, member)
        self.dispatch('raw_presence_update', raw)

    def parse_user_update(self, data: gw.UserUpdateEvent) -> None:
        if self.user is None:
            _log.warning('USER_UPDATE is sent before READY. Discarding.')
            return

        old = copy(self.user)
        self.user._update(data)

        self.dispatch('current_user_update', old, self.user)

    def parse_invite_create(self, data: gw.InviteCreateEvent) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch('invite_create', invite)

    def parse_invite_delete(self, data: gw.InviteDeleteEvent) -> None:
        invite = Invite.from_gateway(state=self, data=data)
        self.dispatch('invite_delete', invite)

    def parse_channel_delete(self, data: gw.ChannelDeleteEvent) -> None:
        channel_id = int(data['id'])
        guild_id = _get_as_snowflake(data, 'guild_id')

        if guild_id is None:
            try:
                channel = self._private_channels.pop(channel_id)
            except KeyError:
                _log.warning('CHANNEL_DELETE referencing an unknown channel ID: %s. Discarding.', channel_id)
            else:
                if isinstance(channel, DMChannel) and channel.recipient is not None:
                    self._private_channels_by_user.pop(channel.recipient.id, None)
                self.dispatch('private_channel_delete', channel)
            return

        guild = self._get_guild(guild_id)
        if guild is None:
            _log.warning('CHANNEL_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        channel = guild.get_channel(channel_id)
        if channel is not None:
            guild._remove_channel(channel)
            self.dispatch('guild_channel_delete', channel)

            if channel.type in (ChannelType.voice, ChannelType.stage_voice):
                for s in guild.scheduled_events:
                    if s.channel_id == channel.id:
                        guild._scheduled_events.pop(s.id)
                        self.dispatch('scheduled_event_delete', s)

            threads = guild._remove_threads_by_channel(channel_id)

            for thread in threads:
                self.dispatch('thread_delete', thread)
                self.dispatch('raw_thread_delete', RawThreadDeleteEvent._from_thread(thread))

    def parse_channel_update(self, data: gw.ChannelUpdateEvent) -> None:
        channel_type = try_enum(ChannelType, data.get('type'))
        channel_id = int(data['id'])
        if channel_type is ChannelType.group:
            channel = self._get_private_channel(channel_id)
            if channel is not None:
                old_channel = copy(channel)
                # the channel is a GroupChannel rather than PrivateChannel
                channel._update(data)  # type: ignore
                self.dispatch('private_channel_update', old_channel, channel)
                return
            else:
                _log.warning('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)

        guild_id = _get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                old_channel = copy(channel)
                channel._update(guild, data)  # type: ignore # the data payload varies based on the channel type.
                self.dispatch('guild_channel_update', old_channel, channel)
            else:
                _log.warning('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
        else:
            _log.warning('CHANNEL_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_channel_update_partial(self, data: gw.ChannelUpdatePartialEvent) -> None:
        channel_id = int(data['id'])
        channel = self._get_channel(channel_id)

        if channel is None:
            _log.warning('CHANNEL_UPDATE_PARTIAL referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        old = copy(channel)

        channel.last_message_id = _get_as_snowflake(data, 'last_message_id')  # type: ignore
        if 'last_pin_timestamp' in data and hasattr(channel, 'last_pin_timestamp'):
            channel.last_pin_timestamp = parse_time(data['last_pin_timestamp'])  # type: ignore

        try:
            is_guild_channel = channel.guild  # pyright: ignore[reportAttributeAccessIssue]
        except AttributeError:
            is_guild_channel = False

        if is_guild_channel:
            self.dispatch('guild_channel_update', old, channel)
        else:
            self.dispatch('private_channel_update', old, channel)

    def parse_channel_create(self, data: gw.ChannelCreateEvent) -> None:
        factory, ch_type = _channel_factory(data['type'])
        if factory is None:
            _log.warning('CHANNEL_CREATE referencing an unknown channel type %s. Discarding.', data['type'])
            return

        guild_id = _get_as_snowflake(data, 'guild_id')
        if guild_id is None:
            channel = factory(me=self.user, state=self, data=data)  # type: ignore
            self._add_private_channel(channel)  # type: ignore
            self.dispatch('private_channel_create', channel)
            return

        guild = self._get_guild(guild_id)
        if guild is None:
            _log.warning('CHANNEL_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        # The factory can't be a DMChannel, GroupChannel or EphemeralDMChannel here
        channel = factory(guild=guild, state=self, data=data)  # type: ignore
        guild._add_channel(channel)  # type: ignore
        self.dispatch('guild_channel_create', channel)

    def parse_channel_pins_update(self, data: gw.ChannelPinsUpdateEvent) -> None:
        channel_id = int(data['channel_id'])
        try:
            guild = self._get_guild(int(data['guild_id']))  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            guild = None
            channel = self._get_private_channel(channel_id)
        else:
            channel = guild and guild._resolve_channel(channel_id)

        if channel is None:
            _log.warning('CHANNEL_PINS_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        last_pin = parse_time(data.get('last_pin_timestamp'))

        if guild is None:
            self.dispatch('private_channel_pins_update', channel, last_pin)
        else:
            self.dispatch('guild_channel_pins_update', channel, last_pin)

    def parse_channel_recipient_add(self, data: gw.ChannelRecipientEvent) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        if channel is None:
            _log.warning('CHANNEL_RECIPIENT_ADD referencing an unknown channel ID: %s. Discarding.', data['channel_id'])
            return

        user = self.store_user(data['user'])
        channel.recipients.append(user)  # type: ignore
        if 'nick' in data:
            channel.nicks[user] = data['nick']  # type: ignore
        self.dispatch('group_join', channel, user)

    def parse_channel_recipient_remove(self, data: gw.ChannelRecipientEvent) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        if channel is None:
            _log.warning('CHANNEL_RECIPIENT_REMOVE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])
            return

        user = self.store_user(data['user'])
        try:
            channel.recipients.remove(user)  # type: ignore
        except ValueError:
            pass
        else:
            self.dispatch('group_remove', channel, user)

    def parse_thread_create(self, data: gw.ThreadCreateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.warning('THREAD_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        existing = guild.get_thread(int(data['id']))
        if existing is not None:  # Shouldn't happen
            old = existing._update(data)
            if old is not None:
                self.dispatch('thread_update', old, existing)
        else:
            thread = Thread(guild=guild, state=self, data=data)
            guild._add_thread(thread)
            if data.get('newly_created', False):
                self.dispatch('thread_create', thread)
            else:
                self.dispatch('thread_join', thread)

    def parse_thread_update(self, data: gw.ThreadUpdateEvent) -> None:
        raw = RawThreadUpdateEvent(data=data)

        self.dispatch('raw_thread_update', raw)
        guild = self._get_guild(raw.guild_id)
        if guild is None:
            _log.warning('THREAD_UPDATE referencing an unknown guild ID: %s. Discarding', raw.guild_id)
            return

        thread_id = int(data['id'])

        existing = guild.get_thread(thread_id)
        if existing is None:
            # Shouldn't happen
            raw.thread = Thread(guild=guild, state=self, data=data)
            guild._add_thread(raw.thread)
        else:
            old = existing._update(data)
            if existing.archived:
                guild._remove_thread(existing)

            raw.old = old
            raw.thread = existing

            if old is not None:
                self.dispatch('thread_update', old, existing)

    def parse_thread_delete(self, data: gw.ThreadDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.warning('THREAD_DELETE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        raw = RawThreadDeleteEvent(data)
        raw.thread = thread = guild.get_thread(raw.thread_id)
        self.dispatch('raw_thread_delete', raw)

        if thread is not None:
            guild._remove_thread(thread)
            self.dispatch('thread_delete', thread)

    def parse_thread_list_sync(self, data: gw.ThreadListSyncEvent) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.warning('THREAD_LIST_SYNC referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        try:
            channel_ids = set(map(int, data['channel_ids']))  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            channel_ids = None
            threads = guild._threads.copy()
        else:
            threads = guild._filter_threads(channel_ids)

        new_threads = {}
        for d in data.get('threads', ()):
            thread_id = int(d['id'])
            try:
                thread = threads.pop(thread_id)
            except KeyError:
                thread = Thread(guild=guild, state=self, data=d)
                new_threads[thread.id] = thread
            else:
                old = thread._update(d)
                if old is not None:
                    self.dispatch('thread_update', old, thread)  # Honestly not sure if this is right
        old_threads = [t for t in threads.values() if t.id not in new_threads]

        for member in data.get('members', ()):
            try:  # Note: member['id'] is the thread_id
                thread = threads[int(member['id'])]
            except KeyError:
                continue
            else:
                thread._add_member(ThreadMember(thread, member))

        for k in new_threads.values():
            guild._add_thread(k)

        for k in old_threads:
            del guild._threads[k.id]
            self.dispatch('thread_delete', k)  # Again, not sure

        for message in data.get('most_recent_messages', ()):
            guild_id = _get_as_snowflake(message, 'guild_id')
            channel, _ = self._get_guild_channel(message)

            # channel will be the correct type here
            message = Message(channel=channel, data=message, state=self)  # type: ignore
            if self._messages is not None:
                self._messages.append(message)

    def parse_thread_member_update(self, data: gw.ThreadMemberUpdate) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.warning('THREAD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        thread_id = int(data['id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        if thread is None:
            _log.warning('THREAD_MEMBER_UPDATE referencing an unknown thread ID: %s. Discarding.', thread_id)
            return

        if thread.me is None:
            me = ThreadMember(thread, data)
            thread.me = me

            # Should be fine:tm:
            self.dispatch('thread_join', me)
        else:
            old_me = copy(thread.me)
            thread.me._from_data(data)
            new_me = thread.me

            if old_me._flags != new_me._flags or old_me.muted != new_me.muted:
                self.dispatch('thread_member_update', old_me, new_me)

    def parse_thread_members_update(self, data: gw.ThreadMembersUpdate) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.warning('THREAD_MEMBERS_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        thread_id = int(data['id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        raw = RawThreadMembersUpdate(data)
        if thread is None:
            _log.warning('THREAD_MEMBERS_UPDATE referencing an unknown thread ID: %s. Discarding.', thread_id)
            return

        added_members = [ThreadMember(thread, d) for d in data.get('added_members', ())]
        removed_member_ids = list(map(int, data.get('removed_member_ids', ())))
        self_id = self.self_id
        for member in added_members:
            if member.id != self_id:
                thread._add_member(member)
                self.dispatch('thread_member_join', member)
            else:
                thread.me = member
                self.dispatch('thread_join', thread)

        for member_id in removed_member_ids:
            member = thread._pop_member(member_id)
            if member_id != self_id:
                self.dispatch('raw_thread_member_remove', raw)
                if member is not None:
                    self.dispatch('thread_member_remove', member)
                else:
                    self.dispatch('raw_thread_member_remove', thread, member_id)
            else:
                self.dispatch('thread_remove', thread)

    def parse_guild_member_add(self, data: gw.GuildMemberAddEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.warning('GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = Member(guild=guild, data=data, state=self)
        if self.member_cache_flags.joined:
            guild._add_member(member)

        if guild._member_count is not None:
            guild._member_count += 1

        self.dispatch('member_join', member)

    def parse_guild_member_remove(self, data: gw.GuildMemberRemoveEvent) -> None:
        user_data = data['user']
        if len(user_data) > 1:
            user = self.store_user(data['user'])
            raw = RawMemberRemoveEvent(data, user)

            guild = self._get_guild(raw.guild_id)
            if guild is not None:
                if guild._member_count is not None:
                    guild._member_count -= 1

                member = guild.get_member(user.id)
                if member is not None:
                    raw.user = member
                    guild._remove_member(member)
                    self.dispatch('member_remove', member)
            else:
                _log.warning('GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

            self.dispatch('raw_member_remove', raw)

    def parse_guild_member_update(self, data: gw.GuildMemberUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        user = data['user']
        user_id = int(user['id'])
        if guild is None:
            _log.warning('GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = guild.get_member(user_id)
        if member is not None:
            old_member = Member._copy(member)
            member._update(data)
            user_update = member._update_inner_user(user)
            if user_update:
                self.dispatch('user_update', user_update[0], user_update[1])

            self.dispatch('member_update', old_member, member)
        else:
            if self.member_cache_flags.joined:
                member = Member(data=data, guild=guild, state=self)  # type: ignore # the data is not complete, contains a delta of values

                # Force an update on the inner user if necessary
                user_update = member._update_inner_user(user)
                if user_update:
                    self.dispatch('user_update', user_update[0], user_update[1])

                guild._add_member(member)

            _log.warning('GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.', user_id)

    def parse_guild_emojis_update(self, data: gw.GuildEmojisUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.warning('GUILD_EMOJIS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_emojis = guild.emojis
        for emoji in before_emojis:
            self._emojis.pop(emoji.id, None)

        guild.emojis = tuple(map(lambda d: self.store_emoji(guild, d), data['emojis']))
        self.dispatch('guild_emojis_update', guild, before_emojis, guild.emojis)

    def parse_guild_stickers_update(self, data: gw.GuildStickersUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.warning('GUILD_STICKERS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_stickers = guild.stickers
        for emoji in before_stickers:
            self._stickers.pop(emoji.id, None)

        guild.stickers = tuple(map(lambda d: self.store_sticker(guild, d), data['stickers']))
        self.dispatch('guild_stickers_update', guild, before_stickers, guild.stickers)

    def parse_auto_moderation_rule_create(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.warning('AUTO_MODERATION_RULE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)

        self.dispatch('automod_rule_create', rule)

    def parse_auto_moderation_rule_update(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.warning('AUTO_MODERATION_RULE_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)

        self.dispatch('automod_rule_update', rule)

    def parse_auto_moderation_rule_delete(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.warning('AUTO_MODERATION_RULE_DELETE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)

        self.dispatch('automod_rule_delete', rule)

    def parse_auto_moderation_action_execution(self, data: AutoModerationActionExecution) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.warning(
                'AUTO_MODERATION_ACTION_EXECUTION referencing an unknown guild ID: %s. Discarding.', data['guild_id']
            )
            return

        execution = AutoModAction(data=data, state=self)

        self.dispatch('automod_action', execution)

    def _get_create_guild(self, data: gw.GuildCreateEvent) -> Guild:
        if data.get('unavailable') is False:
            # GUILD_CREATE with unavailable in the response
            # usually means that the guild has become available
            # and is therefore in the cache
            guild = self._get_guild(int(data['id']))
            if guild is not None:
                guild.unavailable = False
                guild._from_data(data)
                return guild

        return self._add_guild_from_data(data)

    def parse_guild_create(self, data: gw.GuildCreateEvent) -> None:
        guild_id = int(data['id'])
        guild = self._get_guild(guild_id)

        if data.get('unavailable'):
            if guild is None:
                guild = self._get_create_guild(data)
                self.dispatch('guild_join', guild)
            else:
                guild.unavailable = True
                self.dispatch('guild_unavailable', guild)
            return

        joined = guild is None
        guild = self._get_create_guild(data)

        if joined:
            self.dispatch('guild_join', guild)
        else:
            self.dispatch('guild_available', guild)

    def parse_guild_update(self, data: gw.GuildUpdateEvent) -> None:
        guild_id = int(data['id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.', data['id'])
            return

        old_guild = copy(guild)
        guild._from_data(data)
        self.dispatch('guild_update', old_guild, guild)

    def parse_guild_delete(self, data: gw.GuildDeleteEvent) -> None:
        guild_id = int(data['id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        if data.get('unavailable', False):
            # GUILD_DELETE with unavailable being True means that the
            # guild that was available is now currently unavailable
            guild.unavailable = True
            self.dispatch('guild_unavailable', guild)
            return

        # do a cleanup of the messages cache
        if self._messages is not None:
            self._messages: Optional[Deque[Message]] = deque(
                (msg for msg in self._messages if msg.guild != guild), maxlen=self.max_messages
            )

        self._remove_guild(guild)
        self.dispatch('guild_remove', guild)

    def parse_guild_ban_add(self, data: gw.GuildBanAddEvent) -> None:
        # we make the assumption that GUILD_BAN_ADD is done
        # before GUILD_MEMBER_REMOVE is called
        # hence we don't remove it from cache or do anything
        # strange with it, the main purpose of this event
        # is mainly to dispatch to another event worth listening to for logging
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_BAN_ADD referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        try:
            user = User(data=data['user'], state=self)
        except KeyError:
            pass
        else:
            member = guild.get_member(user.id) or user
            self.dispatch('member_ban', guild, member)

    def parse_guild_ban_remove(self, data: gw.GuildBanRemoveEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_BAN_REMOVE referencing an unknown guild ID: %s. Discarding.', guild_id)

        if 'user' in data:
            user = self.store_user(data['user'])
            self.dispatch('member_unban', guild, user)

    def parse_guild_role_create(self, data: gw.GuildRoleCreateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        role_data = data['role']
        role = Role(guild=guild, data=role_data, state=self)
        guild._add_role(role)
        self.dispatch('guild_role_create', role)

    def parse_guild_role_delete(self, data: gw.GuildRoleDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_ROLE_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        role_id = int(data['role_id'])
        try:
            role = guild._remove_role(role_id)
        except KeyError:
            return
        else:
            self.dispatch('guild_role_delete', role)

    def parse_guild_role_update(self, data: gw.GuildRoleUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.warning('GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        role_data = data['role']
        role_id = int(role_data['id'])
        role = guild.get_role(role_id)
        if role is not None:
            old_role = copy(role)
            role._update(role_data)
            self.dispatch('guild_role_update', old_role, role)

    def parse_guild_integrations_update(self, data: gw.GuildIntegrationsUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_INTEGRATIONS_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        self.dispatch('guild_integrations_update', guild)

    def parse_integration_create(self, data: gw.IntegrationCreateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('INTEGRATION_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        cls, _ = _integration_factory(data['type'])
        integration = cls(data=data, guild=guild)
        self.dispatch('integration_create', integration)

    def parse_integration_update(self, data: gw.IntegrationUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('INTEGRATION_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        cls, _ = _integration_factory(data['type'])
        integration = cls(data=data, guild=guild)
        self.dispatch('integration_update', integration)

    def parse_integration_delete(self, data: gw.IntegrationDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('INTEGRATION_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        raw = RawIntegrationDeleteEvent(data, guild=guild)
        self.dispatch('raw_integration_delete', raw)

    def parse_webhooks_update(self, data: gw.WebhooksUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('WEBHOOKS_UPDATE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        channel_id = _get_as_snowflake(data, 'channel_id')
        channel = guild.get_channel(channel_id)

        if channel is None:
            _log.warning('WEBHOOKS_UPDATE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])
            return

        self.dispatch('webhooks_update', channel)

    def parse_stage_instance_create(self, data: gw.StageInstanceCreateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('STAGE_INSTANCE_CREATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        stage_instance = StageInstance(guild=guild, state=self, data=data)
        guild._stage_instances[stage_instance.id] = stage_instance
        self.dispatch('stage_instance_create', stage_instance)

    def parse_stage_instance_update(self, data: gw.StageInstanceUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('STAGE_INSTANCE_UPDATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        stage_instance_id = int(data['id'])
        try:
            stage_instance = guild._stage_instances[stage_instance_id]
        except KeyError:
            _log.warning('STAGE_INSTANCE_UPDATE referencing unknown stage instance ID: %s. Discarding.', data['id'])
            return

        old_stage_instance = copy(stage_instance)
        stage_instance._update(data)
        self.dispatch('stage_instance_update', old_stage_instance, stage_instance)

    def parse_stage_instance_delete(self, data: gw.StageInstanceDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('STAGE_INSTANCE_DELETE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        stage_instance_id = int(data['id'])
        try:
            stage_instance = guild._stage_instances.pop(stage_instance_id)
        except KeyError:
            pass
        else:
            self.dispatch('stage_instance_delete', stage_instance)

    def parse_guild_scheduled_event_create(self, data: gw.GuildScheduledEventCreateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(int(data['guild_id']))

        if guild is None:
            _log.warning('GUILD_SCHEDULED_EVENT_CREATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        scheduled_event = ScheduledEvent(state=self, data=data)
        guild._scheduled_events[scheduled_event.id] = scheduled_event
        self.dispatch('scheduled_event_create', scheduled_event)

    def parse_guild_scheduled_event_update(self, data: gw.GuildScheduledEventUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('SCHEDULED_EVENT_UPDATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        scheduled_event_id = int(data['id'])
        scheduled_event = guild._scheduled_events.get(scheduled_event_id)

        if scheduled_event is None:
            _log.warning(
                'GUILD_SCHEDULED_EVENT_UPDATE referencing unknown scheduled event ID: %s. Discarding.', scheduled_event_id
            )
            return

        old_scheduled_event = copy(scheduled_event)
        scheduled_event._update(data)
        self.dispatch('scheduled_event_update', old_scheduled_event, scheduled_event)

    def parse_guild_scheduled_event_delete(self, data: gw.GuildScheduledEventDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_SCHEDULED_EVENT_DELETE referencing unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        scheduled_event_id = int(data['id'])
        try:
            scheduled_event = guild._scheduled_events.pop(scheduled_event_id)
        except KeyError:
            scheduled_event = ScheduledEvent(state=self, data=data)

        self.dispatch('scheduled_event_delete', scheduled_event)

    def parse_guild_scheduled_event_user_add(self, data: gw.GuildScheduledEventUserAdd) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_SCHEDULED_EVENT_USER_ADD referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        scheduled_event_id = int(data['guild_scheduled_event_id'])
        scheduled_event = guild._scheduled_events.get(scheduled_event_id)

        if scheduled_event is None:
            _log.warning(
                'GUILD_SCHEDULED_EVENT_USER_ADD referencing unknown scheduled event ID: %s. Discarding.',
                scheduled_event_id,
            )
            return

        user_id = int(data['user_id'])
        user = self.get_user(user_id)

        if user is None:
            _log.warning('GUILD_SCHEDULED_EVENT_USER_ADD referencing unknown user ID: %s. Discarding.', user_id)
            return

        scheduled_event._add_user(user)
        self.dispatch('scheduled_event_user_add', scheduled_event, user)

    def parse_guild_scheduled_event_user_remove(self, data: gw.GuildScheduledEventUserRemove) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_SCHEDULED_EVENT_USER_REMOVE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        scheduled_event_id = int(data['guild_scheduled_event_id'])
        scheduled_event = guild._scheduled_events.get(scheduled_event_id)

        if scheduled_event is None:
            _log.warning(
                'GUILD_SCHEDULED_EVENT_USER_REMOVE referencing unknown scheduled event ID: %s. Discarding.',
                scheduled_event_id,
            )
            return

        user_id = int(data['user_id'])
        user = self.get_user(user_id)

        if user is None:
            _log.warning('GUILD_SCHEDULED_EVENT_USER_REMOVE referencing unknown user ID: %s. Discarding.', user_id)
            return

        scheduled_event._pop_user(user.id)
        self.dispatch('scheduled_event_user_remove', scheduled_event, user)

    def parse_guild_soundboard_sound_create(self, data: gw.GuildSoundBoardSoundCreateEvent) -> None:
        guild_id = int(data['guild_id'])  # type: ignore # can't be None here
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_SOUNDBOARD_SOUND_CREATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        sound = SoundboardSound(guild=guild, state=self, data=data)
        guild._add_soundboard_sound(sound)
        self.dispatch('soundboard_sound_create', sound)

    def _update_and_dispatch_sound_update(self, sound: SoundboardSound, data: gw.GuildSoundBoardSoundUpdateEvent):
        old_sound = copy(sound)
        sound._update(data)
        self.dispatch('soundboard_sound_update', old_sound, sound)

    def parse_guild_soundboard_sound_update(self, data: gw.GuildSoundBoardSoundUpdateEvent) -> None:
        guild_id = int(data['guild_id'])  # type: ignore # can't be None here
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_SOUNDBOARD_SOUND_UPDATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        sound_id = int(data['sound_id'])
        sound = guild.get_soundboard_sound(sound_id)
        if sound is None:
            _log.warning('GUILD_SOUNDBOARD_SOUND_UPDATE referencing unknown sound ID: %s. Discarding.', sound_id)
            return

        self._update_and_dispatch_sound_update(sound, data)

    def parse_guild_soundboard_sound_delete(self, data: gw.GuildSoundBoardSoundDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)

        if guild is None:
            _log.warning('GUILD_SOUNDBOARD_SOUND_DELETE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        sound_id = int(data['sound_id'])
        sound = guild.get_soundboard_sound(sound_id)
        if sound is None:
            _log.warning('GUILD_SOUNDBOARD_SOUND_DELETE referencing unknown sound ID: %s. Discarding.', sound_id)
            return

        guild._remove_soundboard_sound(sound)
        self.dispatch('soundboard_sound_delete', sound)

    def parse_guild_soundboard_sounds_update(self, data: gw.GuildSoundBoardSoundsUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('GUILD_SOUNDBOARD_SOUNDS_UPDATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        for raw_sound in data['soundboard_sounds']:
            sound_id = int(raw_sound['sound_id'])
            sound = guild.get_soundboard_sound(sound_id)
            if sound is not None:
                self._update_and_dispatch_sound_update(sound, raw_sound)
            else:
                _log.warning('GUILD_SOUNDBOARD_SOUNDS_UPDATE referencing unknown sound ID: %s. Discarding.', sound_id)

    def parse_application_command_permissions_update(self, data: GuildApplicationCommandPermissionsPayload):
        raw = RawAppCommandPermissionsUpdateEvent(data=data, state=self)
        self.dispatch('raw_app_command_permissions_update', raw)

    def parse_call_create(self, data: gw.CallCreateEvent) -> None:
        channel_id = int(data['channel_id'])
        channel = self._get_private_channel(channel_id)

        if channel is None:
            _log.warning('CALL_CREATE referencing unknown channel ID: %s. Discarding.', channel_id)
            return

        call = self._calls.get(channel_id)
        if call is not None:
            # Should only happen for unavailable calls
            old_call = copy(call)
            call._update(data)
            self.dispatch('call_update', old_call, call)
            return

        message = self._get_message(int(data['message_id']))
        call = channel._add_call(data=data, state=self, message=message, channel=channel)
        self._calls[channel.id] = call
        self.dispatch('call_create', call)

    def parse_call_update(self, data: gw.CallUpdateEvent) -> None:
        channel_id = int(data['channel_id'])
        call = self._calls.get(channel_id)

        if call is None:
            _log.warning('CALL_UPDATE referencing unknown call (channel ID: %s). Discarding.', channel_id)
            return

        old_call = copy(call)
        call._update(data)
        self.dispatch('call_update', old_call, call)

    def parse_call_delete(self, data: gw.CallDeleteEvent) -> None:
        channel_id = int(data['channel_id'])
        call = self._calls.pop(channel_id, None)

        if call is None:
            return

        if data.get('unavailable'):
            old_call = copy(call)
            call.unavailable = True
            self.dispatch('call_update', old_call, call)
            return

        call._delete()
        self._call_message_cache.pop(call._message_id, None)
        self.dispatch('call_delete', call)

    def parse_voice_state_update(self, data: gw.VoiceStateUpdateEvent) -> None:
        guild_id = _get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        channel_id = _get_as_snowflake(data, 'channel_id')
        flags = self.member_cache_flags
        self_id = self.self_id

        if guild_id is not None and guild is None:
            _log.debug('VOICE_STATE_UPDATE referencing unknown guild ID: %s. Discarding.', guild_id)
            return

        user_id = int(data['user_id'])
        if user_id == self_id:
            voice = self._get_voice_client(guild.id if guild else self_id)
            if voice is not None:
                coro = voice.on_voice_state_update(data)
                asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice state update handler'))

        if guild is None:
            user, before, after = self._update_voice_state(data, channel_id)
            if user is None:
                user = Object(user_id)
            self.dispatch('voice_state_update', user, before, after)
            return

        member, before, after = guild._update_voice_state(data, channel_id)
        if member is None:
            _log.debug('VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.', user_id)
            return

        if flags.voice:
            if channel_id is None and flags._voice_only and member.id != self_id:
                guild._remove_member(member)
            elif channel_id is not None:
                guild._add_member(member)

        self.dispatch('voice_state_update', member, before, after)

    def parse_voice_server_update(self, data: gw.VoiceServerUpdateEvent) -> None:
        key_id = _get_as_snowflake(data, 'guild_id')
        if key_id is None:
            key_id = self.self_id

        vc = self._get_voice_client(key_id)
        if vc is not None:
            coro = vc.on_voice_server_update(data)
            asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice server update handler'))

    def parse_voice_channel_effect_send(self, data: gw.VoiceChannelEffectSendEvent):
        guild_id = _get_as_snowflake(data, 'guild_id')
        if guild_id is None:
            guild = None
        else:
            guild = self._get_guild(guild_id)
            if guild is None:
                _log.warning('VOICE_CHANNEL_EFFECT_SEND referencing an unknown guild ID: %s. Discarding.', guild_id)
                return

        effect = VoiceChannelEffect(state=self, data=data, guild=guild)
        self.dispatch('voice_channel_effect', effect)

    def parse_voice_channel_status_update(self, data: gw.VoiceChannelStatusUpdateEvent) -> None:
        raw = RawVoiceChannelStatusUpdateEvent(data)
        guild = self._get_guild(raw.guild_id)
        if guild is not None:
            channel = guild.get_channel(raw.channel_id)
            if channel is not None:
                raw.cached_status = channel.status  # type: ignore # must be a voice channel
                channel.status = raw.status  # type: ignore # must be a voice channel

        self.dispatch('raw_voice_channel_status_update', raw)

    def parse_typing_start(self, data: gw.TypingStartEvent) -> None:
        raw = RawTypingEvent(data)
        raw.user = self.get_user(raw.user_id)
        channel, guild = self._get_guild_channel(data)  # type: ignore

        if channel is not None:
            if raw.user is None:
                if isinstance(channel, (DMChannel, EphemeralDMChannel)):
                    raw.user = channel.recipient
                elif isinstance(channel, GroupChannel):
                    raw.user = find(lambda x: x.id == raw.user_id, channel.recipients)
            if raw.user is None and guild is not None:
                member = guild.get_member(raw.user_id)
                if member is not None:
                    raw.user = member
                elif raw.user is None:
                    member_data = data.get('member')
                    if member_data is not None:
                        raw.user = Member(data=member_data, state=self, guild=guild)

            if raw.user is not None:
                self.dispatch('typing', channel, raw.user, raw.timestamp)

        self.dispatch('raw_typing', raw)

    def parse_entitlement_create(self, data: gw.EntitlementCreateEvent) -> None:
        entitlement = Entitlement(data=data, state=self)
        self.dispatch('entitlement_create', entitlement)

    def parse_entitlement_update(self, data: gw.EntitlementUpdateEvent) -> None:
        entitlement = Entitlement(data=data, state=self)
        self.dispatch('entitlement_update', entitlement)

    def parse_entitlement_delete(self, data: gw.EntitlementDeleteEvent) -> None:
        entitlement = Entitlement(data=data, state=self)
        self.dispatch('entitlement_delete', entitlement)

    def parse_message_poll_vote_add(self, data: gw.PollVoteActionEvent) -> None:
        raw = RawPollVoteActionEvent(data)

        self.dispatch('raw_poll_vote_add', raw)

        message = self._get_message(raw.message_id)
        guild = self._get_guild(raw.guild_id)

        if guild:
            user = guild.get_member(raw.user_id)
        else:
            user = self.get_user(raw.user_id)

        if message and user:
            poll = self._update_poll_counts(message, raw.answer_id, True, raw.user_id == self.self_id)
            if poll:
                self.dispatch('poll_vote_add', user, poll.get_answer(raw.answer_id))

    def parse_message_poll_vote_remove(self, data: gw.PollVoteActionEvent) -> None:
        raw = RawPollVoteActionEvent(data)

        self.dispatch('raw_poll_vote_remove', raw)

        message = self._get_message(raw.message_id)
        guild = self._get_guild(raw.guild_id)

        if guild:
            user = guild.get_member(raw.user_id)
        else:
            user = self.get_user(raw.user_id)

        if message and user:
            poll = self._update_poll_counts(message, raw.answer_id, False, raw.user_id == self.self_id)
            if poll:
                self.dispatch('poll_vote_remove', user, poll.get_answer(raw.answer_id))

    def parse_lobby_create(self, data: gw.LobbyCreateEvent) -> None:
        # This event is dispatched for each pre-existing lobby on startup if capability 1<<16 is not enabled.

        lobby = Lobby(data=data, state=self)
        self._lobbies[lobby.id] = lobby
        self.dispatch('lobby_create', lobby)

    def parse_lobby_update(self, data: gw.LobbyUpdateEvent) -> None:
        lobby_id = int(data['id'])

        after = self._get_lobby(lobby_id)
        if after is None:
            _log.warning('LOBBY_UPDATE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        before = copy(after)
        after._update(data)

        self.dispatch('lobby_update', before, after)

    def parse_lobby_delete(self, data: gw.LobbyDeleteEvent) -> None:
        lobby_id = int(data['id'])

        try:
            lobby = self._lobbies.pop(lobby_id)
        except KeyError:
            _log.warning('LOBBY_DELETE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
        else:
            self.dispatch('lobby_remove', lobby, data['reason'])

    def parse_lobby_member_add(self, data: gw.LobbyMemberAddEvent) -> None:
        lobby_id = int(data['lobby_id'])

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            _log.warning('LOBBY_MEMBER_ADD referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        member = LobbyMember.from_dict(data=data['member'], lobby=lobby, state=self)
        lobby.members.append(member)
        self.dispatch('lobby_join', member)

    # For some reason, SDK treats LOBBY_MEMBER_CONNECT, LOBBY_MEMBER_DISCONNECT and LOBBY_MEMBER_UPDATE as same event
    def parse_lobby_member_connect(self, data: gw.LobbyMemberConnectEvent) -> None:
        self.parse_lobby_member_update(data, event='LOBBY_MEMBER_CONNECT')

    def parse_lobby_member_disconnect(self, data: gw.LobbyMemberDisconnectEvent) -> None:
        self.parse_lobby_member_update(data, event='LOBBY_MEMBER_DISCONNECT')

    # def parse_lobby_member_connect(self, data: gw.LobbyMemberConnectEvent) -> None:
    #     lobby_id = int(data['lobby_id'])

    #     lobby = self._get_lobby(lobby_id)
    #     if lobby is None:
    #         _log.warning('LOBBY_MEMBER_CONNECT referencing an unknown lobby ID: %s. Discarding.', lobby_id)
    #         return

    #     member = LobbyMember.from_dict(data=data['member'], lobby=lobby, state=self)
    #     lobby.members.append(member)
    #     self.dispatch('lobby_connect', member)

    # def parse_lobby_member_disconnect(self, data: gw.LobbyMemberDisconnectEvent) -> None:
    #     lobby_id = int(data['lobby_id'])

    #     lobby = self._get_lobby(lobby_id)
    #     if lobby is None:
    #         _log.warning('LOBBY_MEMBER_DISCONNECT referencing an unknown lobby ID: %s. Discarding.', lobby_id)
    #         return

    #     member = LobbyMember.from_dict(data=data['member'], lobby=lobby, state=self)
    #     lobby.members.append(member)
    #     self.dispatch('lobby_disconnect', member)

    # {
    #   't': 'LOBBY_MEMBER_CONNECT',
    #   's': 194,
    #   'op': 0,
    #   'd': {
    #     'member': {
    #       'user_id': '1073325901825187841',
    #       'user': {'id': '1073325901825187841'},
    #       'metadata': {'baller': 'yus'},
    #       'flags': 1,
    #       'connected': True
    #     },
    #     'lobby_id': 'XXX'
    #   }
    # }

    def parse_lobby_member_update(self, data: gw.LobbyMemberUpdateEvent, *, event: str = 'LOBBY_MEMBER_UPDATE') -> None:
        lobby_id = int(data['lobby_id'])

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            _log.warning('%s referencing an unknown lobby ID: %s. Discarding.', event, lobby_id)
            return

        member_data = data['member']
        member_id = _extract_user_id(member_data)

        new = lobby.get_member(member_id)
        if new is None:
            _log.debug('%s referencing an unknown member ID: %s. Discarding.', event, member_id)
            return

        old = copy(new)
        new._update(member_data)

        self.dispatch('lobby_member_update', old, new)

    def parse_lobby_member_remove(self, data: gw.LobbyMemberRemoveEvent) -> None:
        lobby_id = int(data['lobby_id'])

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            _log.debug('LOBBY_MEMBER_REMOVE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        member_data = data['member']
        member_id = _extract_user_id(member_data)

        removed = None
        for member in lobby.members:
            if member.id == member_id:
                removed = member
                break

        if removed is None:
            _log.debug('LOBBY_MEMBER_REMOVE referencing an unknown member ID: %s.', member_id)

            removed = LobbyMember.from_dict(data=member_data, lobby=lobby, state=self)
        else:
            lobby.members.remove(removed)
            removed._update(member_data)

        self.dispatch('lobby_member_remove', removed)

    def parse_lobby_message_create(self, data: gw.LobbyMessageCreateEvent) -> None:
        channel, _ = self._get_lobby_channel(
            _get_as_snowflake(data, 'channel_id'),
            int(data['lobby_id']),
        )

        message = LobbyMessage(channel=channel, data=data, state=self)
        self.dispatch('lobby_message', message)
        if self._lobby_messages is not None:
            self._lobby_messages.append(message)

        # We ensure that the channel is a TextChannel
        if channel and channel.__class__ is TextChannel:
            channel.last_message_id = message.id  # type: ignore

    def parse_lobby_message_delete(self, data: gw.LobbyMessageDeleteEvent) -> None:
        raw = RawLobbyMessageDeleteEvent(data)
        found = self._get_lobby_message(raw.message_id)
        raw.cached_message = found
        self.dispatch('raw_lobby_message_delete', raw)
        if self._lobby_messages is not None and found is not None:
            self.dispatch('lobby_message_delete', found)
            self._lobby_messages.remove(found)

    def parse_lobby_message_update(self, data: gw.LobbyMessageUpdateEvent) -> None:
        channel, _ = self._get_lobby_channel(
            _get_as_snowflake(data, 'channel_id'),
            int(data['lobby_id']),
        )
        updated_message = LobbyMessage(channel=channel, data=data, state=self)

        raw = RawLobbyMessageUpdateEvent(data=data, message=updated_message)
        cached_message = self._get_lobby_message(updated_message.id)
        if cached_message is not None:
            older_message = copy(cached_message)
            raw.cached_message = older_message
            self.dispatch('raw_lobby_message_edit', raw)
            cached_message._update(data)

            # Coerce the `after` parameter to take the new updated Member
            # ref: #5999
            older_message.author = updated_message.author
            updated_message.metadata = older_message.metadata
            self.dispatch('lobby_message_edit', older_message, updated_message)
        else:
            self.dispatch('raw_lobby_message_edit', raw)

    def parse_lobby_voice_server_update(self, data: gw.LobbyVoiceServerUpdateEvent) -> None:
        key_id = int(data['lobby_id'])

        vc = self._get_voice_client(key_id)
        if vc is not None:
            coro = vc.on_lobby_voice_server_update(data)
            asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice server update handler'))

    def parse_lobby_voice_state_update(self, data: gw.LobbyVoiceStateUpdateEvent) -> None:
        lobby_id = int(data['lobby_id'])
        channel_id = _get_as_snowflake(data, 'channel_id')

        # self.user is *always* cached when this is called
        self_id = self.user.id  # type: ignore

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            _log.warning('LOBBY_VOICE_STATE_UPDATE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        channel = self._get_lobby(channel_id)
        user_id = int(data['user_id'])

        member = lobby.get_member(user_id)
        if member is None:
            _log.warning('LOBBY_VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.', data['user_id'])
            return

        old, new = lobby._update_voice_state(data, channel)
        member.connected = channel is not None
        self.dispatch('lobby_voice_state_update', member, old, new)

        if user_id == self_id:
            voice = self._get_voice_client(lobby.id)
            if voice is not None:
                coro = voice.on_voice_state_update(data)
                asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice state update handler'))

    def parse_relationship_add(self, data: gw.RelationshipAddEvent) -> None:
        r_id = int(data['id'])

        try:
            new = self._relationships[r_id]
        except KeyError:
            relationship = Relationship(state=self, data=data)
            self._relationships[r_id] = relationship
            self.dispatch('relationship_add', relationship)
        else:
            old = copy(new)
            new._update(data)
            old.user = new.user
            self.dispatch('relationship_update', old, new)

    def parse_relationship_update(self, data: gw.RelationshipEvent) -> None:
        r_id = int(data['id'])

        try:
            new = self._relationships[r_id]
        except KeyError:
            relationship = Relationship(state=self, data=data)  # type: ignore
            self._relationships[r_id] = relationship
        else:
            old = copy(new)
            new._update(data)
            old.user = new.user
            self.dispatch('relationship_update', old, new)

    def parse_relationship_remove(self, data: gw.RelationshipEvent) -> None:
        r_id = int(data['id'])

        try:
            old = self._relationships.pop(r_id)
        except KeyError:
            _log.warning('RELATIONSHIP_REMOVE referencing unknown relationship ID: %s. Discarding.', r_id)
        else:
            self.dispatch('relationship_remove', old)

    def parse_game_relationship_add(self, data: gw.GameRelationshipAddEvent) -> None:
        r_id = int(data['id'])

        try:
            new = self._game_relationships[r_id]
        except KeyError:
            game_relationship = GameRelationship(state=self, data=data)
            self._game_relationships[r_id] = game_relationship
            self.dispatch('game_relationship_add', game_relationship)
        else:
            old = copy(new)
            new._update(data)
            self.dispatch('game_relationship_update', old, new)

    def parse_game_relationship_remove(self, data: gw.GameRelationshipRemoveEvent) -> None:
        # TODO: After GAME_RELATIONSHIP_REMOVE, we may get PRESENCE_UPDATE with `guild_id: null`,
        # and `presence_update` gets dispatched, with <Relationship type=implicit>, and <Relationship type=implicit> args
        # This is false, it needs to be fixed

        r_id = int(data['id'])

        try:
            old = self._game_relationships.pop(r_id)
        except KeyError:
            _log.warning('GAME_RELATIONSHIP_REMOVE referencing unknown game relationship ID: %s. Discarding.', r_id)
        else:
            self.dispatch('game_relationship_remove', old)

        ws = self._get_websocket()
        asyncio.create_task(self._prevent_fake_presence_update(ws, r_id))

    async def _prevent_fake_presence_update(self, ws: DiscordWebSocket, user_id: int) -> None:
        fut = ws.wait_for(
            'PRESENCE_UPDATE',
            predicate=(
                lambda data, /: (
                    data.get('guild_id') is None and int(data['user']['id']) == user_id and data['status'] == 'offline'
                )
            ),
        )

        try:
            data = await asyncio.wait_for(fut, timeout=5)
        except asyncio.TimeoutError:
            pass
        else:
            data['__fake__'] = True

    def parse_user_settings_update(self, data: gw.UserSettingsUpdateEvent) -> None:
        old = copy(self.settings)
        self.settings._update(data)
        self.dispatch('settings_update', old, self.settings)
        self.dispatch('internal_settings_update', old, self.settings)

    def parse_sessions_replace(self, payload: gw.SessionsReplaceEvent, *, from_ready: bool = False) -> None:
        data = {s['session_id']: s for s in payload}

        for session_id, session in data.items():
            existing = self._sessions.get(session_id)
            if existing is not None:
                old = copy(existing)
                existing._update(session)
                if not from_ready and (
                    old.status != existing.status
                    or old.active != existing.active
                    or old.activities != existing.activities
                    or old.hidden_activities != existing.hidden_activities
                ):
                    self.dispatch('session_update', old, existing)
            else:
                existing = Session(state=self, data=session)
                self._sessions[session_id] = existing
                if not from_ready:
                    self.dispatch('session_create', existing)

        old_all = None
        if not from_ready:
            removed_sessions = [s for s in self._sessions if s not in data]
            for session_id in removed_sessions:
                if session_id == 'all':
                    old_all = self._sessions.pop('all')
                else:
                    session = self._sessions.pop(session_id)
                    self.dispatch('session_delete', session)

        if 'all' not in self._sessions:
            # The "all" session does not always exist...
            # This usually happens if there is only a single session (us)
            # In the case it is "removed", we try to update the old one
            # Else, we create a new one with fake data
            if len(data) > 1:
                # We have more than one session, this should not happen
                ws = self._get_websocket()
                fake = data[ws.session_id]  # type: ignore
            elif data:
                fake = list(data.values())[0]
            else:
                return

            if old_all is not None:
                old = copy(old_all)
                old_all._update(fake)
                if (
                    old.status != old_all.status
                    or old.active != old_all.active
                    or old.activities != old_all.activities
                    or old.hidden_activities != old_all.hidden_activities
                ):
                    self.dispatch('session_update', old, old_all)
            else:
                old_all = Session._fake_all(state=self, data=fake)
            self._sessions['all'] = old_all

    def parse_subscription_create(self, data: gw.SubscriptionCreateEvent) -> None:
        subscription = Subscription(data=data, state=self)
        self._subscriptions[subscription.id] = subscription
        self.dispatch('subscription_create', subscription)

    def parse_subscription_update(self, data: gw.SubscriptionUpdateEvent) -> None:
        subscription_id = int(data['id'])

        try:
            new = self._subscriptions[subscription_id]
        except KeyError:
            old = None
            new = Subscription(data=data, state=self)
        else:
            old = copy(new)
            new._update(data)

        self.dispatch('subscription_update', old, new)

    def parse_subscription_delete(self, data: gw.SubscriptionDeleteEvent) -> None:
        subscription_id = int(data['id'])

        try:
            subscription = self._subscriptions.pop(subscription_id)
        except KeyError:
            subscription = Subscription(data=data, state=self)
        else:
            subscription._update(data)

        self.dispatch('subscription_delete', subscription)

    def parse_audio_settings_update(self, data: gw.AudioSettingsUpdateEvent) -> None:
        old = AudioSettingsManager._copy(self._audio_settings)
        new = self._audio_settings

        for k, v in data.items():
            context = try_enum(AudioContext, k)
            try:
                audio_settings = new.data[context]
            except KeyError:
                audio_settings = {}
                for i, d in v.items():
                    id = int(i)
                    audio_settings[id] = AudioSettings(data=d, state=self, context=context, id=id)
                new.data[context] = audio_settings
            else:
                for i, d in v.items():
                    id = int(i)

                    try:
                        setting = audio_settings[id]
                    except KeyError:
                        audio_settings[id] = AudioSettings(data=d, state=self, context=context, id=id)
                    else:
                        setting._update(d)

        self.dispatch('audio_settings_update', old, new)

    def parse_user_merge_operation_completed(self, data: gw.UserMergeOperationCompletedEvent) -> None:
        merge_operation_id = int(data['merge_operation_id'])
        source_user_id = int(data['source_user_id'])

        self.dispatch(
            'provisional_account_merged',
            merge_operation_id,
            source_user_id,
        )

    def parse_game_invite_create(self, data: gw.GameInviteCreateEvent) -> None:
        game_invite = GameInvite(data=data, state=self)
        self._game_invites[game_invite.id] = game_invite
        self.dispatch('game_invite_create', game_invite)

    def parse_game_invite_delete(self, data: gw.GameInviteDeleteEvent) -> None:
        invite_id = int(data['invite_id'])
        try:
            game_invite = self._game_invites.pop(invite_id)
        except KeyError:
            _log.warning('GAME_INVITE_DELETE referencing an unknown game invite ID: %s. Discarding.', invite_id)
        else:
            self.dispatch('game_invite_delete', game_invite)

    def parse_game_invite_delete_many(self, data: gw.GameInviteDeleteManyEvent) -> None:
        raw = RawBulkGameInviteDeleteEvent(data)
        for invite_id in raw.invite_ids:
            try:
                invite = self._game_invites.pop(invite_id)
            except KeyError:
                _log.warning('GAME_INVITE_DELETE_MANY referencing an unknown game invite ID: %s. Ignoring.', invite_id)
            else:
                raw.cached_invites.append(invite)

        if raw.cached_invites:
            self.dispatch('bulk_game_invite_delete', raw.cached_invites)
        self.dispatch('raw_bulk_game_invite_delete', raw)

    def parse_stream_create(self, data: gw.StreamCreateEvent) -> None:
        key = data['stream_key']

        try:
            stream = self._streams[key]
        except KeyError:
            stream = Stream(data=data, state=self)
            self._streams[stream.key] = stream
            self.dispatch('stream_create', stream)
        else:
            stream.unavailable = False
            self.dispatch('stream_available', stream)

    def parse_stream_update(self, data: gw.StreamUpdateEvent) -> None:
        key = data['stream_key']
        try:
            new = self._streams[key]
        except KeyError:
            old = PartialStream(key=key, state=self)
            new = Stream(data=data, state=self)
        else:
            old = copy(new)
            new._update(data)
        self.dispatch('stream_update', old, new)

    def parse_stream_delete(self, data: gw.StreamDeleteEvent) -> None:
        key = data['stream_key']

        if data.get('unavailable'):
            try:
                stream = self._streams[key]
            except KeyError:
                stream = PartialStream(key=key, state=self)
            else:
                stream.unavailable = True
            self.dispatch('stream_unavailable', stream)
            return

        try:
            stream = self._streams.pop(key)
        except KeyError:
            stream = PartialStream(key=key, state=self)

        reason = try_enum(StreamDeletionReason, data['reason'])
        self.dispatch('stream_delete', stream, reason)

    # TODO: These events
    # ACTIVITY_INVITE_CREATE (Reverse-engineered the payload, but I need to verify that its actually same)
    # STREAM_SERVER_UPDATE

    def _get_reaction_user(self, channel: MessageableChannel, user_id: int) -> Optional[Union[User, Member]]:
        if isinstance(channel, (TextChannel, Thread, VoiceChannel)):
            return channel.guild.get_member(user_id)
        return self.get_user(user_id)

    def get_reaction_emoji(self, data: PartialEmojiPayload) -> Union[Emoji, PartialEmoji, str]:
        emoji_id = _get_as_snowflake(data, 'id')

        if not emoji_id:
            # the name key will be a str
            return data['name']  # type: ignore

        try:
            return self._emojis[emoji_id]
        except KeyError:
            return PartialEmoji.with_state(
                self, animated=data.get('animated', False), id=emoji_id, name=data['name']  # type: ignore
            )

    def _upgrade_partial_emoji(self, emoji: PartialEmoji) -> Union[Emoji, PartialEmoji, str]:
        emoji_id = emoji.id
        if not emoji_id:
            return emoji.name
        try:
            return self._emojis[emoji_id]
        except KeyError:
            return emoji

    def get_channel(self, id: Optional[int]) -> Optional[Union[Channel, Thread]]:
        if id is None:
            return None

        pm = self._get_private_channel(id)
        if pm is not None:
            return pm

        for guild in self.guilds:
            channel = guild._resolve_channel(id)
            if channel is not None:
                return channel

    def create_message(self, *, channel: MessageableChannel, data: MessagePayload) -> Message:
        return Message(state=self, channel=channel, data=data)

    def get_soundboard_sound(self, id: Optional[int]) -> Optional[SoundboardSound]:
        if id is None:
            return

        for guild in self.guilds:
            sound = guild._resolve_soundboard_sound(id)
            if sound is not None:
                return sound

    @property
    def all_session(self) -> Optional[Session]:
        return self._sessions.get('all')

    @property
    def current_session(self) -> Optional[Session]:
        ws = self._get_websocket()
        return self._sessions.get(ws.session_id)  # type: ignore
