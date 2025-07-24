from __future__ import annotations

from typing import Optional, TypedDict
from typing_extensions import NotRequired

from ...types.snowflake import Snowflake


class PartialGuild(TypedDict):
    id: Snowflake
    name: str
    icon_url: NotRequired[
        Optional[str]
    ]  # If not none, then its https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.png?size=128
