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

from typing import List, Literal, TypedDict
from typing_extensions import NotRequired

# {
#     "input": {
#         "available_devices": [
#             {
#                 "id": "default",
#                 "name": "Default"
#             }
#         ],
#         "device_id": "default",
#         "volume": 0.8075820208202183
#     },
#     "output": {
#         "available_devices": [
#             {
#                 "id": "default",
#                 "name": "Default (Digital Audio (S/PDIF) (High Definition Audio Device))"
#             },
#             {
#                 "id": "{0.0.0.00000000}.{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}",
#                 "name": "Digital Audio (S/PDIF) (High Definition Audio Device)"
#             },
#             {
#                 "id": "{0.0.0.00000000}.{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}",
#                 "name": "Digital Audio (S/PDIF) (High Definition Audio Device)"
#             }
#         ],
#         "device_id": "{0.0.0.00000000}.{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}", # .id from last available_devices element
#         "volume": 140.05719321561588
#     },
#     "mode": {
#         "type": "VOICE_ACTIVITY",
#         "auto_threshold": true,
#         "threshold": -60,
#         "shortcut": [],
#         "delay": 20
#     },
#     "automatic_gain_control": true,
#     "echo_cancellation": true,
#     "noise_suppression": false,
#     "qos": false,
#     "silence_warning": false,
#     "deaf": false,
#     "mute": false
# }


class AvailableDevice(TypedDict):
    id: str
    name: str


class VoiceIOSettings(TypedDict):
    available_devices: List[AvailableDevice]
    device_id: str  # Primary device ID?
    volume: float  # I assume thats 0-200


"""
# function et(e) {
#     let t = E.Z.getSettings()
#         , n = e => Object.values(e).sort( (e, t) => e.index - t.index).map(e => ({
#         id: e.id,
#         name: e.name
#     })), r = e(t);
#     return {
#         input: {
#             available_devices: n(E.Z.getInputDevices()),
#             device_id: t.inputDeviceId,
#             volume: t.inputVolume
#         },
#         output: {
#             available_devices: n(E.Z.getOutputDevices()),
#             device_id: t.outputDeviceId,
#             volume: t.outputVolume
#         },
#         mode: {
#             type: t.mode,
#             auto_threshold: t.modeOptions.autoThreshold,
#             threshold: t.modeOptions.threshold,
#             shortcut: r,
#             delay: t.modeOptions.delay
#         },
#         automatic_gain_control: t.automaticGainControl,
#         echo_cancellation: t.echoCancellation,
#         noise_suppression: t.noiseSuppression,
#         qos: t.qos,
#         silence_warning: t.silenceWarning,
#         deaf: t.deaf,
#         mute: t.mute
#     }
# }
"""

ShortcutKeyComboType = Literal[
    0,  # KEYBOARD_KEY
    1,  # MOUSE_BUTTON
    2,  # KEYBOARD_MODIFIER_KEY
    3,  # GAMEPAD_BUTTON
]


class PartialShortcutKeyCombo(TypedDict):
    type: ShortcutKeyComboType
    code: str
    name: NotRequired[str]


class ShortcutKeyCombo(TypedDict):
    type: ShortcutKeyComboType
    code: str
    name: str


VoiceSettingsModeType = Literal['PUSH_TO_TALK', 'ACTIVITY']


class VoiceSettingsMode(TypedDict):
    type: VoiceSettingsModeType
    auto_threshold: bool
    threshold: int
    shortcut: ShortcutKeyCombo
    delay: int


class VoiceSettings(TypedDict):
    input: VoiceIOSettings
    output: VoiceIOSettings
    mode: VoiceSettingsMode
    automatic_gain_control: bool
    echo_cancellation: bool
    noise_suppression: bool
    qos: bool
    silence_warning: bool
    deaf: bool
    mute: bool
