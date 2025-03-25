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

from typing import TYPE_CHECKING, Optional, Tuple, Union

from .enums import RelationshipType, Status, try_enum
from .mixins import Hashable
from .object import Object
from .presences import ClientStatus
from .utils import _get_as_snowflake, parse_time

if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self

    from .activity import ActivityTypes
    from .presences import RawPresenceUpdateEvent
    from .state import ConnectionState
    from .types.gateway import RelationshipEvent
    from .types.user import User as UserPayload, Relationship as RelationshipPayload
    from .user import User

# fmt: off
__all__ = (
    'Relationship',
)
# fmt: on


class Relationship(Hashable):
    """Represents a relationship in Discord.

    A relationship is like a friendship, a person who is blocked, etc.

    .. container:: operations

        .. describe:: x == y

            Checks if two relationships are equal.

        .. describe:: x != y

            Checks if two relationships are not equal.

        .. describe:: hash(x)

            Return the relationship's hash.

    Attributes
    ----------
    type: :class:`RelationshipType`
        The type of relationship you have.
    user: :class:`User`
        The user you have the relationship with.
    nick: Optional[:class:`str`]
        The user's friend nickname (if applicable).
    spam_request: :class:`bool`
        Whether the friend request was flagged as spam.
    stranger_request: :class:`bool`
        Whether the friend request was sent by a user without a mutual friend or small mutual guild.
    user_ignored: :class:`bool`
        Whether the target user has been ignored by the current user.
    origin_application_id: Optional[:class:`int`]
        The application's ID that created the relationship.
    since: Optional[:class:`~datetime.datetime`]
        When the relationship was created.
        Only available for type :class:`RelationshipType.friend`, :class:`RelationshipType.blocked`, and :class:`RelationshipType.incoming_request`.
    """

    __slots__ = (
        '_state',
        'type',
        'user',
        'nick',
        'client_status',
        'activities',
        'spam_request',
        'stranger_request',
        'user_ignored',
        'origin_application_id',
        'since',
    )

    if TYPE_CHECKING:
        user: User

    def __init__(self, *, state: ConnectionState, data: RelationshipPayload) -> None:
        self._state = state
        self.client_status: ClientStatus = ClientStatus()
        self.activities: Tuple[ActivityTypes, ...] = ()
        self._update(data)

    def _update(self, data: Union[RelationshipPayload, RelationshipEvent]) -> None:
        self.type: RelationshipType = try_enum(RelationshipType, data['type'])

        if 'user' in data:
            self.user: User = self._state.store_user(data['user'])
        elif 'user_id' in data:
            user_id = int(data['user_id'])
            self.user = self._state.get_user(user_id) or Object(id=user_id)  # type: ignore # Lying for better developer UX

        self.nick: Optional[str] = data.get('nickname')
        self.spam_request: bool = data.get('is_spam_request', False)
        self.stranger_request: bool = data.get('stranger_request', False)
        self.user_ignored: bool = data.get('user_ignored', False)
        self.origin_application_id: Optional[int] = _get_as_snowflake(data, 'origin_application_id')
        self.since: Optional[datetime] = parse_time(data.get('since'))

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
    def _from_implicit(cls, *, state: ConnectionState, user: User) -> Relationship:
        self = cls.__new__(cls)
        self._state = state
        self.client_status = ClientStatus()
        self.activities = ()
        self.type = RelationshipType.implicit
        self.nick = None
        self.since = None
        self.user = user
        return self

    @classmethod
    def _copy(cls, relationship: Self, client_status: ClientStatus, activities: Tuple[ActivityTypes, ...]) -> Self:
        self = cls.__new__(cls)  # to bypass __init__

        self._state = relationship._state
        self.client_status = client_status
        self.activities = activities
        self.type = relationship.type
        self.nick = relationship.nick
        self.since = relationship.since
        self.user = relationship.user
        return self

    def __repr__(self) -> str:
        return f'<Relationship user={self.user!r} type={self.type!r} nick={self.nick!r}>'

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

        Deletes the relationship.

        Depending on the type, this could mean unfriending or unblocking the user,
        denying an incoming friend request, discarding an outgoing friend request, etc.

        Raises
        ------
        HTTPException
            Deleting the relationship failed.
        """

        await self._state.http.remove_relationship(self.user.id)

    async def accept(self) -> None:
        """|coro|

        Accepts the relationship request. Only applicable for
        type :class:`RelationshipType.incoming_request`.

        Raises
        ------
        HTTPException
            Accepting the relationship failed.
        """
        await self._state.http.add_relationship(self.user.id)
