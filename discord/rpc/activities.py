from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self

from ..state import BaseConnectionState
from ..user import User
from .types.commands import ActivityParticipant as ActivityParticipantPayload

__all__ = ('ActivityParticipant',)


class ActivityParticipant(User):
    """Represents an activity participant.

    Same as :class:`~discord.User`, except with additional ``nickname`` attribute.

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
