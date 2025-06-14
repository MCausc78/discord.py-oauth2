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

from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from .quests import QuestRewardType, QuestRewardCode
from .sku import SKU
from .snowflake import Snowflake
from .user import User

EntitlementType = Literal[1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13]

EntitlementFulfillmentStatus = Literal[
    0,
    1,
    2,
    3,
    4,
    5,
    6,
    7,
]

EntitlementSourceType = Literal[
    1,
    2,
    3,
    4,
    5,
    6,
    7,
    8,
]
GiftStyle = Literal[
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
]


class Entitlement(TypedDict):
    id: Snowflake
    type: EntitlementType
    sku_id: Snowflake
    application_id: Snowflake
    user_id: Snowflake
    guild_id: NotRequired[Snowflake]
    parent_id: NotRequired[Snowflake]
    deleted: bool
    consumed: NotRequired[bool]
    branches: NotRequired[List[Snowflake]]
    starts_at: Optional[str]
    ends_at: Optional[str]
    promotion_id: Optional[Snowflake]
    subscription_id: NotRequired[Snowflake]
    gift_code_flags: int
    gift_code_batch_id: NotRequired[Snowflake]
    gifter_user_id: NotRequired[Snowflake]
    gift_style: NotRequired[GiftStyle]
    fulfillment_status: NotRequired[EntitlementFulfillmentStatus]
    fulfilled_at: NotRequired[str]
    source_type: NotRequired[EntitlementSourceType]
    tenant_metadata: NotRequired[TenantMetadata]
    sku: NotRequired[SKU]
    # subscription_plan: NotRequired[PartialSubscriptionPlan]


class TenantMetadata(TypedDict):
    quest_reward: QuestRewardsMetadata


class QuestRewardsMetadata(TypedDict):
    tag: QuestRewardType
    reward_code: NotRequired[QuestRewardCode]


class GiftCode(TypedDict):
    code: str
    sku_id: Snowflake
    application_id: Snowflake
    flags: NotRequired[int]
    uses: int
    max_uses: int
    redeemed: bool
    expires_at: Optional[str]
    batch_id: NotRequired[Snowflake]
    entitlement_branches: NotRequired[List[Snowflake]]
    gift_style: NotRequired[Optional[GiftStyle]]
    user: NotRequired[User]
    # store_listing: NotRequired[StoreListing]
    subscription_plan_id: NotRequired[Snowflake]
    # subscription_plan: NotRequired[SubscriptionPlan]
    # subscription_trial: NotRequired[SubscriptionTrial]
    # promotion: NotRequired[Promotion]


EntitlementOwnerType = Literal[1, 2]
