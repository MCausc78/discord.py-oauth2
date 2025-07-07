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

from copy import copy
from datetime import datetime
from typing import Dict, List, Literal, Optional, TYPE_CHECKING, Union, overload

from .activity import CustomActivity
from .color import Color
from .enums import try_enum, AudioContext, SlayerSDKReceiveInGameDMs, Status
from .utils import MISSING, parse_time, utcnow

if TYPE_CHECKING:
    from typing_extensions import Self

    from .guild import Guild
    from .state import ConnectionState
    from .types.settings import (
        GuildFolder as GuildFolderPayload,
        GatewayUserSettings as GatewayUserSettingsPayload,
        UserSettings as UserSettingsPayload,
        AudioSettings as AudioSettingsPayload,
        MuteConfig as MuteConfigPayload,
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
    raw_color: Optional[:class:`int`]
        The folder's color.
    """

    __slots__ = (
        '_state',
        'id',
        'name',
        'guild_ids',
        'raw_color',
    )

    def __init__(self, *, data: GuildFolderPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: Optional[int] = data.get('id')
        self.name: Optional[str] = data.get('name')
        self.guild_ids: List[int] = list(map(int, data.get('guild_ids', ())))
        self.raw_color: Optional[int] = data.get('color')

    @property
    def color(self) -> Optional[Color]:
        """Optional[:class:`Color`]: A property that returns the color for the folder.

        There is an alias for this named :attr:`colour`.
        """
        if self.raw_color is not None:
            return Color(self.raw_color)

    @property
    def colour(self) -> Optional[Color]:
        """Optional[:class:`Colour`]: A property that returns the colour for the folder.

        This is an alias of :attr:`color`.
        """
        return self.color

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

    +---------------------------+----------------------------------------------------------------------+
    | Source                    | Attributes                                                           |
    +---------------------------+----------------------------------------------------------------------+
    | :attr:`Client.settings`   | All except :attr:`receive_in_game_dms`                               |
    +---------------------------+----------------------------------------------------------------------+
    | :meth:`UserSettings.edit` | :attr:`status`, :attr:`custom_activity`, :attr:`receive_in_game_dms` |
    +---------------------------+----------------------------------------------------------------------+

    Attributes
    ----------
    status: :class:`Status`
        The current status. Defaults to :attr:`~Status.online`.

        You must have ``'activities.read'`` or ``'presences.read'`` OAuth2 scope for this attribute to be populated.
    show_current_game: :class:`bool`
        Whether to show the current game. Defaults to ``True``.

        You must have ``'activities.read'`` or ``'presences.read'`` OAuth2 scope for this attribute to be populated.
    guild_folders: List[:class:`GuildFolder`]
        A list of guild folders.

        .. note::

        You must have ``'guilds'`` OAuth2 scope for this attribute to be populated.
    custom_activity: Optional[:class:`CustomActivity`]
        The current custom status.

        You must have ``'activities.read'`` or ``'presences.read'`` OAuth2 scope for this attribute to be populated.
    allow_activity_party_privacy_friends: :class:`bool`
        Whether to allow friends to join your activity without sending a request.

        Defaults to ``True``.

        You must have ``'activities.read'`` or ``'presences.write'`` OAuth2 scope for this attribute to be populated.
    allow_activity_party_privacy_voice_channel: :class:`bool`
        Whether to allow people in the same voice channel as you to join your activity without sending a request. Does not apply to Community guilds.

        Defaults to ``True``.

        You must have ``'activities.read'`` or ``'presences.write'`` OAuth2 scope for this attribute to be populated.
    receive_in_game_dms: :class:`SlayerSDKReceiveInGameDMs`
        A setting for receiving in-game DMs via the social layer API.

        Defaults to :attr:`~SlayerSDKReceiveInGameDMs.all`.
    soundboard_volume: Optional[:class:`float`]
        The volume of the soundboard (0-100).

        You must have ``voice`` OAuth2 scope for this attribute to be populated.

        .. warning::

            This attribute is not updated in real-time, and as such may be out of date sometimes.

    """

    __slots__ = (
        '_state',
        'status',
        'show_current_game',
        'guild_folders',
        'custom_activity',
        'allow_activity_party_privacy_friends',
        'allow_activity_party_privacy_voice_channel',
        'receive_in_game_dms',
        'soundboard_volume',
    )

    def __init__(self, *, data: Union[GatewayUserSettingsPayload, UserSettingsPayload], state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self._update(data)

    def _update(self, data: Union[GatewayUserSettingsPayload, UserSettingsPayload], *, from_ready: bool = False) -> None:
        if 'status' in data or from_ready:
            self.status: Status = try_enum(Status, data.get('status', 'online'))
        elif not hasattr(self, 'status'):
            self.status = Status.online

        if 'show_current_game' in data or from_ready:
            self.show_current_game: bool = data.get('show_current_game', True)
        elif not hasattr(self, 'show_current_game'):
            self.show_current_game = True

        if 'guild_folders' in data or from_ready:
            self.guild_folders: List[GuildFolder] = [
                GuildFolder(data=d, state=self._state) for d in data.get('guild_folders', ())
            ]
        elif not hasattr(self, 'guild_folders'):
            self.guild_folders = []

        if 'custom_status' in data or from_ready:
            custom_status_data = data.get('custom_status')
            self.custom_activity: Optional[CustomActivity] = (
                None if custom_status_data is None else CustomActivity.from_user_settings_payload(custom_status_data)
            )
        elif not hasattr(data, 'custom_status'):
            self.custom_activity = None

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

        if 'slayer_sdk_receive_in_game_dms' in data or from_ready:
            self.receive_in_game_dms: SlayerSDKReceiveInGameDMs = try_enum(
                SlayerSDKReceiveInGameDMs, data.get('slayer_sdk_receive_in_game_dms', 1)
            )
        elif not hasattr(self, 'receive_in_game_dms'):
            self.receive_in_game_dms = SlayerSDKReceiveInGameDMs.all

        # soundboard_volume is voice_and_video.soundboard_settings.volume from protos, which is Voice and Video > Soundboard > Soundboard Volume in client
        if 'soundboard_volume' in data or from_ready:
            self.soundboard_volume: Optional[float] = data.get('soundboard_volume')
        elif not hasattr(self, 'soundboard_volume'):
            self.soundboard_volume = None

    async def edit(
        self,
        *,
        status: Optional[Status] = MISSING,
        custom_activity: Optional[CustomActivity] = MISSING,
        receive_in_game_dms: Optional[SlayerSDKReceiveInGameDMs] = MISSING,
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
        receive_in_game_dms: Optional[:class:`SlayerSDKReceiveInGameDMs`]
            The option for receiving in-game DMs via the social layer API.

            Pass ``None`` to set :attr:`~SlayerSDKReceiveInGameDMs.all`

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

        if receive_in_game_dms is None:
            payload['slayer_sdk_receive_in_game_dms'] = 1
        elif receive_in_game_dms is not MISSING:
            payload['slayer_sdk_receive_in_game_dms'] = receive_in_game_dms.value

        data = await state.http.modify_user_settings(**payload)
        return UserSettings(data=data, state=state)


class AudioSettings:
    """Represents audio settings for an user.

    Attributes
    ----------
    id: :class:`int`
        The user's ID the audio settings are for.
    context: :class:`AudioContext`
        The audio context.
    muted: :class:`bool`
        Whether the user is muted.
    volume: :class:`float`
        The volume of user. This always is between 0 and 200.
    soundboard_muted: :class:`bool`
        Whether the soundboard sounds coming from this user are muted.
    """

    __slots__ = (
        '_state',
        'id',
        'context',
        'muted',
        'volume',
        'soundboard_muted',
    )

    def __init__(
        self,
        *,
        data: AudioSettingsPayload,
        state: ConnectionState,
        context: AudioContext,
        id: int,
    ) -> None:
        self._state: ConnectionState = state
        self.id: int = id
        self.context: AudioContext = context
        self._update(data)

    def _update(self, data: AudioSettingsPayload) -> None:
        self.muted: bool = data['muted']
        self.volume: float = data['volume']
        self.soundboard_muted: bool = data['soundboard_muted']

    @classmethod
    def _default(cls, id: int, context: AudioContext, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.id = id
        self.context = context
        self.muted = False
        self.volume = 100.0
        self.soundboard_muted = False
        return self

    async def edit(
        self,
        *,
        muted: bool = MISSING,
        volume: float = MISSING,
        soundboard_muted: bool = MISSING,
    ) -> AudioSettings:
        """|coro|

        Edits the audio settings.

        All parameters are optional.

        Parameters
        ----------
        muted: :class:`bool`
            Whether the user is muted.
        volume: :class:`float`
            The volume of user. Must be between 0 and 200.
        soundboard_muted: :class:`bool`
            Whether the soundboard sounds coming from this user are muted.

        Raises
        ------
        Forbidden
            You do not have proper permissions to edit the audio settings.
        HTTPException
            Editing audio settings failed.

        Returns
        -------
        :class:`AudioSettings`
            The newly edietd audio settings.
        """
        # Weird Discord bug
        if muted is MISSING and volume is MISSING and soundboard_muted is MISSING:
            return self

        payload = {}
        if muted is not MISSING:
            payload['muted'] = muted
        if volume is not MISSING:
            payload['volume'] = volume
        if soundboard_muted is not MISSING:
            payload['soundboard_muted'] = soundboard_muted

        state = self._state
        await state.http.modify_audio_settings(self.context.value, self.id, **payload)

        ret = copy(self)
        if muted is not MISSING:
            ret.muted = muted
        if volume is not MISSING:
            ret.volume = volume
        if soundboard_muted is not MISSING:
            ret.soundboard_muted = soundboard_muted
        return ret


class AudioSettingsManager:
    """Manager for audio settings.

    Attributes
    ----------
    data: Dict[:class:`AudioContext`, Dict[:class:`int`, :class:`AudioSettings`]]
        The audio settings cache.
    """

    __slots__ = (
        '_state',
        'data',
    )

    def __init__(
        self,
        *,
        data: Dict[AudioContext, Dict[int, AudioSettings]],
        state: ConnectionState,
    ) -> None:
        self._state: ConnectionState = state
        self.data: Dict[AudioContext, Dict[int, AudioSettings]] = data

    @classmethod
    def _copy(cls, instance: AudioSettingsManager) -> Self:
        self = cls.__new__(cls)
        self._state = instance._state
        self.data = {k: copy(v) for k, v in instance.data.items()}
        return self

    @overload
    def get(self, context: AudioContext, user_id: int, *, if_not_exists: Literal[True] = ...) -> AudioSettings:
        ...

    @overload
    def get(self, context: AudioContext, user_id: int, *, if_not_exists: Literal[False] = ...) -> Optional[AudioSettings]:
        ...

    def get(self, context: AudioContext, user_id: int, *, if_not_exists: bool = True) -> Optional[AudioSettings]:
        """Retrieves audio settings from cache.

        Parameters
        ----------
        context: :class:`AudioContext`
            The audio context for settings.
        user_id: :class:`int`
            The user's ID to retrieve audio settings for.
        if_not_exists: :class:`bool`
            Whether to always return non-``None`` value if audio settings were not found for provided user.

            Defaults to ``True``.

        Returns
        -------
        Optional[:class:`AudioSettings`]
            The audio settings.
        """
        try:
            return self.data[context][user_id]
        except KeyError:
            if if_not_exists:
                return AudioSettings._default(
                    id=user_id,
                    context=context,
                    state=self._state,
                )
            return None

    def of(self, context: AudioContext) -> Dict[int, AudioSettings]:
        """Retrieve all audio settings for provided context.

        This is equivalent to: ::

            return manager.data.get(context, {})

        Returns
        -------
        Dict[:class:`int`, :class:`AudioSettings`]
            The mapping of user IDs to audio settings for them.
        """
        try:
            return self.data[context]
        except KeyError:
            return {}


class MuteConfig:
    """An object representing an object's mute status.

    .. container:: operations

        .. describe:: x == y

            Checks if two items are muted.

        .. describe:: x != y

            Checks if two items are not muted.

        .. describe:: str(x)

            Returns the mute status as a string.

        .. describe:: int(x)

            Returns the mute status as an int.

    Attributes
    ----------
    muted: :class:`bool`
        Indicates if the object is muted.
    until: Optional[:class:`datetime.datetime`]
        When the mute will expire.
    """

    def __init__(self, muted: bool, config: Optional[MuteConfigPayload] = None) -> None:
        until = parse_time(config.get('end_time') if config else None)
        if until is not None:
            if until <= utcnow():
                muted = False
                until = None

        self.muted: bool = muted
        self.until: Optional[datetime] = until

    def __repr__(self) -> str:
        return str(self.muted)

    def __int__(self) -> int:
        return int(self.muted)

    def __bool__(self) -> bool:
        return self.muted

    def __eq__(self, other: object) -> bool:
        return self.muted == bool(other)

    def __ne__(self, other: object) -> bool:
        return not self.muted == bool(other)


__all__ = (
    'GuildFolder',
    'UserSettings',
    'AudioSettings',
    'AudioSettingsManager',
    'MuteConfig',
)
