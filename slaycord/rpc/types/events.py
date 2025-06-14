from __future__ import annotations

from typing import Any, Optional, TypedDict
from typing_extensions import NotRequired

from .user import User


class IncomingPacket(TypedDict):
    cmd: str
    data: Any
    nonce: Optional[str]
    evt: Optional[str]


class OutgoingPacket(TypedDict):
    cmd: str
    args: Any
    nonce: str
    evt: NotRequired[str]


class ReadyEventConfig(TypedDict):
    cdn_host: str  # like 'cdn.discordapp.com'
    api_endpoint: str  # like '//canary.discord.com/api'
    environment: str  # like 'production'


class ReadyEvent(TypedDict):
    v: int
    config: ReadyEventConfig
    user: NotRequired[User]
