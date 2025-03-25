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

from typing import TYPE_CHECKING, Optional, Tuple

from .enums import RelationshipType, Status, try_enum
from .mixins import Hashable
from .object import Object
from .presences import ClientStatus
from .utils import parse_time

if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self

    from .activity import ActivityTypes
    from .presences import RawPresenceUpdateEvent
    from .state import ConnectionState
    from .types.user import User as UserPayload, GameRelationship as GameRelationshipPayload
    from .user import User

# fmt: off
__all__ = (
    'GameRelationship',
)
# fmt: on


class GameRelationship(Hashable):
    """Represents a in-game relationship in Discord.

    A game relationship is like a friendship, a friend request to/from someone, etc.

    .. container:: operations

        .. describe:: x == y

            Checks if two relationships are equal.

        .. describe:: x != y

            Checks if two relationships are not equal.

        .. describe:: hash(x)

            Return the relationship's hash.

    Attributes
    ----------
    application_id: :class:`int`
        The application's ID the game relationship belongs to.
    type: :class:`RelationshipType`
        The type of relationship you have.
    user: :class:`User`
        The user you have the relationship with.
    client_status: :class:`ClientStatus`
        Model which holds information about the status of the member on various clients/platforms via presence updates.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The activities that the user is currently doing.

        .. note::

            Due to a Discord API limitation, a user's Spotify activity may not appear
            if they are listening to a song with a title longer
            than 128 characters. See :issue:`1738` for more information.
    since: :class:`~datetime.datetime`
        When the relationship was created.
    dm_access_type: :class:`int`
        The DM access level for the relationship. Currently unknown.
    """

    __slots__ = (
        '_state',
        'application_id',
        'type',
        'user',
        'client_status',
        'activities',
        'since',
        'dm_access_type',
    )

    if TYPE_CHECKING:
        user: User

    def __init__(self, *, state: ConnectionState, data: GameRelationshipPayload) -> None:
        self._state = state
        self.client_status: ClientStatus = ClientStatus()
        self.activities: Tuple[ActivityTypes, ...] = ()
        self._update(data)

    def _update(self, data: GameRelationshipPayload) -> None:
        self.application_id: int = int(data['application_id'])
        self.type: RelationshipType = try_enum(RelationshipType, data['type'])
        if 'user' in data:
            self.user: User = self._state.store_user(data['user'])
        elif 'user_id' in data:
            user_id = int(data['user_id'])
            self.user = self._state.get_user(user_id) or Object(id=user_id)  # type: ignore # Lying for better developer UX
        self.since: datetime = parse_time(data['since'])
        self.dm_access_type: int = data.get('dm_access_type', 0)  # I've seen it always 0

    def _presence_update(self, raw: RawPresenceUpdateEvent, user: UserPayload) -> Optional[Tuple[User, User]]:
        self.activities = raw.activities
        self.client_status = raw.client_status

        if len(user) > 1:
            return self._update_inner_user(user)

    def _update_inner_user(self, user: UserPayload) -> Optional[Tuple[User, User]]:
        u = self.user
        if isinstance(u, Object):
            self.user = self._state.store_user(user, dispatch=False)
            return None

        original = (
            u.name,
            u.discriminator,
            u._avatar,
            u.global_name,
            u._public_flags,
            u._avatar_decoration_data['sku_id'] if u._avatar_decoration_data is not None else None,
        )

        decoration_payload = user.get('avatar_decoration_data')
        # These keys seem to always be available
        modified = (
            user['username'],
            user['discriminator'],
            user['avatar'],
            user.get('global_name'),
            user.get('public_flags', 0),
            decoration_payload['sku_id'] if decoration_payload is not None else None,
        )
        if original != modified:
            to_return = User._copy(self.user)
            u.name, u.discriminator, u._avatar, u.global_name, u._public_flags, u._avatar_decoration_data = (
                user['username'],
                user['discriminator'],
                user['avatar'],
                user.get('global_name'),
                user.get('public_flags', 0),
                decoration_payload,
            )
            # Signal to dispatch on_user_update
            return to_return, u

    @classmethod
    def _copy(cls, relationship: Self, client_status: ClientStatus, activities: Tuple[ActivityTypes, ...]) -> Self:
        self = cls.__new__(cls)  # to bypass __init__

        self._state = relationship._state
        self.application_id = relationship.application_id
        self.type = relationship.type
        self.user = relationship.user
        self.client_status = client_status
        self.activities = activities
        self.since = relationship.since
        self.dm_access_type = relationship.dm_access_type

        return self

    def __repr__(self) -> str:
        return f'<GameRelationship user={self.user!r} type={self.type!r}>'

    @property
    def id(self) -> int:
        """:class:`int`: Returns the relationship's ID."""
        return self.user.id

    @property
    def status(self) -> Status:
        """:class:`Status`: The user's overall status.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.
        """
        return self.client_status.status

    @property
    def raw_status(self) -> str:
        """:class:`str`: The user's overall status as a string value.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.
        """
        return self.client_status.raw_status

    @property
    def mobile_status(self) -> Status:
        """:class:`Status`: The user's status on a mobile device, if applicable.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.
        """
        return try_enum(Status, self.client_status.mobile or 'offline')

    @property
    def desktop_status(self) -> Status:
        """:class:`Status`: The user's status on the desktop client, if applicable.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.
        """
        return try_enum(Status, self.client_status.desktop or 'offline')

    @property
    def web_status(self) -> Status:
        """:class:`Status`: The user's status on the web client, if applicable.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.
        """
        return try_enum(Status, self.client_status.web or 'offline')

    @property
    def embedded_status(self) -> Status:
        """:class:`Status`: The user's status on the embedded client, if applicable.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.
        """
        return try_enum(Status, self.client_status.web or 'offline')

    def is_on_mobile(self) -> bool:
        """:class:`bool`: A helper function that determines if a user is active on a mobile device.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.
        """
        return self.client_status.is_on_mobile()

    @property
    def activity(self) -> Optional[ActivityTypes]:
        """Optional[Union[:class:`BaseActivity`, :class:`Spotify`]]: Returns the primary
        activity the user is currently doing. Could be ``None`` if no activity is being done.

        .. note::

            This is only reliably provided for type :class:`RelationshipType.friend`.

        .. note::

            Due to a Discord API limitation, this may be ``None`` if
            the user is listening to a song on Spotify with a title longer
            than 128 characters. See :issue:`1738` for more information.

        .. note::

            A user may have multiple activities, these can be accessed under :attr:`activities`.
        """
        if self.activities:
            return self.activities[0]

    async def delete(self) -> None:
        """|coro|

        Deletes the game relationship.

        Depending on the type, this could mean unfriending the user,
        denying an incoming friend request, discarding an outgoing friend request, etc.

        Raises
        ------
        HTTPException
            Deleting the relationship failed.
        """

        await self._state.http.remove_game_relationship(self.user.id)

    async def accept(self) -> None:
        """|coro|

        Accepts the game relationship request. Only applicable for
        type :class:`RelationshipType.incoming_request`.

        Raises
        ------
        HTTPException
            Accepting the relationship failed.
        """
        await self._state.http.add_game_relationship(self.user.id)
