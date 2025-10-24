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

from typing import Optional, TYPE_CHECKING, Union

from ..utils import parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from .types.commands import GetQuestEnrollmentStatusResponse as GetQuestEnrollmentStatusResponsePayload
    from .types.events import QuestEnrollmentStatusUpdateEvent as QuestEnrollmentStatusUpdateEventPayload

# fmt: off
__all__ = (
    'QuestEnrollmentStatus',
)
# fmt: on

class QuestEnrollmentStatus:
    """Represents enrollment status for a quest.
    
    Attributes
    ----------
    quest_id: :class:`int`
        The quest's ID the enrollment status is for.
    enrolled: :class:`bool`
        Whether the user accepted the quest.
    enrolled_at: Optional[:class:`~datetime.datetime`]
        When the user accepted the quest.
    """

    __slots__ = (
        'quest_id',
        'enrolled',
        'enrolled_at',
    )

    def __init__(
        self,
        data: Union[
            GetQuestEnrollmentStatusResponsePayload,
            QuestEnrollmentStatusUpdateEventPayload,
        ],
    ) -> None:
        self.quest_id: int = int(data['quest_id'])
        self.enrolled: bool = data.get('is_enrolled', False)
        self.enrolled_at: Optional[datetime] = parse_time(data.get('enrolled_at'))

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return other.quest_id == self.quest_id
        return NotImplemented
    
    def __hash__(self) -> int:
        return self.quest_id >> 22