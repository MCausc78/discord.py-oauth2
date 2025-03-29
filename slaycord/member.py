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
import inspect
import itertools
from operator import attrgetter
from typing import Awaitable, Callable, List, Optional, TYPE_CHECKING, Tuple, TypeVar, Union

import slaycord.abc

from . import utils
from .asset import Asset
from .colour import Colour
from .enums import Status
from .flags import MemberFlags
from .permissions import Permissions
from .presences import ClientStatus
from .user import BaseUser, ClientUser, User, _UserTag

__all__ = (
    'VoiceState',
    'Member',
)

T = TypeVar('T', bound=type)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .activity import ActivityTypes
    from .channel import DMChannel, VoiceChannel, StageChannel
    from .flags import PublicUserFlags
    from .guild import Guild
    from .message import Message
    from .presences import RawPresenceUpdateEvent
    from .role import Role
    from .state import ConnectionState
    from .types.gateway import GuildMemberUpdateEvent
    from .types.member import (
        MemberWithUser as MemberWithUserPayload,
        Member as MemberPayload,
        UserWithMember as UserWithMemberPayload,
    )
    from .types.user import User as UserPayload, AvatarDecorationData
    from .types.voice import (
        GuildVoiceState as GuildVoiceStatePayload,
        VoiceState as VoiceStatePayload,
    )

    VocalGuildChannel = Union[VoiceChannel, StageChannel]


class VoiceState:
    """Represents a Discord user's voice state.

    Attributes
    ----------
    deaf: :class:`bool`
        Indicates if the user is currently deafened by the guild.
    mute: :class:`bool`
        Indicates if the user is currently muted by the guild.
    self_mute: :class:`bool`
        Indicates if the user is currently muted by their own accord.
    self_deaf: :class:`bool`
        Indicates if the user is currently deafened by their own accord.
    self_stream: :class:`bool`
        Indicates if the user is currently streaming via 'Go Live' feature.

        .. versionadded:: 1.3

    self_video: :class:`bool`
        Indicates if the user is currently broadcasting video.
    suppress: :class:`bool`
        Indicates if the user is suppressed from speaking.

        Only applies to stage channels.

        .. versionadded:: 1.7

    requested_to_speak_at: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies the date and time in UTC that the member
        requested to speak. It will be ``None`` if they are not requesting to speak
        anymore or have been accepted to speak.

        Only applicable to stage channels.

        .. versionadded:: 1.7

    afk: :class:`bool`
        Indicates if the user is currently in the AFK channel in the guild.
    channel: Optional[Union[:class:`VoiceChannel`, :class:`StageChannel`]]
        The voice channel that the user is currently connected to. ``None`` if the user
        is not currently in a voice channel.
    """

    __slots__ = (
        'session_id',
        'deaf',
        'mute',
        'self_mute',
        'self_stream',
        'self_video',
        'self_deaf',
        'afk',
        'channel',
        'requested_to_speak_at',
        'suppress',
    )

    def __init__(
        self, *, data: Union[VoiceStatePayload, GuildVoiceStatePayload], channel: Optional[VocalGuildChannel] = None
    ):
        self.session_id: Optional[str] = data.get('session_id')
        self._update(data, channel)

    def _update(self, data: Union[VoiceStatePayload, GuildVoiceStatePayload], channel: Optional[VocalGuildChannel]):
        self.self_mute: bool = data.get('self_mute', False)
        self.self_deaf: bool = data.get('self_deaf', False)
        self.self_stream: bool = data.get('self_stream', False)
        self.self_video: bool = data.get('self_video', False)
        self.afk: bool = data.get('suppress', False)
        self.mute: bool = data.get('mute', False)
        self.deaf: bool = data.get('deaf', False)
        self.suppress: bool = data.get('suppress', False)
        self.requested_to_speak_at: Optional[datetime.datetime] = utils.parse_time(data.get('request_to_speak_timestamp'))
        self.channel: Optional[VocalGuildChannel] = channel

    def __repr__(self) -> str:
        attrs = [
            ('self_mute', self.self_mute),
            ('self_deaf', self.self_deaf),
            ('self_stream', self.self_stream),
            ('suppress', self.suppress),
            ('requested_to_speak_at', self.requested_to_speak_at),
            ('channel', self.channel),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {inner}>'


def flatten_user(cls: T) -> T:
    for attr, value in itertools.chain(BaseUser.__dict__.items(), User.__dict__.items()):
        # ignore private/special methods
        if attr.startswith('_'):
            continue

        # don't override what we already have
        if attr in cls.__dict__:
            continue

        # if it's a slotted attribute or a property, redirect it
        # slotted members are implemented as member_descriptors in Type.__dict__
        if not hasattr(value, '__annotations__'):
            getter = attrgetter('_user.' + attr)
            setattr(cls, attr, property(getter, doc=f'Equivalent to :attr:`User.{attr}`'))
        else:
            # Technically, this can also use attrgetter
            # However I'm not sure how I feel about "functions" returning properties
            # It probably breaks something in Sphinx.
            # probably a member function by now
            def generate_function(x):
                # We want sphinx to properly show coroutine functions as coroutines
                if inspect.iscoroutinefunction(value):

                    async def general(self, *args, **kwargs):  # type: ignore
                        return await getattr(self._user, x)(*args, **kwargs)

                else:

                    def general(self, *args, **kwargs):
                        return getattr(self._user, x)(*args, **kwargs)

                general.__name__ = x
                return general

            func = generate_function(attr)
            func = utils.copy_doc(value)(func)
            setattr(cls, attr, func)

    return cls


@flatten_user
class Member(slaycord.abc.Messageable, _UserTag):
    """Represents a Discord member to a :class:`Guild`.

    This implements a lot of the functionality of :class:`User`.

    .. container:: operations

        .. describe:: x == y

            Checks if two members are equal.
            Note that this works with :class:`User` instances too.

        .. describe:: x != y

            Checks if two members are not equal.
            Note that this works with :class:`User` instances too.

        .. describe:: hash(x)

            Returns the member's hash.

        .. describe:: str(x)

            Returns the member's handle (e.g. ``name`` or ``name#discriminator``).

    Attributes
    ----------
    joined_at: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies the date and time in UTC that the member joined the guild.
        If the member left and rejoined the guild, this will be the latest date. In certain cases, this can be ``None``.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The activities that the user is currently doing.

        .. note::

            Due to a Discord API limitation, a user's Spotify activity may not appear
            if they are listening to a song with a title longer
            than 128 characters. See :issue:`1738` for more information.

    guild: :class:`Guild`
        The guild that the member belongs to.
    nick: Optional[:class:`str`]
        The guild specific nickname of the user. Takes precedence over the global name.
    pending: :class:`bool`
        Whether the member is pending member verification.

        .. versionadded:: 1.6
    premium_since: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies the date and time in UTC when the member used their
        "Nitro boost" on the guild, if available. This could be ``None``.
    timed_out_until: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies the date and time in UTC that the member's time out will expire.
        This will be set to ``None`` or a time in the past if the user is not timed out.

        .. versionadded:: 2.0
    client_status: :class:`ClientStatus`
        Model which holds information about the status of the member on various clients/platforms via presence updates.

        .. versionadded:: 2.5
    """

    __slots__ = (
        '_roles',
        'joined_at',
        'premium_since',
        'activities',
        'guild',
        'pending',
        'nick',
        'timed_out_until',
        '_permissions',
        'client_status',
        '_user',
        '_state',
        '_avatar',
        '_banner',
        '_flags',
        '_avatar_decoration_data',
    )

    if TYPE_CHECKING:
        name: str
        id: int
        discriminator: str
        global_name: Optional[str]
        bot: bool
        system: bool
        created_at: datetime.datetime
        default_avatar: Asset
        avatar: Optional[Asset]
        dm_channel: Optional[DMChannel]
        create_dm: Callable[[], Awaitable[DMChannel]]
        mutual_guilds: List[Guild]
        public_flags: PublicUserFlags
        banner: Optional[Asset]
        accent_color: Optional[Colour]
        accent_colour: Optional[Colour]
        avatar_decoration: Optional[Asset]
        avatar_decoration_sku_id: Optional[int]

    def __init__(self, *, data: MemberWithUserPayload, guild: Guild, state: ConnectionState):
        self._state: ConnectionState = state
        if 'user' in data:
            self._user: User = state.store_user(data['user'])
        elif 'user_id' in data:
            self._user: User = state._users[int(data['user_id'])]
        self.guild: Guild = guild
        self.joined_at: Optional[datetime.datetime] = utils.parse_time(data.get('joined_at'))
        self.premium_since: Optional[datetime.datetime] = utils.parse_time(data.get('premium_since'))
        self._roles: utils.SnowflakeList = utils.SnowflakeList(map(int, data['roles']))
        self.client_status: ClientStatus = ClientStatus()
        self.activities: Tuple[ActivityTypes, ...] = ()
        self.nick: Optional[str] = data.get('nick', None)
        self.pending: bool = data.get('pending', False)
        self._avatar: Optional[str] = data.get('avatar')
        self._banner: Optional[str] = data.get('banner')
        self._permissions: Optional[int]
        self._flags: int = data['flags']
        self._avatar_decoration_data: Optional[AvatarDecorationData] = data.get('avatar_decoration_data')
        try:
            self._permissions = int(data['permissions'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            self._permissions = None

        self.timed_out_until: Optional[datetime.datetime] = utils.parse_time(data.get('communication_disabled_until'))

    def __str__(self) -> str:
        return str(self._user)

    def __repr__(self) -> str:
        return (
            f'<Member id={self._user.id} name={self._user.name!r} global_name={self._user.global_name!r}'
            f' bot={self._user.bot} nick={self.nick!r} guild={self.guild!r}>'
        )

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self._user)

    @classmethod
    def _from_message(cls, *, message: Message, data: MemberPayload) -> Self:
        author = message.author
        data['user'] = author._to_minimal_user_json()  # type: ignore
        return cls(data=data, guild=message.guild, state=message._state)  # type: ignore

    @classmethod
    def _from_client_user(cls, *, user: ClientUser, guild: Guild, state: ConnectionState) -> Self:
        data = {
            'roles': [],
            'user': user._to_minimal_user_json(),
            'flags': 0,
        }
        return cls(data=data, guild=guild, state=state)  # type: ignore

    def _update_from_message(self, data: MemberPayload) -> None:
        self.joined_at = utils.parse_time(data.get('joined_at'))
        self.premium_since = utils.parse_time(data.get('premium_since'))
        self._roles = utils.SnowflakeList(map(int, data['roles']))
        self.nick = data.get('nick', None)
        self.pending = data.get('pending', False)
        self.timed_out_until = utils.parse_time(data.get('communication_disabled_until'))
        self._flags = data.get('flags', 0)

    @classmethod
    def _try_upgrade(cls, *, data: UserWithMemberPayload, guild: Guild, state: ConnectionState) -> Union[User, Self]:
        # A User object with a 'member' key
        try:
            member_data = data.pop('member')
        except KeyError:
            return state.create_user(data)
        else:
            member_data['user'] = data  # type: ignore
            return cls(data=member_data, guild=guild, state=state)  # type: ignore

    @classmethod
    def _copy(cls, member: Self) -> Self:
        self = cls.__new__(cls)  # to bypass __init__

        self._roles = utils.SnowflakeList(member._roles, is_sorted=True)
        self.joined_at = member.joined_at
        self.premium_since = member.premium_since
        self.client_status = member.client_status
        self.guild = member.guild
        self.nick = member.nick
        self.pending = member.pending
        self.activities = member.activities
        self.timed_out_until = member.timed_out_until
        self._flags = member._flags
        self._permissions = member._permissions
        self._state = member._state
        self._avatar = member._avatar
        self._banner = member._banner
        self._avatar_decoration_data = member._avatar_decoration_data

        # Reference will not be copied unless necessary by PRESENCE_UPDATE
        # See below
        self._user = member._user
        return self

    async def _get_channel(self) -> DMChannel:
        ch = await self.create_dm()
        return ch

    def _update(self, data: GuildMemberUpdateEvent) -> None:
        # the nickname change is optional,
        # if it isn't in the payload then it didn't change
        try:
            self.nick = data['nick']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            pass

        try:
            self.pending = data['pending']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            pass

        self.premium_since = utils.parse_time(data.get('premium_since'))
        self.timed_out_until = utils.parse_time(data.get('communication_disabled_until'))
        self._roles = utils.SnowflakeList(map(int, data['roles']))
        self._avatar = data.get('avatar')
        self._banner = data.get('banner')
        self._flags = data.get('flags', 0)
        self._avatar_decoration_data = data.get('avatar_decoration_data')

    def _presence_update(self, raw: RawPresenceUpdateEvent, user: UserPayload) -> Optional[Tuple[User, User]]:
        self.activities = raw.activities
        self.client_status = raw.client_status

        if len(user) > 1:
            return self._update_inner_user(user)

    def _update_inner_user(self, user: UserPayload) -> Optional[Tuple[User, User]]:
        u = self._user
        original = (
            u.name,
            u.discriminator,
            u._avatar,
            u.global_name,
            u._public_flags,
            u._avatar_decoration_data['sku_id'] if u._avatar_decoration_data is not None else None,
        )

        decoration_payload = user.get('avatar_decoration_data')
        # These keys seem to always be available
        modified = (
            user['username'],
            user['discriminator'],
            user['avatar'],
            user.get('global_name'),
            user.get('public_flags', 0),
            decoration_payload['sku_id'] if decoration_payload is not None else None,
        )
        if original != modified:
            to_return = User._copy(self._user)
            u.name, u.discriminator, u._avatar, u.global_name, u._public_flags, u._avatar_decoration_data = (
                user['username'],
                user['discriminator'],
                user['avatar'],
                user.get('global_name'),
                user.get('public_flags', 0),
                decoration_payload,
            )
            # Signal to dispatch on_user_update
            return to_return, u

    @property
    def status(self) -> Status:
        """:class:`Status`: The member's overall status. If the value is unknown, then it will be a :class:`str` instead."""
        return self.client_status.status

    @property
    def raw_status(self) -> str:
        """:class:`str`: The member's overall status as a string value.

        .. versionadded:: 1.5
        """
        return self.client_status._status

    @status.setter
    def status(self, value: Status) -> None:
        # internal use only
        self.client_status._status = str(value)

    @property
    def mobile_status(self) -> Status:
        """:class:`Status`: The member's status on a mobile device, if applicable."""
        return self.client_status.mobile_status

    @property
    def desktop_status(self) -> Status:
        """:class:`Status`: The member's status on the desktop client, if applicable."""
        return self.client_status.desktop_status

    @property
    def web_status(self) -> Status:
        """:class:`Status`: The member's status on the web client, if applicable."""
        return self.client_status.web_status

    @property
    def embedded_status(self) -> Status:
        """:class:`Status`: The member's status on the embedded (PlayStation, Xbox, in-game) client, if applicable."""
        return self.client_status.embedded_status

    def is_on_mobile(self) -> bool:
        """A helper function that determines if a member is active on a mobile device.

        Returns
        -------
        :class:`bool`
        """
        return self.client_status.is_on_mobile()

    @property
    def colour(self) -> Colour:
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the member. If the default colour is the one rendered then an instance
        of :meth:`Colour.default` is returned.

        There is an alias for this named :attr:`color`.
        """

        roles = self.roles[1:]  # remove @everyone

        # highest order of the colour is the one that gets rendered.
        # if the highest is the default colour then the next one with a colour
        # is chosen instead
        for role in reversed(roles):
            if role.colour.value:
                return role.colour
        return Colour.default()

    @property
    def color(self) -> Colour:
        """:class:`Colour`: A property that returns a color denoting the rendered color for
        the member. If the default color is the one rendered then an instance of :meth:`Colour.default`
        is returned.

        There is an alias for this named :attr:`colour`.
        """
        return self.colour

    @property
    def roles(self) -> List[Role]:
        """List[:class:`Role`]: A :class:`list` of :class:`Role` that the member belongs to. Note
        that the first element of this list is always the default '@everyone'
        role.

        These roles are sorted by their position in the role hierarchy.
        """
        result = []
        g = self.guild
        for role_id in self._roles:
            role = g.get_role(role_id)
            if role:
                result.append(role)
        default_role = g.default_role
        if default_role:
            result.append(default_role)
        result.sort()
        return result

    @property
    def display_icon(self) -> Optional[Union[str, Asset]]:
        """Optional[Union[:class:`str`, :class:`Asset`]]: A property that returns the role icon that is rendered for
        this member. If no icon is shown then ``None`` is returned.

        .. versionadded:: 2.0
        """

        roles = self.roles[1:]  # remove @everyone
        for role in reversed(roles):
            icon = role.display_icon
            if icon:
                return icon

        return None

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the member."""
        return f'<@{self._user.id}>'

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        For regular users this is just their global name or their username,
        but if they have a guild specific nickname then that
        is returned instead.
        """
        return self.nick or self.global_name or self.name

    @property
    def display_avatar(self) -> Asset:
        """:class:`Asset`: Returns the member's display avatar.

        For regular members this is just their avatar, but
        if they have a guild specific avatar then that
        is returned instead.

        .. versionadded:: 2.0
        """
        return self.guild_avatar or self._user.avatar or self._user.default_avatar

    @property
    def guild_avatar(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the guild avatar
        the member has. If unavailable, ``None`` is returned.

        .. versionadded:: 2.0
        """
        if self._avatar is None:
            return None
        return Asset._from_guild_avatar(self._state, self.guild.id, self.id, self._avatar)

    @property
    def display_banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the member's displayed banner, if any.

        This is the member's guild banner if available, otherwise it's their
        global banner. If the member has no banner set then ``None`` is returned.

        .. versionadded:: 2.5
        """
        return self.guild_banner or self._user.banner

    @property
    def guild_banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the guild banner
        the member has. If unavailable, ``None`` is returned.

        .. versionadded:: 2.5
        """
        if self._banner is None:
            return None
        return Asset._from_guild_banner(self._state, self.guild.id, self.id, self._banner)

    @property
    def activity(self) -> Optional[ActivityTypes]:
        """Optional[Union[:class:`BaseActivity`, :class:`Spotify`]]: Returns the primary
        activity the user is currently doing. Could be ``None`` if no activity is being done.

        .. note::

            Due to a Discord API limitation, this may be ``None`` if
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :issue:`1738` for more information.

        .. note::

            A user may have multiple activities, these can be accessed under :attr:`activities`.
        """
        if self.activities:
            return self.activities[0]

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the member is mentioned in the specified message.

        Parameters
        ----------
        message: :class:`Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the member is mentioned in the message.
        """
        if message.guild is None or message.guild.id != self.guild.id:
            return False

        if self._user.mentioned_in(message):
            return True

        return any(self._roles.has(role.id) for role in message.role_mentions)

    @property
    def top_role(self) -> Role:
        """:class:`Role`: Returns the member's highest role.

        This is useful for figuring where a member stands in the role
        hierarchy chain.
        """
        guild = self.guild
        if len(self._roles) == 0:
            return guild.default_role

        return max(guild.get_role(rid) or guild.default_role for rid in self._roles)

    @property
    def guild_permissions(self) -> Permissions:
        """:class:`Permissions`: Returns the member's guild permissions.

        This only takes into consideration the guild permissions
        and not most of the implied permissions or any of the
        channel permission overwrites. For 100% accurate permission
        calculation, please use :meth:`abc.GuildChannel.permissions_for`.

        This does take into consideration guild ownership, the
        administrator implication, and whether the member is timed out.

        .. versionchanged:: 2.0
            Member timeouts are taken into consideration.
        """

        if self.guild.owner_id == self.id:
            return Permissions.all()

        base = Permissions.none()
        for r in self.roles:
            base.value |= r.permissions.value

        if base.administrator:
            return Permissions.all()

        if self.is_timed_out():
            base.value &= Permissions._timeout_mask()

        return base

    @property
    def resolved_permissions(self) -> Optional[Permissions]:
        """Optional[:class:`Permissions`]: Returns the member's resolved permissions
        from an interaction.

        This is only available in interaction contexts and represents the resolved
        permissions of the member in the channel the interaction was executed in.
        This is more or less equivalent to calling :meth:`abc.GuildChannel.permissions_for`
        but stored and returned as an attribute by the Discord API rather than computed.

        .. versionadded:: 2.0
        """
        if self._permissions is None:
            return None
        return Permissions(self._permissions)

    @property
    def voice(self) -> Optional[VoiceState]:
        """Optional[:class:`VoiceState`]: Returns the member's current voice state."""
        return self.guild._voice_state_for(self._user.id)

    @property
    def flags(self) -> MemberFlags:
        """:class:`MemberFlags`: Returns the member's flags.

        .. versionadded:: 2.2
        """
        return MemberFlags._from_value(self._flags)

    def get_role(self, role_id: int, /) -> Optional[Role]:
        """Returns a role with the given ID from roles which the member has.

        .. versionadded:: 2.0

        Parameters
        ----------
        role_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Role`]
            The role or ``None`` if not found in the member's roles.
        """
        return self.guild.get_role(role_id) if self._roles.has(role_id) else None

    def is_timed_out(self) -> bool:
        """Returns whether this member is timed out.

        .. versionadded:: 2.0

        Returns
        -------
        :class:`bool`
            ``True`` if the member is timed out. ``False`` otherwise.
        """
        if self.timed_out_until is not None:
            return utils.utcnow() < self.timed_out_until
        return False
