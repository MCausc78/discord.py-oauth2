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

import asyncio
import logging
import sys
import struct
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING, Tuple
from typing_extensions import Self

from ..utils import _from_json, _to_json
from .errors import RPCException
from .utils import get_ipc_path

if TYPE_CHECKING:
    from .client import Client

# fmt: off
__all__ = (
    'IPCTransport',
)
# fmt: on

_log = logging.getLogger(__name__)

_SEND_STRUCT = struct.Struct('<II')
_RECV_STRUCT = struct.Struct('<ii')


class IPCTransport:
    __slots__ = (
        '_dispatch',
        '_event_parsers',
        '_nonce_sequence',
        '_pending_requests',
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
        self._nonce_sequence: int = 0
        self._pending_requests: Dict[str, asyncio.Future[Any]] = {}
        self._reader: asyncio.StreamReader = reader
        self._writer: asyncio.StreamWriter = writer

    async def close(self) -> None:
        self._writer.close()

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
        transport._event_parsers = client._connection.parsers
        return transport

    async def recv(self) -> Tuple[int, Any]:
        raw_length = await self._reader.read(8)
        if raw_length:
            code: int
            length: int
            code, length = _RECV_STRUCT.unpack(raw_length)
            data = await self._reader.read(length)
            _log.debug('For IPC event: %i %s', code, data)
            return code, data

        raise StopAsyncIteration

    async def send(self, op: int, payload: Any, /) -> None:
        raw = _to_json(payload)
        _log.debug('Sending IPC event: %s', raw)

        self._writer.write(_SEND_STRUCT.pack(op, len(raw)) + raw.encode('utf-8'))

    async def poll_event(self) -> bool:
        op, data = await self.recv()

        self._dispatch('raw_event', op, data)

        if op == 1:
            payload = _from_json(data)

            cmd = payload['cmd']
            evt = payload.get('evt')

            # 1 b'{"cmd":"DISPATCH","data":{"code":4000,"message":"Payload requires a nonce"},"evt":"ERROR","nonce":null}'

            if evt == 'ERROR':
                nonce = payload.get('nonce')
                if nonce:
                    try:
                        future = self._pending_requests.pop(nonce)
                    except KeyError:
                        pass
                    else:
                        data = payload['data']
                        exc = RPCException(code=data['code'], text=data['message'])
                        future.set_exception(exc)
                else:
                    data = payload['data']
                    raise RPCException(code=data['code'], text=data['message'])
            elif cmd == 'DISPATCH':
                try:
                    parser = self._event_parsers[evt]
                except KeyError:
                    _log.warning('Unknown IPC event %s.', evt)
                else:
                    parser(payload.get('data'))
            else:
                # Else it's a response
                nonce = payload.get('nonce')
                if nonce:
                    try:
                        future = self._pending_requests.pop(nonce)
                    except KeyError:
                        pass
                    else:
                        future.set_result(payload.get('data'))
                else:
                    _log.warning('Received a response without nonce: %s', nonce)
        elif op == 2:
            return False
        elif op == 3:
            await self.send(4, data)
        elif op == 4:
            pass
        else:
            _log.warning('Unknown IPC opcode %s.', op, data)

        return True

    async def send_command(self, command: str, args: Any, *, event: Optional[str] = None) -> Any:
        """|coro|

        Sends a IPC command and waits for result.

        Parameters
        ----------
        command: :class:`str`
            The command, like ``SET_ACTIVITY``.
        args: Any
            The arguments for the command.
        event: Optional[:class:`str`]
            The event to subscribe to. Required if command is ``SUBSCRIBE`` or ``UNSUBSCRIBE``.
        """
        future = asyncio.Future()
        nonce = str(self._nonce_sequence)
        self._nonce_sequence += 1
        self._pending_requests[nonce] = future

        payload = {
            'cmd': command,
            'args': args,
            'nonce': nonce,
        }
        if event:
            payload['evt'] = event

        await self.send(1, payload)
        return await future
