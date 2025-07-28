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

from ..enums import Enum

__all__ = (
    'CertifiedDeviceType',
    'DeepLinkLocation',
    'LayoutMode',
    'LogLevel',
    'Opcode',
    'OrientationLockState',
    'PromptBehavior',
    'ShortcutKeyComboType',
    'ThermalState',
    'VoiceConnectionState',
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


class LayoutMode(Enum):
    focused = 0
    pip = 1
    grid = 2


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


class ThermalState(Enum):
    nominal = 0
    fair = 1
    serious = 2
    critical = 3


class VoiceConnectionState(Enum):
    disconnected = 'DISCONNECTED'
    awaiting_endpoint = 'AWAITING_ENDPOINT'
    authenticating = 'AUTHENTICATING'
    connecting = 'CONNECTING'
    rtc_disconnected = 'RTC_DISCONNECTED'
    rtc_connecting = 'RTC_CONNECTING'
    rtc_connected = 'RTC_CONNECTED'
    no_route = 'NO_ROUTE'
    ice_checking = 'ICE_CHECKING'
    dtls_conneccting = 'DTLS_CONNECTING'


class VoiceSettingsModeType(Enum):
    ptt = 'PUSH_TO_TALK'
    voice_activity = 'VOICE_ACTIVITY'
