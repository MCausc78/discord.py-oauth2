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

from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from .types.commands import (
        SetConfigRequest as SetConfigRequestPayload,
        SetConfigResponse as SetConfigResponsePayload,
    )

# fmt: off
__all__ = (
    'EmbeddedActivityConfig',
)
# fmt: on


class EmbeddedActivityConfig:
    """Represents configuration for an embedded activtiy.

    Attributes
    ----------
    use_interactive_pip: :class:`bool`
        Whether the picture-in-picture is interactive.
    """

    __slots__ = ('use_interactive_pip',)

    def __init__(self, data: Union[SetConfigRequestPayload, SetConfigResponsePayload]) -> None:
        self.use_interactive_pip: bool = data['use_interactive_pip']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} use_interactive_pip={self.use_interactive_pip!r}>'
