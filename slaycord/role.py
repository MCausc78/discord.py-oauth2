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

from typing import Any, List, Optional, TYPE_CHECKING, Union

from .asset import Asset
from .color import Color
from .flags import RoleFlags
from .mixins import Hashable
from .permissions import Permissions
from .utils import _get_as_snowflake, snowflake_time

__all__ = (
    'PRIMARY_HOLOGRAPHIC_ROLE_COLOR',
    'SECONDARY_HOLOGRAPHIC_ROLE_COLOR',
    'TERTIARY_HOLOGRAPHIC_ROLE_COLOR',
    'RoleColors',
    'RoleTags',
    'Role',
)

if TYPE_CHECKING:
    import datetime
    from typing_extensions import Self

    from .guild import Guild
    from .member import Member
    from .state import ConnectionState
    from .types.role import (
        Role as RolePayload,
        RoleColors as RoleColorsPayload,
        RoleTags as RoleTagsPayload,
    )

PRIMARY_HOLOGRAPHIC_ROLE_COLOR: int = 0xA9C9FF
SECONDARY_HOLOGRAPHIC_ROLE_COLOR: int = 0xFFBBEC
TERTIARY_HOLOGRAPHIC_ROLE_COLOR: int = 0xFFC3A0


class RoleColors:
    """Represents colors of a role.

    Attributes
    ----------
    primary_color: :class:`int`
        The primary role color.
    secondary_color: :class:`int`
        The secondary role color.
    tertiary_color: :class:`int`
        The tertiary role color.

    """

    __slots__ = (
        'primary_color',
        'secondary_color',
        'tertiary_color',
    )

    def __init__(
        self,
        *,
        primary_color: int,
        secondary_color: Optional[int] = None,
        tertiary_color: Optional[int] = None,
    ) -> None:
        self.primary_color: int = primary_color
        self.secondary_color: Optional[int] = secondary_color
        self.tertiary_color: Optional[int] = tertiary_color

    @classmethod
    def from_dict(cls, data: RoleColorsPayload) -> Self:
        return cls(
            primary_color=data['primary_color'],
            secondary_color=data.get('secondary_color'),
            tertiary_color=data.get('tertiary_color'),
        )

    def is_holographic(self) -> bool:
        """:class:`bool`: Whether the role colors are holographic."""
        return (
            self.primary_color == PRIMARY_HOLOGRAPHIC_ROLE_COLOR
            and self.secondary_color == SECONDARY_HOLOGRAPHIC_ROLE_COLOR
            and self.tertiary_color == TERTIARY_HOLOGRAPHIC_ROLE_COLOR
        )

    @classmethod
    def holographic(cls) -> Self:
        """A factory method that returns a :class:`RoleColors` instance with holographic colors."""
        return cls(
            primary_color=PRIMARY_HOLOGRAPHIC_ROLE_COLOR,
            secondary_color=SECONDARY_HOLOGRAPHIC_ROLE_COLOR,
            tertiary_color=TERTIARY_HOLOGRAPHIC_ROLE_COLOR,
        )


class RoleTags:
    """Represents tags on a role.

    A role tag is a piece of extra information attached to a managed role
    that gives it context for the reason the role is managed.

    While this can be accessed, a useful interface is also provided in the
    :class:`Role` and :class:`Guild` classes as well.

    .. versionadded:: 1.6

    Attributes
    ----------
    bot_id: Optional[:class:`int`]
        The bot's user ID that manages this role.
    integration_id: Optional[:class:`int`]
        The integration ID that manages the role.
    subscription_listing_id: Optional[:class:`int`]
        The ID of this role's subscription SKU and listing.

        .. versionadded:: 2.2
    """

    __slots__ = (
        'bot_id',
        'integration_id',
        '_premium_subscriber',
        '_available_for_purchase',
        'subscription_listing_id',
        '_guild_connections',
    )

    def __init__(self, data: RoleTagsPayload):
        self.bot_id: Optional[int] = _get_as_snowflake(data, 'bot_id')
        self.integration_id: Optional[int] = _get_as_snowflake(data, 'integration_id')
        self.subscription_listing_id: Optional[int] = _get_as_snowflake(data, 'subscription_listing_id')

        # NOTE: The API returns "null" for this if it's valid, which corresponds to None.
        # This is different from other fields where "null" means "not there".
        # So in this case, a value of None is the same as True.
        # Which means we would need a different sentinel.
        self._premium_subscriber: bool = 'premium_subscriber' in data
        self._available_for_purchase: bool = 'available_for_purchase' in data
        self._guild_connections: bool = 'guild_connections' in data

    def is_bot_managed(self) -> bool:
        """:class:`bool`: Whether the role is associated with a bot."""
        return self.bot_id is not None

    def is_premium_subscriber(self) -> bool:
        """:class:`bool`: Whether the role is the premium subscriber, AKA "boost", role for the guild."""
        return self._premium_subscriber

    def is_integration(self) -> bool:
        """:class:`bool`: Whether the role is managed by an integration."""
        return self.integration_id is not None

    def is_available_for_purchase(self) -> bool:
        """:class:`bool`: Whether the role is available for purchase.

        .. versionadded:: 2.2
        """
        return self._available_for_purchase

    def is_guild_connection(self) -> bool:
        """:class:`bool`: Whether the role is a guild's linked role.

        .. versionadded:: 2.2
        """
        return self._guild_connections

    def __repr__(self) -> str:
        return (
            f'<RoleTags bot_id={self.bot_id} integration_id={self.integration_id} '
            f'premium_subscriber={self.is_premium_subscriber()}>'
        )


class Role(Hashable):
    """Represents a Discord role in a :class:`Guild`.

    .. container:: operations

        .. describe:: x == y

            Checks if two roles are equal.

        .. describe:: x != y

            Checks if two roles are not equal.

        .. describe:: x > y

            Checks if a role is higher than another in the hierarchy.

        .. describe:: x < y

            Checks if a role is lower than another in the hierarchy.

        .. describe:: x >= y

            Checks if a role is higher or equal to another in the hierarchy.

        .. describe:: x <= y

            Checks if a role is lower or equal to another in the hierarchy.

        .. describe:: hash(x)

            Return the role's hash.

        .. describe:: str(x)

            Returns the role's name.

    Attributes
    ----------
    id: :class:`int`
        The ID for the role.
    guild: :class:`Guild`
        The guild the role belongs to.
    name: :class:`str`
        The name of the role.
    hoist: :class:`bool`
        Indicates if the role will be displayed separately from other members.
    colors: :class:`RoleColors`
        The role colors.
    position: :class:`int`
        The position of the role. This number is usually positive. The bottom
        role has a position of 0.

        .. warning::

            Multiple roles can have the same position number. As a consequence
            of this, comparing via role position is prone to subtle bugs if
            checking for role hierarchy. The recommended and correct way to
            compare for roles in the hierarchy is using the comparison
            operators on the role objects themselves.

    unicode_emoji: Optional[:class:`str`]
        The role's unicode emoji, if available.

        .. note::

            If :attr:`icon` is not ``None``, it is displayed as role icon
            instead of the unicode emoji under this attribute.

            If you want the icon that a role has displayed, consider using :attr:`display_icon`.

        .. versionadded:: 2.0

    managed: :class:`bool`
        Indicates if the role is managed by the guild through some form of
        integrations such as Twitch.
    mentionable: :class:`bool`
        Indicates if the role can be mentioned by users.
    tags: Optional[:class:`RoleTags`]
        The role tags associated with this role.
    """

    __slots__ = (
        '_state',
        '_flags',
        'id',
        'guild',
        'name',
        'hoist',
        '_permissions',
        '_color',
        'colors',
        'position',
        '_icon',
        'unicode_emoji',
        'managed',
        'mentionable',
        'tags',
    )

    def __init__(self, *, guild: Guild, state: ConnectionState, data: RolePayload):
        self.guild: Guild = guild
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(data)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return f'<Role id={self.id} name={self.name!r}>'

    def __lt__(self, other: object) -> bool:
        if not isinstance(other, Role) or not isinstance(self, Role):
            return NotImplemented

        if self.guild != other.guild:
            raise RuntimeError('Cannot compare roles from two different guilds')

        # the @everyone role is always the lowest role in hierarchy
        guild_id = self.guild.id
        if self.id == guild_id:
            # everyone_role < everyone_role -> False
            return other.id != guild_id

        if self.position < other.position:
            return True

        if self.position == other.position:
            return self.id > other.id

        return False

    def __le__(self, other: Any) -> bool:
        r = Role.__lt__(other, self)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def __gt__(self, other: Any) -> bool:
        return Role.__lt__(other, self)

    def __ge__(self, other: object) -> bool:
        r = Role.__lt__(self, other)
        if r is NotImplemented:
            return NotImplemented
        return not r

    def _update(self, data: RolePayload) -> None:
        self.name: str = data['name']
        self._permissions: int = int(data.get('permissions', 0))
        self.position: int = data.get('position', 0)
        self._color: int = data.get('color', 0)
        self.colors: RoleColors = RoleColors.from_dict(
            data=data.get('colors')
            or {
                'primary_color': self._color,
                'secondary_color': None,
                'tertiary_color': None,
            }
        )
        self.hoist: bool = data.get('hoist', False)
        self._icon: Optional[str] = data.get('icon')
        self.unicode_emoji: Optional[str] = data.get('unicode_emoji')
        self.managed: bool = data.get('managed', False)
        self.mentionable: bool = data.get('mentionable', False)
        self.tags: Optional[RoleTags]
        self._flags: int = data.get('flags', 0)

        try:
            self.tags = RoleTags(data['tags'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            self.tags = None

    def is_default(self) -> bool:
        """:class:`bool`: Checks if the role is the default role."""
        return self.guild.id == self.id

    def is_bot_managed(self) -> bool:
        """:class:`bool`: Whether the role is associated with a bot.

        .. versionadded:: 1.6
        """
        return self.tags is not None and self.tags.is_bot_managed()

    def is_premium_subscriber(self) -> bool:
        """:class:`bool`: Whether the role is the premium subscriber, AKA "boost", role for the guild.

        .. versionadded:: 1.6
        """
        return self.tags is not None and self.tags.is_premium_subscriber()

    def is_integration(self) -> bool:
        """:class:`bool`: Whether the role is managed by an integration.

        .. versionadded:: 1.6
        """
        return self.tags is not None and self.tags.is_integration()

    def is_assignable(self) -> bool:
        """:class:`bool`: Whether the role is able to be assigned or removed by the bot.

        .. versionadded:: 2.0
        """
        me = self.guild.me
        return not self.is_default() and not self.managed and (me.top_role > self or me.id == self.guild.owner_id)

    @property
    def permissions(self) -> Permissions:
        """:class:`Permissions`: Returns the role's permissions."""
        return Permissions(self._permissions)

    @property
    def color(self) -> Color:
        """:class:`Color`: Returns the role color. An alias exists under ``colour``."""
        return Color(self._color)

    @property
    def colour(self) -> Color:
        """:class:`Colour`: Returns the role colour.

        This is an alias of :attr:`color`.
        """
        return self.color

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`.Asset`]: Returns the role's icon asset, if available.

        .. note::
            If this is ``None``, the role might instead have unicode emoji as its icon
            if :attr:`unicode_emoji` is not ``None``.

            If you want the icon that a role has displayed, consider using :attr:`display_icon`.

        .. versionadded:: 2.0
        """
        if self._icon is None:
            return None
        return Asset._from_icon(self._state, self.id, self._icon, path='role')

    @property
    def display_icon(self) -> Optional[Union[Asset, str]]:
        """Optional[Union[:class:`.Asset`, :class:`str`]]: Returns the role's display icon, if available.

        .. versionadded:: 2.0
        """
        return self.icon or self.unicode_emoji

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the role's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention a role."""
        return f'<@&{self.id}>'

    @property
    def members(self) -> List[Member]:
        """List[:class:`Member`]: Returns all the members with this role."""
        all_members = list(self.guild._members.values())
        if self.is_default():
            return all_members

        role_id = self.id
        return [member for member in all_members if member._roles.has(role_id)]

    @property
    def flags(self) -> RoleFlags:
        """:class:`RoleFlags`: Returns the role's flags.

        .. versionadded:: 2.4
        """
        return RoleFlags._from_value(self._flags)
