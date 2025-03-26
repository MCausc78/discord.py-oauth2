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
from .utils import MISSING

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.settings import (
        GuildFolder as GuildFolderPayload,
        GatewayUserSettings as GatewayUserSettingsPayload,
        UserSettings as UserSettingsPayload,
    )


class GuildFolder:
    """Represents a guild folder or position if :attr:`id` is ``None``.

    Attributes
    ----------
    id: Optional[:class:`int`]
        The folder's ID.
    name: Optional[:class:`str`]
        The folder's name.
    guild_ids: List[:class:`int`]
        The guild's IDs in this folder.
    color Optional[:class:`int`]
        The folder's color.
    """

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

    @property
    def guilds(self) -> List[Guild]:
        """List[:class:`Guild`]: The guilds in this folder."""
        state = self._state

        guilds = []
        for guild_id in self.guild_ids:
            guild = state._get_guild(guild_id)
            if guild is not None:
                guilds.append(guild)

        return guilds


class UserSettings:
    """Represents user settings.

    Depending on where they were retrieved from, only some attributes might be present,
    and rest of attributes are set to their default values.

    +---------------------------+---------------------------------------------+
    | Source                    | Attributes                                  |
    +---------------------------+---------------------------------------------+
    | :attr:`Client.settings`   | All                                         |
    +---------------------------+---------------------------------------------+
    | :meth:`UserSettings.edit` | :attr:`status`, and :attr:`custom_activity` |
    +---------------------------+---------------------------------------------+

    Attributes
    ----------
    status: :class:`Status`
        The current status. Defaults to :attr:`~Status.online`.
    custom_activity: Optional[:class:`CustomActivity`]
        The current custom status.
    show_current_game: :class:`bool`
        Whether to show the current game. Defaults to ``True``.
    allow_activity_party_privacy_friends: :class:`bool`
        Whether to allow friends to join your activity without sending a request.

        Defaults to ``True``.
    allow_activity_party_privacy_voice_channel: :class:`bool`
        Whether to allow people in the same voice channel as you to join your activity without sending a request. Does not apply to Community guilds.

        Defaults to ``True``.
    """

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

    async def edit(
        self,
        *,
        status: Optional[Status] = MISSING,
        custom_activity: Optional[CustomActivity] = None,
    ) -> UserSettings:
        """|coro|

        Edits the user settings.

        All parameters are optional.

        Parameters
        ----------
        status: Optional[:class:`Status`]
            The status to set. Pass ``None`` to set :attr:`~Status.online`.
        custom_activity: Optional[:class:`CustomActivity`]
            The custom status to set.

        Raises
        ------
        HTTPException
            Editing the user settings failed.

        Returns
        -------
        :class:`UserSettings`
            The newly updated user settings.
        """

        state = self._state

        payload = {}

        if status is None:
            payload['status'] = Status.online.value
        elif status is not MISSING:
            payload['status'] = status.value

        if custom_activity is None:
            payload['custom_status'] = None
        elif custom_activity is not MISSING:
            payload['custom_status'] = custom_activity.to_user_settings_payload()

        data = await state.http.modify_user_settings(**payload)
        return UserSettings(data=data, state=state)


__all__ = (
    'GuildFolder',
    'UserSettings',
)
