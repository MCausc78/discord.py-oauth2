"""
The MIT License (MIT)

Copyright (c) 2025-present MCausc78

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

from datetime import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

from .asset import Asset
from .color import Color
from .mixins import Hashable
from .partial_emoji import PartialEmoji
from .enums import try_enum, GuildBadgeType, GuildVisibility
from .utils import _get_as_snowflake, snowflake_time

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.guild import GuildFeature
    from .types.profile import (
        GuildProfile as GuildProfilePayload,
        GameActivity as GameActivityPayload,
        GuildTrait as GuildTraitPayload,
    )


class GuildProfile(Hashable):
    """Represents a guild profile.

    This is referred to as a "server" in the official Discord UI.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    id: :class:`int`
        The guild's ID.
    name: :class:`str`
        The guild name.
    approximate_member_count: :class:`int`
        The approximate number of members in the guild.
    approximate_presence_count: :class:`int`
        The approximate number of members currently active in the guild.
        Offline members are excluded.
    description: :class:`str`
        The guild's description.
    primary_brand_color: :class:`Color`
        The guild's accent color.
    game_application_ids: List[:class:`int`]
        The IDs of the applications representing the games the guild plays.
    game_activity: Dict[:class:`int`, :class:`GameActivity`]
        The activity of the guild in each game.
    tag: Optional[:class:`str`]
        The clan tag of the guild, if any.
    badge_type: :class:`GuildBadgeType`
        The clan badge shown on the guild's tag.
    primary_badge_color: :class:`Color`
        The primary color of the badge.
    secondary_badge_color: :class:`Color`
        The secondary color of the badge.
    traits: List[:class:`GuildTrait`]
        A list of terms used to describe the guild's interest and personality.
    features: List[:class:`str`]
        A list of features that the guild has. The features that a guild can have are
        subject to arbitrary change by Discord. A list of guild features can be found
        in :userdoccers:`Discord Userdoccers <resources/guild#guild-features>`.
    visibility: :class:`GuildVisibility`
        The visibility level of the guild.
    premium_subscription_count: :class:`int`
        The number of "boosts" this guild currently has.
    premium_tier: :class:`int`
        The premium tier for this guild. Corresponds to "Nitro Server" in the official UI.
        The number goes from 0 to 3 inclusive.
    """

    __slots__ = (
        '_state',
        'id',
        'name',
        '_icon',
        'approximate_member_count',
        'approximate_presence_count',
        'description',
        'primary_brand_color',
        '_banner',
        'game_application_ids',
        'game_activity',
        'tag',
        'badge_type',
        'primary_badge_color',
        'secondary_badge_color',
        '_badge',
        'traits',
        'features',
        'visibility',
        '_custom_banner',
        'premium_subscription_count',
        'premium_tier',
    )

    def __init__(self, *, data: GuildProfilePayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self._update(data)

    def _update(self, data: GuildProfilePayload) -> None:
        state = self._state

        self.name: str = data['name']
        self._icon: Optional[str] = data.get('icon_hash')
        self.approximate_member_count: int = data['member_count']
        self.approximate_presence_count: int = data['online_count']
        self.description: str = data['description']
        self.primary_brand_color: Color = Color.from_str(data['brand_color_primary'])
        self._banner: Optional[str] = data.get('banner_hash')
        self.game_application_ids: List[int] = list(map(int, data['game_application_ids']))
        self.game_activity: Dict[int, GameActivity] = {
            int(k): GameActivity(data=vd) for k, vd in data['game_activity'].items()
        }
        self.tag: Optional[str] = data.get('tag')
        self.badge_type: GuildBadgeType = try_enum(GuildBadgeType, data['badge'])
        self.primary_badge_color: Color = Color.from_str(data['badge_color_primary'])
        self.secondary_badge_color: Color = Color.from_str(data['badge_color_secondary'])
        self._badge: str = data['badge_hash']
        self.traits: List[GuildTrait] = [GuildTrait(data=d, state=state) for d in data['traits']]
        self.features: List[GuildFeature] = data['features']
        self.visibility: GuildVisibility = try_enum(GuildVisibility, data['visibility'])
        self._custom_banner: Optional[str] = data.get('custom_banner_hash')
        self.premium_subscription_count: int = data['premium_subscription_count']
        self.premium_tier: int = data['premium_tier']

    @property
    def created_at(self) -> datetime:
        """:class:`~datetime.datetime`: Returns the guild's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's icon asset, if available."""
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's banner asset, if available.

        .. deprecated:: 3.0
        """
        if self._banner is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._banner, path='banners')

    @property
    def badge(self) -> Optional[Asset]:
        """:class:`Asset`: Returns the guild's badge, if available."""
        return Asset._from_primary_guild(self._state, self.id, self._badge)

    @property
    def discovery_splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's discovery splash asset, if available."""
        if self._custom_banner is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._custom_banner, path='discovery-splashes')


class GameActivity:
    """Represents a game activity.

    Attributes
    ----------
    level: :class:`int`
        The activity level of the clan in the game.
    score: :class:`int`
        The activity score of the clan in the game
    """

    __slots__ = (
        'level',
        'score',
    )

    def __init__(self, *, data: GameActivityPayload) -> None:
        self.level: int = data['activity_level']
        self.score: int = data['activity_score']


class GuildTrait:
    """Represents a guild trait.

    Attributes
    ----------
    emoji: Optional[:class:`PartialEmoji`]
        The emoji.
    label: :class:`str`
        The trait name.
    position: :class:`int`
        The position of trait in array for sorting.
    """

    __slots__ = (
        'emoji',
        'label',
        'position',
    )

    def __init__(self, *, data: GuildTraitPayload, state: ConnectionState) -> None:
        emoji_id = _get_as_snowflake(data, 'emoji_id')
        emoji_name = data.get('emoji_name')
        emoji_animated = data.get('emoji_animated', False)

        if emoji_id is None and emoji_name is None:
            emoji = None
        else:
            emoji = PartialEmoji.with_state(
                state,
                name=emoji_name or '',
                animated=emoji_animated,
                id=emoji_id,
            )

        self.emoji: Optional[PartialEmoji] = emoji
        self.label: str = data['label']
        self.position: int = data['position']


__all__ = (
    'GuildProfile',
    'GameActivity',
    'GuildTrait',
)
