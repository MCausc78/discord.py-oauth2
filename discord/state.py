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
    Dict,
    Optional,
    TYPE_CHECKING,
    Union,
    Callable,
    Any,
    List,
    TypeVar,
    Coroutine,
    Sequence,
    Generic,
    Tuple,
    Deque,
)
import weakref

from . import utils
from ._types import ClientT
from .activity import BaseActivity, Session, create_activity
from .automod import AutoModRule, AutoModAction
from .channel import *
from .channel import _private_channel_factory, _channel_factory
from .emoji import Emoji
from .enums import ChannelType, try_enum, Status
from .flags import ApplicationFlags, Intents, MemberCacheFlags
from .game_relationship import GameRelationship
from .guild import Guild
from .integrations import _integration_factory
from .invite import Invite
from .lobby import LobbyMember, Lobby
from .member import Member
from .mentions import AllowedMentions
from .message import Message
from .object import Object
from .partial_emoji import PartialEmoji
from .presences import ClientStatus, RawPresenceUpdateEvent
from .raw_models import *
from .relationship import Relationship
from .role import Role
from .scheduled_event import ScheduledEvent
from .settings import UserSettings
from .sku import Entitlement
from .soundboard import SoundboardSound
from .stage_instance import StageInstance
from .sticker import GuildSticker
from .subscription import Subscription
from .threads import Thread, ThreadMember
from .user import User, ClientUser

if TYPE_CHECKING:
    from .abc import PrivateChannel
    from .gateway import DiscordWebSocket
    from .guild import GuildChannel
    from .http import HTTPClient
    from .message import MessageableChannel
    from .poll import Poll
    from .voice_client import VoiceProtocol

    from .types import gateway as gw
    from .types.activity import Activity as ActivityPayload
    from .types.automod import AutoModerationRule, AutoModerationActionExecution
    from .types.channel import DMChannel as DMChannelPayload
    from .types.command import GuildApplicationCommandPermissions as GuildApplicationCommandPermissionsPayload
    from .types.emoji import Emoji as EmojiPayload, PartialEmoji as PartialEmojiPayload
    from .types.guild import Guild as GuildPayload
    from .types.message import Message as MessagePayload, PartialMessage as PartialMessagePayload
    from .types.sticker import GuildSticker as GuildStickerPayload
    from .types.user import User as UserPayload, PartialUser as PartialUserPayload

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
        _get_websocket: Callable[..., DiscordWebSocket]
        _get_client: Callable[..., ClientT]
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
        self.loop: asyncio.AbstractEventLoop = utils.MISSING
        self.http: HTTPClient = http
        self.max_messages: Optional[int] = options.get('max_messages', 1000)
        if self.max_messages is not None and self.max_messages <= 0:
            self.max_messages = 1000

        self.dispatch: Callable[..., Any] = dispatch
        self.handlers: Dict[str, Callable[..., Any]] = handlers
        self.hooks: Dict[str, Callable[..., Coroutine[Any, Any, Any]]] = hooks
        self.application_id: Optional[int] = utils._get_as_snowflake(options, 'application_id')
        self.application_name: str = utils.MISSING
        self.application_flags: ApplicationFlags = utils.MISSING
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

        intents = options.get('intents', None)
        if intents is not None:
            if not isinstance(intents, Intents):
                raise TypeError(f'intents parameter must be Intent not {type(intents)!r}')
        else:
            intents = Intents.default()

        if not intents.guilds:
            _log.warning('Guilds intent seems to be disabled. This may cause state related issues.')

        cache_flags = options.get('member_cache_flags', None)
        if cache_flags is None:
            cache_flags = MemberCacheFlags.from_intents(intents)
        else:
            if not isinstance(cache_flags, MemberCacheFlags):
                raise TypeError(f'member_cache_flags parameter must be MemberCacheFlags not {type(cache_flags)!r}')

            cache_flags._verify_intents(intents)

        self.member_cache_flags: MemberCacheFlags = cache_flags
        self._activities: List[ActivityPayload] = activities
        self._status: Optional[str] = status
        self._intents: Intents = intents
        self.raw_presence_flag: bool = options.get('enable_raw_presences', utils.MISSING)
        if self.raw_presence_flag is utils.MISSING:
            self.raw_presence_flag = not intents.members and intents.presences

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
        return self._intents.emojis_and_stickers

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
        self._users: weakref.WeakValueDictionary[int, User] = weakref.WeakValueDictionary()
        # self._users: Dict[int, User] = {}
        self._emojis: Dict[int, Emoji] = {}
        self._stickers: Dict[int, GuildSticker] = {}
        self._guilds: Dict[int, Guild] = {}

        self._lobbies: Dict[int, Lobby] = {}
        self._game_relationships: Dict[int, GameRelationship] = {}
        self._relationships: Dict[int, Relationship] = {}
        self._sessions: Dict[str, Session] = {}
        self._subscriptions: Dict[int, Subscription] = {}

        self.analytics_token: Optional[str] = None
        self.av_sf_protocol_floor: int = -1
        self.disabled_gateway_events: Tuple[str, ...] = ()
        self.disabled_functions: Tuple[str, ...] = ()
        self.disclose: List[str] = []
        self.scopes: Tuple[str, ...] = ()
        self.settings: UserSettings = UserSettings(data={}, state=self)

        self._voice_clients: Dict[int, VoiceProtocol] = {}

        # LRU of max size 128
        self._private_channels: OrderedDict[int, PrivateChannel] = OrderedDict()
        # extra dict to look up private channels by user id
        self._private_channels_by_user: Dict[int, DMChannel] = {}

        if self.max_messages is not None:
            self._messages: Optional[Deque[Message]] = deque(maxlen=self.max_messages)
        else:
            self._messages: Optional[Deque[Message]] = None

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
        ret.value = self._intents.value
        return ret

    @property
    def voice_clients(self) -> List[VoiceProtocol]:
        return list(self._voice_clients.values())

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
        return utils.SequenceProxy(self._guilds.values())

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
        return utils.SequenceProxy(self._emojis.values())

    @property
    def stickers(self) -> Sequence[GuildSticker]:
        return utils.SequenceProxy(self._stickers.values())

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
        return utils.SequenceProxy(self._private_channels.values())

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

    def _get_private_channel_by_user(self, user_id: Optional[int]) -> Optional[DMChannel]:
        # the keys of self._private_channels are ints
        return self._private_channels_by_user.get(user_id)  # type: ignore

    def _add_private_channel(self, channel: PrivateChannel) -> None:
        channel_id = channel.id
        self._private_channels[channel_id] = channel

        if len(self._private_channels) > 128:
            _, to_remove = self._private_channels.popitem(last=False)
            if isinstance(to_remove, DMChannel) and to_remove.recipient:
                self._private_channels_by_user.pop(to_remove.recipient.id, None)

        if isinstance(channel, DMChannel) and channel.recipient:
            self._private_channels_by_user[channel.recipient.id] = channel

    def add_dm_channel(self, data: DMChannelPayload) -> DMChannel:
        # self.user is *always* cached when this is called
        channel = DMChannel(me=self.user, state=self, data=data)  # type: ignore
        self._add_private_channel(channel)
        return channel

    def _remove_private_channel(self, channel: PrivateChannel) -> None:
        self._private_channels.pop(channel.id, None)
        if isinstance(channel, DMChannel):
            recipient = channel.recipient
            if recipient is not None:
                self._private_channels_by_user.pop(recipient.id, None)

    def _get_message(self, msg_id: Optional[int]) -> Optional[Message]:
        return utils.find(lambda m: m.id == msg_id, reversed(self._messages)) if self._messages else None

    def _add_guild_from_data(self, data: GuildPayload) -> Guild:
        guild = Guild(data=data, state=self)
        self._add_guild(guild)
        return guild

    def _get_guild_channel(
        self, data: PartialMessagePayload, guild_id: Optional[int] = None
    ) -> Tuple[Union[Channel, Thread], Optional[Guild]]:
        channel_id = int(data['channel_id'])
        try:
            guild_id = guild_id or int(data['guild_id'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
            guild = self._get_guild(guild_id)
        except KeyError:
            channel = DMChannel._from_message(self, channel_id, int(data.get('id', 0)) or None)
            guild = None
        else:
            channel = guild and guild._resolve_channel(channel_id)

        return channel or PartialMessageable(state=self, guild_id=guild_id, id=channel_id), guild

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
        self.disabled_gateway_events = tuple(feature_flags.get('disabled_gateway_events', ()))
        self.disabled_functions = tuple(feature_flags.get('disabled_functions', ()))
        self.settings._update(data.get('user_settings') or {}, from_ready=True)

        if self.application_id is None:
            try:
                application = data['application']
            except KeyError:
                pass
            else:
                self.application_id = utils._get_as_snowflake(application, 'id')
                self.application_name: str = application['name']
                self.application_flags: ApplicationFlags = ApplicationFlags._from_value(application['flags'])

        for guild_data in data.get('guilds', ()):
            self._add_guild_from_data(guild_data)  # _add_guild_from_data requires a complete Guild payload

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

        self.dispatch('connect')

        # Before dispatching ready, we wait for READY_SUPPLEMENTAL
        # It has initial presence cache, as well omitted private channels

    def parse_ready_supplemental(self, data: gw.ReadySupplementalEvent) -> None:
        merged_presences = data.get('merged_presences') or {}

        guilds = []

        for guild_data, guild_members_data, guild_presences_data in zip(
            data.get('guilds', ()),
            data.get('merged_members', ()),
            merged_presences.get('guilds', ()),
        ):
            guild_id = int(guild_data['id'])
            guild = self._get_guild(guild_id)

            if guild is None:
                _log.debug('READY_SUPPLEMENTAL referencing an unknown guild ID: %s. Discarding.', guild_id)
                continue

            members = [Member(data=guild_member_data, guild=guild, state=self) for guild_member_data in guild_members_data]  # type: ignore # ???
            for member in members:
                guild._add_member(member)

            guild_presences = []
            for guild_presence_data in guild_presences_data:
                event = RawPresenceUpdateEvent.__new__(RawPresenceUpdateEvent)
                event.user_id = int(guild_presence_data['user_id'])  # type: ignore
                event.client_status = ClientStatus(
                    status=guild_presence_data['status'], data=guild_presence_data['client_status']
                )
                event.activities = tuple(create_activity(d, self) for d in guild_presence_data['activities'])
                event.guild_id = guild_id
                event.guild = guild

                guild_presences.append(event)
                member = guild.get_member(event.user_id)
                if member is not None:
                    member._presence_update(event, guild_presence_data['user'])

            guilds.append(
                SupplementalGuild(
                    id=guild_id,
                    members=members,
                    presences=guild_presences,
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

        raw = RawReadyEvent(
            state=self,
            disclose=disclose,
            friend_presences=friend_presences,
            guilds=guilds,
        )

        self.call_handlers('ready')
        self.dispatch('ready', raw)

    def parse_resumed(self, data: gw.ResumedEvent) -> None:
        self.dispatch('resumed')

    def parse_message_create(self, data: gw.MessageCreateEvent) -> None:
        channel, _ = self._get_guild_channel(data)
        # channel would be the correct type here
        message = Message(channel=channel, data=data, state=self)  # type: ignore
        self.dispatch('message', message)
        if self._messages is not None:
            self._messages.append(message)
        # we ensure that the channel is either a TextChannel, VoiceChannel, or Thread
        if channel and channel.__class__ in (TextChannel, VoiceChannel, Thread, StageChannel):
            channel.last_message_id = message.id  # type: ignore

    def parse_message_delete(self, data: gw.MessageDeleteEvent) -> None:
        raw = RawMessageDeleteEvent(data)
        found = self._get_message(raw.message_id)
        raw.cached_message = found
        self.dispatch('raw_message_delete', raw)
        if self._messages is not None and found is not None:
            self.dispatch('message_delete', found)
            self._messages.remove(found)

    def parse_message_delete_bulk(self, data: gw.MessageDeleteBulkEvent) -> None:
        raw = RawBulkMessageDeleteEvent(data)
        if self._messages:
            found_messages = [message for message in self._messages if message.id in raw.message_ids]
        else:
            found_messages = []
        raw.cached_messages = found_messages
        self.dispatch('raw_bulk_message_delete', raw)
        if found_messages:
            self.dispatch('bulk_message_delete', found_messages)
            for msg in found_messages:
                # self._messages won't be None here
                self._messages.remove(msg)  # type: ignore

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
        self.dispatch('raw_reaction_add', raw)

        # rich interface here
        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            reaction = message._add_reaction(data, emoji, raw.user_id)
            user = raw.member or self._get_reaction_user(message.channel, raw.user_id)

            if user:
                self.dispatch('reaction_add', reaction, user)

    def parse_message_reaction_remove_all(self, data: gw.MessageReactionRemoveAllEvent) -> None:
        raw = RawReactionClearEvent(data)
        self.dispatch('raw_reaction_clear', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            old_reactions = message.reactions.copy()
            message.reactions.clear()
            self.dispatch('reaction_clear', message, old_reactions)

    def parse_message_reaction_remove(self, data: gw.MessageReactionRemoveEvent) -> None:
        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = self
        raw = RawReactionActionEvent(data, emoji, 'REACTION_REMOVE')
        self.dispatch('raw_reaction_remove', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            emoji = self._upgrade_partial_emoji(emoji)
            try:
                reaction = message._remove_reaction(data, emoji, raw.user_id)
            except (AttributeError, ValueError):  # eventual consistency lol
                pass
            else:
                user = self._get_reaction_user(message.channel, raw.user_id)
                if user:
                    self.dispatch('reaction_remove', reaction, user)

    def parse_message_reaction_remove_emoji(self, data: gw.MessageReactionRemoveEmojiEvent) -> None:
        emoji = PartialEmoji.from_dict(data['emoji'])
        emoji._state = self
        raw = RawReactionClearEmojiEvent(data, emoji)
        self.dispatch('raw_reaction_clear_emoji', raw)

        message = self._get_message(raw.message_id)
        if message is not None:
            try:
                reaction = message._clear_emoji(emoji)
            except (AttributeError, ValueError):  # eventual consistency lol
                pass
            else:
                if reaction:
                    self.dispatch('reaction_clear_emoji', reaction)

    def parse_presence_update(self, data: gw.PresenceUpdateEvent) -> None:
        raw = RawPresenceUpdateEvent(data=data, state=self)

        if self.raw_presence_flag:
            self.dispatch('raw_presence_update', raw)

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
            self.dispatch('presence_update', old, relationship)
            return

        if raw.guild is None:
            _log.debug('PRESENCE_UPDATE referencing an unknown guild ID: %s. Discarding.', raw.guild_id)
            return

        member = raw.guild.get_member(raw.user_id)

        if member is None:
            _log.debug('PRESENCE_UPDATE referencing an unknown member ID: %s. Discarding', raw.user_id)
            return

        old_member = Member._copy(member)
        user_update = member._presence_update(raw=raw, user=data['user'])

        if user_update:
            self.dispatch('user_update', user_update[0], user_update[1])

        self.dispatch('presence_update', old_member, member)

    def parse_user_update(self, data: gw.UserUpdateEvent) -> None:
        if self.user is None:
            _log.debug('USER_UPDATE is sent before READY. Discarding.')
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
        guild_id = utils._get_as_snowflake(data, 'guild_id')

        if guild_id is None:
            try:
                channel = self._private_channels.pop(channel_id)
            except KeyError:
                _log.debug('CHANNEL_DELETE referencing an unknown channel ID: %s. Discarding.', channel_id)
            else:
                if isinstance(channel, DMChannel) and channel.recipient is not None:
                    self._private_channels_by_user.pop(channel.recipient.id, None)
                self.dispatch('private_channel_delete', channel)
            return

        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('CHANNEL_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)
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
                _log.debug('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)

        guild_id = utils._get_as_snowflake(data, 'guild_id')
        guild = self._get_guild(guild_id)
        if guild is not None:
            channel = guild.get_channel(channel_id)
            if channel is not None:
                old_channel = copy(channel)
                channel._update(guild, data)  # type: ignore # the data payload varies based on the channel type.
                self.dispatch('guild_channel_update', old_channel, channel)
            else:
                _log.debug('CHANNEL_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
        else:
            _log.debug('CHANNEL_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_channel_update_partial(self, data: gw.ChannelUpdatePartialEvent) -> None:
        channel_id = int(data['id'])
        channel = self._get_private_channel(channel_id)

        if channel is None:
            _log.debug('CHANNEL_UPDATE_PARTIAL referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        old = copy(channel)

        channel.last_message_id = utils._get_as_snowflake(data, 'last_message_id')  # type: ignore
        if 'last_pin_timestamp' in data and hasattr(channel, 'last_pin_timestamp'):
            channel.last_pin_timestamp = utils.parse_time(data['last_pin_timestamp'])  # type: ignore

        self.dispatch('private_channel_update', old, channel)

    def parse_channel_create(self, data: gw.ChannelCreateEvent) -> None:
        factory, ch_type = _channel_factory(data['type'])
        if factory is None:
            _log.debug('CHANNEL_CREATE referencing an unknown channel type %s. Discarding.', data['type'])
            return

        guild_id = utils._get_as_snowflake(data, 'guild_id')
        if guild_id is None:
            channel = factory(me=self.user, state=self, data=data)  # type: ignore
            self._add_private_channel(channel)  # type: ignore
            self.dispatch('private_channel_create', channel)
            return

        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('CHANNEL_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        # The factory can't be a DMChannel or GroupChannel here
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
            _log.debug('CHANNEL_PINS_UPDATE referencing an unknown channel ID: %s. Discarding.', channel_id)
            return

        last_pin = utils.parse_time(data.get('last_pin_timestamp'))

        if guild is None:
            self.dispatch('private_channel_pins_update', channel, last_pin)
        else:
            self.dispatch('guild_channel_pins_update', channel, last_pin)

    def parse_channel_recipient_add(self, data: gw.ChannelRecipientEvent) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        if channel is None:
            _log.debug('CHANNEL_RECIPIENT_ADD referencing an unknown channel ID: %s. Discarding.', data['channel_id'])
            return

        user = self.store_user(data['user'])
        channel.recipients.append(user)  # type: ignore
        if 'nick' in data:
            channel.nicks[user] = data['nick']  # type: ignore
        self.dispatch('group_join', channel, user)

    def parse_channel_recipient_remove(self, data: gw.ChannelRecipientEvent) -> None:
        channel = self._get_private_channel(int(data['channel_id']))
        if channel is None:
            _log.debug('CHANNEL_RECIPIENT_REMOVE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])
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
            _log.debug('THREAD_CREATE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        thread = Thread(guild=guild, state=guild._state, data=data)
        has_thread = guild.get_thread(thread.id)
        guild._add_thread(thread)
        if not has_thread:
            if data.get('newly_created'):
                if thread.parent.__class__ is ForumChannel:
                    thread.parent.last_message_id = thread.id  # type: ignore

                self.dispatch('thread_create', thread)
            else:
                self.dispatch('thread_join', thread)

    def parse_thread_update(self, data: gw.ThreadUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_UPDATE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        raw = RawThreadUpdateEvent(data)
        raw.thread = thread = guild.get_thread(raw.thread_id)
        self.dispatch('raw_thread_update', raw)
        if thread is not None:
            old = copy(thread)
            thread._update(data)
            if thread.archived:
                guild._remove_thread(thread)
            self.dispatch('thread_update', old, thread)
        else:
            thread = Thread(guild=guild, state=guild._state, data=data)
            if not thread.archived:
                guild._add_thread(thread)
            self.dispatch('thread_join', thread)

    def parse_thread_delete(self, data: gw.ThreadDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_DELETE referencing an unknown guild ID: %s. Discarding', guild_id)
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
            _log.debug('THREAD_LIST_SYNC referencing an unknown guild ID: %s. Discarding.', guild_id)
            return

        try:
            channel_ids = {int(i) for i in data['channel_ids']}  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            # If not provided, then the entire guild is being synced
            # So all previous thread data should be overwritten
            previous_threads = guild._threads.copy()
            guild._clear_threads()
        else:
            previous_threads = guild._filter_threads(channel_ids)

        threads = {d['id']: guild._store_thread(d) for d in data.get('threads', ())}

        for member in data.get('members', ()):
            try:
                # note: member['id'] is the thread_id
                thread = threads[member['id']]
            except KeyError:
                continue
            else:
                thread._add_member(ThreadMember(thread, member))

        for thread in threads.values():
            old = previous_threads.pop(thread.id, None)
            if old is None:
                self.dispatch('thread_join', thread)

        for thread in previous_threads.values():
            self.dispatch('thread_remove', thread)

    def parse_thread_member_update(self, data: gw.ThreadMemberUpdate) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        thread_id = int(data['id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        if thread is None:
            _log.debug('THREAD_MEMBER_UPDATE referencing an unknown thread ID: %s. Discarding', thread_id)
            return

        member = ThreadMember(thread, data)
        thread.me = member

    def parse_thread_members_update(self, data: gw.ThreadMembersUpdate) -> None:
        guild_id = int(data['guild_id'])
        guild: Optional[Guild] = self._get_guild(guild_id)
        if guild is None:
            _log.debug('THREAD_MEMBERS_UPDATE referencing an unknown guild ID: %s. Discarding', guild_id)
            return

        thread_id = int(data['id'])
        thread: Optional[Thread] = guild.get_thread(thread_id)
        raw = RawThreadMembersUpdate(data)
        if thread is None:
            _log.debug('THREAD_MEMBERS_UPDATE referencing an unknown thread ID: %s. Discarding', thread_id)
            return

        self.dispatch('raw_thread_members_update', raw)
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
            if member_id != self_id:
                member = thread._pop_member(member_id)
                if member is not None:
                    self.dispatch('thread_member_remove', member)
            else:
                self.dispatch('thread_remove', thread)

    def parse_guild_member_add(self, data: gw.GuildMemberAddEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_MEMBER_ADD referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        member = Member(guild=guild, data=data, state=self)
        if self.member_cache_flags.joined:
            guild._add_member(member)

        if guild._member_count is not None:
            guild._member_count += 1

        self.dispatch('member_join', member)

    def parse_guild_member_remove(self, data: gw.GuildMemberRemoveEvent) -> None:
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
            _log.debug('GUILD_MEMBER_REMOVE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

        self.dispatch('raw_member_remove', raw)

    def parse_guild_member_update(self, data: gw.GuildMemberUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        user = data['user']
        user_id = int(user['id'])
        if guild is None:
            _log.debug('GUILD_MEMBER_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
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
            _log.debug('GUILD_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.', user_id)

    def parse_guild_emojis_update(self, data: gw.GuildEmojisUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_EMOJIS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_emojis = guild.emojis
        for emoji in before_emojis:
            self._emojis.pop(emoji.id, None)
        # guild won't be None here
        guild.emojis = tuple(map(lambda d: self.store_emoji(guild, d), data['emojis']))
        self.dispatch('guild_emojis_update', guild, before_emojis, guild.emojis)

    def parse_guild_stickers_update(self, data: gw.GuildStickersUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_STICKERS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        before_stickers = guild.stickers
        for emoji in before_stickers:
            self._stickers.pop(emoji.id, None)

        guild.stickers = tuple(map(lambda d: self.store_sticker(guild, d), data['stickers']))
        self.dispatch('guild_stickers_update', guild, before_stickers, guild.stickers)

    def parse_auto_moderation_rule_create(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_RULE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)

        self.dispatch('automod_rule_create', rule)

    def parse_auto_moderation_rule_update(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_RULE_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)

        self.dispatch('automod_rule_update', rule)

    def parse_auto_moderation_rule_delete(self, data: AutoModerationRule) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_RULE_DELETE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        rule = AutoModRule(data=data, guild=guild, state=self)

        self.dispatch('automod_rule_delete', rule)

    def parse_auto_moderation_action_execution(self, data: AutoModerationActionExecution) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('AUTO_MODERATION_ACTION_EXECUTION referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
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
        guild = self._get_guild(int(data['id']))
        if guild is not None:
            old_guild = copy(guild)
            guild._from_data(data)
            self.dispatch('guild_update', old_guild, guild)
        else:
            _log.debug('GUILD_UPDATE referencing an unknown guild ID: %s. Discarding.', data['id'])

    def parse_guild_delete(self, data: gw.GuildDeleteEvent) -> None:
        guild = self._get_guild(int(data['id']))
        if guild is None:
            _log.debug('GUILD_DELETE referencing an unknown guild ID: %s. Discarding.', data['id'])
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
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                user = User(data=data['user'], state=self)
            except KeyError:
                pass
            else:
                member = guild.get_member(user.id) or user
                self.dispatch('member_ban', guild, member)

    def parse_guild_ban_remove(self, data: gw.GuildBanRemoveEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None and 'user' in data:
            user = self.store_user(data['user'])
            self.dispatch('member_unban', guild, user)

    def parse_guild_role_create(self, data: gw.GuildRoleCreateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('GUILD_ROLE_CREATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])
            return

        role_data = data['role']
        role = Role(guild=guild, data=role_data, state=self)
        guild._add_role(role)
        self.dispatch('guild_role_create', role)

    def parse_guild_role_delete(self, data: gw.GuildRoleDeleteEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            role_id = int(data['role_id'])
            try:
                role = guild._remove_role(role_id)
            except KeyError:
                return
            else:
                self.dispatch('guild_role_delete', role)
        else:
            _log.debug('GUILD_ROLE_DELETE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_role_update(self, data: gw.GuildRoleUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            role_data = data['role']
            role_id = int(role_data['id'])
            role = guild.get_role(role_id)
            if role is not None:
                old_role = copy(role)
                role._update(role_data)
                self.dispatch('guild_role_update', old_role, role)
        else:
            _log.debug('GUILD_ROLE_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_integrations_update(self, data: gw.GuildIntegrationsUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            self.dispatch('guild_integrations_update', guild)
        else:
            _log.debug('GUILD_INTEGRATIONS_UPDATE referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_integration_create(self, data: gw.IntegrationCreateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data['type'])
            integration = cls(data=data, guild=guild)
            self.dispatch('integration_create', integration)
        else:
            _log.debug('INTEGRATION_CREATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_integration_update(self, data: gw.IntegrationUpdateEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            cls, _ = _integration_factory(data['type'])
            integration = cls(data=data, guild=guild)
            self.dispatch('integration_update', integration)
        else:
            _log.debug('INTEGRATION_UPDATE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_integration_delete(self, data: gw.IntegrationDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            raw = RawIntegrationDeleteEvent(data)
            self.dispatch('raw_integration_delete', raw)
        else:
            _log.debug('INTEGRATION_DELETE referencing an unknown guild ID: %s. Discarding.', guild_id)

    def parse_webhooks_update(self, data: gw.WebhooksUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is None:
            _log.debug('WEBHOOKS_UPDATE referencing an unknown guild ID: %s. Discarding', data['guild_id'])
            return

        channel_id = utils._get_as_snowflake(data, 'channel_id')
        channel = guild.get_channel(channel_id)  # type: ignore # None is okay here
        if channel is not None:
            self.dispatch('webhooks_update', channel)
        else:
            _log.debug('WEBHOOKS_UPDATE referencing an unknown channel ID: %s. Discarding.', data['channel_id'])

    def parse_stage_instance_create(self, data: gw.StageInstanceCreateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            stage_instance = StageInstance(guild=guild, state=self, data=data)
            guild._stage_instances[stage_instance.id] = stage_instance
            self.dispatch('stage_instance_create', stage_instance)
        else:
            _log.debug('STAGE_INSTANCE_CREATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_stage_instance_update(self, data: gw.StageInstanceUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            stage_instance = guild._stage_instances.get(int(data['id']))
            if stage_instance is not None:
                old_stage_instance = copy(stage_instance)
                stage_instance._update(data)
                self.dispatch('stage_instance_update', old_stage_instance, stage_instance)
            else:
                _log.debug('STAGE_INSTANCE_UPDATE referencing unknown stage instance ID: %s. Discarding.', data['id'])
        else:
            _log.debug('STAGE_INSTANCE_UPDATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_stage_instance_delete(self, data: gw.StageInstanceDeleteEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            try:
                stage_instance = guild._stage_instances.pop(int(data['id']))
            except KeyError:
                pass
            else:
                self.dispatch('stage_instance_delete', stage_instance)
        else:
            _log.debug('STAGE_INSTANCE_DELETE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_create(self, data: gw.GuildScheduledEventCreateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = ScheduledEvent(state=self, data=data)
            guild._scheduled_events[scheduled_event.id] = scheduled_event
            self.dispatch('scheduled_event_create', scheduled_event)
        else:
            _log.debug('SCHEDULED_EVENT_CREATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_update(self, data: gw.GuildScheduledEventUpdateEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = guild._scheduled_events.get(int(data['id']))
            if scheduled_event is not None:
                old_scheduled_event = copy(scheduled_event)
                scheduled_event._update(data)
                self.dispatch('scheduled_event_update', old_scheduled_event, scheduled_event)
            else:
                _log.debug('SCHEDULED_EVENT_UPDATE referencing unknown scheduled event ID: %s. Discarding.', data['id'])
        else:
            _log.debug('SCHEDULED_EVENT_UPDATE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_delete(self, data: gw.GuildScheduledEventDeleteEvent) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = guild._scheduled_events.pop(int(data['id']), ScheduledEvent(state=self, data=data))
            self.dispatch('scheduled_event_delete', scheduled_event)
        else:
            _log.debug('SCHEDULED_EVENT_DELETE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_user_add(self, data: gw.GuildScheduledEventUserAdd) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = guild._scheduled_events.get(int(data['guild_scheduled_event_id']))
            if scheduled_event is not None:
                user = self.get_user(int(data['user_id']))
                if user is not None:
                    scheduled_event._add_user(user)
                    self.dispatch('scheduled_event_user_add', scheduled_event, user)
                else:
                    _log.debug('SCHEDULED_EVENT_USER_ADD referencing unknown user ID: %s. Discarding.', data['user_id'])
            else:
                _log.debug(
                    'SCHEDULED_EVENT_USER_ADD referencing unknown scheduled event ID: %s. Discarding.',
                    data['guild_scheduled_event_id'],
                )
        else:
            _log.debug('SCHEDULED_EVENT_USER_ADD referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_scheduled_event_user_remove(self, data: gw.GuildScheduledEventUserRemove) -> None:
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            scheduled_event = guild._scheduled_events.get(int(data['guild_scheduled_event_id']))
            if scheduled_event is not None:
                user = self.get_user(int(data['user_id']))
                if user is not None:
                    scheduled_event._pop_user(user.id)
                    self.dispatch('scheduled_event_user_remove', scheduled_event, user)
                else:
                    _log.debug('SCHEDULED_EVENT_USER_REMOVE referencing unknown user ID: %s. Discarding.', data['user_id'])
            else:
                _log.debug(
                    'SCHEDULED_EVENT_USER_REMOVE referencing unknown scheduled event ID: %s. Discarding.',
                    data['guild_scheduled_event_id'],
                )
        else:
            _log.debug('SCHEDULED_EVENT_USER_REMOVE referencing unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_guild_soundboard_sound_create(self, data: gw.GuildSoundBoardSoundCreateEvent) -> None:
        guild_id = int(data['guild_id'])  # type: ignore # can't be None here
        guild = self._get_guild(guild_id)
        if guild is not None:
            sound = SoundboardSound(guild=guild, state=self, data=data)
            guild._add_soundboard_sound(sound)
            self.dispatch('soundboard_sound_create', sound)
        else:
            _log.debug('GUILD_SOUNDBOARD_SOUND_CREATE referencing unknown guild ID: %s. Discarding.', guild_id)

    def _update_and_dispatch_sound_update(self, sound: SoundboardSound, data: gw.GuildSoundBoardSoundUpdateEvent):
        old_sound = copy(sound)
        sound._update(data)
        self.dispatch('soundboard_sound_update', old_sound, sound)

    def parse_guild_soundboard_sound_update(self, data: gw.GuildSoundBoardSoundUpdateEvent) -> None:
        guild_id = int(data['guild_id'])  # type: ignore # can't be None here
        guild = self._get_guild(guild_id)
        if guild is not None:
            sound_id = int(data['sound_id'])
            sound = guild.get_soundboard_sound(sound_id)
            if sound is not None:
                self._update_and_dispatch_sound_update(sound, data)
            else:
                _log.warning('GUILD_SOUNDBOARD_SOUND_UPDATE referencing unknown sound ID: %s. Discarding.', sound_id)
        else:
            _log.debug('GUILD_SOUNDBOARD_SOUND_UPDATE referencing unknown guild ID: %s. Discarding.', guild_id)

    def parse_guild_soundboard_sound_delete(self, data: gw.GuildSoundBoardSoundDeleteEvent) -> None:
        guild_id = int(data['guild_id'])
        guild = self._get_guild(guild_id)
        if guild is not None:
            sound_id = int(data['sound_id'])
            sound = guild.get_soundboard_sound(sound_id)
            if sound is not None:
                guild._remove_soundboard_sound(sound)
                self.dispatch('soundboard_sound_delete', sound)
            else:
                _log.warning('GUILD_SOUNDBOARD_SOUND_DELETE referencing unknown sound ID: %s. Discarding.', sound_id)
        else:
            _log.debug('GUILD_SOUNDBOARD_SOUND_DELETE referencing unknown guild ID: %s. Discarding.', guild_id)

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

    def parse_voice_state_update(self, data: gw.VoiceStateUpdateEvent) -> None:
        guild = self._get_guild(utils._get_as_snowflake(data, 'guild_id'))
        channel_id = utils._get_as_snowflake(data, 'channel_id')
        flags = self.member_cache_flags
        # self.user is *always* cached when this is called
        self_id = self.user.id  # type: ignore
        if guild is not None:
            if int(data['user_id']) == self_id:
                voice = self._get_voice_client(guild.id)
                if voice is not None:
                    coro = voice.on_voice_state_update(data)
                    asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice state update handler'))

            member, before, after = guild._update_voice_state(data, channel_id)  # type: ignore
            if member is not None:
                if flags.voice:
                    if channel_id is None and flags._voice_only and member.id != self_id:
                        # Only remove from cache if we only have the voice flag enabled
                        guild._remove_member(member)
                    elif channel_id is not None:
                        guild._add_member(member)

                self.dispatch('voice_state_update', member, before, after)
            else:
                _log.debug('VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.', data['user_id'])

    def parse_voice_channel_effect_send(self, data: gw.VoiceChannelEffectSendEvent):
        guild = self._get_guild(int(data['guild_id']))
        if guild is not None:
            effect = VoiceChannelEffect(state=self, data=data, guild=guild)
            self.dispatch('voice_channel_effect', effect)
        else:
            _log.debug('VOICE_CHANNEL_EFFECT_SEND referencing an unknown guild ID: %s. Discarding.', data['guild_id'])

    def parse_voice_channel_status_update(self, data: gw.VoiceChannelStatusUpdateEvent) -> None:
        raw = RawVoiceChannelStatusUpdateEvent(data)
        guild = self._get_guild(raw.guild_id)
        if guild is not None:
            channel = guild.get_channel(raw.channel_id)
            if channel is not None:
                raw.cached_status = channel.status  # type: ignore # must be a voice channel
                channel.status = raw.status  # type: ignore # must be a voice channel

        self.dispatch('raw_voice_channel_status_update', raw)

    def parse_voice_server_update(self, data: gw.VoiceServerUpdateEvent) -> None:
        key_id = int(data['guild_id'])

        vc = self._get_voice_client(key_id)
        if vc is not None:
            coro = vc.on_voice_server_update(data)
            asyncio.create_task(logging_coroutine(coro, info='Voice Protocol voice server update handler'))

    def parse_typing_start(self, data: gw.TypingStartEvent) -> None:
        raw = RawTypingEvent(data)
        raw.user = self.get_user(raw.user_id)
        channel, guild = self._get_guild_channel(data)

        if channel is not None:
            if raw.user is None:
                if isinstance(channel, DMChannel):
                    raw.user = channel.recipient
                elif isinstance(channel, GroupChannel):
                    raw.user = utils.find(lambda x: x.id == raw.user_id, channel.recipients)
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
            _log.debug('LOBBY_UPDATE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        before = copy(after)
        after._update(data)

        self.dispatch('lobby_update', before, after)

    def parse_lobby_delete(self, data: gw.LobbyDeleteEvent) -> None:
        lobby_id = int(data['id'])

        try:
            lobby = self._lobbies.pop(lobby_id)
        except KeyError:
            _log.debug('LOBBY_DELETE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
        else:
            self.dispatch('lobby_remove', lobby, data['reason'])

    def parse_lobby_member_add(self, data: gw.LobbyMemberAddEvent) -> None:
        lobby_id = int(data['lobby_id'])

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            _log.debug('LOBBY_MEMBER_ADD referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        member = LobbyMember.from_dict(data=data['member'], lobby=lobby, state=self)
        lobby.members.append(member)
        self.dispatch('lobby_join', member)

    def parse_lobby_member_update(self, data: gw.LobbyMemberUpdateEvent) -> None:
        lobby_id = int(data['lobby_id'])

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            _log.debug('LOBBY_MEMBER_UPDATE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        member_data = data['member']
        member_id = int(member_data['id'])

        new = lobby.get_member(member_id)
        if new is None:
            _log.debug('LOBBY_MEMBER_UPDATE referencing an unknown member ID: %s. Discarding.', member_id)
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
        member_id = int(member_data['id'])

        removed = None
        for member in lobby.members:
            if member.id == member_id:
                removed = member
                break

        if removed is None:
            _log.debug('LOBBY_MEMBER_REMOVE referencing an unknown member ID: %s.', member_id)

            removed = LobbyMember.from_dict(data=member_data, lobby=lobby, state=self)
        else:
            removed._update(member_data)

        self.dispatch('lobby_member_remove', removed)

    def parse_lobby_voice_state_update(self, data: gw.LobbyVoiceStateUpdateEvent) -> None:
        lobby_id = int(data['lobby_id'])
        channel_id = utils._get_as_snowflake(data, 'channel_id')

        # self.user is *always* cached when this is called
        self_id = self.user.id  # type: ignore

        lobby = self._get_lobby(lobby_id)
        if lobby is None:
            _log.debug('LOBBY_VOICE_STATE_UPDATE referencing an unknown lobby ID: %s. Discarding.', lobby_id)
            return

        channel = self._get_lobby(channel_id)
        user_id = int(data['user_id'])

        member = lobby.get_member(user_id)
        if member is None:
            _log.debug('LOBBY_VOICE_STATE_UPDATE referencing an unknown member ID: %s. Discarding.', data['user_id'])
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
        r_id = int(data['id'])

        try:
            old = self._game_relationships.pop(r_id)
        except KeyError:
            _log.warning('GAME_RELATIONSHIP_REMOVE referencing unknown game relationship ID: %s. Discarding.', r_id)
        else:
            self.dispatch('game_relationship_remove', old)

    def parse_user_settings_update(self, data: gw.UserSettingsUpdateEvent) -> None:
        old = copy(self.settings)
        self.settings._update(data)
        self.dispatch('settings_update', old, self.settings)
        self.dispatch('internal_settings_update', old, self.settings)

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

    def _get_reaction_user(self, channel: MessageableChannel, user_id: int) -> Optional[Union[User, Member]]:
        if isinstance(channel, (TextChannel, Thread, VoiceChannel)):
            return channel.guild.get_member(user_id)
        return self.get_user(user_id)

    def get_reaction_emoji(self, data: PartialEmojiPayload) -> Union[Emoji, PartialEmoji, str]:
        emoji_id = utils._get_as_snowflake(data, 'id')

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
        return self._sessions.get(self.session_id)  # type: ignore
