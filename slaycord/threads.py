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

import array
from datetime import datetime
from typing import Dict, List, Literal, Optional, TYPE_CHECKING, Union

from .abc import GuildChannel
from .errors import ClientException
from .enums import ChannelType, try_enum
from .flags import ChannelFlags
from .mixins import Hashable
from .permissions import Permissions
from .utils import _get_as_snowflake, parse_time

__all__ = (
    'Thread',
    'ThreadMember',
)

if TYPE_CHECKING:
    from .channel import TextChannel, CategoryChannel, ForumChannel, ForumTag
    from .guild import Guild
    from .member import Member
    from .message import Message
    from .role import Role
    from .state import ConnectionState
    from .types.threads import (
        Thread as ThreadPayload,
        ThreadMember as ThreadMemberPayload,
        ThreadMetadata,
    )

    ThreadChannelType = Literal[ChannelType.news_thread, ChannelType.public_thread, ChannelType.private_thread]


class Thread(Hashable):
    """Represents a Discord thread.

    .. container:: operations

        .. describe:: x == y

            Checks if two threads are equal.

        .. describe:: x != y

            Checks if two threads are not equal.

        .. describe:: hash(x)

            Returns the thread's hash.

        .. describe:: str(x)

            Returns the thread's name.

    .. versionadded:: 2.0

    Attributes
    ----------
    name: :class:`str`
        The thread name.
    guild: :class:`Guild`
        The guild the thread belongs to.
    id: :class:`int`
        The thread ID. This is the same as the thread starter message ID.
    parent_id: :class:`int`
        The parent :class:`TextChannel` or :class:`ForumChannel` ID this thread belongs to.
    owner_id: :class:`int`
        The user's ID that created this thread.
    last_message_id: Optional[:class:`int`]
        The last message ID of the message sent to this thread. It may
        *not* point to an existing or valid message.
    slowmode_delay: :class:`int`
        The number of seconds a member must wait between sending messages
        in this thread. A value of ``0`` denotes that it is disabled.
        Bots and users with :attr:`~Permissions.manage_channels` or
        :attr:`~Permissions.manage_messages` bypass slowmode.
    message_count: :class:`int`
        An approximate number of messages in this thread.
    member_count: :class:`int`
        An approximate number of members in this thread. This caps at 50.
    me: Optional[:class:`ThreadMember`]
        A thread member representing yourself, if you've joined the thread.
        This could not be available.
    archived: :class:`bool`
        Whether the thread is archived.
    locked: :class:`bool`
        Whether the thread is locked.
    invitable: :class:`bool`
        Whether non-moderators can add other non-moderators to this thread.
        This is always ``True`` for public threads.
    archiver_id: Optional[:class:`int`]
        The user's ID that archived this thread.

        .. note::
            Due to an API change, the ``archiver_id`` will always be ``None`` and can only be obtained via the audit log.

    auto_archive_duration: :class:`int`
        The duration in minutes until the thread is automatically hidden from the channel list.
        Usually a value of 60, 1440, 4320 and 10080.
    archive_timestamp: :class:`datetime.datetime`
        An aware timestamp of when the thread's archived status was last updated in UTC.
    """

    __slots__ = (
        'name',
        'id',
        'guild',
        '_type',
        '_state',
        '_members',
        'owner_id',
        'parent_id',
        'last_message_id',
        'message_count',
        'member_count',
        'slowmode_delay',
        'me',
        'locked',
        'archived',
        'invitable',
        'archiver_id',
        'auto_archive_duration',
        'archive_timestamp',
        '_created_at',
        '_flags',
        '_applied_tags',
    )

    def __init__(self, *, guild: Guild, state: ConnectionState, data: ThreadPayload) -> None:
        self._state: ConnectionState = state
        self.guild: Guild = guild
        self._members: Dict[int, ThreadMember] = {}
        self._from_data(data)

    def __repr__(self) -> str:
        return (
            f'<Thread id={self.id!r} name={self.name!r} parent={self.parent}'
            f' owner_id={self.owner_id!r} locked={self.locked} archived={self.archived}>'
        )

    def __str__(self) -> str:
        return self.name

    def _from_data(self, data: ThreadPayload):
        self.id: int = int(data['id'])
        self.parent_id: int = int(data['parent_id'])
        self.owner_id: int = int(data['owner_id'])
        self.name: str = data['name']
        self._type: ThreadChannelType = try_enum(ChannelType, data['type'])  # type: ignore
        self.last_message_id: Optional[int] = _get_as_snowflake(data, 'last_message_id')
        self.slowmode_delay: int = data.get('rate_limit_per_user', 0)
        self.message_count: int = data['message_count']
        self.member_count: int = data['member_count']
        self._flags: int = data.get('flags', 0)
        # SnowflakeList is sorted, but this would not be proper for applied tags, where order actually matters.
        self._applied_tags: array.array[int] = array.array('Q', map(int, data.get('applied_tags', ())))
        self._unroll_metadata(data['thread_metadata'])

        self.me: Optional[ThreadMember]
        try:
            member = data['member']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            self.me = None
        else:
            self.me = ThreadMember(self, member)

    def _unroll_metadata(self, data: ThreadMetadata):
        self.archived: bool = data['archived']
        self.archiver_id: Optional[int] = _get_as_snowflake(data, 'archiver_id')
        self.auto_archive_duration: int = data['auto_archive_duration']
        self.archive_timestamp: datetime = parse_time(data['archive_timestamp'])
        self.locked: bool = data.get('locked', False)
        self.invitable: bool = data.get('invitable', True)
        self._created_at: Optional[datetime] = parse_time(data.get('create_timestamp'))

    def _update(self, data: ThreadPayload) -> None:
        try:
            self.name = data['name']
        except KeyError:
            pass

        self.slowmode_delay = data.get('rate_limit_per_user', 0)
        self._flags: int = data.get('flags', 0)
        self._applied_tags: array.array[int] = array.array('Q', map(int, data.get('applied_tags', ())))

        try:
            self._unroll_metadata(data['thread_metadata'])
        except KeyError:
            pass

    @property
    def type(self) -> ThreadChannelType:
        """:class:`ChannelType`: The channel's Discord type."""
        return self._type

    @property
    def parent(self) -> Optional[Union[ForumChannel, TextChannel]]:
        """Optional[Union[:class:`ForumChannel`, :class:`TextChannel`]]: The parent channel this thread belongs to."""
        return self.guild.get_channel(self.parent_id)  # type: ignore

    @property
    def flags(self) -> ChannelFlags:
        """:class:`ChannelFlags`: The flags associated with this thread."""
        return ChannelFlags._from_value(self._flags)

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member this thread belongs to."""
        return self.guild.get_member(self.owner_id)

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the thread."""
        return f'<#{self.id}>'

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the thread.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'

    @property
    def members(self) -> List[ThreadMember]:
        """List[:class:`ThreadMember`]: A list of thread members in this thread.

        This requires :attr:`Intents.members` to be properly filled. Most of the time however,
        this data is not provided by the gateway and a call to :meth:`fetch_members` is
        needed.
        """
        return list(self._members.values())

    @property
    def applied_tags(self) -> List[ForumTag]:
        """List[:class:`ForumTag`]: A list of tags applied to this thread.

        .. versionadded:: 2.1
        """
        tags = []
        if self.parent is None or self.parent.type != ChannelType.forum:
            return tags

        parent = self.parent
        for tag_id in self._applied_tags:
            tag = parent.get_tag(tag_id)
            if tag is not None:
                tags.append(tag)

        return tags

    @property
    def starter_message(self) -> Optional[Message]:
        """Returns the thread starter message from the cache.

        The message might not be cached, valid, or point to an existing message.

        Note that the thread starter message ID is the same ID as the thread.

        Returns
        -------
        Optional[:class:`Message`]
            The thread starter message or ``None`` if not found.
        """
        return self._state._get_message(self.id)

    @property
    def last_message(self) -> Optional[Message]:
        """Returns the last message from this thread from the cache.

        The message might not be valid or point to an existing message.

        .. admonition:: Reliable Fetching
            :class: helpful

            For a slightly more reliable method of fetching the
            last message, consider using either :meth:`history`
            or :meth:`fetch_message` with the :attr:`last_message_id`
            attribute.

        Returns
        -------
        Optional[:class:`Message`]
            The last message in this channel or ``None`` if not found.
        """
        return self._state._get_message(self.last_message_id) if self.last_message_id else None

    @property
    def category(self) -> Optional[CategoryChannel]:
        """The category channel the parent channel belongs to, if applicable.

        Raises
        ------
        ClientException
            The parent channel was not cached and returned ``None``.

        Returns
        -------
        Optional[:class:`CategoryChannel`]
            The parent channel's category.
        """

        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')
        return parent.category

    @property
    def category_id(self) -> Optional[int]:
        """The category channel ID the parent channel belongs to, if applicable.

        Raises
        ------
        ClientException
            The parent channel was not cached and returned ``None``.

        Returns
        -------
        Optional[:class:`int`]
            The parent channel's category ID.
        """

        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')
        return parent.category_id

    @property
    def created_at(self) -> Optional[datetime]:
        """An aware timestamp of when the thread was created in UTC.

        .. note::

            This timestamp only exists for threads created after 9 January 2022, otherwise returns ``None``.
        """
        return self._created_at

    def is_private(self) -> bool:
        """:class:`bool`: Whether the thread is a private thread.

        A private thread is only viewable by those that have been explicitly
        invited or have :attr:`~.Permissions.manage_threads`.
        """
        return self._type is ChannelType.private_thread

    def is_news(self) -> bool:
        """:class:`bool`: Whether the thread is a news thread.

        A news thread is a thread that has a parent that is a news channel,
        i.e. :meth:`.TextChannel.is_news` is ``True``.
        """
        return self._type is ChannelType.news_thread

    def is_nsfw(self) -> bool:
        """:class:`bool`: Whether the thread is NSFW or not.

        An NSFW thread is a thread that has a parent that is an NSFW channel,
        i.e. :meth:`.TextChannel.is_nsfw` is ``True``.
        """
        parent = self.parent
        return parent is not None and parent.is_nsfw()

    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        """Handles permission resolution for the :class:`~slaycord.Member`
        or :class:`~slaycord.Role`.

        Since threads do not have their own permissions, they mostly
        inherit them from the parent channel with some implicit
        permissions changed.

        Parameters
        ----------
        obj: Union[:class:`~slaycord.Member`, :class:`~slaycord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Raises
        ------
        ClientException
            The parent channel was not cached and returned ``None``

        Returns
        -------
        :class:`~slaycord.Permissions`
            The resolved permissions for the member or role.
        """

        parent = self.parent
        if parent is None:
            raise ClientException('Parent channel not found')

        base = GuildChannel.permissions_for(parent, obj)

        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages_in_threads:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

        return base

    # def get_partial_message(self, message_id: int, /) -> PartialMessage:
    #     """Creates a :class:`PartialMessage` from the message ID.

    #     This is useful if you want to work with a message and only have its ID without
    #     doing an unnecessary API call.

    #     .. versionadded:: 2.0

    #     Parameters
    #     ----------
    #     message_id: :class:`int`
    #         The message ID to create a partial message for.

    #     Returns
    #     -------
    #     :class:`PartialMessage`
    #         The partial message.
    #     """

    #     from .message import PartialMessage

    #     return PartialMessage(channel=self, id=message_id)

    def _add_member(self, member: ThreadMember, /) -> None:
        self._members[member.id] = member

    def _pop_member(self, member_id: int, /) -> Optional[ThreadMember]:
        return self._members.pop(member_id, None)


class ThreadMember(Hashable):
    """Represents a Discord thread member.

    .. container:: operations

        .. describe:: x == y

            Checks if two thread members are equal.

        .. describe:: x != y

            Checks if two thread members are not equal.

        .. describe:: hash(x)

            Returns the thread member's hash.

        .. describe:: str(x)

            Returns the thread member's name.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: :class:`int`
        The thread member's ID.
    thread_id: :class:`int`
        The thread's ID.
    joined_at: :class:`datetime.datetime`
        The time the member joined the thread in UTC.
    """

    __slots__ = (
        'id',
        'thread_id',
        'joined_at',
        'flags',
        '_state',
        'parent',
    )

    def __init__(self, parent: Thread, data: ThreadMemberPayload) -> None:
        self.parent: Thread = parent
        self._state: ConnectionState = parent._state
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<ThreadMember id={self.id} thread_id={self.thread_id} joined_at={self.joined_at!r}>'

    def _from_data(self, data: ThreadMemberPayload) -> None:
        self.id: int
        try:
            self.id = int(data['user_id'])
        except KeyError:
            self.id = self._state.self_id  # type: ignore

        self.thread_id: int
        try:
            self.thread_id = int(data['id'])
        except KeyError:
            self.thread_id = self.parent.id

        self.joined_at: datetime = parse_time(data['join_timestamp'])
        self.flags: int = data['flags']

    @property
    def thread(self) -> Thread:
        """:class:`Thread`: The thread this member belongs to."""
        return self.parent
