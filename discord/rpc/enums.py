from __future__ import annotations

from ..enums import Enum

__all__ = (
    'CertifiedDeviceType',
    'DeepLinkLocation',
    'Opcode',
    'OrientationLockState',
    'PromptBehavior',
    'ShortcutKeyComboType',
    'VoiceSettingsModeType',
)


class CertifiedDeviceType(Enum):
    audio_input = 'audioinput'
    audio_output = 'audiooutput'
    video_input = 'videoinput'


class DeepLinkLocation(Enum):
    user_settings = 'USER_SETTINGS'
    changelog = 'CHANGELOG'
    library = 'LIBRARY'
    store_home = 'STORE_HOME'
    store_listing = 'STORE_LISTING'
    pick_guild_settings = 'PICK_GUILD_SETTINGS'
    channel = 'CHANNEL'
    quest_home = 'QUEST_HOME'
    discovery_game_results = 'DISCOVERY_GAME_RESULTS'
    oauth2 = 'OAUTH2'
    shop = 'SHOP'
    features = 'FEATURES'
    activities = 'ACTIVITIES'


class LogLevel(Enum):
    log = 'log'
    warn = 'warn'
    debug = 'debug'
    info = 'info'
    error = 'error'


class Opcode(Enum):
    handshake = 0
    frame = 1
    close = 2
    ping = 3
    pong = 4


class OrientationLockState(Enum):
    unlocked = 1
    portrait = 2
    landscape = 3


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
