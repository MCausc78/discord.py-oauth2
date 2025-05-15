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

from base64 import b64encode
import sys
from typing import Any, Dict, Final, Literal, Mapping, Optional, TYPE_CHECKING

from .enums import Enum
from .utils import _ReactiveMappingProxy, _to_json, copy_doc

if TYPE_CHECKING:
    from typing_extensions import Self

    from .utils import MaybeAwaitable

    PropertyAt = Literal[
        'both',
        'gateway',
        'http',
    ]

DEFAULT_USER_AGENT: Final[str] = "Discord Embedded/0.0.8"
SDK_CLIENT_BUILD_NUMBER: Final[int] = 304683


class ClientOperatingSystem(Enum):
    android = 'Android'
    ios = 'iOS'
    linux = 'Linux'
    osx = 'Mac OS X'
    playstation = 'Playstation'
    windows = 'Windows'
    unknown = 'Unknown'
    xbox = 'Xbox'

    @classmethod
    def default(cls) -> Self:
        lookup = {
            'android': cls.android,
            'darwin': cls.osx,
            'ios': cls.ios,
            'linux': cls.linux,
            'win32': cls.windows,
            'cygwin': cls.windows,
        }
        return lookup.get(sys.platform, cls.unknown)  # type: ignore


class Impersonate:
    """An ABC that details client properties values and how to impersonate client.

    The following implement this ABC:

    - :class:`~discord.DefaultImpersonate`
    - :class:`~discord.SimpleImpersonate`

    Client properties are used for analytics and anti-abuse systems. See
    `documentation <https://docs.discord.food/reference#client-properties>`_ for details.

    .. versionadded:: 3.0
    """

    __slots__ = ()

    async def setup(self) -> None:
        """|coro|

        Called when client properties need to be set.
        """

    def get_client_properties(self) -> MaybeAwaitable[Dict[str, Any]]:
        """|maybecoro|

        Return client properties as :class:`dict`.
        """
        raise NotImplementedError

    def get_client_properties_base64(self) -> MaybeAwaitable[str]:
        """|maybecoro|

        Return client properties as base64-encoded :class:`str`.
        """
        raise NotImplementedError

    def get_http_user_agent(self) -> MaybeAwaitable[str]:
        """|maybecoro|

        Return user agent used to make HTTP requests.
        """
        raise NotImplementedError

    def get_http_initial_headers(self) -> MaybeAwaitable[Dict[str, str]]:
        """|maybecoro|

        Return initial headers used to make HTTP request.
        """
        raise NotImplementedError

    def get_websocket_user_agent(self) -> MaybeAwaitable[str]:
        """|maybecoro|

        Return user agent used to make WebSocket connection.
        """
        raise NotImplementedError

    def get_websocket_initial_headers(self) -> MaybeAwaitable[Dict[str, str]]:
        """|maybecoro|

        Return initial headers used to make WebSocket connection.
        """
        raise NotImplementedError


class DefaultImpersonate(Impersonate):
    """A default implementation of :class:`~discord.Impersonate`.

    Attributes
    ----------
    user_agent: :class:`str`
        The user agent used to make HTTP requests.
    websocket_user_agent: :class:`str`
        The user agent used to make WebSocket connections.

    Parameters
    ----------
    os: Optional[:class:`ClientOperatingSystem`]
        The operating system to send in properties.
    """

    __slots__ = (
        '_cs_http_value_base64',
        '_gateway_value',
        '_http_value',
        'user_agent',
        'websocket_user_agent',
    )

    def __init__(self, *, os: Optional[ClientOperatingSystem] = None) -> None:
        # [2025-03-18 22:06:32.443] [1456] (gateway_socket.cpp:698): sending - {
        #   "d": {
        #     "capabilities":69680,
        #     "intents":416026624,
        #     "properties":{
        #       "browser":"Discord Embedded",
        #       "client_build_number":304683,
        #       "device":"console",
        #       "os":"Windows",
        #       "version":1
        #     },
        #     "token":"Bearer xxx"
        #   },
        #   "op":2
        # }

        if os is None:
            os = ClientOperatingSystem.default()

        self.user_agent: str = "Discord Embedded/0.0.8"
        self.websocket_user_agent: str = "WebSocket++/0.8.3-dev"

        self._gateway_value: Dict[str, Any] = {
            "browser": "Discord Embedded",
            "client_build_number": SDK_CLIENT_BUILD_NUMBER,
            "device": "console",  # :clueless:
            "os": os.value,
            "version": 1,  # That's what populates :attr:`Session.version`
        }
        self._http_value: Dict[str, Any] = {
            "browser": "Discord Embedded",
            "browser_user_agent": self.user_agent,
            "browser_version": "0.0.8",
            "client_build_number": SDK_CLIENT_BUILD_NUMBER,
            "design_id": 0,  # ???
            "os": os.value,
            "release_channel": "unknown",
        }
        self._update_cached_properties()

    def _update_cached_properties(self) -> None:
        self._cs_http_value_base64: str = b64encode(_to_json(self._http_value).encode()).decode()

    @property
    def gateway_value(self) -> Mapping[str, Any]:
        """Mapping[:class:`str`, Any]: The client properties sent over Gateway."""
        return self._gateway_value

    @gateway_value.setter
    def gateway_value(self, value: Mapping[str, Any]) -> None:
        self._gateway_value = dict(value)

    @property
    def http_value(self) -> Mapping[str, Any]:
        """Mapping[:class:`str`, Any]: The client properties sent over HTTP.

        Modifying anything in returned object will automatically update headers.
        """
        return _ReactiveMappingProxy(original=self._http_value, updater=self._update_cached_properties)

    @http_value.setter
    def http_value(self, value: Mapping[str, Any]) -> None:
        self._http_value = dict(value)
        self._update_cached_properties()

    def put(self, key: str, value: Any, *, at: PropertyAt = 'both') -> Self:
        """Put a super property.

        Parameters
        ----------
        key: :class:`str`
            The key to insert super property at.
        value: Any
            The value to insert.
        at: :class:`str`
            Must be one of:

            - ``'both'``: Put super property to Gateway and HTTP properties.
            - ``'gateway'``: Put super property only to Gateway properties.
            - ``'http'``: Put super property only to HTTP properties.

        Returns
        -------
        Self
            This instance for chaining.
        """
        if at == 'both':
            self._gateway_value[key] = value
            self._http_value[key] = value
            self._update_cached_properties()
        elif at == 'gateway':
            self._gateway_value[key] = value
        elif at == 'http':
            self._http_value[key] = value
            self._update_cached_properties()
        else:
            raise TypeError(f'Unknown location {at}')
        return self

    def without(self, /, *keys: str, at: PropertyAt = 'both') -> Self:
        """Remove super properties.

        Parameters
        ----------
        \\*keys: :class:`str`
            The keys to remove from super properties.
        at: :class:`str`
            Must be one of:

            - ``'both'``: Remove super properties from Gateway and HTTP properties.
            - ``'gateway'``: Remove super properties only from Gateway properties.
            - ``'http'``: Remove super properties only from HTTP properties.

        Returns
        -------
        Self
            This instance for chaining.
        """
        if at == 'both':
            for key in keys:
                self._gateway_value.pop(key, None)
                self._http_value.pop(key, None)
            self._update_cached_properties()
        elif at == 'gateway':
            for key in keys:
                self._gateway_value.pop(key, None)
        elif at == 'http':
            for key in keys:
                self._http_value.pop(key, None)
            self._update_cached_properties()
        else:
            raise TypeError(f'Unknown location {at}')
        return self

    def with_user_agent(self, value: str, /) -> Self:
        """Sets HTTP user agent to provided value."""
        self.user_agent = value
        return self

    def with_websocket_user_agent(self, value: str, /) -> Self:
        """Sets WebSocket user agent to provided value."""
        self.websocket_user_agent = value
        return self

    @copy_doc(Impersonate.get_client_properties)
    def get_client_properties(self) -> MaybeAwaitable[Dict[str, Any]]:
        return self._gateway_value

    @copy_doc(Impersonate.get_client_properties_base64)
    def get_client_properties_base64(self) -> MaybeAwaitable[str]:
        return self._cs_http_value_base64

    @copy_doc(Impersonate.get_http_user_agent)
    def get_http_user_agent(self) -> MaybeAwaitable[str]:
        return self.user_agent

    @copy_doc(Impersonate.get_http_initial_headers)
    def get_http_initial_headers(self) -> MaybeAwaitable[Dict[str, str]]:
        return {}

    @copy_doc(Impersonate.get_websocket_user_agent)
    def get_websocket_user_agent(self) -> MaybeAwaitable[str]:
        return self.websocket_user_agent

    @copy_doc(Impersonate.get_websocket_initial_headers)
    def get_websocket_initial_headers(self) -> MaybeAwaitable[Dict[str, str]]:
        return {}


class SimpleImpersonate(Impersonate):
    """A simple implementation of :class:`~discord.Impersonate`."""

    __slots__ = (
        '_cs_http_value_base64',
        '_gateway_initial_headers',
        '_gateway_value',
        '_http_initial_headers',
        '_http_user_agent',
        '_http_value',
        '_websocket_user_agent',
    )

    def __init__(
        self,
        *,
        initial_headers: Optional[Dict[str, Any]] = None,
        value: Optional[Dict[str, Any]] = None,
        gateway_initial_headers: Optional[Dict[str, Any]] = None,
        gateway_value: Optional[Dict[str, Any]] = None,
        http_initial_headers: Optional[Dict[str, Any]] = None,
        http_value: Optional[Dict[str, Any]] = None,
        http_user_agent: Optional[str] = None,
        user_agent: Optional[str] = None,
        websocket_user_agent: Optional[str] = None,
    ) -> None:
        if value is not None:
            if gateway_value is not None and http_value is not None:
                gateway_value = gateway_value | value  # type: ignore
                http_value = http_value | value  # type: ignore
            elif gateway_value is None:
                gateway_value = value
            if http_value is None:
                http_value = value
        elif gateway_value is None and http_value is not None:
            gateway_value = http_value
        elif gateway_value is not None and http_value is None:
            http_value = gateway_value
        elif gateway_value is None and http_value is None:
            raise TypeError(
                'Specify either any of gateway_value, http_value if value is not provided, or one (or none at all) of gateway_value and http_value if value is provided'
            )

        # TODO: Extract `browser_user_agent` from provided super properties if could not find user agent for gateway/HTTP
        if user_agent is not None:
            if websocket_user_agent is not None and http_user_agent is not None:
                raise TypeError('Cannot specify user_agent, websocket_user_agent and http_user_agent at once')

            if websocket_user_agent is None:
                websocket_user_agent = user_agent
            if http_user_agent is None:
                http_user_agent = user_agent
        elif websocket_user_agent is None and http_user_agent is not None:
            websocket_user_agent = http_user_agent
        elif websocket_user_agent is not None and http_user_agent is None:
            http_user_agent = websocket_user_agent
        elif websocket_user_agent is None and http_user_agent is None:
            raise TypeError(
                'Specify either any of websocket_user_agent, http_user_agent if user_agent is not provided, or one (or none at all) of websocket_user_agent and http_user_agent if user_agent is provided'
            )

        if initial_headers is not None:
            if gateway_initial_headers is not None and http_initial_headers is not None:
                raise TypeError('Cannot specify initial_headers, gateway_initial_headers and http_initial_headers at once')

            if gateway_initial_headers is None:
                gateway_initial_headers = initial_headers
            if http_initial_headers is None:
                http_initial_headers = initial_headers
        elif gateway_initial_headers is None and http_initial_headers is not None:
            gateway_initial_headers = http_initial_headers
        elif gateway_initial_headers is not None and http_initial_headers is None:
            http_initial_headers = gateway_initial_headers
        elif gateway_initial_headers is None and http_initial_headers is None:
            gateway_initial_headers = {}
            http_initial_headers = {}

        # I think it's already set...
        self._gateway_initial_headers: Dict[str, Any] = gateway_initial_headers  # type: ignore
        self._gateway_value: Dict[str, Any] = gateway_value  # type: ignore
        self._http_initial_headers: Dict[str, Any] = http_initial_headers  # type: ignore
        self._http_value: Dict[str, Any] = http_value  # type: ignore
        self._http_user_agent: str = http_user_agent  # type: ignore
        self._websocket_user_agent: str = websocket_user_agent  # type: ignore
        self._update_cached_properties()

    def _update_cached_properties(self) -> None:
        self._cs_http_value_base64: str = b64encode(_to_json(self._http_value).encode()).decode()

    @copy_doc(Impersonate.get_client_properties)
    def get_client_properties(self) -> MaybeAwaitable[Dict[str, Any]]:
        return self._gateway_value

    @copy_doc(Impersonate.get_client_properties_base64)
    def get_client_properties_base64(self) -> MaybeAwaitable[str]:
        return self._cs_http_value_base64

    @copy_doc(Impersonate.get_http_user_agent)
    def get_http_user_agent(self) -> MaybeAwaitable[str]:
        return self._http_user_agent

    @copy_doc(Impersonate.get_http_initial_headers)
    def get_http_initial_headers(self) -> MaybeAwaitable[Dict[str, str]]:
        return self._http_initial_headers

    @copy_doc(Impersonate.get_websocket_user_agent)
    def get_websocket_user_agent(self) -> MaybeAwaitable[str]:
        return self._websocket_user_agent

    @copy_doc(Impersonate.get_websocket_initial_headers)
    def get_websocket_initial_headers(self) -> MaybeAwaitable[Dict[str, str]]:
        return self._gateway_initial_headers


__all__ = (
    'ClientOperatingSystem',
    'Impersonate',
    'DefaultImpersonate',
    'SimpleImpersonate',
)
