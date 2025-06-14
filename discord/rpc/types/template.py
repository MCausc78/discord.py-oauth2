from __future__ import annotations

from typing import Literal, Optional, TypedDict

from ...types.guild import Guild
from ...types.snowflake import Snowflake
from ...types.user import User


class Template(TypedDict):
    code: str
    state: Literal['RESOLVED']
    name: str
    description: str
    creatorId: Snowflake
    creator: User
    createdAt: str
    updatedAt: str
    sourceGuildId: Snowflake
    serializeSourceGuild: Guild
    usageCount: int
    isDirty: Optional[bool]
