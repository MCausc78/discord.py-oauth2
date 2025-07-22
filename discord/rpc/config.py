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

    __slots__ = (
        'use_interactive_pip',
    )

    def __init__(self, data: Union[SetConfigRequestPayload, SetConfigResponsePayload]) -> None:
        self.use_interactive_pip: bool = data['use_interactive_pip']

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} use_interactive_pip={self.use_interactive_pip!r}>'
