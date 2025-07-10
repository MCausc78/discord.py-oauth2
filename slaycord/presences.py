"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union

from .activity import create_activity
from .appinfo import PartialAppInfo
from .enums import try_enum, Status
from .utils import MISSING, _RawReprMixin, _get_as_snowflake

if TYPE_CHECKING:
    from typing_extensions import Self

    from .activity import ActivityTypes
    from .game_relationship import GameRelationship
    from .guild import Guild
    from .member import Member
    from .relationship import Relationship
    from .state import ConnectionState
    from .types.channel import VoiceChannel as VoiceChannelPayload
    from .types.presences import (
        Presence as PresencePayload,
        ClientStatus as ClientStatusPayload,
        Presences as PresencesPayload,
        XboxPresences as XboxPresencesPayload,
    )
    from .types.voice import GuildVoiceState as GuildVoiceStatePayload
    from .user import User

__all__ = (
    'ClientStatus',
    'Presence',
    'Presences',
)


class ClientStatus:
    """Represents the :ddocs:`Client Status Object <events/gateway-events#client-status-object>` from Discord,
    which holds information about the status of the user on various clients/platforms, with additional helpers.

    .. versionadded:: 2.5
    """

    __slots__ = ('_status', 'desktop', 'mobile', 'web', 'embedded')

    def __init__(self, *, status: str = MISSING, data: ClientStatusPayload = MISSING) -> None:
        self._status: str = status or 'offline'

        data = data or {}
        self.desktop: Optional[str] = data.get('desktop')
        self.mobile: Optional[str] = data.get('mobile')
        self.web: Optional[str] = data.get('web')
        self.embedded: Optional[str] = data.get('embedded')

    def __repr__(self) -> str:
        attrs = [
            ('_status', self._status),
            ('desktop', self.desktop),
            ('mobile', self.mobile),
            ('web', self.web),
            ('embedded', self.embedded),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {inner}>'

    def _update(self, status: str, data: ClientStatusPayload, /) -> None:
        self._status = status

        self.desktop = data.get('desktop')
        self.mobile = data.get('mobile')
        self.web = data.get('web')
        self.embedded = data.get('embedded')

    @classmethod
    def _copy(cls, client_status: Self, /) -> Self:
        self = cls.__new__(cls)  # bypass __init__

        self._status = client_status._status

        self.desktop = client_status.desktop
        self.mobile = client_status.mobile
        self.web = client_status.web
        self.embedded = client_status.embedded

        return self

    @property
    def status(self) -> Status:
        """:class:`Status`: The user's overall status. If the value is unknown, then it will be a :class:`str` instead."""
        return try_enum(Status, self._status)

    @property
    def raw_status(self) -> str:
        """:class:`str`: The user's overall status as a string value."""
        return self._status

    @property
    def mobile_status(self) -> Status:
        """:class:`Status`: The user's status on a mobile device, if applicable."""
        return try_enum(Status, self.mobile or 'offline')

    @property
    def desktop_status(self) -> Status:
        """:class:`Status`: The user's status on the desktop client, if applicable."""
        return try_enum(Status, self.desktop or 'offline')

    @property
    def web_status(self) -> Status:
        """:class:`Status`: The user's status on the web client, if applicable."""
        return try_enum(Status, self.web or 'offline')

    @property
    def embedded_status(self) -> Status:
        """:class:`Status`: The user's status on the embedded (PlayStation, Xbox, in-game) client, if applicable."""
        return try_enum(Status, self.embedded or 'offline')

    def is_on_mobile(self) -> bool:
        """:class:`bool`: A helper function that determines if a user is active on a mobile device."""
        return self.mobile is not None


class Presence(_RawReprMixin):
    """Represents the payload for a :func:`on_raw_presence_update` event.

    .. versionadded:: 2.5

    .. versionchanged:: 3.0

        ``RawPresenceUpdateEvent`` was renamed to ``Presence``.

    Attributes
    ----------
    user_id: :class:`int`
        The ID of the user that triggered the presence update.
    user: Optional[:class:`User`]
        The user that triggered the presence update, if available.
    guild_id: Optional[:class:`int`]
        The guild ID for the users presence update. Could be ``None``.
    guild: Optional[:class:`Guild`]
        The guild associated with the presence update and user. Could be ``None``.
    client_status: :class:`ClientStatus`
        The :class:`~.ClientStatus` model which holds information about the status of the user on various clients.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The activities the user is currently doing. Due to a Discord API limitation, a user's Spotify activity may not appear
        if they are listening to a song with a title longer than ``128`` characters. See :issue:`1738` for more information.
    hidden_activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The hidden activities the user is currently doing. Due to a Discord API limitation, a user's Spotify activity may not appear
        if they are listening to a song with a title longer than ``128`` characters. See :issue:`1738` for more information.
    pair: Optional[Union[Tuple[:class:`Member`, :class:`Member`], Tuple[:class:`Relationship`, :class:`Relationship`], Tuple[:class:`GameRelationship`, :class:`GameRelationship`]]
        The ``(old, new)`` pair representing old and new presence.
    """

    __slots__ = (
        'user_id',
        'user',
        'client_status',
        'activities',
        'hidden_activities',
        'guild_id',
        'guild',
        'pair',
    )

    def __init__(self, *, data: PresencePayload, state: ConnectionState, full_user: bool = False) -> None:
        user_data = data['user']

        self.user_id: int = int(user_data['id'])
        self.user: Optional[User] = state.store_user(user_data) if full_user else None  # type: ignore
        self.client_status: ClientStatus = ClientStatus(status=data['status'], data=data['client_status'])
        self.activities: Tuple[ActivityTypes, ...] = tuple(create_activity(d, state) for d in data.get('activities', ()))
        self.hidden_activities: Tuple[ActivityTypes, ...] = tuple(
            create_activity(d, state) for d in data.get('hidden_activities', ())
        )
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')
        self.guild: Optional[Guild] = state._get_guild(self.guild_id)
        self.pair: Optional[
            Union[Tuple[Member, Member], Tuple[Relationship, Relationship], Tuple[GameRelationship, GameRelationship]]
        ] = None


class Presences:
    """Represents presences for all your relationships.

    Attributes
    ----------
    guilds: List[:class:`Guild`]
        The guilds. This is a massively partial object, and will have only :attr:`~Guild.id`,
        :attr:`~Guild.name`, :attr:`~Guild.icon`, :attr:`~Guild.voice_channels` populated.

        Voice channels of this guild are also partial, and only following attributes are populated with real values:

        - :attr:`~VoiceChannel.id`
        - :attr:`~VoiceChannel.name`

        Voice states will have only :attr:`~VoiceState.self_stream`, :attr:`~VoiceState.channel` populated.
    presences: List[:class:`Presence`]
        The presences for all your relationships.
    applications: List[:class:`PartialAppInfo`]
        The applications found across all presences.
    connected_account_ids: Dict[:class:`int`, List[:class:`str`]]
        A mapping of user ID to their list of connected Xbox account IDs.

        This is available only from :class:`Client.fetch_presences_for_xbox`.
    """

    __slots__ = (
        '_state',
        'guilds',
        'presences',
        'applications',
        'connected_account_ids',
    )

    def __init__(self, *, data: Union[PresencesPayload, XboxPresencesPayload], state: ConnectionState) -> None:
        self._state: ConnectionState = state

        from .guild import Guild

        guilds: List[Guild] = []

        for guild_data in data.get('guilds', ()):
            # I wish I didn't had to do this,
            # but it seems to be only way to provide
            # sane interface across the entire library

            guild_id = guild_data['guild_id']

            transformed_channels: List[VoiceChannelPayload] = []
            transformed_voice_states: List[GuildVoiceStatePayload] = []

            for vc in guild_data.get('voice_channels', ()):
                vc_id = vc['channel_id']

                transformed_channel: VoiceChannelPayload = {
                    'id': vc_id,
                    'type': 2,
                    'name': vc['channel_name'],
                    'guild_id': guild_id,
                    'position': 0,
                    'permission_overwrites': [],
                    'nsfw': False,
                    'parent_id': None,
                    'bitrate': 0,
                    'user_limit': 0,
                }
                transformed_channels.append(transformed_channel)

                streamer_ids = [int(vs['user_id']) for vs in vc.get('streams', ())]
                for user_id in map(int, vc.get('users', ())):
                    transformed_voice_state: GuildVoiceStatePayload = {
                        'user_id': user_id,
                        'session_id': '',
                        'deaf': False,
                        'mute': False,
                        'self_deaf': False,
                        'self_mute': False,
                        'self_video': False,
                        'suppress': False,
                        'self_stream': user_id in streamer_ids,
                        'channel_id': vc_id,
                        'guild_id': guild_id,
                    }
                    transformed_voice_states.append(transformed_voice_state)

            transformed_guild_data: Dict[str, Any] = {
                'id': guild_id,
                'name': guild_data['guild_name'],
                'icon': guild_data.get('guild_icon'),
                'channels': transformed_channels,
                'voice_states': transformed_voice_states,
            }
            guild = Guild(data=transformed_guild_data, state=state)  # type: ignore
            guilds.append(guild)

        self.guilds: List[Guild] = guilds
        self.presences: List[Presence] = [Presence(data=d, state=state, full_user=True) for d in data.get('presences', ())]
        self.applications: List[PartialAppInfo] = [PartialAppInfo(data=d, state=state) for d in data.get('applications', ())]
        self.connected_account_ids: Dict[int, List[str]] = {
            int(d['user_id']): d['provider_ids'] for d in data.get('connected_account_ids', ())
        }
