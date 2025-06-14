from __future__ import annotations

from typing import Optional, TypedDict
from typing_extensions import NotRequired

from ...types.snowflake import Snowflake
from ...types.user import RelationshipType
from .presence import RelationshipPresence


class AvatarDecorationData(TypedDict):
    asset: str
    skuId: NotRequired[Snowflake]
    expiresAt: NotRequired[int]


class User(TypedDict):
    id: Snowflake
    username: str
    discriminator: str
    global_name: Optional[str]
    avatar: Optional[str]
    avatar_decoration_data: Optional[AvatarDecorationData]
    bot: bool
    flags: int
    premium_type: int


class Relationship(TypedDict):
    type: RelationshipType
    user: User
    presence: RelationshipPresence
