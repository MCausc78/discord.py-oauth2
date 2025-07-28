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

from datetime import datetime, timezone
from typing import List, Optional, TYPE_CHECKING

from ..enums import try_enum
from .enums import VoiceConnectionState

if TYPE_CHECKING:
    from .types.events import (
        VoiceConnectionStatusEventPing as VoiceConnectionPingPayload,
        VoiceConnectionStatusEvent as VoiceConnectionStatusPayload,
    )

__all__ = (
    'VoiceConnectionPing',
    'VoiceConnectionStatus',
)


class VoiceConnectionPing:
    """Represents a ping to voice server.

    Attributes
    ----------
    at: :class:`~datetime.datetime`
        When the ping was made.
    value: :class:`int`
        The latency in milliseconds.
    """

    __slots__ = (
        'at',
        'value',
    )

    def __init__(self, data: VoiceConnectionPingPayload) -> None:
        self.at: datetime = datetime.fromtimestamp(data['time'] / 1000.0, tz=timezone.utc)
        self.value: int = data['value']


class VoiceConnectionStatus:
    __slots__ = (
        'state',
        'hostname',
        'pings',
        'average_ping',
        'last_ping',
    )

    def __init__(self, data: VoiceConnectionStatusPayload) -> None:
        self.state: VoiceConnectionState = try_enum(VoiceConnectionState, data['state'])
        self.hostname: str = data.get('hostname', '')
        self.pings: List[VoiceConnectionPing] = list(map(VoiceConnectionPing, data.get('pings', ())))
        self.average_ping: int = data.get('average_ping', 0)
        self.last_ping: Optional[int] = data.get('last_ping')
