from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING

from ..embeds import Embed
from ..enums import try_enum, MessageType
from ..message import Attachment
from ..mixins import Hashable
from ..user import User
from ..utils import parse_time

if TYPE_CHECKING:
    from datetime import datetime

    from .channel import GuildChannel
    from .state import RPCConnectionState
    from .types.message import (
        ContentComponent as ContentComponentPayload,
        Message as MessagePayload,
    )


class Message(Hashable):
    r"""Represents a message from Discord.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two messages are equal.

        .. describe:: x != y

            Checks if two messages are not equal.

        .. describe:: hash(x)

            Returns the message's hash.

    Attributes
    ----------
    id: :class:`int`
        The message ID.
    type: :class:`MessageType`
        The type of message. In most cases this should not be checked, but it is helpful
        in cases where it might be a system message for :attr:`system_content`.
    author: :class:`~oauth2cord.User`
        A :class:`~oauth2cord.User` that sent the message.
    blocked: :class:`bool`
        Whether the message author is blocked.
    bot: :class:`bool`
        Whether the message author is bot.
    content: :class:`str`
        The actual contents of the message.
    content_parsed: List[:class:`dict`]
        A list of message content components.
    attachments: List[:class:`Attachment`]
        A list of attachments given to a message.
    embeds: List[:class:`Embed`]
        A list of embeds the message has.
    tts: :class:`bool`
        Specifies if the message was done with text-to-speech.
        This can only be accurately received in :func:`on_message` due to
        a Discord limitation.
    edited_at: Optional[:class:`~datetime.datetime`]:
        An aware UTC datetime object containing the edited time of the message.
    mentions: List[:class:`int`]
        A list of IDs of users that were mentioned. For messages that are not of type
        :attr:`MessageType.default`\, this array can be used to aid in system messages.
        For more information, see :attr:`system_content`.

        .. warning::

            The order of the mentions list is not in any particular order so you should
            not rely on it. This is a Discord limitation, not one with the library.
    mention_everyone: :class:`bool`
        Specifies if the message mentions everyone.

        .. note::

            This does not check if the ``@everyone`` or the ``@here`` text is in the message itself.
            Rather this boolean indicates if either the ``@everyone`` or the ``@here`` text is in the message
            **and** it did end up mentioning.
    role_mentions: List[:class:`int`]
        A list of IDs of roles that were mentioned.
    pinned: :class:`bool`
        Specifies if the message is currently pinned.
    author_color: Optional[:class:`str`]
        The CSS color of the author.
    nick: Optional[:class:`str`]
        The rendered nick of the author.
    """

    __slots__ = (
        '_state',
        'id',
        'channel',
        'channel_id',
        'type',
        'author',
        'blocked',
        'bot',
        'content',
        'content_parsed',
        'attachments',
        'embeds',
        'tts',
        'edited_at',
        'mentions',
        'mention_everyone',
        'role_mentions',
        'pinned',
        'author_color',
        'nick',
    )

    def __init__(
        self, *, data: MessagePayload, channel: Optional[GuildChannel] = None, channel_id: int = 0, state: RPCConnectionState
    ) -> None:
        if channel and not channel_id:
            channel_id = channel.id

        self._state: RPCConnectionState = state
        self.id: int = int(data['id'])
        self.channel: Optional[GuildChannel] = channel
        self.channel_id: int = channel_id

        self._update(data)

    def _update(self, data: MessagePayload) -> None:
        state = self._state

        author_data = data.get('author')

        self.type: MessageType = try_enum(MessageType, data['type'])
        self.author: Optional[User] = None if author_data is None else User._from_rpc(author_data, state)
        self.blocked: bool = data['blocked']
        self.bot: bool = data['bot']
        self.content: str = data['content']
        self.content_parsed: List[ContentComponentPayload] = data.get('content_parsed', [])
        self.attachments: List[Attachment] = [Attachment(data=d, state=state) for d in data['attachments']]
        self.embeds: List[Embed] = list(map(Embed._from_rpc, data['embeds']))
        self.tts: bool = data['tts']
        self.edited_at: Optional[datetime] = parse_time(data.get('edited_timestamp'))
        self.mentions: List[int] = list(map(int, data['mentions']))
        self.mention_everyone: bool = data['mention_everyone']
        self.role_mentions: List[int] = list(map(int, data['mention_roles']))
        self.pinned: bool = data['pinned']
        self.author_color: Optional[str] = data.get('author_color')
        self.nick: Optional[str] = data.get('nick')
