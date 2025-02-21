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

from typing import Literal, Optional, TYPE_CHECKING, Tuple, TypeVar

from ..components import TextDisplay as TextDisplayComponent
from ..enums import ComponentType
from .item import Item

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..types.components import TextDisplay as TextDisplayPayload
    from .view import View

# fmt: off
__all__ = (
    'TextDisplay',
)
# fmt: on

V = TypeVar('V', bound='View', covariant=True)


class TextDisplay(Item[V]):
    """Represents a UI text display component.

    .. versionadded:: 2.5

    Parameters
    ----------
    content: :class:`str`
        The content of text display component.
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
        content: str,
        *,
        row: Optional[int] = None,
    ) -> None:
        super().__init__()

        self._underlying = TextDisplayComponent._raw_construct(
            content=content,
        )
        self.row = row

    def __str__(self) -> str:
        return self.content

    @property
    def width(self) -> int:
        return 5

    @property
    def content(self) -> str:
        """:class:`str`: The content of text display component."""
        return self._underlying.content

    @content.setter
    def content(self, value: str) -> None:
        self._underlying.content = value

    def to_component_dict(self) -> TextDisplayPayload:
        return self._underlying.to_dict()

    @classmethod
    def from_component(cls, component: TextDisplayComponent) -> Self:
        return cls(
            content=component.content,
            row=None,
        )

    @property
    def type(self) -> Literal[ComponentType.text_display]:
        return self._underlying.type

    def is_dispatchable(self) -> bool:
        return False
