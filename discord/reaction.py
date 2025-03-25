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
from typing import TYPE_CHECKING, Union, Optional


# fmt: off
__all__ = (
    'Reaction',
)
# fmt: on

if TYPE_CHECKING:
    from .types.message import Reaction as ReactionPayload
    from .message import Message
    from .partial_emoji import PartialEmoji
    from .emoji import Emoji


class Reaction:
    """Represents a reaction to a message.

    Depending on the way this object was created, some of the attributes can
    have a value of ``None``.

    .. container:: operations

        .. describe:: x == y

            Checks if two reactions are equal. This works by checking if the emoji
            is the same. So two messages with the same reaction will be considered
            "equal".

        .. describe:: x != y

            Checks if two reactions are not equal.

        .. describe:: hash(x)

            Returns the reaction's hash.

        .. describe:: str(x)

            Returns the string form of the reaction's emoji.

    Attributes
    -----------
    emoji: Union[:class:`Emoji`, :class:`PartialEmoji`, :class:`str`]
        The reaction emoji. May be a custom emoji, or a unicode emoji.
    count: :class:`int`
        Number of times this reaction was made. This is a sum of :attr:`normal_count` and :attr:`burst_count`.
    me: :class:`bool`
        If the user sent this reaction.
    message: :class:`Message`
        Message this reaction is for.
    me_burst: :class:`bool`
        If the user sent this super reaction.

        .. versionadded:: 2.4
    normal_count: :class:`int`
        The number of times this reaction was made using normal reactions.
        This is not available in the gateway events such as :func:`on_reaction_add`
        or :func:`on_reaction_remove`.

        .. versionadded:: 2.4
    burst_count: :class:`int`
        The number of times this reaction was made using super reactions.
        This is not available in the gateway events such as :func:`on_reaction_add`
        or :func:`on_reaction_remove`.

        .. versionadded:: 2.4
    """

    __slots__ = ('message', 'count', 'emoji', 'me', 'me_burst', 'normal_count', 'burst_count')

    def __init__(self, *, message: Message, data: ReactionPayload, emoji: Optional[Union[PartialEmoji, Emoji, str]] = None):
        self.message: Message = message
        self.emoji: Union[PartialEmoji, Emoji, str] = emoji or message._state.get_reaction_emoji(data['emoji'])
        self.count: int = data.get('count', 1)
        self.me: bool = data['me']
        details = data.get('count_details', {})
        self.normal_count: int = details.get('normal', 0)
        self.burst_count: int = details.get('burst', 0)
        self.me_burst: bool = data.get('me_burst', False)

    def is_custom_emoji(self) -> bool:
        """:class:`bool`: If this is a custom emoji."""
        return not isinstance(self.emoji, str)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and other.emoji == self.emoji

    def __ne__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return other.emoji != self.emoji
        return True

    def __hash__(self) -> int:
        return hash(self.emoji)

    def __str__(self) -> str:
        return str(self.emoji)

    def __repr__(self) -> str:
        return f'<Reaction emoji={self.emoji!r} me={self.me} count={self.count}>'
