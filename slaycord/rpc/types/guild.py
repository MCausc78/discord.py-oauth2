from __future__ import annotations

from typing import TypedDict
from typing_extensions import NotRequired

from ...types.snowflake import Snowflake


class PartialGuild(TypedDict):
    id: Snowflake
    name: str
    icon_url: NotRequired[str]  # I thought this is Optional, but apparently not
