from __future__ import annotations

from typing import Optional, TYPE_CHECKING

from ..enums import ButtonStyle

if TYPE_CHECKING:
    from .types.commands import ShareInteractionRequestComponentButton as ShareInteractionRequestComponentButtonPayload

# fmt: off
__all__ = (
    'Button',
)
# fmt: on

class Button:
    """Represents a button when sharing an interaction.
    
    Attributes
    ----------
    style: :class:`~discord.ButtonStyle`
        The button's style.
    label: Optional[:class:`str`]
        The label. Can be only up to 80 characters long.
    custom_id: Optional[:class:`str`]
        The developer-defined ID of the button. Can be only up to 100 characters long.
    """

    __slots__ = (
        'style',
        'label',
        'custom_id',
    )

    def __init__(
        self,
        *,
        style: ButtonStyle = ButtonStyle.secondary,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
    ) -> None:
        self.style: ButtonStyle = style
        self.label: Optional[str] = label
        self.custom_id: Optional[str] = custom_id
    
    def to_dict(self) -> ShareInteractionRequestComponentButtonPayload:
        payload: ShareInteractionRequestComponentButtonPayload = {
            'type': 1,
            'style': self.style.value,  # type: ignore
        }
        if self.label is not None:
            payload['label'] = self.label
        if self.custom_id is not None:
            payload['custom_id'] = self.custom_id    
        return payload