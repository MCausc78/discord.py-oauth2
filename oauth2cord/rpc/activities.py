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

from typing import TYPE_CHECKING

from ..user import User

if TYPE_CHECKING:
    from typing_extensions import Self

    from ..state import BaseConnectionState
    from .types.commands import ActivityParticipant as ActivityParticipantPayload

# fmt: off
__all__ = (
    'ActivityParticipant',
)
# fmt: on


class ActivityParticipant(User):
    """Represents an activity participant.

    Same as :class:`~oauth2cord.User`, except with additional ``nickname`` attribute.

    Attributes
    ----------
    nickname: Optional[:class:`str`]
        The nickname that the user has for the current guild.
    """

    __slots__ = ('nickname',)

    @classmethod
    def _from_rpc(cls, data: ActivityParticipantPayload, state: BaseConnectionState) -> Self:
        self = super()._from_rpc(data, state)
        self.nickname = data.get('nickname')
        return self
