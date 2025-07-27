from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from ..enums import try_enum
from .enums import CertifiedDeviceType

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.commands import CertifiedDevice as CertifiedDevicePayload


class CertifiedDevice:
    """Represents a certified device.

    Attributes
    ----------
    type: :class:`CertifiedDeviceType`
        The type of the certified device.
    id: :class:`str`
        The certified device's Windows UUID.
    vendor_name: :class:`str`
        The name of the hardware vendor.
    vendor_url: :class:`str`
        The URL to the hardware vendor.
    model_name: :class:`str`
        The name of the model.
    model_url: :class:`str`
        The URL to the model.
    related: Optional[List[:class:`str`]]
        A list of UUIDs representing related devices.
    echo_cancellation: Optional[:class:`bool`]
        Indicates if the device's native echo cancellation is enabled.

        Only applicable if type is :attr:`~CertifiedDeviceType.audio_input`.
    noise_suppression: Optional[:class:`bool`]
        Indicates if the device's native noise suppression is enabled.

        Only applicable if type is :attr:`~CertifiedDeviceType.audio_input`.
    automatic_gain_control: Optional[:class:`bool`]
        Indicates if the device's automatic gain control is enabled.

        Only applicable if type is :attr:`~CertifiedDeviceType.audio_input`.
    hardware_mute: Optional[:class:`bool`]
        Indicates if the device's is muted hardware-wise.

        Only applicable if type is :attr:`~CertifiedDeviceType.audio_input`.
    """

    __slots__ = (
        'type',
        'id',
        'vendor_name',
        'vendor_url',
        'model_name',
        'model_url',
        'related',
        'echo_cancellation',
        'noise_suppression',
        'automatic_gain_control',
        'hardware_mute',
    )

    def __init__(
        self,
        id: str,
        *,
        type: CertifiedDeviceType,
        vendor_name: str,
        vendor_url: str,
        model_name: str,
        model_url: str,
        related: Optional[List[str]] = None,
        echo_cancellation: Optional[bool] = None,
        noise_suppression: Optional[bool] = None,
        automatic_gain_control: Optional[bool] = None,
        hardware_mute: Optional[bool] = None,
    ) -> None:
        self.id: str = id
        self.type: CertifiedDeviceType = type
        self.vendor_name: str = vendor_name
        self.vendor_url: str = vendor_url
        self.model_name: str = model_name
        self.model_url: str = model_url
        self.related: Optional[List[str]] = related
        self.echo_cancellation: Optional[bool] = echo_cancellation
        self.noise_suppression: Optional[bool] = noise_suppression
        self.automatic_gain_control: Optional[bool] = automatic_gain_control
        self.hardware_mute: Optional[bool] = hardware_mute

    @classmethod
    def from_dict(cls, data: CertifiedDevicePayload) -> Self:
        vendor_data = data['vendor']
        model_data = data['model']

        return cls(
            type=try_enum(CertifiedDeviceType, data['type']),
            id=data['id'],
            vendor_name=vendor_data['name'],
            vendor_url=vendor_data['url'],
            model_name=model_data['name'],
            model_url=model_data['url'],
            related=data.get('related'),
            echo_cancellation=data.get('echo_cancellation'),
            noise_suppression=data.get('noise_suppression'),
            automatic_gain_control=data.get('automatic_gain_control'),
            hardware_mute=data.get('hardware_mute'),
        )

    def to_dict(self) -> CertifiedDevicePayload:
        payload: CertifiedDevicePayload = {
            'type': self.type.value,
            'id': self.id,
            'vendor': {
                'name': self.vendor_name,
                'url': self.vendor_url,
            },
            'model': {
                'name': self.model_name,
                'url': self.model_url,
            },
        }
        if self.related is not None:
            payload['related'] = self.related
        if self.echo_cancellation is not None:
            payload['echo_cancellation'] = self.echo_cancellation
        if self.noise_suppression is not None:
            payload['noise_suppression'] = self.noise_suppression
        if self.automatic_gain_control is not None:
            payload['automatic_gain_control'] = self.automatic_gain_control
        if self.hardware_mute is not None:
            payload['hardware_mute'] = self.hardware_mute

        return payload
