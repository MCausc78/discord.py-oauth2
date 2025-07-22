from __future__ import annotations

from ..enums import Enum

__all__ = (
    'Opcode',
    'PromptBehavior',
)


class Opcode(Enum):
    handshake = 0
    frame = 1
    close = 2
    ping = 3
    pong = 4


class PromptBehavior(Enum):
    none = 'none'
    consent = 'consent'
