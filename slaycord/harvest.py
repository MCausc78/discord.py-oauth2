from __future__ import annotations

from typing import Dict, Optional, TYPE_CHECKING

from .enums import try_enum, HarvestBackendState, HarvestBackendType, HarvestState, HarvestStatus
from .mixins import Hashable
from .utils import parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from .types.harvest import (
        Harvest as HarvestPayload,
    )


class Harvest(Hashable):
    """Represents an user's data harvest.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The ID of the harvest.
    user_id: :class:`int`
        The ID of the user being harvested.
    email: :class:`str`
        The email the harvest will be sent to.
    state: :class:`HarvestState`
        The state of the harvest.
    status: :class:`HarvestStatus`
        The status of the harvest.
    created_at: :class:`~datetime.datetime`
        When the harvest was created.
    completed_at: Optional[:class:`~datetime.datetime`]
        When the harvest was completed.
    polled_at: Optional[:class:`~datetime.datetime`]
        When the harvest was last polled.
    backends: Dict[:class:`HarvestBackendType`, :class:`HarvestBackendState`]
        A dictionary of each backend being harvested to its state.
    updated_at: :class:`~datetime.datetime`
        When the harvest was last updated.
    shadow_run: :class:`bool`
        Whether the harvest is a shadow run.
    user_is_staff: :class:`bool`
        Whether the user being harvested is a Discord employee.
    is_provisional: :class:`bool`
        Whether the user being harvested is a provisional user account.
    sla_email_sent: :class:`bool`
        Whether an email has been sent informing the user that the archive is taking longer than expected.
    bypass_cooldown: :class:`bool`
        Whether the harvest bypasses the cooldown period for requesting harvests.
    """

    __slots__ = (
        'id',
        'user_id',
        'email',
        'state',
        'status',
        'created_at',
        'completed_at',
        'polled_at',
        'backends',
        'updated_at',
        'shadow_run',
        'user_is_staff',
        'is_provisional',
        'sla_email_sent',
        'bypass_cooldown',
    )

    def __init__(self, *, data: HarvestPayload) -> None:
        raw_harvest_metadata = data['harvest_metadata']

        self.id: int = int(data['harvest_id'])
        self.user_id: int = int(data['user_id'])
        self.email: str = data['email']
        self.state: HarvestState = try_enum(HarvestState, data['state'])
        self.status: HarvestStatus = try_enum(HarvestStatus, data['status'])
        self.created_at: datetime = parse_time(data['created_at'])
        self.completed_at: Optional[datetime] = parse_time(data.get('completed_at'))
        self.polled_at: Optional[datetime] = parse_time(data.get('polled_at'))
        self.backends: Dict[HarvestBackendType, HarvestBackendState] = {
            try_enum(HarvestBackendType, k): try_enum(HarvestBackendState, v) for k, v in data['backends'].items()
        }
        self.updated_at: datetime = parse_time(data['updated_at'])
        self.shadow_run: bool = data['shadow_run']
        self.user_is_staff: bool = raw_harvest_metadata.get('user_is_staff', False)
        self.is_provisional: bool = raw_harvest_metadata.get('is_provisional', False)
        self.sla_email_sent: bool = raw_harvest_metadata.get('sla_email_sent', False)
        self.bypass_cooldown: bool = raw_harvest_metadata.get('bypass_cooldown', False)
