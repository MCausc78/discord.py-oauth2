from __future__ import annotations

import inspect
from typing import Any, Callable, Dict, TYPE_CHECKING

from ..state import BaseConnectionState

if TYPE_CHECKING:
    from ..http import HTTPClient
    from .types.events import (
        ReadyEvent as ReadyEventPayload,
    )


class RPCConnectionState(BaseConnectionState):
    __slots__ = (
        'dispatch',
        'parsers',
        'v',
        'cdn_host',
        'api_endpoint',
        'environment',
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
        self.v: int = 0
        self.cdn_host: str = ''
        self.api_endpoint: str = ''
        self.environment: str = 'production'

    def parse_ready(self, data: ReadyEventPayload) -> None:
        config_data = data['config']

        self.v = data['v']
        self.cdn_host = config_data['cdn_host']
        self.api_endpoint = config_data['api_endpoint']
        self.environment = config_data['environment']

        # TODO: When we implement BaseConnectionState we will be able to implement this:
        # self.user = User(data=config_data['user'], state=self)

        self.dispatch('ready')
