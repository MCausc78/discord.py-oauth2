from __future__ import annotations

from ..enums import Enum

__all__ = (
    'Opcode',
    'PromptBehavior',
    'ShortcutKeyComboType',
    'VoiceSettingsModeType',
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


class ShortcutKeyComboType(Enum):
    keyboard_key = 0
    mouse_button = 1
    keyboard_modifier_key = 2
    gamepad_button = 3


class VoiceSettingsModeType(Enum):
    ptt = 'PUSH_TO_TALK'
    voice_activity = 'VOICE_ACTIVITY'
