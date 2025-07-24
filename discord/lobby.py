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
import datetime
from typing import Dict, List, Optional, TYPE_CHECKING, Tuple

from .abc import Messageable
from .flags import LobbyMemberFlags
from .mixins import Hashable
from .utils import MISSING, _from_json, _get_as_snowflake, find, parse_time, snowflake_time

if TYPE_CHECKING:
    from typing_extensions import Self

    from .abc import MessageableDestinationType, Snowflake
    from .guild import GuildChannel
    from .state import ConnectionState
    from .types.channel import LinkedLobby as LinkedLobbyPayload
    from .types.lobby import (
        LobbyMember as LobbyMemberPayload,
        LobbyVoiceState as LobbyVoiceStatePayload,
        Lobby as LobbyPayload,
    )
    from .user import User


def _extract_user_id(data: LobbyMemberPayload, /) -> int:
    if 'id' in data:
        return int(data['id'])
    if 'user_id' in data:
        return int(data['user_id'])
    return 0


class LinkedLobby:
    """Represents channel link to a lobby.

    .. versionadded:: 3.0

    Attributes
    ----------
    application_id: :class:`int`
        The application's ID the lobby belongs to.
    lobby_id: :class:`int`
        The lobby's ID the channel was linked to.
    linker_id: :class:`int`
        The user's ID who linked channel to a lobby.
    linked_at: :class:`~datetime.datetime`
        When the channel was linked to a lobby.
    """

    __slots__ = (
        '_state',
        'application_id',
        'lobby_id',
        'linker_id',
        'linked_at',
    )

    def __init__(self, *, data: LinkedLobbyPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.application_id: int = int(data['application_id'])
        self.lobby_id: int = int(data['lobby_id'])
        self.linker_id: int = int(data['linked_by'])
        self.linked_at: datetime.datetime = parse_time(data['linked_at'])

    @property
    def lobby(self) -> Optional[Lobby]:
        """Optional[:class:`Lobby`]: The lobby the channel was linked to."""
        return self._state.get_lobby(self.lobby_id)

    @property
    def linker(self) -> Optional[User]:
        """Optional[:class:`User`]: The user who linked channel to a lobby."""
        return self._state.get_user(self.linker_id)


class LobbyMember(Hashable):
    """Represents a Discord member to a :class:`Lobby`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The user's ID.
    lobby: :class:`Lobby`
        The lobby the member belongs to.
    metadata: Optional[Dict[:class:`str`, :class:`str`]]
        The member's metadata.
    connected: :class:`bool`
        Whether the member is connected to a call in the lobby.
    """

    __slots__ = (
        '_state',
        'id',
        'lobby',
        'metadata',
        '_flags',
        'connected',
    )

    def __init__(
        self, id: int, *, metadata: Optional[Dict[str, str]] = None, flags: Optional[LobbyMemberFlags] = None
    ) -> None:
        self._state: Optional[ConnectionState] = None
        self.id: int = id
        self.lobby: Lobby = MISSING
        self.metadata: Optional[Dict[str, str]] = metadata
        self._flags: int

        if flags is None:
            self._flags = 0
        else:
            self._flags = flags.value

        self.connected: bool = False

    @classmethod
    def from_dict(cls, *, data: LobbyMemberPayload, lobby: Lobby, state: ConnectionState) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.id = _extract_user_id(data)
        self.lobby = lobby
        self._update(data)
        return self

    def _update(self, data: LobbyMemberPayload) -> None:
        self.metadata = data.get('metadata')
        self._flags = data.get('flags', 0)
        self.connected = data.get('connected', False)

    def to_dict(self) -> LobbyMemberPayload:
        return {
            'id': self.id,
            'metadata': self.metadata,
            'flags': self._flags,
        }

    @property
    def flags(self) -> LobbyMemberFlags:
        """:class:`LobbyMemberFlags`: Returns the lobby member's flags."""
        return LobbyMemberFlags._from_value(self._flags)

    @property
    def voice(self) -> Optional[LobbyVoiceState]:
        """Optional[:class:`LobbyVoiceState`]: Returns the member's current voice state."""
        return self.lobby._voice_state_for(self.id)


class LobbyVoiceState:
    """Represents a Discord user's voice state in a lobby.

    .. versionadded:: 3.0

    Attributes
    ----------
    deaf: :class:`bool`
        Indicates if the user is currently deafened by the lobby.
    mute: :class:`bool`
        Indicates if the user is currently muted by the lobby.
    self_mute: :class:`bool`
        Indicates if the user is currently muted by their own accord.
    self_deaf: :class:`bool`
        Indicates if the user is currently deafened by their own accord.
    self_stream: :class:`bool`
        Indicates if the user is currently streaming via 'Go Live' feature.
    self_video: :class:`bool`
        Indicates if the user is currently broadcasting video.
    suppress: :class:`bool`
        Indicates if the user is suppressed from speaking.

        Only applies to stage channels.
    requested_to_speak_at: Optional[:class:`datetime.datetime`]
        An aware datetime object that specifies the date and time in UTC that the member
        requested to speak. It will be ``None`` if they are not requesting to speak
        anymore or have been accepted to speak.

        Only applicable to stage channels.
    afk: :class:`bool`
        Indicates if the user is currently in the AFK channel in the guild.
    channel: Optional[:class:`Lobby`]
        The lobby that the user is currently connected to. ``None`` if the user
        is not currently in a lobby call.
    lobby: :class:`Lobby`
        The lobby.
    """

    __slots__ = (
        'session_id',
        'deaf',
        'mute',
        'self_mute',
        'self_stream',
        'self_video',
        'self_deaf',
        'afk',
        'channel',
        'lobby',
        'requested_to_speak_at',
        'suppress',
    )

    def __init__(self, *, data: LobbyVoiceStatePayload, channel: Optional[Lobby] = None, lobby: Lobby):
        self.session_id: Optional[str] = data.get('session_id')
        self._update(data, channel, lobby)

    def _update(self, data: LobbyVoiceStatePayload, channel: Optional[Lobby], lobby: Lobby):
        self.self_mute: bool = data.get('self_mute', False)
        self.self_deaf: bool = data.get('self_deaf', False)
        self.self_stream: bool = data.get('self_stream', False)
        self.self_video: bool = data.get('self_video', False)
        self.afk: bool = data.get('suppress', False)
        self.mute: bool = data.get('mute', False)
        self.deaf: bool = data.get('deaf', False)
        self.suppress: bool = data.get('suppress', False)
        self.requested_to_speak_at: Optional[datetime.datetime] = parse_time(data.get('request_to_speak_timestamp'))
        self.channel: Optional[Lobby] = channel
        self.lobby: Lobby = lobby

    def __repr__(self) -> str:
        attrs = [
            ('self_mute', self.self_mute),
            ('self_deaf', self.self_deaf),
            ('self_stream', self.self_stream),
            ('suppress', self.suppress),
            ('requested_to_speak_at', self.requested_to_speak_at),
            ('channel', self.channel),
            ('lobby', self.lobby),
        ]
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<{self.__class__.__name__} {inner}>'


class Lobby(Hashable, Messageable):
    """Represents a Discord lobby.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two lobbies are the same.

        .. describe:: x != y

            Checks if two lobbies are not the same.

        .. describe:: hash(x)

            Return the lobby's hash.

    Attributes
    ----------
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
        'region',
        '_voice_states',
    )

    def __init__(self, *, state: ConnectionState, data: LobbyPayload):
        self._state = state
        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self._voice_states: Dict[int, LobbyVoiceState] = {}
        self._update(data)

    def _update(self, data: LobbyPayload) -> None:
        metadata = data.get('metadata')
        if metadata is not None and isinstance(metadata, str):
            metadata = _from_json(metadata)

        state = self._state

        self.metadata: Optional[Dict[str, str]] = metadata
        self.members: List[LobbyMember] = [LobbyMember.from_dict(data=d, lobby=self, state=state) for d in data['members']]
        self.linked_channel: Optional[GuildChannel] = None

        linked_channel_data = data.get('linked_channel')
        if linked_channel_data is not None:
            from .channel import _guild_channel_factory

            cls, _ = _guild_channel_factory(linked_channel_data['type'])
            if cls is not None:
                guild_id = int(linked_channel_data['guild_id'])
                guild = state.get_or_create_unavailable_guild(guild_id)
                if guild is not None:
                    self.linked_channel = cls(data=linked_channel_data, guild=guild, state=state)  # type: ignore

        self.region: Optional[str] = data.get('region')

        if 'voice_states' in data:
            for voice_state_data in data['voice_states']:
                channel_id = _get_as_snowflake(voice_state_data, 'channel_id')
                self._update_voice_state(voice_state_data, state.get_lobby(channel_id))

    def __repr__(self) -> str:
        return f'<Lobby id={self.id} application_id={self.application_id} members={self.members!r}>'

    def _update_voice_state(
        self, data: LobbyVoiceStatePayload, channel: Optional[Lobby]
    ) -> Tuple[LobbyVoiceState, LobbyVoiceState]:
        user_id = int(data['user_id'])
        try:
            # check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy(after)
            after._update(data, channel, self)
        except KeyError:
            # if we're here then we're getting added into the cache
            after = LobbyVoiceState(data=data, channel=channel, lobby=self)
            before = LobbyVoiceState(data=data, channel=None, lobby=self)
            self._voice_states[user_id] = after

        return before, after

    def _voice_state_for(self, user_id: int, /) -> Optional[LobbyVoiceState]:
        return self._voice_states.get(user_id)

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the lobby's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def voice_states(self) -> Dict[int, LobbyVoiceState]:
        """Returns a mapping of member IDs who have voice states in this lobby.

        .. note::

            This function is intentionally low level to replace :attr:`voice_members`
            when the member cache is unavailable.

        Returns
        -------
        Mapping[:class:`int`, :class:`LobbyVoiceState`]
            The mapping of member ID to their lobby voice state.
        """
        # fmt: off
        return {
            key: value
            for key, value in self._voice_states.items()
            if value.channel is not None and value.channel.id == self.id
        }
        # fmt: on

    def get_member(self, user_id: int, /) -> Optional[LobbyMember]:
        """Returns a member with the given ID.

        Parameters
        ----------
        user_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`LobbyMember`]
            The member or ``None`` if not found.
        """
        return find(lambda member, /: member.id == user_id, self.members)

    async def _get_messageable_destination(self) -> Tuple[int, MessageableDestinationType]:
        return (self.id, 'lobby')

    async def leave(self) -> None:
        """|coro|

        Leaves the lobby.

        Raises
        ------
        HTTPException
            Leaving failed.
        """
        await self._state.http.leave_lobby(self.id)

    async def create_invite(self, *, target: Optional[Snowflake] = None) -> str:
        """|coro|

        Creates an invite for channel linked to this lobby.

        Parameters
        ----------
        target: Optional[:class:`User`]
            The user to create the invite for. If ``None``, the invite will be acceptable only
            by you.

        Raises
        ------
        Forbidden
            You do not have permissions to create lobby invite.
        HTTPException
            Creating the lobby invite failed.
        """

        state = self._state
        http = state.http
        if target is None:
            data = await http.create_lobby_invite_for_current_user(self.id)
        else:
            data = await http.create_lobby_invite(self.id, target.id)

        return data['code']

    async def link(self, to: Snowflake) -> Lobby:
        """|coro|

        Links the lobby to a channel.

        You must have :attr:`~LobbyMemberFlags.can_link_lobby` to do this.

        Parameters
        ----------
        to: :class:`TextChannel`
            The channel to link the lobby to.

        Raises
        ------
        Forbidden
            You do not have permissions to link lobby to a channel.
        HTTPException
            Linking the lobby failed.

        Returns
        -------
        :class:`Lobby`
            The newly updated lobby.
        """

        state = self._state
        data = await state.http.set_linked_lobby(self.id, channel_id=to.id)
        return Lobby(data=data, state=state)

    async def unlink(self) -> Lobby:
        """|coro|

        Unlinks the lobby from a channel.

        You must have :attr:`~LobbyMemberFlags.can_link_lobby` to do this.

        Raises
        ------
        Forbidden
            You do not have permissions to unlink lobby from a channel.
        HTTPException
            Unlinking the lobby failed.

        Returns
        -------
        :class:`Lobby`
            The newly updated lobby.
        """

        state = self._state
        data = await state.http.set_linked_lobby(self.id, channel_id=None)
        return Lobby(data=data, state=state)


__all__ = (
    'LinkedLobby',
    'LobbyMember',
    'LobbyVoiceState',
    'Lobby',
)
