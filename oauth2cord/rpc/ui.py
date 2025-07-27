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
    style: :class:`~oauth2cord.ButtonStyle`
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
