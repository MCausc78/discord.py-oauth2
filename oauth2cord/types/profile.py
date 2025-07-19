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

from typing import Dict, List, Literal, Optional, TypedDict

from .guild import GuildFeature
from .snowflake import Snowflake


class GuildProfile(TypedDict):
    id: Snowflake
    name: str
    icon_hash: Optional[str]
    member_count: int
    online_count: int
    description: str
    brand_color_primary: str
    banner_hash: Optional[str]
    game_application_ids: List[Snowflake]
    game_activity: Dict[Snowflake, GameActivity]
    tag: Optional[str]
    badge: GuildBadgeType
    badge_color_primary: str
    badge_color_secondary: str
    badge_hash: str
    traits: List[GuildTrait]
    features: List[GuildFeature]
    visibility: GuildVisibility
    custom_banner_hash: Optional[str]
    premium_subscription_count: int
    premium_tier: int


class GameActivity(TypedDict):
    activity_level: int
    activity_score: int


class GuildTrait(TypedDict):
    emoji_id: Optional[Snowflake]
    emoji_name: Optional[str]
    emoji_animated: bool
    label: str
    position: int


GuildBadgeType = Literal[
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
    9,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    17,
    18,
    19,
    20,
]

GuildVisibility = Literal[1, 2, 3]
