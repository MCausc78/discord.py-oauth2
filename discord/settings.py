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

from typing import List, Optional, TYPE_CHECKING, Union

from .activity import CustomActivity
from .enums import Status, try_enum

if TYPE_CHECKING:
    from .state import ConnectionState
    from .types.settings import (
        GuildFolder as GuildFolderPayload,
        GatewayUserSettings as GatewayUserSettingsPayload,
        UserSettings as UserSettingsPayload,
    )


class GuildFolder:
    __slots__ = (
        '_state',
        'id',
        'name',
        'guild_ids',
        'color',
    )

    def __init__(self, *, data: GuildFolderPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: Optional[int] = data.get('id')
        self.name: Optional[str] = data.get('name')
        self.guild_ids: List[int] = list(map(int, data.get('guild_ids', ())))
        self.color: Optional[int] = data.get('color')


class UserSettings:
    def __init__(self, *, data: Union[GatewayUserSettingsPayload, UserSettingsPayload], state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: Union[GatewayUserSettingsPayload, UserSettingsPayload], *, from_ready: bool = False) -> None:
        if 'status' in data or from_ready:
            self.status: Status = try_enum(Status, data.get('status', 'online'))
        elif not hasattr(self, 'status'):
            self.status = Status.online

        if 'custom_status' in data or from_ready:
            custom_status_data = data.get('custom_status')
            self.custom_activity: Optional[CustomActivity] = (
                None if custom_status_data is None else CustomActivity.from_user_settings_payload(custom_status_data)
            )
        elif not hasattr(data, 'custom_status'):
            self.custom_activity = None

        if 'show_current_game' in data or from_ready:
            self.show_current_game: bool = data.get('show_current_game', True)
        elif not hasattr(self, 'show_current_game'):
            self.show_current_game = True

        if 'allow_activity_party_privacy_friends' in data or from_ready:
            self.allow_activity_party_privacy_friends: bool = data.get('allow_activity_party_privacy_friends', True)
        elif not hasattr(self, 'allow_activity_party_privacy_friends'):
            self.allow_activity_party_privacy_friends = True

        if 'allow_activity_party_privacy_voice_channel' in data or from_ready:
            self.allow_activity_party_privacy_voice_channel: bool = data.get(
                'allow_activity_party_privacy_voice_channel', True
            )
        elif not hasattr(self, 'allow_activity_party_privacy_voice_channel'):
            self.allow_activity_party_privacy_voice_channel = True


__all__ = (
    'GuildFolder',
    'UserSettings',
)
