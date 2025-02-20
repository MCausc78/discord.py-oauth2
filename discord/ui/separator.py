"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

import os
from typing import List, Optional, TYPE_CHECKING, Tuple

from ..components import Section as SectionComponent
from ..enums import ComponentType, TextStyle
from ..utils import MISSING
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..types.components import TextInput as TextInputPayload
    from .text_display import TextDisplay
    from .thumbnail import Thumbnail
    from .button import Button

# fmt: off
__all__ = (
    'Section',
)
# fmt: on

V = TypeVar('V', bound='View', covariant=True)

# message.components.max_length = 10
# message.components.total_nested_components_in_tree = 30
# section.components.max_length = 3
# media_gallery.items.max_length = 10
# container.components.max_length = 10


class Section(Item[V]):
    """Represents a UI section.

    .. versionadded:: 2.5

    Parameters
    ----------
    children: List[:class:`discord.ui.TextDisplay`]
        The children components that this holds. Can be only up to 3 components.
    accessory: Union[:class:`discord.ui.Thumbnail`, :class:`discord.ui.Button`]
        The section accessory.
    row: Optional[:class:`int`]
        The relative row this button belongs to. A Discord component can only have 5
        rows. By default, items are arranged automatically into those 5 rows. If you'd
        like to control the relative positioning of the row then passing an index is advised.
        For example, row=1 will show up before row=2. Defaults to ``None``, which is automatic
        ordering. The row number must be between 0 and 4 (i.e. zero indexed).
    """

    __item_repr_attributes__: Tuple[str, ...] = (
        'children',
        'accessory',
    )

    def __init__(
        self,
        *,
        children: List[TextDisplay],
        accessory: Union[Thumbnail, Button],
        row: Optional[int] = None,
    ) -> None:
        super().__init__()

        self._underlying = SectionComponent._raw_construct(
            children=children,
            accessory=accessory,
        )
        self.row = row

    def __str__(self) -> str:
        return self.value

    @property
    def width(self) -> int:
        return 1

    @property
    def value(self) -> str:
        """:class:`str`: The value of the text input."""
        return self._value or ''

    @property
    def label(self) -> str:
        """:class:`str`: The label of the text input."""
        return self._underlying.label

    @label.setter
    def label(self, value: str) -> None:
        self._underlying.label = value

    @property
    def placeholder(self) -> Optional[str]:
        """:class:`str`: The placeholder text to display when the text input is empty."""
        return self._underlying.placeholder

    @placeholder.setter
    def placeholder(self, value: Optional[str]) -> None:
        self._underlying.placeholder = value

    @property
    def required(self) -> bool:
        """:class:`bool`: Whether the text input is required."""
        return self._underlying.required

    @required.setter
    def required(self, value: bool) -> None:
        self._underlying.required = value

    @property
    def min_length(self) -> Optional[int]:
        """:class:`int`: The minimum length of the text input."""
        return self._underlying.min_length

    @min_length.setter
    def min_length(self, value: Optional[int]) -> None:
        self._underlying.min_length = value

    @property
    def max_length(self) -> Optional[int]:
        """:class:`int`: The maximum length of the text input."""
        return self._underlying.max_length

    @max_length.setter
    def max_length(self, value: Optional[int]) -> None:
        self._underlying.max_length = value

    @property
    def style(self) -> TextStyle:
        """:class:`discord.TextStyle`: The style of the text input."""
        return self._underlying.style

    @style.setter
    def style(self, value: TextStyle) -> None:
        self._underlying.style = value

    @property
    def default(self) -> Optional[str]:
        """:class:`str`: The default value of the text input."""
        return self._underlying.value

    @default.setter
    def default(self, value: Optional[str]) -> None:
        self._underlying.value = value

    def to_component_dict(self) -> TextInputPayload:
        return self._underlying.to_dict()

    @classmethod
    def from_component(cls, component: TextInputComponent) -> Self:
        return cls(
            label=component.label,
            style=component.style,
            custom_id=component.custom_id,
            placeholder=component.placeholder,
            default=component.value,
            required=component.required,
            min_length=component.min_length,
            max_length=component.max_length,
            row=None,
        )

    @property
    def type(self) -> Literal[ComponentType.text_input]:
        return self._underlying.type

    def is_dispatchable(self) -> bool:
        return False
