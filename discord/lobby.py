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

import datetime
from typing import Dict, List, Optional, TYPE_CHECKING

from . import utils
from .channel import _guild_channel_factory
from .mixins import Hashable

if TYPE_CHECKING:
    from .guild import GuildChannel
    from .state import ConnectionState
    from .types.lobby import Lobby as LobbyPayload

__all__ = ('Lobby',)


class Lobby(Hashable):
    """Represents a Discord lobby.

    .. versionadded:: 2.6

    Attributes
    -----------
    id: :class:`int`
        The lobby's ID.
    application_id: :class:`int`
        The application's ID that created the lobby.
    metadata: Optional[Dict[:class:`str`, :class:`str`]]
        The lobby's metadata.
    members: List[:class:`LobbyMember`]
        The lobby's members.
    linked_channel: Optional[:class:`abc.GuildChannel`]
        The channel linked to the lobby.
    """

    __slots__ = (
        '_state',
        'id',
        'application_id',
        'metadata',
        'members',
        'linked_channel',
    )

    def __init__(self, *, state: ConnectionState, data: LobbyPayload):
        self._state = state

        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self.metadata: Optional[Dict[str, str]] = data.get('metadata')
        self.members: List[LobbyMember] = [LobbyMember(data=d, lobby=self, state=state) for d in data['members']]
        self.linked_channel: Optional[GuildChannel] = None

        linked_channel_data = data.get('linked_channel')
        if linked_channel_data is not None:
            cls, _ = _guild_channel_factory()
            if cls is not None:
                guild_id = int(data['guild_id'])
                guild = state._get_guild(guild_id)
                if guild is not None:
                    self.linked_channel = cls(data=linked_channel_data, guild=guild, state=state)

    def __repr__(self) -> str:
        return f'<Lobby id={self.id} application_id={self.application_id} members={self.members!r}>'

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the lobby's creation time in UTC."""
        return utils.snowflake_time(self.id)
