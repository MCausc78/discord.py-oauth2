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

from typing import Any, Dict, Optional, TYPE_CHECKING

from .enums import try_enum, ConnectionType
from .mixins import Hashable
from .utils import _from_json, parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from .state import ConnectionState
    from .types.game_invite import GameInvite as GameInvitePayload
    from .user import User

__all__ = ('GameInvite',)


class GameInvite(Hashable):
    """Represents a game invite.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two game invites are the same.

        .. describe:: x != y

            Checks if two game invites are not the same.

        .. describe:: hash(x)

            Returns the game invite's hash.

        .. describe:: str(x)

            Returns a string representation of the game invite.

    Attributes
    ----------
    id: :class:`int`
        The ID of the game invite.
    created_at: :class:`~datetime.datetime`
        When the game invite was created.
    ttl: :class:`int`
        Duration in seconds when the game invite expires in.
    inviter_id: :class:`int`
        The ID of the user that invited you to game.
    recipient_id: :class:`int`
        The ID of the user that received the game invite.
    platform_type: :class:`ConnectionType`
        The platform type. Currently only :attr:`~ConnectionType.xbox` is permitted here.
    launch_parameters: :class:`str`
        The launch parameters, typically a JSON string.
    parsed_launch_parameters: Dict[:class:`str`, Any]
        A dictionary representing the parameters for launching game.
        It contains the following optional and nullable keys:

        - ``titleId``: A string representing the ID of game invite title. (?)
        - ``inviteToken``: A string representing the game invite token.
    installed: :class:`bool`
        Whether the game is installed.
    joinable: :class:`bool`
        Whether the game is joinable.
    fallback_url: Optional[:class:`str`]
        The URL for installing the game.
    game_icon_url: :class:`str`
        The game's icon URL.
    game_name: :class:`str`
        The game's name.
    """

    __slots__ = (
        '_state',
        'id',
        'created_at',
        'ttl',
        'inviter_id',
        'recipient_id',
        'platform_type',
        'launch_parameters',
        'parsed_launch_parameters',
        'installed',
        'joinable',
        'fallback_url',
        'game_icon_url',
        'game_name',
    )

    def __init__(self, *, data: GameInvitePayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['invite_id'])
        self.created_at: datetime = parse_time(data['created_at'])
        self.ttl: int = data['ttl']
        self.inviter_id: int = int(data['inviter_id'])
        self.recipient_id: int = int(data['recipient_id'])
        self.platform_type: ConnectionType = try_enum(ConnectionType, data['platform_type'])

        self.launch_parameters: str = data['launch_parameters']
        try:
            self.parsed_launch_parameters: Dict[str, Any] = _from_json(self.launch_parameters)
        except Exception:
            self.parsed_launch_parameters = {}

        self.installed: bool = data.get('installed', False)
        self.joinable: bool = data.get('joinable', False)
        self.fallback_url: Optional[str] = data.get('fallback_url')
        self.game_icon_url: str = data['application_asset']
        self.game_name: str = data['application_name']

    def __repr__(self) -> str:
        return f'<GameInvite id={self.id} platform_type={self.platform_type!r} inviter_id={self.inviter_id} game_name={self.game_name!r}>'

    def __str__(self) -> str:
        return f'Invite to {self.game_name} on {self.platform_type.value.capitalize()}'

    @property
    def inviter(self) -> Optional[User]:
        """Optional[:class:`User`]: The user that created this invite."""
        return self._state.get_user(self.inviter_id)

    @property
    def recipient(self) -> Optional[User]:
        """Optional[:class:`User`]: The user that received this game invite."""
        return self._state.get_user(self.recipient_id)
