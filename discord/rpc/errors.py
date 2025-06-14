from __future__ import annotations

from ..errors import DiscordException

__all__ = ('RPCException',)


class RPCException(DiscordException):
    """Exception that's raised when a RPC request operation fails.

    Attributes
    ----------
    code: :class:`int`
        The Discord specific error code for the failure.
    text: :class:`str`
        The text of the error. Could be an empty string.
    """

    def __init__(self, *, code: int, text: str) -> None:
        self.code: int = code
        self.text: str = text
        super().__init__(f'{self.text} (error code: {self.code})')
