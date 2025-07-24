from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING, Union

from ..enums import try_enum
from ..utils import MISSING
from .enums import ShortcutKeyComboType, VoiceSettingsModeType
from .voice_state import Pan

if TYPE_CHECKING:
    from typing_extensions import Self

    from .state import RPCConnectionState
    from .types.commands import (
        SetUserVoiceSettingsResponse as SetUserVoiceSettingsResponsePayload,
        SetVoiceSettingsRequestIO as SetVoiceSettingsRequestIOPayload,
        SetVoiceSettingsRequestMode as SetVoiceSettingsRequestModePayload,
    )
    from .types.settings import (
        AvailableDevice as AvailableDevicePayload,
        VoiceIOSettings as VoiceIOSettingsPayload,
        PartialShortcutKeyCombo as PartialShortcutKeyComboPayload,
        ShortcutKeyCombo as ShortcutKeyComboPayload,
        VoiceSettingsMode as VoiceSettingsModePayload,
        VoiceSettings as VoiceSettingsPayload,
    )

__all__ = (
    'UserVoiceSettings',
    'AvailableDevice',
    'VoiceIOSettings',
    'ShortcutKeyCombo',
    'PartialVoiceSettingsMode',
    'VoiceSettingsMode',
    'VoiceSettings',
)

class UserVoiceSettings:
    """Represents voice settings for a specific user.
    
    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The target user's ID these voice settings are set for.
    pan: :class:`Pan`
        The pan of the target user, set locally.
    volume: :class:`float`
        The volume of the target user, set locally.
    mute: :class:`bool`
        Indicates whether the user muted target locally.
    """

    __slots__ = (
        '_state',
        'id',
        'pan',
        'volume',
        'mute',
    )

    def __init__(self, *, data: SetUserVoiceSettingsResponsePayload, state: RPCConnectionState) -> None:
        self._state: RPCConnectionState = state
        self.id: int = int(data['user_id'])
        self.pan: Pan = Pan.from_dict(data['pan'])
        self.volume: float = data['volume']
        self.mute: bool = data['mute']

class AvailableDevice:
    __slots__ = (
        'id',
        'name',
    )

    def __init__(self, *, id: str, name: str) -> None:
        self.id: str = id
        self.name: str = name
    
    @classmethod
    def from_dict(cls, data: AvailableDevicePayload) -> Self:
        return cls(id=data['id'], name=data['name'])

    def to_dict(self) -> AvailableDevicePayload:
        return {'id': self.id, 'name': self.name}

class VoiceIOSettings:
    """Represents I/O voice settings.
    
    .. versionadded:: 3.0

    Attributes
    ----------
    available_devices: List[:class:`AvailableDevice`]
        The available devices.

        This is received only and setting will have no effect.
    device_id: :class:`str`
        The ID of the primary device.
    volume: :class:`float`
        The input voice level. Must be between 0 and 100.
    """

    __slots__ = (
        'available_devices',
        'device_id',
        'volume',
    )

    def __init__(self, *, available_devices: Optional[List[AvailableDevice]] = None, device_id: str, volume: float) -> None:
        if available_devices is None:
            available_devices = []
        
        self.available_devices: List[AvailableDevice] = available_devices
        self.device_id: str = device_id
        self.volume: float = volume
    
    @classmethod
    def from_dict(cls, data: VoiceIOSettingsPayload) -> Self:
        return cls(
            available_devices=list(map(AvailableDevice.from_dict, data['available_devices'])),
            device_id=data['device_id'],
            volume=data['volume'],
        )

    def to_partial_dict(self) -> SetVoiceSettingsRequestIOPayload:
        return {'device_id': self.device_id, 'volume': self.volume}

    def to_dict(self) -> VoiceIOSettingsPayload:
        return {
            'available_devices': [ad.to_dict() for ad in self.available_devices],
            'device_id': self.device_id,
            'volume': self.volume,
        }
    

class ShortcutKeyCombo:
    """Represents a shortcut key combo for PTT (Push-To-Talk).

    Attributes
    ----------
    type: :class:`ShortcutKeyComboType`
        The type of the combo.
    code: :class:`int`
        The code of the combo.
    name: Optional[:class:`str`]
        The name of the combo.
    """

    __slots__ = (
        'type',
        'code',
        'name',
    )

    def __init__(self, code: int, *, type: ShortcutKeyComboType, name: Optional[str] = None) -> None:
        self.type: ShortcutKeyComboType = type
        self.code: int = code
        self.name: Optional[str] = name
    
    @classmethod
    def from_dict(cls, data: Union[PartialShortcutKeyComboPayload, ShortcutKeyComboPayload]) -> Self:
        return cls(
            type=try_enum(ShortcutKeyComboType, data['type']),
            code=data['code'],
            name=data.get('name'),
        )

    def to_partial_dict(self) -> PartialShortcutKeyComboPayload:
        payload: PartialShortcutKeyComboPayload = {
            'type': self.type.value,
            'code': self.code,
        }
        if self.name is not None:
            payload['name'] = self.name
        return payload

    def to_dict(self) -> ShortcutKeyComboPayload:
        return {
            'type': self.type.value,
            'code': self.code,
            'name': self.name or '',
        }

class PartialVoiceSettingsMode:
    """Represents a modification of voice settings mode.

    Unmodified fields will have their values set to :attr:`~discord.utils.MISSING` (except for ``type``).

    .. versionadded:: 3.0

    Attributes
    ----------
    type: :class:`VoiceSettingsModeType`
        The new type of the voice settings mode.
    auto_threshold: :class:`bool`
        Indicates if the voice activity threshold should be automatically set.
    threshold: :class:`int`
        The new threshold for voice activity (in dB). Must between -100 and 0.
    shortcut: List[:class:`ShortcutKeyCombo`]
        The shortcut key combos for PTT.
    delay: :class:`int`
        The new PTT release delay in milliseconds. Must be between 0 and 2000.
    """
    
    __slots__ = (
        'type',
        'auto_threshold',
        'threshold',
        'shortcut',
        'delay',
    )

    def __init__(
        self,
        *,
        type: VoiceSettingsModeType,
        auto_threshold: bool = MISSING,
        threshold: int = MISSING,
        shortcut: List[ShortcutKeyCombo] = MISSING,
        delay: int = MISSING,
    ) -> None:
        self.type: VoiceSettingsModeType = type
        self.auto_threshold: bool = auto_threshold
        self.threshold: int = threshold
        self.shortcut: List[ShortcutKeyCombo] = shortcut
        self.delay: int = delay

    def to_dict(self) -> SetVoiceSettingsRequestModePayload:
        payload: SetVoiceSettingsRequestModePayload = {'type': self.type.value}
        
        if self.auto_threshold is not MISSING:
            payload['auto_threshold'] = self.auto_threshold
        
        if self.threshold is not MISSING:
            payload['threshold'] = self.threshold
        
        if self.shortcut is not MISSING:
            payload['shortcut'] = [s.to_partial_dict() for s in self.shortcut]
        
        if self.delay is not MISSING:
            payload['delay'] = self.delay
        
        return payload
        
class VoiceSettingsMode:
    """Represents the voice settings mode.

    .. versionadded:: 3.0
    
    Attributes
    ----------
    type: :class:`VoiceSettingsModeType`
        The type of the voice settings mode.
    auto_threshold: :class:`bool`
        Indicates if the voice activity threshold is automatically set.
    threshold: :class:`int`
        The threshold for voice activity (in dB). Must between -100 and 0.
    shortcut: List[:class:`ShortcutKeyCombo`]
        The shortcut key combos for PTT.
    delay: :class:`int`
        The PTT release delay in milliseconds. Must be between 0 and 2000.
    """
    
    __slots__ = (
        'type',
        'auto_threshold',
        'threshold',
        'shortcut',
        'delay',
    )

    def __init__(self, data: VoiceSettingsModePayload) -> None:
        self.type: VoiceSettingsModeType = try_enum(VoiceSettingsModeType, data['type'])
        self.auto_threshold: bool = data['auto_threshold']
        self.threshold: int = data['threshold']
        self.shortcut: List[ShortcutKeyCombo] = list(map(ShortcutKeyCombo.from_dict, data['shortcut']))
        self.delay: int = data['delay']

    def to_dict(self) -> VoiceSettingsModePayload:
        payload: VoiceSettingsModePayload = {
            'type': self.type.value,
            'auto_threshold': self.auto_threshold,
            'threshold': self.threshold,
            'shortcut': [s.to_dict() for s in self.shortcut],
            'delay': self.delay,
        }
        return payload

class VoiceSettings:
    """Represents voice settings.

    .. versionadded:: 3.0

    Attributes
    ----------
    input: :class:`VoiceIOSettings`
        The input settings.
    output: :class:`VoiceIOSettings`
        The output settings.
    mode: :class:`VoiceSettingsMode`
        The voice mode settings.
    automatic_gain_control: :class:`bool`
        Indicates if automatic gain control is enabled.
    echo_cancellation: :class:`bool`
        Indicates if echo cancellation is enabled.
    noise_suppression: :class:`bool`
        Indicates if the background noise is being suppressed.
    qos: :class:`bool`
        Indicates if Voice Quality of Service (QoS) is enabled.
    silence_warning: :class:`bool`
        Indicates if the silence warning notice is disabled.
    deaf: :class:`bool`
        Indicates if the user is deafened by their accord.
    mute: :class:`bool`
        Indicates if the user is muted by their accord.
    """

    __slots__ = (
        '_state',
        'input',
        'output',
        'mode',
        'automatic_gain_control',
        'echo_cancellation',
        'noise_suppression',
        'qos',
        'silence_warning',
        'deaf',
        'mute',
    )

    def __init__(self, *, data: VoiceSettingsPayload, state: RPCConnectionState) -> None:
        self._state: RPCConnectionState = state
        self.input: VoiceIOSettings = VoiceIOSettings.from_dict(data['input'])
        self.output: VoiceIOSettings = VoiceIOSettings.from_dict(data['output'])
        self.mode: VoiceSettingsMode = VoiceSettingsMode(data['mode'])
        self.automatic_gain_control: bool = data['automatic_gain_control']
        self.echo_cancellation: bool = data['echo_cancellation']
        self.noise_suppression: bool = data['noise_suppression']
        self.qos: bool = data['qos']
        self.silence_warning: bool = data['silence_warning']
        self.deaf: bool = data['deaf']
        self.mute: bool = data['mute']