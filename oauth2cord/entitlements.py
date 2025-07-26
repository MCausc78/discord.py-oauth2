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

from typing import List, Optional, TYPE_CHECKING

from .enums import try_enum, EntitlementFulfillmentStatus, EntitlementSourceType, EntitlementType, GiftStyle, QuestRewardType
from .flags import GiftFlags
from .mixins import Hashable
from .quests import QuestRewardCode
from .sku import SKU
from .utils import _get_as_snowflake, parse_time, snowflake_time, utcnow

if TYPE_CHECKING:
    from datetime import datetime

    from .guild import Guild
    from .state import BaseConnectionState
    from .types.entitlements import (
        Entitlement as EntitlementPayload,
        TenantMetadata as TenantMetadataPayload,
        QuestRewardsMetadata as QuestRewardsMetadataPayload,
        GiftCode as GiftPayload,
    )
    from .user import User

__all__ = (
    'Entitlement',
    'TenantMetadata',
    'QuestRewardsMetadata',
    'Gift',
)


class Entitlement(Hashable):
    """Represents a Discord entitlement.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two entitlements are equal.

        .. describe:: x != y

            Checks if two entitlements are not equal.

        .. describe:: hash(x)

            Returns the entitlement's hash.

    Attributes
    ----------
    id: :class:`int`
        The entitlement's ID.
    type: :class:`EntitlementType`
        The type of the entitlement.
    sku_id: :class:`int`
        The ID of the SKU that the entitlement belongs to.
    application_id: :class:`int`
        The ID of the application that the entitlement belongs to.
    user_id: :class:`int`
        The ID of the user that is granted access to the entitlement.
    guild_id: Optional[:class:`int`]
        The guild's ID who is granted access to the SKU.
    parent_id: Optional[:class:`int`]
        The parent entitlement's ID.
    deleted: :class:`bool`
        Whether the entitlement has been deleted.
    consumed: :class:`bool`
        For consumable items, whether the entitlement has been consumed.
    branch_ids: List[:class:`int`]
        The IDs of the granted application branches.
    starts_at: Optional[:class:`~datetime.datetime`]
        A UTC start date after which the entitlement is valid.
    ends_at: Optional[:class:`~datetime.datetime`]
        A UTC date after which entitlement is no longer valid.
    promotion_id: Optional[:class:`int`]
        The ID of the promotion this entitlement is from.
    subscription_id: Optional[:class:`int`]
        The ID of the subscription this entitlement is from.
    gift_batch_id: Optional[:class:`int`]
        The ID of the batch the gift attached to this entitlement from.
    gifter_id: Optional[:class:`int`]
        The user's ID who gifted this entitlement.
    gift_style: Optional[:class:`GiftStyle`]
        The style of the gift attached to this entitlement.
    fulfillment_status: Optional[:class:`EntitlementFulfillmentStatus`]
        The tenant fulfillment status of the entitlement.
    fulfilled_at: Optional[:class:`~datetime.datetime`]
        When the entitlement was fulfilled.
    source_type: Optional[:class:`EntitlementSourceType`]
        The type of the source this entitlement is from.
    tenant_metadata: Optional[:class:`TenantMetadata`]
        The tenant metadata for the entitlement.
    sku: Optional[:class:`SKU`]
        The granted SKU.
    """

    __slots__ = (
        '_state',
        'id',
        'type',
        'sku_id',
        'application_id',
        'user_id',
        'guild_id',
        'parent_id',
        'deleted',
        'consumed',
        'branch_ids',
        'starts_at',
        'ends_at',
        'promotion_id',
        'subscription_id',
        '_gift_flags',
        'gift_batch_id',
        'gifter_id',
        'gift_style',
        'fulfillment_status',
        'fullfilled_at',
        'source_type',
        'tenant_metadata',
        'sku',
        # 'subscription_plan',
    )

    def __init__(self, *, data: EntitlementPayload, state: BaseConnectionState) -> None:
        self._state: BaseConnectionState = state
        self.id: int = int(data['id'])
        self._update(data)

    def _update(self, data: EntitlementPayload, /) -> None:
        state = self._state

        raw_gift_style = data.get('gift_style')
        raw_fulfillment_status = data.get('fulfillment_status')
        raw_source_type = data.get('source_type')
        raw_tenant_metadata = data.get('tenant_metadata')
        raw_sku = data.get('sku')

        self.type: EntitlementType = try_enum(EntitlementType, data['type'])
        self.sku_id: int = int(data['sku_id'])
        self.application_id: int = int(data['application_id'])
        self.user_id: int = int(data['user_id'])
        self.parent_id: Optional[int] = _get_as_snowflake(data, 'parent_id')
        self.deleted: bool = data['deleted']
        self.consumed: bool = data.get('consumed', False)
        self.branch_ids: List[int] = list(map(int, data.get('branches', ())))
        self.starts_at: Optional[datetime] = parse_time(data.get('starts_at'))
        self.ends_at: Optional[datetime] = parse_time(data.get('ends_at'))
        self.promotion_id: Optional[int] = _get_as_snowflake(data, 'promotion_id')
        self.subscription_id: Optional[int] = _get_as_snowflake(data, 'subscription_id')
        self._gift_flags: int = data['gift_code_flags']
        self.gift_batch_id: Optional[int] = _get_as_snowflake(data, 'gift_code_batch_id')
        self.gifter_id: Optional[int] = _get_as_snowflake(data, 'gifter_user_id')
        self.gift_style: Optional[GiftStyle] = None if raw_gift_style is None else try_enum(GiftStyle, raw_gift_style)
        self.fulfillment_status: Optional[EntitlementFulfillmentStatus] = (
            None if raw_fulfillment_status is None else try_enum(EntitlementFulfillmentStatus, raw_fulfillment_status)
        )
        self.fullfilled_at: Optional[datetime] = parse_time(data.get('fulfilled_at'))
        self.source_type: Optional[EntitlementSourceType] = (
            None if raw_source_type is None else try_enum(EntitlementSourceType, raw_source_type)
        )
        self.tenant_metadata: Optional[TenantMetadata] = (
            None if raw_tenant_metadata is None else TenantMetadata(data=raw_tenant_metadata, state=state)
        )
        self.sku: Optional[SKU] = None if raw_sku is None else SKU(data=raw_sku, state=state)

    @property
    def gift_flags(self) -> GiftFlags:
        """:class:`GiftFlags`: The gift's flags."""
        return GiftFlags._from_value(self._gift_flags)

    def __repr__(self) -> str:
        return f'<Entitlement id={self.id} type={self.type!r} user_id={self.user_id}>'

    @property
    def user(self) -> Optional[User]:
        """Optional[:class:`User`]: The user that is granted access to the entitlement."""
        if self.user_id is None:
            return None
        return self._state.get_user(self.user_id)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild that is granted access to the entitlement."""
        return self._state.get_guild(self.guild_id)

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the entitlement's creation time in UTC."""
        return snowflake_time(self.id)

    def is_expired(self) -> bool:
        """:class:`bool`: Returns ``True`` if the entitlement is expired. Will be always False for test entitlements."""
        if self.ends_at is None:
            return False
        return utcnow() >= self.ends_at

    async def consume(self) -> None:
        """|coro|

        Marks a one-time purchase entitlement as consumed.

        Raises
        ------
        NotFound
            The entitlement could not be found.
        HTTPException
            Consuming the entitlement failed.
        """

        await self._state.http.consume_application_entitlement(self.application_id, self.id)

    async def delete(self) -> None:
        """|coro|

        Deletes the entitlement.

        Raises
        ------
        NotFound
            The entitlement could not be found.
        HTTPException
            Deleting the entitlement failed.
        """

        await self._state.http.delete_application_entitlement(self.application_id, self.id)


class TenantMetadata:
    """Represents tenant metadata for entitlement.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two tenant metadatas are equal.

        .. describe:: x != y

            Checks if two tenant metadatas are not equal.

    Attributes
    ----------
    quest_reward: :class:`QuestRewardsMetadata`
        The metadata about the quest rewards granted by the entitlement.
    """

    __slots__ = ('quest_reward',)

    def __init__(self, *, data: TenantMetadataPayload, state: BaseConnectionState) -> None:
        self.quest_reward: QuestRewardsMetadata = QuestRewardsMetadata(data=data['quest_reward'], state=state)

    def __eq__(self, other: object, /) -> bool:
        return self is other or (isinstance(other, TenantMetadata) and self.quest_reward == other.quest_reward)

    def __ne__(self, other: object, /) -> bool:
        return self is not other and (not isinstance(other, TenantMetadata) or self.quest_reward != other.quest_reward)


class QuestRewardsMetadata:
    """Represents metadata about the quest rewards.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two quest rewards metadatas are equal.

        .. describe:: x != y

            Checks if two quest rewards metadatas are not equal.

    Attributes
    ----------
    tag: :class:`QuestRewardType`
        The reward's type of the entitlement.
    reward_code: Optional[:class:`QuestRewardCode`]
        The reward granted by the entitlement.
    """

    __slots__ = (
        'tag',
        'reward_code',
    )

    def __init__(self, *, data: QuestRewardsMetadataPayload, state: BaseConnectionState) -> None:
        raw_reward_code = data.get('reward_code')

        self.tag: QuestRewardType = try_enum(QuestRewardType, data['tag'])
        self.reward_code: Optional[QuestRewardCode] = (
            None if raw_reward_code is None else QuestRewardCode(data=raw_reward_code, state=state)
        )

    def __eq__(self, other: object, /) -> bool:
        return self is other or (
            isinstance(other, QuestRewardsMetadata) and self.tag == other.tag and self.reward_code == other.reward_code
        )

    def __ne__(self, other: object, /) -> bool:
        return self is not other and (
            not isinstance(other, QuestRewardsMetadata) or self.tag != other.tag or self.reward_code != other.reward_code
        )


class Gift:
    """Represents a Discord gift.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two gifts are equal.

        .. describe:: x != y

            Checks if two gifts are not equal.

        .. describe:: hash(x)

            Returns the gift's hash.

        .. describe:: str(x)

            Returns the gift's URL.

    Attributes
    ----------
    code: :class:`str`
        The code of the gift.
    sku_id: :class:`int`
        The granted SKU's ID.
    application_id: :class:`int`
        The application's ID that owns granted SKU.
    uses: :class:`int`
        How many times the gift has been used.
    max_uses: :class:`int`
        The maximum number of times the gift can be used.
    redeemed: :class:`bool`
        Whether you redeemed this gift.
    expires_at: Optional[:class:`~datetime.datetime`]
        When the gift expires.
    batch_id: Optional[:class:`int`]
        The batch's ID this gift is from.
    entitlement_branch_ids: List[:class:`int`]
        The IDs of the application branches granted by this gift.
    style: Optional[:class:`GiftStyle`]
        The gift's style.
    user: Optional[:class:`User`]
        The user who created this gift.
    subscription_plan_id: Optional[:class:`int`]
        The ID of the subscription plan this gift grants.
    """

    __slots__ = (
        '_state',
        'code',
        'sku_id',
        'application_id',
        '_flags',
        'uses',
        'max_uses',
        'redeemed',
        'expires_at',
        'batch_id',
        'entitlement_branch_ids',
        'style',
        'user',
        # 'store_listing',
        'subscription_plan_id',
        # 'subscription_plan',
        # 'subscription_trial',
        # 'promotion',
    )

    def __init__(self, *, data: GiftPayload, state: BaseConnectionState) -> None:
        self._state: BaseConnectionState = state
        self.code: str = data['code']
        self.sku_id: int = int(data['sku_id'])
        self.application_id: int = int(data['application_id'])
        self._update(data)

    def _update(self, data: GiftPayload) -> None:
        raw_gift_style = data.get('gift_style')
        raw_user = data.get('user')

        self._flags: int = data.get('flags', 0)
        self.uses: int = data['uses']
        self.max_uses: int = data['max_uses']
        self.redeemed: bool = data['redeemed']
        self.expires_at: Optional[datetime] = parse_time(data.get('expires_at'))
        self.batch_id: Optional[int] = _get_as_snowflake(data, 'batch_id')
        self.entitlement_branch_ids: List[int] = list(map(int, data.get('entitlement_branches', ())))
        self.style: Optional[GiftStyle] = None if raw_gift_style is None else try_enum(GiftStyle, raw_gift_style)
        self.user: Optional[User] = None if raw_user is None else self._state.store_user(raw_user)

    def __eq__(self, other: object, /) -> bool:
        return self is other or isinstance(other, Gift) and self.code == other.code

    def __ne__(self, other: object, /) -> bool:
        return self is not other and (not isinstance(other, Gift) or self.code != other.code)

    def __hash__(self) -> int:
        return hash(self.code)

    def __repr__(self) -> str:
        return f'<Gift code={self.code!r} uses={self.uses!r} max_uses={self.max_uses!r}>'

    def __str__(self) -> str:
        return self.url

    @property
    def flags(self) -> GiftFlags:
        """:class:`GiftFlags`: The flags of the gift this entitlement is attached to."""
        return GiftFlags._from_value(self._flags)

    @property
    def url(self) -> str:
        """:class:`str`: The URL to this gift."""
        return f'discord.gift/{self.code}'
