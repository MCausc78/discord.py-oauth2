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

from typing import Dict, List, Optional, TYPE_CHECKING, Union

from .enums import try_enum, ConnectionType
from .guild import UserGuild
from .integrations import Integration

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.connections import (
        PartialConnection as PartialConnectionPayload,
        Connection as ConnectionPayload,
    )

__all__ = ('Connection',)


class Connection:
    __slots__ = (
        '_state',
        'id',
        'type',
        'name',
        'verified',
        'metadata',
        'metadata_visible',
        'revoked',
        'integrations',
        'friend_sync',
        'show_activity',
        'two_way_link',
        'visible',
    )

    def __init__(
        self,
        *,
        data: Union[PartialConnectionPayload, ConnectionPayload],
        state: ConnectionState,
    ) -> None:
        self._state: ConnectionState = state
        self.id: str = data['id']
        self.type: ConnectionType = try_enum(ConnectionType, data['type'])
        self._update(data)

    def _update(self, data: Union[PartialConnectionPayload, ConnectionPayload]) -> None:
        self.name: str = data.get('name', '')
        self.verified: bool = data['verified']
        self.metadata: Optional[Dict[str, str]] = data.get('metadata')
        self.metadata_visible: bool = bool(data.get('metadata_visibility', 1))
        self.revoked: bool = data.get('revoked', False)
        self.integrations: List[Integration] = [
            Integration(
                data=d,  # type: ignore
                guild=UserGuild(data=d['guild'], state=self._state),  # type: ignore
            )
            for d in data.get('integrations', ())
        ]
        self.friend_sync: bool = data.get('friend_sync', False)
        self.show_activity: bool = data.get('show_activity', False)
        self.two_way_link: bool = data.get('two_way_link', False)
        self.visible: bool = bool(data.get('visibility', 1))
