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
from typing import List, TYPE_CHECKING

from .utils import MISSING, _bytes_to_base64_data

if TYPE_CHECKING:
    from typing_extensions import Self

    from .state import ConnectionState
    from .types.stream import Stream as StreamPayload

__all__ = (
    'PartialStream',
    'Stream',
)


class PartialStream:
    """Represents a partial stream.

    Attributes
    ----------
    key: :class:`str`
        The stream key.
    """

    __slots__ = (
        '_state',
        'key',
    )

    def __init__(self, *, key: str, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.key: str = key

    def __repr__(self) -> str:
        return f'<PartialStream key={self.key!r}>'

    async def delete(self) -> None:
        """|coro|

        Deletes the stream.

        This is a WebSocket operation.
        """
        ws = self._state._get_websocket()
        await ws.delete_stream(self.key)

    async def edit(
        self,
        *,
        paused: bool = MISSING,
        thumbnail: bytes = MISSING,
    ) -> Self:
        """|coro|

        Edits the stream.

        All parameters are optional.

        Parameters
        ----------
        paused: :class:`bool`
            Whether to pause the stream.

            This is a WebSocket operation.
        thumbnail: :class:`bytes`
            The stream preview to upload.

            This is an HTTP operation.

        Raises
        ------
        HTTPException
            The stream key was invalid, or editing the stream failed.

        Returns
        -------
        Self
            The newly updated stream.
        """
        state = self._state
        if paused is not MISSING:
            ws = state._get_websocket()
            await ws.set_stream_paused(self.key, paused=paused)
        if thumbnail is not MISSING:
            await state.http.upload_stream_preview(
                self.key,
                thumbnail=_bytes_to_base64_data(thumbnail),
            )
        ret = copy(self)
        if isinstance(ret, Stream) and paused is not MISSING:
            ret.paused = paused
        return ret

    async def watch(self) -> None:
        """|coro|

        Starts watching the stream.

        This is a WebSocket operation.
        """
        ws = self._state._get_websocket()
        await ws.watch_stream(self.key)


class Stream(PartialStream):
    """Represents a stream.

    Attributes
    ----------
    key: :class:`str`
        The stream key.
    rtc_server_id: :class:`int`
        The ID of the RTC server for the stream.
        This is used when connecting to voice.

        May be zero in :func:`on_stream_update` if stream was not cached.
    region: :class:`str`
        The voice region the stream is in.
    viewer_ids: List[:class:`int`]
        The IDs of the viewers currently watching the stream.
    paused: :class:`bool`
        Whether the stream is paused.
    unavailable: :class:`bool`
        Whether the stream is currently unavailable due to outage.
    """

    __slots__ = (
        'rtc_server_id',
        'region',
        'viewer_ids',
        'paused',
        'unavailable',
    )

    def __init__(self, *, data: StreamPayload, state: ConnectionState) -> None:
        super().__init__(key=data['stream_key'], state=state)
        self.rtc_server_id: int = int(data.get('rtc_server_id', 0))
        self.unavailable: bool = False
        self._update(data)

    def __repr__(self) -> str:
        return f'<Stream key={self.key!r} region={self.region!r} paused={self.paused!r} unavailable={self.unavailable!r}>'

    def _update(self, data: StreamPayload, /) -> None:
        self.region: str = data['region']
        self.viewer_ids: List[int] = list(map(int, data['viewer_ids']))
        self.paused: bool = data['paused']
