from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from ..state import BaseConnectionState
from ..user import ClientUser

if TYPE_CHECKING:
    from ..http import HTTPClient
    from .types.events import (
        ReadyEvent as ReadyEventPayload,
    )


class RPCConnectionState(BaseConnectionState):
    __slots__ = (
        'dispatch',
        'parsers',
        'version',
        'cdn_host',
        'api_endpoint',
        'environment',
        'user',
    )

    def __init__(self, *, dispatch: Callable[..., None], http: HTTPClient) -> None:
        super().__init__(dispatch=dispatch, http=http)
        self.parsers: Dict[str, Callable[[Any], None]]
        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func

        self.clear()

    def clear(self) -> None:
        self.version: int = 0
        self.cdn_host: str = ''
        self.api_endpoint: str = ''
        self.environment: str = 'production'
        self.user: Optional[ClientUser] = None

    async def close(self) -> None:
        pass

    def parse_ready(self, data: ReadyEventPayload) -> None:
        config_data = data['config']
        user_data = data.get('user')

        self.version = data['v']
        self.cdn_host = config_data['cdn_host']
        self.api_endpoint = config_data['api_endpoint']
        self.environment = config_data['environment']
        self.user = ClientUser._from_rpc(user_data, self) if user_data else None

        self.dispatch('ready')
