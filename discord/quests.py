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

from .enums import try_enum, QuestPlatformType
from .utils import parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from .state import ConnectionState
    from .types.quests import QuestRewardCode as QuestRewardCodePayload

__all__ = ('QuestRewardCode',)


class QuestRewardCode:
    """Represents a quest's reward code.

    .. container:: operations

        .. describe:: x == y

            Checks if two quest reward codes are the same.

        .. describe:: x != y

            Checks if two quest reward codes are not the same.

        .. describe:: hash(x)

            Returns the quest reward code's hash.

        .. describe:: str(x)

            Returns :attr:`code`.

    Attributes
    ----------
    quest_id: :class:`int`
        The ID of the quest.
    code: :class:`str`
        The code.
    platform: :class:`QuestPlatformType`
        The platform this redeem code applies to.
    user_id: :class:`int`
        The user's ID this code belongs to.
    claimed_at: :class:`~datetime.datetime`
        When the quest was claimed by user.
    tier: :class:`int`
        The reward tier this code belongs to.

        Only applicable if the quest's ``assignment_method`` is set to ``TIERED``.
    """

    __slots__ = (
        'quest_id',
        'code',
        'platform',
        'user_id',
        'claimed_at',
        'tier',
    )

    def __init__(self, *, data: QuestRewardCodePayload, state: ConnectionState) -> None:
        self.quest_id: int = int(data['quest_id'])
        self.code: str = data['code']
        self.platform: QuestPlatformType = try_enum(QuestPlatformType, data['platform'])
        self.user_id: int = int(data['user_id'])
        self.claimed_at: datetime = parse_time(data['claimed_at'])
        self.tier: Optional[int] = data.get('tier')

    def __eq__(self, other: object, /) -> bool:
        return self is other or (
            isinstance(other, QuestRewardCode)
            and self.quest_id == other.quest_id
            and self.code == other.code
            and self.user_id == other.user_id
        )

    def __ne__(self, other: object, /) -> bool:
        if self is other:
            return False

        if isinstance(other, QuestRewardCode):
            return self.quest_id != other.quest_id and self.code != other.code and self.user_id != other.user_id

        return True

    def __hash__(self) -> int:
        return hash(self.code)

    def __str__(self) -> str:
        return self.code
