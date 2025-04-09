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

import datetime
from typing import (
    Any,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    TypeVar,
    Union,
)

import slaycord.abc

from . import utils
from .asset import Asset
from .enums import (
    ChannelType,
    ForumLayoutType,
    ForumOrderType,
    try_enum,
    VideoQualityMode,
    EntityType,
    VoiceChannelEffectAnimationType,
)
from .flags import ChannelFlags
from .lobby import LinkedLobby
from .mixins import Hashable
from .object import Object
from .partial_emoji import _EmojiTag, PartialEmoji
from .permissions import Permissions
from .scheduled_event import ScheduledEvent
from .soundboard import BaseSoundboardSound
from .stage_instance import StageInstance
from .threads import Thread

__all__ = (
    'TextChannel',
    'VoiceChannel',
    'StageChannel',
    'DMChannel',
    'CategoryChannel',
    'ForumTag',
    'ForumChannel',
    'GroupChannel',
    'EphemeralDMChannel',
    'PartialMessageable',
    'VoiceChannelEffect',
    'VoiceChannelSoundEffect',
    '_guild_channel_factory',
    '_private_channel_factory',
    '_channel_factory',
    '_threaded_channel_factory',
    '_threaded_guild_channel_factory',
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import Snowflake
    from .guild import Guild, GuildChannel as GuildChannelType
    from .member import Member, VoiceState
    from .message import Message, PartialMessage, EmojiInputType
    from .role import Role
    from .state import ConnectionState
    from .types.channel import (
        TextChannel as TextChannelPayload,
        NewsChannel as NewsChannelPayload,
        VoiceChannel as VoiceChannelPayload,
        StageChannel as StageChannelPayload,
        DMChannel as DMChannelPayload,
        CategoryChannel as CategoryChannelPayload,
        GroupDMChannel as GroupChannelPayload,
        GroupDMNickname as GroupDMNicknamePayload,
        ForumChannel as ForumChannelPayload,
        MediaChannel as MediaChannelPayload,
        ForumTag as ForumTagPayload,
        VoiceChannelEffect as VoiceChannelEffectPayload,
    )
    from .types.soundboard import BaseSoundboardSound as BaseSoundboardSoundPayload
    from .types.threads import ThreadArchiveDuration
    from .user import ClientUser, User, BaseUser

    OverwriteKeyT = TypeVar('OverwriteKeyT', Role, BaseUser, Object, Union[Role, Member, Object])


class ThreadWithMessage(NamedTuple):
    thread: Thread
    message: Message


class VoiceChannelEffectAnimation(NamedTuple):
    id: int
    type: VoiceChannelEffectAnimationType


class VoiceChannelSoundEffect(BaseSoundboardSound):
    """Represents a Discord voice channel sound effect.

    .. versionadded:: 2.5

    .. container:: operations

        .. describe:: x == y

            Checks if two sound effects are equal.

        .. describe:: x != y

            Checks if two sound effects are not equal.

        .. describe:: hash(x)

            Returns the sound effect's hash.

    Attributes
    ----------
    id: :class:`int`
        The ID of the sound.
    volume: :class:`float`
        The volume of the sound as floating point percentage (e.g. ``1.0`` for 100%).
    """

    __slots__ = ('_state',)

    def __init__(self, *, state: ConnectionState, id: int, volume: float):
        data: BaseSoundboardSoundPayload = {
            'sound_id': id,
            'volume': volume,
        }
        super().__init__(state=state, data=data)

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} id={self.id} volume={self.volume}>"

    @property
    def created_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the snowflake's creation time in UTC.
        Returns ``None`` if it's a default sound."""
        if self.is_default():
            return None
        else:
            return utils.snowflake_time(self.id)

    def is_default(self) -> bool:
        """:class:`bool`: Whether it's a default sound or not."""
        # if it's smaller than the Discord Epoch it cannot be a snowflake
        return self.id < utils.DISCORD_EPOCH


class VoiceChannelEffect:
    """Represents a Discord voice channel effect.

    .. versionadded:: 2.5

    Attributes
    ----------
    channel: :class:`VoiceChannel`
        The channel in which the effect is sent.
    user: Optional[:class:`Member`]
        The user who sent the effect. ``None`` if not found in cache.
    animation: Optional[:class:`VoiceChannelEffectAnimation`]
        The animation the effect has. Returns ``None`` if the effect has no animation.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the effect.
    sound: Optional[:class:`VoiceChannelSoundEffect`]
        The sound of the effect. Returns ``None`` if it's an emoji effect.
    """

    __slots__ = ('channel', 'user', 'animation', 'emoji', 'sound')

    def __init__(self, *, state: ConnectionState, data: VoiceChannelEffectPayload, guild: Guild):
        self.channel: VoiceChannel = guild.get_channel(int(data['channel_id']))  # type: ignore # will always be a VoiceChannel
        self.user: Optional[Member] = guild.get_member(int(data['user_id']))
        self.animation: Optional[VoiceChannelEffectAnimation] = None

        animation_id = data.get('animation_id')
        if animation_id is not None:
            animation_type = try_enum(VoiceChannelEffectAnimationType, data['animation_type'])  # type: ignore # cannot be None here
            self.animation = VoiceChannelEffectAnimation(id=animation_id, type=animation_type)

        emoji = data.get('emoji')
        self.emoji: Optional[PartialEmoji] = PartialEmoji.from_dict(emoji) if emoji is not None else None
        self.sound: Optional[VoiceChannelSoundEffect] = None

        sound_id: Optional[int] = utils._get_as_snowflake(data, 'sound_id')
        if sound_id is not None:
            sound_volume = data.get('sound_volume') or 0.0
            self.sound = VoiceChannelSoundEffect(state=state, id=sound_id, volume=sound_volume)

    def __repr__(self) -> str:
        attrs = [
            ('channel', self.channel),
            ('user', self.user),
            ('animation', self.animation),
            ('emoji', self.emoji),
            ('sound', self.sound),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f"<{self.__class__.__name__} {inner}>"

    def is_sound(self) -> bool:
        """:class:`bool`: Whether the effect is a sound or not."""
        return self.sound is not None


class TextChannel(slaycord.abc.Messageable, slaycord.abc.GuildChannel, Hashable):
    """Represents a Discord guild text channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    topic: Optional[:class:`str`]
        The channel's topic. ``None`` if it doesn't exist.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    linked_lobby: Optional[:class:`~slaycord.LinkedLobby`]
        The lobby linked to the channel.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work" or "age restricted".
    default_auto_archive_duration: :class:`int`
        The default auto archive duration in minutes for threads created in this channel.

        .. versionadded:: 2.0
    default_thread_slowmode_delay: :class:`int`
        The default slowmode delay in seconds for threads created in this channel.

        .. versionadded:: 2.3
    """

    __slots__ = (
        '_overwrites',
        '_state',
        '_type',
        'name',
        'guild',
        'id',
        'category_id',
        'topic',
        'position',
        'linked_lobby',
        'last_message_id',
        'slowmode_delay',
        'nsfw',
        'default_auto_archive_duration',
        'default_thread_slowmode_delay',
    )

    def __init__(self, *, state: ConnectionState, guild: Guild, data: Union[TextChannelPayload, NewsChannelPayload]):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self._type: Literal[0, 5] = data['type']
        self._update(guild, data)

    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('nsfw', self.nsfw),
            ('news', self.is_news()),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'

    def _update(self, guild: Guild, data: Union[TextChannelPayload, NewsChannelPayload]) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.topic: Optional[str] = data.get('topic')
        self.position: int = data['position']
        self.nsfw: bool = data.get('nsfw', False)
        # Does this need coercion into `int`? No idea yet.
        self.slowmode_delay: int = data.get('rate_limit_per_user', 0)
        self.default_auto_archive_duration: ThreadArchiveDuration = data.get('default_auto_archive_duration', 1440)
        self.default_thread_slowmode_delay: int = data.get('default_thread_rate_limit_per_user', 0)
        self._type: Literal[0, 5] = data.get('type', self._type)
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')

        linked_lobby_data = data.get('linked_lobby')
        if linked_lobby_data is None:
            self.linked_lobby: Optional[LinkedLobby] = None
        else:
            self.linked_lobby = LinkedLobby(data=linked_lobby_data, state=self._state)

        self._fill_overwrites(data)

    async def _get_messageable_destination(
        self,
    ) -> Tuple[int, slaycord.abc.MessageableDestinationType,]:
        ll = self.linked_lobby
        if ll is None:
            return (self.id, 'channel')
        return (ll.lobby_id, 'lobby')

    @property
    def type(self) -> Literal[ChannelType.text, ChannelType.news]:
        """:class:`ChannelType`: The channel's Discord type."""
        if self._type == 0:
            return ChannelType.text
        return ChannelType.news

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.text.value

    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return None

    @utils.copy_doc(slaycord.abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)
        self._apply_implicit_permissions(base)

        # text channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all members that can see this channel."""
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    @property
    def threads(self) -> List[Thread]:
        """List[:class:`Thread`]: Returns all the threads that you can see.

        .. versionadded:: 2.0
        """
        return [thread for thread in self.guild._threads.values() if thread.parent_id == self.id]

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the channel is NSFW."""
        return self.nsfw

    def is_news(self) -> bool:
        """:class:`bool`: Checks if the channel is a news channel."""
        return self._type == ChannelType.news.value

    @property
    def last_message(self) -> Optional[Message]:
        """Retrieves the last message from this channel in cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        -------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        .. versionchanged:: 2.0

            ``message_id`` parameter is now positional-only.

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)

    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        """Returns a thread with the given ID.

        .. note::

            This does not always retrieve archived threads, as they are not retained in the internal
            cache. Use :func:`Guild.fetch_channel` instead.

        .. versionadded:: 2.0

        Parameters
        ----------
        thread_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Thread`]
            The returned thread or ``None`` if not found.
        """
        return self.guild.get_thread(thread_id)


class VocalGuildChannel(slaycord.abc.GuildChannel, Hashable):
    __slots__ = (
        'name',
        'id',
        'guild',
        'nsfw',
        'bitrate',
        'user_limit',
        '_state',
        'position',
        'slowmode_delay',
        '_overwrites',
        'category_id',
        'rtc_region',
        'video_quality_mode',
        'last_message_id',
    )

    def __init__(self, *, state: ConnectionState, guild: Guild, data: Union[VoiceChannelPayload, StageChannelPayload]):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(guild, data)

    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.guild.id, 'guild_id'

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.guild.id, self.id

    def _update(self, guild: Guild, data: Union[VoiceChannelPayload, StageChannelPayload]) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.nsfw: bool = data.get('nsfw', False)
        self.rtc_region: Optional[str] = data.get('rtc_region')
        self.video_quality_mode: VideoQualityMode = try_enum(VideoQualityMode, data.get('video_quality_mode', 1))
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.position: int = data['position']
        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self.bitrate: int = data['bitrate']
        self.user_limit: int = data['user_limit']
        self._fill_overwrites(data)

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.voice.value

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the channel is NSFW.

        .. versionadded:: 2.0
        """
        return self.nsfw

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all members that are currently inside this voice channel."""
        ret = []
        for user_id, state in self.guild._voice_states.items():
            if state.channel and state.channel.id == self.id:
                member = self.guild.get_member(user_id)
                if member is not None:
                    ret.append(member)
        return ret

    @property
    def voice_states(self) -> Dict[int, VoiceState]:
        """Returns a mapping of member IDs who have voice states in this channel.

        .. versionadded:: 1.3

        .. note::

            This function is intentionally low level to replace :attr:`members`
            when the member cache is unavailable.

        Returns
        -------
        Mapping[:class:`int`, :class:`VoiceState`]
            The mapping of member ID to a voice state.
        """
        # fmt: off
        return {
            key: value
            for key, value in self.guild._voice_states.items()
            if value.channel and value.channel.id == self.id
        }
        # fmt: on

    @property
    def scheduled_events(self) -> List[ScheduledEvent]:
        """List[:class:`ScheduledEvent`]: Returns all scheduled events for this channel.

        .. versionadded:: 2.0
        """
        return [event for event in self.guild.scheduled_events if event.channel_id == self.id]

    @utils.copy_doc(slaycord.abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)
        self._apply_implicit_permissions(base)

        # voice channels cannot be edited by people who can't connect to them
        # It also implicitly denies all other voice perms
        if not base.connect:
            denied = Permissions.voice()
            denied.update(manage_channels=True, manage_roles=True)
            base.value &= ~denied.value
        return base

    @property
    def last_message(self) -> Optional[Message]:
        """Retrieves the last message from this channel in cache.

        The message might not be valid or point to an existing message.

        .. versionadded:: 2.0

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        -------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 2.0

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)  # type: ignore # VocalGuildChannel is an impl detail


class VoiceChannel(VocalGuildChannel):
    """Represents a Discord guild voice channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work" or "age restricted".

        .. versionadded:: 2.0
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a voice channel.
    rtc_region: Optional[:class:`str`]
        The region for the voice channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.

        .. versionadded:: 1.7

        .. versionchanged:: 2.0
            The type of this attribute has changed to :class:`str`.
    video_quality_mode: :class:`VideoQualityMode`
        The camera video quality for the voice channel's participants.

        .. versionadded:: 2.0
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.

        .. versionadded:: 2.0
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.

        .. versionadded:: 2.2
    status: Optional[:class:`str`]
        The status of the voice channel. ``None`` if no status is set.
        This is not available for the fetch methods such as :func:`Guild.fetch_channel`
        or :func:`Client.fetch_channel`.
    """

    __slots__ = ('status',)

    def __init__(self, *, state: ConnectionState, guild: Guild, data: VoiceChannelPayload) -> None:
        super().__init__(state=state, guild=guild, data=data)
        self.status: Optional[str] = data.get('status') or None  # empty string -> None

    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('rtc_region', self.rtc_region),
            ('position', self.position),
            ('bitrate', self.bitrate),
            ('video_quality_mode', self.video_quality_mode),
            ('user_limit', self.user_limit),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'

    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return EntityType.voice

    @property
    def type(self) -> Literal[ChannelType.voice]:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.voice


class StageChannel(VocalGuildChannel):
    """Represents a Discord guild stage channel.

    .. versionadded:: 1.7

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns the channel's name.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`Guild`
        The guild the channel belongs to.
    id: :class:`int`
        The channel ID.
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work" or "age restricted".

        .. versionadded:: 2.0
    topic: Optional[:class:`str`]
        The channel's topic. ``None`` if it isn't set.
    category_id: Optional[:class:`int`]
        The category channel ID this channel belongs to, if applicable.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a stage channel.
    rtc_region: Optional[:class:`str`]
        The region for the stage channel's voice communication.
        A value of ``None`` indicates automatic voice region detection.
    video_quality_mode: :class:`VideoQualityMode`
        The camera video quality for the stage channel's participants.

        .. versionadded:: 2.0
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.

        .. versionadded:: 2.2
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this channel. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.

        .. versionadded:: 2.2
    """

    __slots__ = ('topic',)

    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('topic', self.topic),
            ('rtc_region', self.rtc_region),
            ('position', self.position),
            ('bitrate', self.bitrate),
            ('video_quality_mode', self.video_quality_mode),
            ('user_limit', self.user_limit),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'

    def _update(self, guild: Guild, data: StageChannelPayload) -> None:
        super()._update(guild, data)
        self.topic: Optional[str] = data.get('topic')

    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return EntityType.stage_instance

    @property
    def requesting_to_speak(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who are requesting to speak in the stage channel."""
        return [member for member in self.members if member.voice and member.voice.requested_to_speak_at is not None]

    @property
    def speakers(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who have been permitted to speak in the stage channel.

        .. versionadded:: 2.0
        """
        return [
            member
            for member in self.members
            if member.voice and not member.voice.suppress and member.voice.requested_to_speak_at is None
        ]

    @property
    def listeners(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who are listening in the stage channel.

        .. versionadded:: 2.0
        """
        return [member for member in self.members if member.voice and member.voice.suppress]

    @property
    def moderators(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who are moderating the stage channel.

        .. versionadded:: 2.0
        """
        required_permissions = Permissions.stage_moderator()
        return [member for member in self.members if self.permissions_for(member) >= required_permissions]

    @property
    def type(self) -> Literal[ChannelType.stage_voice]:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.stage_voice

    @property
    def instance(self) -> Optional[StageInstance]:
        """Optional[:class:`StageInstance`]: The running stage instance of the stage channel.

        .. versionadded:: 2.0
        """
        return utils.get(self.guild.stage_instances, channel_id=self.id)


class CategoryChannel(slaycord.abc.GuildChannel, Hashable):
    """Represents a Discord channel category.

    These are useful to group channels to logical compartments.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the category's hash.

        .. describe:: str(x)

            Returns the category's name.

    Attributes
    ----------
    name: :class:`str`
        The category name.
    guild: :class:`Guild`
        The guild the category belongs to.
    id: :class:`int`
        The category channel ID.
    position: :class:`int`
        The position in the category list. This is a number that starts at 0. e.g. the
        top category is position 0.
    nsfw: :class:`bool`
        If the channel is marked as "not safe for work".

        .. note::

            To check if the channel or the guild of that channel are marked as NSFW, consider :meth:`is_nsfw` instead.
    """

    __slots__ = ('name', 'id', 'guild', 'nsfw', '_state', 'position', '_overwrites', 'category_id')

    def __init__(self, *, state: ConnectionState, guild: Guild, data: CategoryChannelPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(guild, data)

    def __repr__(self) -> str:
        return f'<CategoryChannel id={self.id} name={self.name!r} position={self.position} nsfw={self.nsfw}>'

    def _update(self, guild: Guild, data: CategoryChannelPayload) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.nsfw: bool = data.get('nsfw', False)
        self.position: int = data['position']
        self._fill_overwrites(data)

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.category.value

    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return None

    @property
    def type(self) -> Literal[ChannelType.category]:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.category

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the category is NSFW."""
        return self.nsfw

    @property
    def channels(self) -> List[GuildChannelType]:
        """List[:class:`abc.GuildChannel`]: Returns the channels that are under this category.

        These are sorted by the official Discord UI, which places voice channels below the text channels.
        """

        def comparator(channel):
            return (not isinstance(channel, TextChannel), channel.position)

        ret = [c for c in self.guild.channels if c.category_id == self.id]
        ret.sort(key=comparator)
        return ret

    @property
    def text_channels(self) -> List[TextChannel]:
        """List[:class:`TextChannel`]: Returns the text channels that are under this category."""
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, TextChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def voice_channels(self) -> List[VoiceChannel]:
        """List[:class:`VoiceChannel`]: Returns the voice channels that are under this category."""
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, VoiceChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def stage_channels(self) -> List[StageChannel]:
        """List[:class:`StageChannel`]: Returns the stage channels that are under this category.

        .. versionadded:: 1.7
        """
        ret = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, StageChannel)]
        ret.sort(key=lambda c: (c.position, c.id))
        return ret

    @property
    def forums(self) -> List[ForumChannel]:
        """List[:class:`ForumChannel`]: Returns the forum channels that are under this category.

        .. versionadded:: 2.4
        """
        r = [c for c in self.guild.channels if c.category_id == self.id and isinstance(c, ForumChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r


class ForumTag(Hashable):
    """Represents a forum tag that can be applied to a thread within a :class:`ForumChannel`.

    .. versionadded:: 2.1

    .. container:: operations

        .. describe:: x == y

            Checks if two forum tags are equal.

        .. describe:: x != y

            Checks if two forum tags are not equal.

        .. describe:: hash(x)

            Returns the forum tag's hash.

        .. describe:: str(x)

            Returns the forum tag's name.


    Attributes
    ----------
    id: :class:`int`
        The ID of the tag. If this was manually created then the ID will be ``0``.
    name: :class:`str`
        The name of the tag. Can only be up to 20 characters.
    moderated: :class:`bool`
        Whether this tag can only be added or removed by a moderator with
        the :attr:`~Permissions.manage_threads` permission.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji that is used to represent this tag.
        Note that if the emoji is a custom emoji, it will *not* have name information.
    """

    __slots__ = ('name', 'id', 'moderated', 'emoji')

    def __init__(self, *, name: str, emoji: Optional[EmojiInputType] = None, moderated: bool = False) -> None:
        self.name: str = name
        self.id: int = 0
        self.moderated: bool = moderated
        self.emoji: Optional[PartialEmoji] = None
        if isinstance(emoji, _EmojiTag):
            self.emoji = emoji._to_partial()
        elif isinstance(emoji, str):
            self.emoji = PartialEmoji.from_str(emoji)
        elif emoji is not None:
            raise TypeError(f'emoji must be a Emoji, PartialEmoji, str or None not {emoji.__class__.__name__}')

    @classmethod
    def from_data(cls, *, state: ConnectionState, data: ForumTagPayload) -> Self:
        self = cls.__new__(cls)
        self.name = data['name']
        self.id = int(data['id'])
        self.moderated = data.get('moderated', False)

        emoji_name = data['emoji_name'] or ''
        emoji_id = utils._get_as_snowflake(data, 'emoji_id') or None  # Coerce 0 -> None
        if not emoji_name and not emoji_id:
            self.emoji = None
        else:
            self.emoji = PartialEmoji.with_state(state=state, name=emoji_name, id=emoji_id)
        return self

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            'name': self.name,
            'moderated': self.moderated,
        }
        if self.emoji is not None:
            payload.update(self.emoji._to_forum_tag_payload())
        else:
            payload.update(emoji_id=None, emoji_name=None)

        if self.id:
            payload['id'] = self.id

        return payload

    def __repr__(self) -> str:
        return f'<ForumTag id={self.id} name={self.name!r} emoji={self.emoji!r} moderated={self.moderated}>'

    def __str__(self) -> str:
        return self.name


class ForumChannel(slaycord.abc.GuildChannel, Hashable):
    """Represents a Discord guild forum channel.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two forums are equal.

        .. describe:: x != y

            Checks if two forums are not equal.

        .. describe:: hash(x)

            Returns the forum's hash.

        .. describe:: str(x)

            Returns the forum's name.

    Attributes
    ----------
    name: :class:`str`
        The forum name.
    guild: :class:`Guild`
        The guild the forum belongs to.
    id: :class:`int`
        The forum ID.
    category_id: Optional[:class:`int`]
        The category channel ID this forum belongs to, if applicable.
    topic: Optional[:class:`str`]
        The forum's topic. ``None`` if it doesn't exist. Called "Guidelines" in the UI.
        Can be up to 4096 characters long.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    last_message_id: Optional[:class:`int`]
        The last thread ID that was created on this forum. This technically also
        coincides with the message ID that started the thread that was created.
        It may *not* point to an existing or valid thread or message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between creating threads
        in this forum. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    nsfw: :class:`bool`
        If the forum is marked as "not safe for work" or "age restricted".
    default_auto_archive_duration: :class:`int`
        The default auto archive duration in minutes for threads created in this forum.
    default_thread_slowmode_delay: :class:`int`
        The default slowmode delay in seconds for threads created in this forum.

        .. versionadded:: 2.1
    default_reaction_emoji: Optional[:class:`PartialEmoji`]
        The default reaction emoji for threads created in this forum to show in the
        add reaction button.

        .. versionadded:: 2.1
    default_layout: :class:`ForumLayoutType`
        The default layout for posts in this forum channel.
        Defaults to :attr:`ForumLayoutType.not_set`.

        .. versionadded:: 2.2
    default_sort_order: Optional[:class:`ForumOrderType`]
        The default sort order for posts in this forum channel.

        .. versionadded:: 2.3
    """

    __slots__ = (
        'name',
        'id',
        'guild',
        'topic',
        '_state',
        '_flags',
        '_type',
        'nsfw',
        'category_id',
        'position',
        'slowmode_delay',
        '_overwrites',
        'last_message_id',
        'default_auto_archive_duration',
        'default_thread_slowmode_delay',
        'default_reaction_emoji',
        'default_layout',
        'default_sort_order',
        '_available_tags',
        '_flags',
    )

    def __init__(self, *, state: ConnectionState, guild: Guild, data: Union[ForumChannelPayload, MediaChannelPayload]):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self._type: Literal[15, 16] = data['type']
        self._update(guild, data)

    def __repr__(self) -> str:
        attrs = [
            ('id', self.id),
            ('name', self.name),
            ('position', self.position),
            ('nsfw', self.nsfw),
            ('category_id', self.category_id),
        ]
        joined = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {joined}>'

    def _update(self, guild: Guild, data: Union[ForumChannelPayload, MediaChannelPayload]) -> None:
        self.guild: Guild = guild
        self.name: str = data['name']
        self.category_id: Optional[int] = utils._get_as_snowflake(data, 'parent_id')
        self.topic: Optional[str] = data.get('topic')
        self.position: int = data['position']
        self.nsfw: bool = data.get('nsfw', False)
        self.slowmode_delay: int = data.get('rate_limit_per_user', 0)
        self.default_auto_archive_duration: ThreadArchiveDuration = data.get('default_auto_archive_duration', 1440)
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        # This takes advantage of the fact that dicts are ordered since Python 3.7
        tags = [ForumTag.from_data(state=self._state, data=tag) for tag in data.get('available_tags', ())]
        self.default_thread_slowmode_delay: int = data.get('default_thread_rate_limit_per_user', 0)
        self.default_layout: ForumLayoutType = try_enum(ForumLayoutType, data.get('default_forum_layout', 0))
        self._available_tags: Dict[int, ForumTag] = {tag.id: tag for tag in tags}

        self.default_reaction_emoji: Optional[PartialEmoji] = None
        default_reaction_emoji = data.get('default_reaction_emoji')
        if default_reaction_emoji:
            self.default_reaction_emoji = PartialEmoji.with_state(
                state=self._state,
                id=utils._get_as_snowflake(default_reaction_emoji, 'emoji_id') or None,  # Coerce 0 -> None
                name=default_reaction_emoji.get('emoji_name') or '',
            )

        self.default_sort_order: Optional[ForumOrderType] = None
        default_sort_order = data.get('default_sort_order')
        if default_sort_order is not None:
            self.default_sort_order = try_enum(ForumOrderType, default_sort_order)

        self._flags: int = data.get('flags', 0)
        self._fill_overwrites(data)

    @property
    def type(self) -> Literal[ChannelType.forum, ChannelType.media]:
        """:class:`ChannelType`: The channel's Discord type."""
        if self._type == 16:
            return ChannelType.media
        return ChannelType.forum

    @property
    def _sorting_bucket(self) -> int:
        return ChannelType.text.value

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all members that can see this channel.

        .. versionadded:: 2.5
        """
        return [m for m in self.guild.members if self.permissions_for(m).read_messages]

    @property
    def _scheduled_event_entity_type(self) -> Optional[EntityType]:
        return None

    @utils.copy_doc(slaycord.abc.GuildChannel.permissions_for)
    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        base = super().permissions_for(obj)
        self._apply_implicit_permissions(base)

        # text channels do not have voice related permissions
        denied = Permissions.voice()
        base.value &= ~denied.value
        return base

    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        """Returns a thread with the given ID.

        .. note::

            This does not always retrieve archived threads, as they are not retained in the internal
            cache. Use :func:`Guild.fetch_channel` instead.

        .. versionadded:: 2.2

        Parameters
        ----------
        thread_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Thread`]
            The returned thread or ``None`` if not found.
        """
        thread = self.guild.get_thread(thread_id)
        if thread is not None and thread.parent_id == self.id:
            return thread
        return None

    @property
    def threads(self) -> List[Thread]:
        """List[:class:`Thread`]: Returns all the threads that you can see."""
        return [thread for thread in self.guild._threads.values() if thread.parent_id == self.id]

    @property
    def flags(self) -> ChannelFlags:
        """:class:`ChannelFlags`: The flags associated with this thread.

        .. versionadded:: 2.1
        """
        return ChannelFlags._from_value(self._flags)

    @property
    def available_tags(self) -> Sequence[ForumTag]:
        """Sequence[:class:`ForumTag`]: Returns all the available tags for this forum.

        .. versionadded:: 2.1
        """
        return utils.SequenceProxy(self._available_tags.values())

    def get_tag(self, tag_id: int, /) -> Optional[ForumTag]:
        """Returns the tag with the given ID.

        .. versionadded:: 2.1

        Parameters
        ----------
        tag_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`ForumTag`]
            The tag with the given ID, or ``None`` if not found.
        """
        return self._available_tags.get(tag_id)

    def is_nsfw(self) -> bool:
        """:class:`bool`: Checks if the forum is NSFW."""
        return self.nsfw

    def is_media(self) -> bool:
        """:class:`bool`: Checks if the channel is a media channel.

        .. versionadded:: 2.4
        """
        return self._type == ChannelType.media.value


class DMChannel(slaycord.abc.Messageable, slaycord.abc.Connectable, slaycord.abc.PrivateChannel, Hashable):
    """Represents a Discord direct message channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel.

    Attributes
    ----------
    id: :class:`int`
        The direct message channel ID.
    recipient: :class:`User`
        The user you are participating with in the direct message channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.

        .. versionadded:: 2.0
    last_pin_timestamp: Optional[:class:`datetime.datetime`]
        When the last pinned message was pinned. ``None`` if there are no pinned messages.

        .. versionadded:: 2.0
    """

    __slots__ = (
        'id',
        'recipient',
        'me',
        'last_message_id',
        'last_pin_timestamp',
        '_message_request',
        '_requested_at',
        '_spam',
        '_state',
    )

    def __init__(self, *, me: ClientUser, state: ConnectionState, data: DMChannelPayload):
        self._state: ConnectionState = state

        recipients = data.get('recipients')
        if recipients:
            self.recipient: Optional[User] = state.store_user(recipients[0])
        elif 'recipient_ids' in data:
            self.recipient = state.get_user(int(data['recipient_ids'][0]))
        else:
            self.recipient = None

        self.me: ClientUser = me
        self.id: int = int(data['id'])
        self._update(data)

    def _update(self, data: DMChannelPayload) -> None:
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('last_pin_timestamp'))
        self._message_request: Optional[bool] = data.get('is_message_request')
        self._requested_at: Optional[datetime.datetime] = utils.parse_time(data.get('is_message_request_timestamp'))
        self._spam: bool = data.get('is_spam', False)

    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.me.id, 'self_id'

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.me.id, self.id

    async def _get_messageable_destination(
        self,
    ) -> Tuple[int, slaycord.abc.MessageableDestinationType,]:
        recipient = self.recipient
        if recipient is None:
            return (self.id, 'channel')
        return (recipient.id, 'user')

    def __str__(self) -> str:
        if self.recipient:
            return f'Direct Message with {self.recipient}'
        return 'Direct Message with Unknown User'

    def __repr__(self) -> str:
        return f'<DMChannel id={self.id} recipient={self.recipient!r}>'

    @classmethod
    def _from_message(cls, state: ConnectionState, channel_id: int, message_id: Optional[int]) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.recipient = None
        # state.user won't be None here
        self.me = state.user  # type: ignore
        self.id = channel_id
        self.last_message_id = message_id
        self.last_pin_timestamp = None
        self._message_request = False
        self._requested_at = None
        self._spam = False
        return self

    @property
    def type(self) -> Literal[ChannelType.private]:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.private

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this DM channel belongs to. Always ``None``.

        This is mainly provided for compatibility purposes in duck typing.

        .. versionadded:: 2.0
        """
        return None

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/@me/{self.id}'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the direct message channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def requested_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the message request's creation time in UTC, if applicable."""
        return self._requested_at

    def is_message_request(self) -> bool:
        """:class:`bool`: Indicates if the direct message is/was a message request."""
        return self._message_request is not None

    def is_accepted(self) -> bool:
        """:class:`bool`: Indicates if the message request is accepted. For regular direct messages, this is always ``True``."""
        return not self._message_request if self._message_request is not None else True

    def is_spam(self) -> bool:
        """:class:`bool`: Indicates if the direct message is a spam message request."""
        return self._spam

    def permissions_for(self, obj: Any = None, /) -> Permissions:
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to ``True`` except:

        - :attr:`~Permissions.send_tts_messages`: You cannot send TTS messages in a DM.
        - :attr:`~Permissions.manage_messages`: You cannot delete others messages in a DM.
        - :attr:`~Permissions.create_private_threads`: There are no threads in a DM.
        - :attr:`~Permissions.create_public_threads`: There are no threads in a DM.
        - :attr:`~Permissions.manage_threads`: There are no threads in a DM.
        - :attr:`~Permissions.send_messages_in_threads`: There are no threads in a DM.

        .. versionchanged:: 2.0

            ``obj`` parameter is now positional-only.

        .. versionchanged:: 2.1

            Thread related permissions are now set to ``False``.

        Parameters
        ----------
        obj: :class:`User`
            The user to check permissions for. This parameter is ignored
            but kept for compatibility with other ``permissions_for`` methods.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions.
        """
        return Permissions._dm_permissions()

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        .. versionchanged:: 2.0

            ``message_id`` parameter is now positional-only.

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)


class GroupChannel(slaycord.abc.PrivateChannel, Hashable):
    """Represents a Discord group channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel

    Attributes
    ----------
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.
    last_pin_timestamp: Optional[:class:`datetime.datetime`]
        When the last pinned message was pinned. ``None`` if there are no pinned messages.
    recipients: List[:class:`User`]
        The users you are participating with in the group channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    id: :class:`int`
        The group channel ID.
    owner_id: :class:`int`
        The owner ID that owns the group channel.
    managed: :class:`bool`
        Whether the group channel is managed by an application.

        This restricts the operations that can be performed on the channel,
        and means :attr:`owner` will usually be ``None``.
    application_id: Optional[:class:`int`]
        The ID of the managing application, if any.
    name: Optional[:class:`str`]
        The group channel's name if provided.
    nicks: Dict[:class:`User`, :class:`str`]
        A mapping of users to their respective nicknames in the group channel.
    origin_channel_id: Optional[:class:`int`]
        The ID of the DM this group channel originated from, if any.
        This can only be accurately received in :func:`on_private_channel_create`
        due to a Discord limitation.
    """

    __slots__ = (
        '_state',
        'id',
        'last_message_id',
        'last_pin_timestamp',
        'recipients',
        'owner_id',
        'managed',
        'application_id',
        'nicks',
        'origin_channel_id',
        '_icon',
        'name',
        'me',
    )

    def __init__(self, *, me: ClientUser, state: ConnectionState, data: GroupChannelPayload):
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.me: ClientUser = me
        self._update(data)

    def _update(self, data: GroupChannelPayload) -> None:
        self.owner_id: int = int(data['owner_id'])
        self._icon: Optional[str] = data.get('icon')
        self.name: Optional[str] = data.get('name')
        self.recipients: List[User]
        if 'recipients' in data:
            self.recipients = [self._state.store_user(u) for u in data['recipients']]
        elif 'recipient_ids' in data:
            self.recipients = []
            for recipient_id_str in data['recipient_ids']:
                recipient_id = int(recipient_id_str)
                recipient = self._state.get_user(recipient_id) or Object(id=recipient_id)
                self.recipients.append(recipient)  # type: ignore
        elif not hasattr(self, 'recipients'):
            self.recipients = []
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('last_pin_timestamp'))
        self.managed: bool = data.get('managed', False)
        self.application_id: Optional[int] = utils._get_as_snowflake(data, 'application_id')
        self.nicks: Dict[User, str] = self._unroll_nicks(data.get('nicks', ()))
        self.origin_channel_id: Optional[int] = utils._get_as_snowflake(data, 'origin_channel_id')

    def _unroll_nicks(
        self, data: Union[List[GroupDMNicknamePayload], Tuple[GroupDMNicknamePayload, ...]]
    ) -> Dict[User, str]:
        ret = {}
        for entry in data:
            user_id = int(entry['id'])
            user = utils.get(self.recipients, id=user_id)
            if user:
                ret[user] = entry['nick']
        return ret

    def __str__(self) -> str:
        if self.name:
            return self.name

        if len(self.recipients) == 0:
            return 'Unnamed'

        return ', '.join(map(lambda x: x.name, self.recipients))

    def __repr__(self) -> str:
        return f'<GroupChannel id={self.id} name={self.name!r}>'

    @property
    def type(self) -> Literal[ChannelType.group]:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.group

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this group channel belongs to. Always ``None``.

        This is mainly provided for compatibility purposes in duck typing.

        .. versionadded:: 2.0
        """
        return None

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the channel's icon asset if available."""
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='channel')

    @property
    def origin_channel(self) -> Optional[DMChannel]:
        """Optional[:class:`DMChannel`]: The DM this group channel originated from, if any.

        This can only be accurately received in :func:`on_private_channel_create`
        due to a Discord limitation.
        """
        return self._state._get_private_channel(self.origin_channel_id) if self.origin_channel_id else None  # type: ignore

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/@me/{self.id}'

    def permissions_for(self, obj: Snowflake, /) -> Permissions:
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to ``True`` except:

        - :attr:`~Permissions.send_tts_messages`: You cannot send TTS messages in a DM.
        - :attr:`~Permissions.manage_messages`: You cannot delete others messages in a DM.
        - :attr:`~Permissions.create_private_threads`: There are no threads in a DM.
        - :attr:`~Permissions.create_public_threads`: There are no threads in a DM.
        - :attr:`~Permissions.manage_threads`: There are no threads in a DM.
        - :attr:`~Permissions.send_messages_in_threads`: There are no threads in a DM.

        This also checks the kick_members permission if the user is the owner.

        .. versionchanged:: 2.0

            ``obj`` parameter is now positional-only.

        .. versionchanged:: 2.1

            Thread related permissions are now set to ``False``.

        Parameters
        ----------
        obj: :class:`~slaycord.abc.Snowflake`
            The user to check permissions for.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions for the user.
        """

        base = Permissions._dm_permissions()
        base.mention_everyone = True

        if obj.id == self.owner_id:
            base.kick_members = True

        return base


class EphemeralDMChannel(slaycord.abc.Messageable, slaycord.abc.Connectable, slaycord.abc.PrivateChannel, Hashable):
    """Represents a Discord ephemeral direct message channel.

    .. container:: operations

        .. describe:: x == y

            Checks if two channels are equal.

        .. describe:: x != y

            Checks if two channels are not equal.

        .. describe:: hash(x)

            Returns the channel's hash.

        .. describe:: str(x)

            Returns a string representation of the channel.

    Attributes
    ----------
    id: :class:`int`
        The direct message channel ID.
    recipients: Tuple[:class:`User`, ...]
        The users participating in the ephemral direct message channel.
    recipient: :class:`User`
        The user you are participating with in the direct message channel.
    me: :class:`ClientUser`
        The user presenting yourself.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this channel. It may
        *not* point to an existing or valid message.

        .. versionadded:: 2.0
    last_pin_timestamp: Optional[:class:`datetime.datetime`]
        When the last pinned message was pinned. ``None`` if there are no pinned messages.

        .. versionadded:: 2.0
    """

    __slots__ = (
        'id',
        'recipient',
        'recipients',
        'me',
        'last_message_id',
        'last_pin_timestamp',
        '_message_request',
        '_requested_at',
        '_spam',
        '_state',
    )

    def __init__(self, *, me: ClientUser, state: ConnectionState, data: DMChannelPayload):
        self._state: ConnectionState = state

        recipients_data = data.get('recipients')
        if recipients_data:
            self.recipients: Tuple[User, ...] = tuple(state.store_user(d, dispatch=False) for d in recipients_data)
            self.recipient: Optional[User] = utils.find(lambda recipient: recipient.id != me.id, self.recipients)
        else:
            self.recipients = ()
            self.recipient = None

        self.me: ClientUser = me
        self.id: int = int(data['id'])
        self._update(data)

    def _update(self, data: DMChannelPayload) -> None:
        self.last_message_id: Optional[int] = utils._get_as_snowflake(data, 'last_message_id')
        self.last_pin_timestamp: Optional[datetime.datetime] = utils.parse_time(data.get('last_pin_timestamp'))
        self._message_request: Optional[bool] = data.get('is_message_request')
        self._requested_at: Optional[datetime.datetime] = utils.parse_time(data.get('is_message_request_timestamp'))
        self._spam: bool = data.get('is_spam', False)

    def _get_voice_client_key(self) -> Tuple[int, str]:
        return self.me.id, 'self_id'

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        return self.me.id, self.id

    async def _get_messageable_destination(
        self,
    ) -> Tuple[int, slaycord.abc.MessageableDestinationType,]:
        recipient = self.recipient
        if recipient is None:
            return (self.id, 'channel')
        return (recipient.id, 'user')

    def __str__(self) -> str:
        if self.recipient:
            return f'Ephemeral Direct Message with {self.recipient}'
        return 'Ephemeral Direct Message with Unknown User'

    def __repr__(self) -> str:
        return f'<EphemeralDMChannel id={self.id} recipient={self.recipient!r}>'

    @classmethod
    def _from_message(cls, state: ConnectionState, channel_id: int, message_id: Optional[int]) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.recipient = None
        # state.user won't be None here
        self.me = state.user  # type: ignore
        self.id = channel_id
        self.last_message_id = message_id
        self.last_pin_timestamp = None
        self._message_request = False
        self._requested_at = None
        self._spam = False
        return self

    @property
    def type(self) -> Literal[ChannelType.ephemeral_dm]:
        """:class:`ChannelType`: The channel's Discord type."""
        return ChannelType.ephemeral_dm

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this Ephemeral DM channel belongs to. Always ``None``.

        This is mainly provided for compatibility purposes in duck typing.

        .. versionadded:: 2.0
        """
        return None

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/@me/{self.id}'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the direct message channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    @property
    def requested_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the message request's creation time in UTC, if applicable."""
        return self._requested_at

    def is_message_request(self) -> bool:
        """:class:`bool`: Indicates if the direct message is/was a message request."""
        return self._message_request is not None

    def is_accepted(self) -> bool:
        """:class:`bool`: Indicates if the message request is accepted. For regular direct messages, this is always ``True``."""
        return not self._message_request if self._message_request is not None else True

    def is_spam(self) -> bool:
        """:class:`bool`: Indicates if the direct message is a spam message request."""
        return self._spam

    def permissions_for(self, obj: Any = None, /) -> Permissions:
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Actual direct messages do not really have the concept of permissions.

        This returns all the Text related permissions set to ``True`` except:

        - :attr:`~Permissions.send_tts_messages`: You cannot send TTS messages in a DM.
        - :attr:`~Permissions.manage_messages`: You cannot delete others messages in a DM.
        - :attr:`~Permissions.create_private_threads`: There are no threads in a DM.
        - :attr:`~Permissions.create_public_threads`: There are no threads in a DM.
        - :attr:`~Permissions.manage_threads`: There are no threads in a DM.
        - :attr:`~Permissions.send_messages_in_threads`: There are no threads in a DM.

        .. versionchanged:: 2.0

            ``obj`` parameter is now positional-only.

        .. versionchanged:: 2.1

            Thread related permissions are now set to ``False``.

        Parameters
        ----------
        obj: :class:`User`
            The user to check permissions for. This parameter is ignored
            but kept for compatibility with other ``permissions_for`` methods.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions.
        """
        return Permissions._dm_permissions()

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        .. versionadded:: 1.6

        .. versionchanged:: 2.0

            ``message_id`` parameter is now positional-only.

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)


class PartialMessageable(slaycord.abc.Messageable, Hashable):
    """Represents a partial messageable to aid with working messageable channels when
    only a channel ID is present.

    The only way to construct this class is through :meth:`Client.get_partial_messageable`.

    Note that this class is trimmed down and has no rich attributes.

    .. versionadded:: 2.0

    .. container:: operations

        .. describe:: x == y

            Checks if two partial messageables are equal.

        .. describe:: x != y

            Checks if two partial messageables are not equal.

        .. describe:: hash(x)

            Returns the partial messageable's hash.

    Attributes
    ----------
    id: :class:`int`
        The channel ID associated with this partial messageable.
    guild_id: Optional[:class:`int`]
        The guild ID associated with this partial messageable.
    type: Optional[:class:`ChannelType`]
        The channel type associated with this partial messageable, if given.
    """

    def __init__(self, state: ConnectionState, id: int, guild_id: Optional[int] = None, type: Optional[ChannelType] = None):
        self._state: ConnectionState = state
        self.id: int = id
        self.guild_id: Optional[int] = guild_id
        self.type: Optional[ChannelType] = type

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} type={self.type!r}>'

    async def _get_messageable_destination(
        self,
    ) -> Tuple[int, slaycord.abc.MessageableDestinationType]:
        if self.type == ChannelType.private:
            type = 'user'
        elif self.type == ChannelType.lobby:
            type = 'lobby'
        else:
            type = 'channel'

        return (self.id, type)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild this partial messageable is in."""
        return self._state._get_guild(self.guild_id)

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel."""
        if self.guild_id is None:
            return f'https://discord.com/channels/@me/{self.id}'
        return f'https://discord.com/channels/{self.guild_id}/{self.id}'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return utils.snowflake_time(self.id)

    def permissions_for(self, obj: Any = None, /) -> Permissions:
        """Handles permission resolution for a :class:`User`.

        This function is there for compatibility with other channel types.

        Since partial messageables cannot reasonably have the concept of
        permissions, this will always return :meth:`Permissions.none`.

        Parameters
        ----------
        obj: :class:`User`
            The user to check permissions for. This parameter is ignored
            but kept for compatibility with other ``permissions_for`` methods.

        Returns
        -------
        :class:`Permissions`
            The resolved permissions.
        """

        return Permissions.none()

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the channel.

        .. versionadded:: 2.5
        """
        return f'<#{self.id}>'

    def get_partial_message(self, message_id: int, /) -> PartialMessage:
        """Creates a :class:`PartialMessage` from the message ID.

        This is useful if you want to work with a message and only have its ID without
        doing an unnecessary API call.

        Parameters
        ----------
        message_id: :class:`int`
            The message ID to create a partial message for.

        Returns
        -------
        :class:`PartialMessage`
            The partial message.
        """

        from .message import PartialMessage

        return PartialMessage(channel=self, id=message_id)


def _guild_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)
    if value is ChannelType.text:
        return TextChannel, value
    elif value is ChannelType.voice:
        return VoiceChannel, value
    elif value is ChannelType.category:
        return CategoryChannel, value
    elif value is ChannelType.news:
        return TextChannel, value
    elif value is ChannelType.stage_voice:
        return StageChannel, value
    elif value is ChannelType.forum:
        return ForumChannel, value
    elif value is ChannelType.media:
        return ForumChannel, value
    else:
        return None, value


def _private_channel_factory(channel_type: int):
    value = try_enum(ChannelType, channel_type)

    if value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    elif value is ChannelType.ephemeral_dm:
        return EphemeralDMChannel, value
    else:
        return None, value


def _channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if value is ChannelType.private:
        return DMChannel, value
    elif value is ChannelType.group:
        return GroupChannel, value
    elif value is ChannelType.ephemeral_dm:
        return EphemeralDMChannel, value
    else:
        return cls, value


def _threaded_channel_factory(channel_type: int):
    cls, value = _channel_factory(channel_type)
    if value in (ChannelType.private_thread, ChannelType.public_thread, ChannelType.news_thread):
        return Thread, value
    return cls, value


def _threaded_guild_channel_factory(channel_type: int):
    cls, value = _guild_channel_factory(channel_type)
    if value in (ChannelType.private_thread, ChannelType.public_thread, ChannelType.news_thread):
        return Thread, value
    return cls, value
