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

from typing import Optional, TYPE_CHECKING

from .message import Message

if TYPE_CHECKING:
    from .state import RPCConnectionState
    from .types.events import NotificationCreateEvent as NotificationPayload

# fmt: off
__all__ = (
    'Notification',
)
# fmt: on


class Notification:
    """Represents a notification.

    Attributes
    ----------
    message: :class:`Message`
        The message that triggered the notification.
    icon_url: Optional[:class:`str`]
        The icon URL.
    title: :class:`str`
        The notification's title.
    body: :class:`str`
        The notification's body.
    """

    __slots__ = (
        'message',
        'icon_url',
        'title',
        'body',
    )

    def __init__(self, *, data: NotificationPayload, state: RPCConnectionState) -> None:
        self.message: Message = Message(data=data['message'], channel_id=int(data['channel_id']), state=state)
        self.icon_url: Optional[str] = data.get('icon_url')
        self.title: str = data['title']
        self.body: str = data['body']
