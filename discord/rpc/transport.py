from __future__ import annotations

import asyncio
import logging
import sys
import struct
from typing import Any, Callable, Optional, TYPE_CHECKING, Tuple
from typing_extensions import Self

from ..utils import _from_json, _to_json
from .utils import get_ipc_path

if TYPE_CHECKING:
    from .client import Client

_log = logging.getLogger(__name__)

_SEND_STRUCT = struct.Struct('<II')
_RECV_STRUCT = struct.Struct('<ii')


class IPCTransport:
    __slots__ = (
        '_command_parsers',
        '_dispatch',
        '_event_parsers',
        '_reader',
        '_writer',
    )

    def __init__(
        self,
        *,
        dispatch: Callable[..., None],
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        self._dispatch: Callable[..., None] = dispatch
        self._reader: asyncio.StreamReader = reader
        self._writer: asyncio.StreamWriter = writer

    @classmethod
    async def from_client(
        cls,
        client: Client,
        *,
        pipe: Optional[int] = None,
        timeout: Optional[float] = 30,
    ) -> Self:
        path = get_ipc_path(pipe)

        _log.info('Found IPC path: %s.', path)

        dispatch = client.dispatch
        reader: asyncio.StreamReader
        writer: asyncio.StreamWriter

        if sys.platform in ('linux', 'darwin'):
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(path),  # type: ignore
                timeout,
            )
        elif sys.platform == 'win32':
            reader = asyncio.StreamReader(loop=client.loop)
            rp = asyncio.StreamReaderProtocol(reader, loop=client.loop)
            writer, _ = await asyncio.wait_for(
                client.loop.create_pipe_connection(lambda: rp, path),  # type: ignore
                timeout,
            )

        _log.debug('Connection is opened.')
        transport = cls(dispatch=dispatch, reader=reader, writer=writer)
        return transport

    async def recv(self) -> Tuple[int, Any]:
        raw_length = await self._reader.read(8)
        code: int
        length: int
        code, length = _RECV_STRUCT.unpack(raw_length)
        data = await self._reader.read(length)
        _log.debug('For IPC event: %i %s', code, data)
        return code, data

    async def send(self, op: int, payload: Any, /) -> None:
        raw = _to_json(payload)

        self._writer.write(_SEND_STRUCT.pack(op, len(raw)) + raw.encode('utf-8'))

    async def poll_event(self) -> None:
        op, data = await self.recv()

        self._dispatch('raw_event', op, data)
        if op == 1:
            # TODO
            pass  # d = _from_json(data)
