from __future__ import annotations

from typing import List, Literal, TypedDict

# from typing_extensions import NotRequired

from ...types.snowflake import Snowflake
from .message import Message
from .voice_state import VoiceState

GuildChannelType = Literal[
    0,
    2,
    4,
    5,
    6,
    10,
    11,
    12,
    13,
    14,
    15,
    16,
    # 17: LOBBY
    # 18: DM_SDK
]


class PartialGuildChannel(TypedDict):
    id: Snowflake
    name: str
    type: GuildChannelType


class GuildChannel(PartialGuildChannel):
    topic: str
    bitrate: int
    user_limit: int
    guild_id: Snowflake
    position: int
    messages: List[Message]
    voice_states: List[VoiceState]
