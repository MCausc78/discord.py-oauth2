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

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union

import discord.abc

from .asset import Asset
from .color import Color
from .enums import (
    try_enum,
    DefaultAvatar,
    DisplayNameEffect,
    DisplayNameFont,
    PremiumType,
    RelationshipType,
)
from .flags import PublicUserFlags
from .primary_guild import PrimaryGuild
from .utils import MISSING, _get_as_snowflake, snowflake_time

if TYPE_CHECKING:
    from typing_extensions import Self

    from datetime import datetime

    from .channel import DMChannel, GroupChannel, EphemeralDMChannel
    from .game_relationship import GameRelationship
    from .guild import Guild
    from .member import VoiceState
    from .message import Message
    from .relationship import Relationship
    from .rpc.types.user import User as RPCUserPayload
    from .state import BaseConnectionState
    from .types.channel import DMChannel as DMChannelPayload
    from .types.user import (
        PartialUser as PartialUserPayload,
        User as UserPayload,
        AvatarDecorationData as AvatarDecorationDataPayload,
        PrimaryGuild as PrimaryGuildPayload,
        DisplayNameStyle as DisplayNameStylePayload,
    )


__all__ = (
    'DisplayNameStyle',
    'User',
    'ClientUser',
)


class _UserTag:
    __slots__ = ()

    id: int


class DisplayNameStyle:
    """Represents how an user's name gets displayed, such as font, colors, gradient, glow.

    Attributes
    ----------
    font: :class:`DisplayNameFont`
        The font for the display name.
    effect: :class:`DisplayNameEffect`
        The effect for the display name.
    raw_colors: List[:class:`int`]
        A list of colors encoded in hexdecimal format.
    """

    __slots__ = (
        'font',
        'effect',
        'raw_colors',
    )

    def __init__(self, data: DisplayNameStylePayload) -> None:
        self.font: DisplayNameFont = try_enum(DisplayNameFont, data['font_id'])
        self.effect: DisplayNameEffect = try_enum(DisplayNameEffect, data['effect_id'])
        self.raw_colors: List[int] = data['colors']

    def to_dict(self) -> DisplayNameStylePayload:
        return {
            'font_id': self.font.value,
            'effect_id': self.effect.value,
            'colors': self.raw_colors,
        }

    @property
    def colors(self) -> List[Color]:
        """List[:class:`Color`]: A list of colors.

        There is an alias for this named :attr:`colours`.
        """
        return list(map(Color, self.raw_colors))

    @property
    def colours(self) -> List[Color]:
        """List[:class:`Colour`]: A list of colours.

        This is an alias of :attr:`colors`.
        """
        return self.colors


class BaseUser(_UserTag):
    __slots__ = (
        'name',
        'id',
        'discriminator',
        'global_name',
        '_avatar',
        '_banner',
        '_accent_color',
        'bot',
        'system',
        '_public_flags',
        '_state',
        '_avatar_decoration_data',
        '_primary_guild',
        'display_name_style',
    )

    if TYPE_CHECKING:
        name: str
        id: int
        discriminator: str
        global_name: Optional[str]
        bot: bool
        system: bool
        _state: BaseConnectionState
        _avatar: Optional[str]
        _banner: Optional[str]
        _accent_color: Optional[int]
        _public_flags: int
        _avatar_decoration_data: Optional[AvatarDecorationDataPayload]
        _primary_guild: Optional[PrimaryGuildPayload]
        display_name_style: Optional[DisplayNameStyle]

    def __init__(self, *, state: BaseConnectionState, data: Union[UserPayload, PartialUserPayload]) -> None:
        self._state: BaseConnectionState = state
        self._update(data)

    def __repr__(self) -> str:
        return (
            f"<BaseUser id={self.id} name={self.name!r} global_name={self.global_name!r}"
            f" bot={self.bot} system={self.system}>"
        )

    def __str__(self) -> str:
        if self.discriminator == '0':
            return self.name
        return f'{self.name}#{self.discriminator}'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _UserTag) and other.id == self.id

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return self.id >> 22

    def _update(self, data: Union[UserPayload, PartialUserPayload]) -> None:
        display_name_style_data = data.get('display_name_styles')

        self.id = int(data['id'])
        self.name = data['username']
        self.discriminator = data['discriminator']
        self.global_name = data.get('global_name')
        self._avatar = data['avatar']
        self._banner = data.get('banner')
        self._accent_color = data.get('accent_color')
        self._public_flags = data.get('public_flags', 0)
        self.bot = data.get('bot', False)
        self.system = data.get('system', False)
        self._avatar_decoration_data = data.get('avatar_decoration_data')
        self._primary_guild = data.get('primary_guild')
        self.display_name_style = None if display_name_style_data is None else DisplayNameStyle(display_name_style_data)

    @classmethod
    def _copy(cls, user: Self) -> Self:
        self = cls.__new__(cls)  # bypass __init__

        self.id = user.id
        self.name = user.name
        self.discriminator = user.discriminator
        self.global_name = user.global_name
        self._avatar = user._avatar
        self._banner = user._banner
        self._accent_color = user._accent_color
        self.bot = user.bot
        self._state = user._state
        self._public_flags = user._public_flags
        self._avatar_decoration_data = user._avatar_decoration_data
        self._primary_guild = user._primary_guild
        self.display_name_style = user.display_name_style

        return self

    def _to_minimal_user_json(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            'id': self.id,
            'username': self.name,
            'discriminator': self.discriminator,
            'avatar': self._avatar,
            'banner': self._banner,
            'accent_color': self._accent_color,
            'global_name': self.global_name,
            'bot': self.bot,
            'avatar_decoration_data': self._avatar_decoration_data,
            'primary_guild': self._primary_guild,
            'display_name_style': None if self.display_name_style is None else self.display_name_style.to_dict(),
        }
        return payload

    @classmethod
    def _from_rpc(cls, data: RPCUserPayload, state: BaseConnectionState) -> Self:
        avatar_decoration_data = data.get('avatar_decoration_data')
        if avatar_decoration_data is None:
            add: Optional[AvatarDecorationDataPayload] = None
        else:
            add: Optional[AvatarDecorationDataPayload] = {
                'asset': avatar_decoration_data['asset'],
                'sku_id': avatar_decoration_data['skuId'],
            }

        transformed_payload: UserPayload = {
            'id': data['id'],
            'username': data['username'],
            'discriminator': data['discriminator'],
            'avatar': data.get('avatar'),
            'global_name': data.get('global_name'),
            'avatar_decoration_data': add,
            'primary_guild': None,
            'bot': data['bot'],
            'flags': data['flags'],
            'premium_type': data['premium_type'],  # type: ignore
        }
        return cls(data=transformed_payload, state=state)

    @property
    def voice(self) -> Optional[VoiceState]:
        """Optional[:class:`VoiceState`]: Returns the user's current voice state."""
        return self._state._voice_state_for(self.id)

    @property
    def public_flags(self) -> PublicUserFlags:
        """:class:`PublicUserFlags`: The publicly available flags the user has."""
        return PublicUserFlags._from_value(self._public_flags)

    @property
    def avatar(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the avatar the user has.

        If the user has not uploaded a global avatar, ``None`` is returned.
        If you want the avatar that a user has displayed, consider :attr:`display_avatar`.
        """
        if self._avatar is not None:
            return Asset._from_avatar(self._state, self.id, self._avatar)
        return None

    @property
    def default_avatar(self) -> Asset:
        """:class:`Asset`: Returns the default avatar for a given user."""
        if self.discriminator in ('0', '0000'):
            avatar_id = (self.id >> 22) % len(DefaultAvatar)
        else:
            avatar_id = int(self.discriminator) % 5

        return Asset._from_default_avatar(self._state, avatar_id)

    @property
    def display_avatar(self) -> Asset:
        """:class:`Asset`: Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        return self.avatar or self.default_avatar

    @property
    def avatar_decoration(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns an :class:`Asset` for the avatar decoration the user has.

        If the user has not set an avatar decoration, ``None`` is returned.

        .. versionadded:: 2.4
        """
        if self._avatar_decoration_data is not None:
            return Asset._from_avatar_decoration(self._state, self._avatar_decoration_data['asset'])
        return None

    @property
    def avatar_decoration_sku_id(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns the SKU ID of the avatar decoration the user has.

        If the user has not set an avatar decoration, ``None`` is returned.

        .. versionadded:: 2.4
        """
        if self._avatar_decoration_data is not None:
            return _get_as_snowflake(self._avatar_decoration_data, 'sku_id')
        return None

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the user's banner asset, if available.

        .. versionadded:: 2.0


        .. note::
            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._banner is None:
            return None
        return Asset._from_user_banner(self._state, self.id, self._banner)

    @property
    def accent_color(self) -> Optional[Color]:
        """Optional[:class:`Color`]: Returns the user's accent color, if applicable.

        A user's accent color is only shown if they do not have a banner.
        This will only be available if the user explicitly sets a color.

        There is an alias for this named :attr:`accent_colour`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        if self._accent_color is None:
            return None
        return Color(self._accent_color)

    @property
    def accent_colour(self) -> Optional[Color]:
        """Optional[:class:`Color`]: Returns the user's accent colour, if applicable.

        A user's accent colour is only shown if they do not have a banner.
        This will only be available if the user explicitly sets a colour.

        This is an alias of :attr:`accent_color`.

        .. versionadded:: 2.0

        .. note::

            This information is only available via :meth:`Client.fetch_user`.
        """
        return self.accent_color

    @property
    def color(self) -> Color:
        """:class:`Color`: A property that returns a color denoting the rendered color
        for the user. This always returns :meth:`Color.default`.

        There is an alias for this named :attr:`colour`.
        """
        return Color.default()

    @property
    def colour(self) -> Color:
        """:class:`Colour`: A property that returns a colour denoting the rendered colour
        for the user. This always returns :meth:`Colour.default`.

        This is an alias of :attr:`color`.
        """
        return self.color

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        return f'<@{self.id}>'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the user's creation time in UTC.

        This is when the user's Discord account was created.
        """
        return snowflake_time(self.id)

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name.

        For regular users this is just their global name or their username,
        but if they have a guild specific nickname then that
        is returned instead.
        """
        if self.global_name:
            return self.global_name
        return self.name

    @property
    def primary_guild(self) -> PrimaryGuild:
        """:class:`PrimaryGuild`: Returns the user's primary guild."""
        if self._primary_guild is None:
            return PrimaryGuild._default(self._state)
        return PrimaryGuild(data=self._primary_guild, state=self._state)

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the user is mentioned in the specified message.

        Parameters
        ----------
        message: :class:`Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """

        if message.mention_everyone:
            return True

        return any(user.id == self.id for user in message.mentions)

    @property
    def game_relationship(self) -> Optional[GameRelationship]:
        """Optional[:class:`GameRelationship`]: Returns the :class:`GameRelationship` with this user if applicable, ``None`` otherwise."""
        return self._state.get_game_relationship(self.id)

    @property
    def relationship(self) -> Optional[Relationship]:
        """Optional[:class:`Relationship`]: Returns the :class:`Relationship` with this user if applicable, ``None`` otherwise."""
        return self._state.get_relationship(self.id)

    def is_friend(self) -> bool:
        """:class:`bool`: Checks if the user is your friend."""
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.friend

    def is_game_friend(self) -> bool:
        """:class:`bool`: Checks if the user is your friend in-game."""
        r = self.game_relationship
        if r is None:
            return False
        return r.type is RelationshipType.friend

    def is_blocked(self) -> bool:
        """:class:`bool`: Checks if the user is blocked."""
        r = self.relationship
        if r is None:
            return False
        return r.type is RelationshipType.blocked

    def is_ignored(self) -> bool:
        """:class:`bool`: Checks if the user is ignored."""
        r = self.relationship
        if r is None:
            return False
        return r.user_ignored


class ClientUser(BaseUser):
    """Represents your Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's handle (e.g. ``name`` or ``name#discriminator``).

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is a legacy concept that is no longer used.
    global_name: Optional[:class:`str`]
        The user's global nickname, taking precedence over the username in display.

        .. versionadded:: 2.3
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).

        .. versionadded:: 1.3
    display_name_style: Optional[:class:`DisplayNameStyle`]
        The style for the display name.

        .. versionadded:: 3.0
    verified: :class:`bool`
        Specifies if the user's email is verified.
    email: Optional[:class:`str`]
        The email the user used when registering.
    locale: Optional[:class:`str`]
        The IETF language tag used to identify the language the user is using.
    mfa_enabled: :class:`bool`
        Specifies if the user has MFA turned on and working.
    premium_type: :class:`PremiumType`
        Specifies the type of premium a user has (i.e. Nitro, Nitro Classic, or Nitro Basic).
    """

    __slots__ = (
        'email',
        'locale',
        '_flags',
        'verified',
        'mfa_enabled',
        'premium_type',
        '__weakref__',
    )

    if TYPE_CHECKING:
        verified: bool
        email: Optional[str]
        locale: Optional[str]
        mfa_enabled: bool
        premium_type: PremiumType
        _flags: int

    def __init__(self, *, data: UserPayload, state: BaseConnectionState) -> None:
        super().__init__(data=data, state=state)

    def __repr__(self) -> str:
        return (
            f'<ClientUser id={self.id} name={self.name!r} global_name={self.global_name!r}'
            f' bot={self.bot} verified={self.verified} mfa_enabled={self.mfa_enabled}>'
        )

    def _update(self, data: UserPayload) -> None:
        super()._update(data)
        # There's actually an Optional[str] phone field as well but it's not given through OAuth2
        self.verified = data.get('verified', False)
        self.email = data.get('email')
        self.locale = data.get('locale')
        self._flags = data.get('flags', 0)
        self.mfa_enabled = data.get('mfa_enabled', False)
        self.premium_type = try_enum(PremiumType, data.get('premium_type', 0))

    async def edit(self, *, global_name: Optional[str] = MISSING) -> ClientUser:
        """|coro|

        Edits the current profile of the client.

        .. versionchanged:: 2.0
            The edit is no longer in-place, instead the newly edited client user is returned.

        .. versionchanged:: 2.0
            This function will now raise :exc:`ValueError` instead of
            ``InvalidArgument``.

        Parameters
        ----------
        global_name: :class:`str`
            The new global name you wish to change to.

        Raises
        ------
        HTTPException
            Editing your profile failed.

        Returns
        -------
        :class:`ClientUser`
            The newly edited client user.
        """
        payload: Dict[str, Any] = {}
        if global_name is not MISSING:
            payload['global_name'] = global_name

        data: UserPayload = await self._state.http.edit_profile(payload)
        return ClientUser(data=data, state=self._state)

    @property
    def mutual_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        return list(self._state.guilds)


class User(BaseUser, discord.abc.Messageable):
    """Represents a Discord user.

    .. container:: operations

        .. describe:: x == y

            Checks if two users are equal.

        .. describe:: x != y

            Checks if two users are not equal.

        .. describe:: hash(x)

            Return the user's hash.

        .. describe:: str(x)

            Returns the user's handle (e.g. ``name`` or ``name#discriminator``).

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    id: :class:`int`
        The user's unique ID.
    discriminator: :class:`str`
        The user's discriminator. This is a legacy concept that is no longer used.
    global_name: Optional[:class:`str`]
        The user's global nickname, taking precedence over the username in display.

        .. versionadded:: 2.3
    bot: :class:`bool`
        Specifies if the user is a bot account.
    system: :class:`bool`
        Specifies if the user is a system user (i.e. represents Discord officially).
    display_name_style: Optional[:class:`DisplayNameStyle`]
        The style for the display name.

        .. versionadded:: 3.0
    """

    __slots__ = ('__weakref__',)

    def __repr__(self) -> str:
        return f'<User id={self.id} name={self.name!r} global_name={self.global_name!r} bot={self.bot}>'

    async def _get_messageable_destination(
        self,
    ) -> Tuple[int, discord.abc.MessageableDestinationType]:
        return (self.id, 'user')

    @property
    def dm_channel(self) -> Optional[Union[DMChannel, EphemeralDMChannel]]:
        """Optional[Union[:class:`DMChannel`, :class:`EphemeralDMChannel`]]: Returns the channel associated with this user if it exists.

        If this returns ``None``, you can create a DM channel by calling the
        :meth:`create_dm` coroutine function.
        """
        return self._state._get_private_channel_by_user(self.id)

    @property
    def mutual_groups(self) -> List[GroupChannel]:
        """List[:class:`GroupChannel`]: The groups that the user shares with the client.

        .. note::

            This will only return mutual groups within the client's internal cache.
        """
        from .channel import GroupChannel

        return [
            ch for ch in self._state.private_channel_map.values() if isinstance(ch, GroupChannel) and self in ch.recipients
        ]

    @property
    def mutual_guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: The guilds that the user shares with the client.

        .. note::

            This will only return mutual guilds within the client's internal cache.

        .. versionadded:: 1.7
        """
        user_id = self.id
        return [guild for guild in self._state.guild_map.values() if user_id in guild._members]

    async def create_dm(self) -> Union[DMChannel, EphemeralDMChannel]:
        """|coro|

        Creates a :class:`DMChannel` with this user.

        This should be rarely called, as this is done transparently for most
        people.

        Returns
        -------
        Union[:class:`.DMChannel`, :class:`.EphemeralDMChannel`]
            The channel that was created.
        """
        found = self.dm_channel
        if found is not None:
            return found

        state = self._state
        data: DMChannelPayload = await state.http.start_private_message(self.id)
        return state.add_dm_channel(data)

    async def block(self) -> None:
        """|coro|

        Blocks the user.

        Raises
        ------
        Forbidden
            Not allowed to block this user.
        HTTPException
            Blocking the user failed.
        """
        await self._state.http.add_relationship(self.id, type=RelationshipType.blocked.value)

    async def unblock(self) -> None:
        """|coro|

        Unblocks the user.

        Raises
        ------
        Forbidden
            Not allowed to unblock this user.
        HTTPException
            Unblocking the user failed.
        """
        await self._state.http.remove_relationship(self.id)

    async def remove_friend(self) -> None:
        """|coro|

        Removes the user as a friend.

        Raises
        ------
        Forbidden
            Not allowed to remove this user as a friend.
        HTTPException
            Removing the user as a friend failed.
        """
        await self._state.http.remove_relationship(self.id)

    async def remove_game_friend(self) -> None:
        """|coro|

        Removes the user as a in-game friend.

        Raises
        ------
        Forbidden
            Not allowed to remove this user as a in-game friend.
        HTTPException
            Removing the user as a in-game friend failed.
        """
        await self._state.http.remove_game_relationship(self.id)

    async def send_friend_request(self) -> None:
        """|coro|

        Sends the user a friend request.

        Raises
        ------
        Forbidden
            Not allowed to send a friend request to the user.
        HTTPException
            Sending the friend request failed.
        """
        await self._state.http.add_relationship(self.id)

    async def send_game_friend_request(self) -> None:
        """|coro|

        Sends the user a in-game friend request.

        Raises
        ------
        Forbidden
            Not allowed to send a game friend request to the user.
        HTTPException
            Sending the game friend request failed.
        """
        await self._state.http.add_game_relationship(self.id)
