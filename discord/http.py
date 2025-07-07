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

import asyncio
from collections import deque
import datetime
from inspect import isawaitable
import io
import logging
import os
from typing import (
    Any,
    ClassVar,
    Coroutine,
    Dict,
    Iterable,
    List,
    Literal,
    NamedTuple,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Type,
    TypeVar,
    Union,
)
from urllib.parse import quote as _uriquote

import aiohttp
from multidict import CIMultiDict

from . import __version__
from .errors import HTTPException, RateLimited, Forbidden, NotFound, LoginFailure, DiscordServerError, GatewayNotFound
from .file import File
from .gateway import DiscordClientWebSocketResponse
from .mentions import AllowedMentions
from .utils import (
    MISSING,
    _from_json,
    _to_json,
    snowflake_time,
    utcnow,
)

_log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self

    from .embeds import Embed
    from .flags import MessageFlags
    from .impersonate import Impersonate
    from .message import Attachment
    from .poll import Poll

    from .types import (
        billing,
        channel,
        commands,
        connections,
        entitlements,
        game_invite,
        guild,
        harvest,
        invite,
        lobby,
        member,
        message,
        oauth2,
        presences,
        settings,
        subscription,
        template,
        user,
        widget,
    )
    from .types.snowflake import Snowflake, SnowflakeList

    T = TypeVar('T')
    BE = TypeVar('BE', bound=BaseException)
    Response = Coroutine[Any, Any, T]


async def json_or_text(response: aiohttp.ClientResponse) -> Union[Dict[str, Any], str]:
    text = await response.text(encoding='utf-8')
    try:
        if response.headers['content-type'] == 'application/json':
            return _from_json(text)
    except KeyError:
        # Thanks Cloudflare
        pass

    return text


class MultipartParameters(NamedTuple):
    payload: Optional[Dict[str, Any]]
    multipart: Optional[List[Dict[str, Any]]]
    files: Optional[Sequence[File]]

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BE]],
        exc: Optional[BE],
        traceback: Optional[TracebackType],
    ) -> None:
        if self.files:
            for file in self.files:
                file.close()


def handle_message_parameters(
    content: Optional[str] = MISSING,
    *,
    username: str = MISSING,
    avatar_url: Any = MISSING,
    tts: bool = MISSING,
    nonce: Optional[Union[int, str]] = None,
    flags: MessageFlags = MISSING,
    file: File = MISSING,
    files: Sequence[File] = MISSING,
    embed: Optional[Embed] = MISSING,
    embeds: Sequence[Embed] = MISSING,
    attachments: Sequence[Union[Attachment, File]] = MISSING,
    # view: Optional[View] = MISSING,
    allowed_mentions: Optional[AllowedMentions] = MISSING,
    message_reference: Optional[message.MessageReference] = MISSING,
    stickers: Optional[SnowflakeList] = MISSING,
    previous_allowed_mentions: Optional[AllowedMentions] = None,
    mention_author: Optional[bool] = None,
    thread_name: str = MISSING,
    channel_payload: Dict[str, Any] = MISSING,
    applied_tags: Optional[SnowflakeList] = MISSING,
    poll: Optional[Poll] = MISSING,
    metadata: Optional[Dict[str, str]] = MISSING,
) -> MultipartParameters:
    if files is not MISSING and file is not MISSING:
        raise TypeError('Cannot mix file and files keyword arguments.')
    if embeds is not MISSING and embed is not MISSING:
        raise TypeError('Cannot mix embed and embeds keyword arguments.')

    if file is not MISSING:
        files = [file]

    if attachments is not MISSING and files is not MISSING:
        raise TypeError('Cannot mix attachments and files keyword arguments.')

    payload = {}
    if embeds is not MISSING:
        if len(embeds) > 10:
            raise ValueError('embeds has a maximum of 10 elements.')
        payload['embeds'] = [e.to_dict() for e in embeds]

    if embed is not MISSING:
        if embed is None:
            payload['embeds'] = []
        else:
            payload['embeds'] = [embed.to_dict()]

    if content is not MISSING:
        if content is not None:
            payload['content'] = str(content)
        else:
            payload['content'] = None

    # if view is not MISSING:
    #     if view is not None:
    #         payload['components'] = view.to_components()
    #     else:
    #         payload['components'] = []

    if nonce is not None:
        payload['nonce'] = str(nonce)
        payload['enforce_nonce'] = True

    if message_reference is not MISSING:
        payload['message_reference'] = message_reference

    if stickers is not MISSING:
        if stickers is not None:
            payload['sticker_ids'] = stickers
        else:
            payload['sticker_ids'] = []

    if tts is not MISSING:
        payload['tts'] = tts

    if avatar_url:
        payload['avatar_url'] = str(avatar_url)
    if username:
        payload['username'] = username

    if flags is not MISSING:
        payload['flags'] = flags.value

    if thread_name is not MISSING:
        payload['thread_name'] = thread_name

    if allowed_mentions:
        if previous_allowed_mentions is not None:
            payload['allowed_mentions'] = previous_allowed_mentions.merge(allowed_mentions).to_dict()
        else:
            payload['allowed_mentions'] = allowed_mentions.to_dict()
    elif previous_allowed_mentions is not None:
        payload['allowed_mentions'] = previous_allowed_mentions.to_dict()

    if mention_author is not None:
        if 'allowed_mentions' not in payload:
            payload['allowed_mentions'] = AllowedMentions().to_dict()
        payload['allowed_mentions']['replied_user'] = mention_author

    if attachments is MISSING:
        attachments = files
    else:
        files = [a for a in attachments if isinstance(a, File)]

    if attachments is not MISSING:
        file_index = 0
        attachments_payload = []
        for attachment in attachments:
            if isinstance(attachment, File):
                attachments_payload.append(attachment.to_dict(file_index))
                file_index += 1
            else:
                attachments_payload.append(attachment.to_dict())

        payload['attachments'] = attachments_payload

    if applied_tags is not MISSING:
        if applied_tags is not None:
            payload['applied_tags'] = applied_tags
        else:
            payload['applied_tags'] = []

    if poll not in (MISSING, None):
        payload['poll'] = poll._to_dict()

    if metadata is not MISSING:
        payload['metadata'] = metadata

    if channel_payload is not MISSING:
        payload = {
            'message': payload,
        }
        payload.update(channel_payload)

    multipart = []
    if files:
        multipart.append({'name': 'payload_json', 'value': _to_json(payload)})
        payload = None
        for index, file in enumerate(files):
            multipart.append(
                {
                    'name': f'files[{index}]',
                    'value': file.fp,
                    'filename': file.filename,
                    'content_type': 'application/octet-stream',
                }
            )

    return MultipartParameters(payload=payload, multipart=multipart, files=files)


INTERNAL_API_VERSION: int = 9


def _set_api_version(value: int):
    global INTERNAL_API_VERSION

    if not isinstance(value, int):
        raise TypeError(f'expected int not {value.__class__.__name__}')

    if value not in (9, 10):
        raise ValueError(f'expected either 9 or 10 not {value}')

    INTERNAL_API_VERSION = value
    Route.BASE = f'https://gaming-sdk.com/api/v{value}'


class Route:
    BASE: ClassVar[str] = 'https://gaming-sdk.com/api/v9'

    def __init__(self, method: str, path: str, *, metadata: Optional[str] = None, **parameters: Any) -> None:
        self.path: str = path
        self.method: str = method
        # Metadata is a special string used to differentiate between known sub rate limits
        # Since these can't be handled generically, this is the next best way to do so.
        self.metadata: Optional[str] = metadata
        url = self.BASE + self.path
        if parameters:
            url = url.format_map({k: _uriquote(v, safe='') if isinstance(v, str) else v for k, v in parameters.items()})
        self.url: str = url

        # major parameters:
        self.channel_id: Optional[Snowflake] = parameters.get('channel_id')
        self.guild_id: Optional[Snowflake] = parameters.get('guild_id')
        self.webhook_id: Optional[Snowflake] = parameters.get('webhook_id')
        self.webhook_token: Optional[str] = parameters.get('webhook_token')

    @property
    def key(self) -> str:
        """The bucket key is used to represent the route in various mappings."""
        if self.metadata:
            return f'{self.method} {self.path}:{self.metadata}'
        return f'{self.method} {self.path}'

    @property
    def major_parameters(self) -> str:
        """Returns the major parameters formatted a string.

        This needs to be appended to a bucket hash to constitute as a full rate limit key.
        """
        return '+'.join(
            str(k) for k in (self.channel_id, self.guild_id, self.webhook_id, self.webhook_token) if k is not None
        )


class Ratelimit:
    """Represents a Discord rate limit.

    This is similar to a semaphore except tailored to Discord's rate limits. This is aware of
    the expiry of a token window, along with the number of tokens available. The goal of this
    design is to increase throughput of requests being sent concurrently rather than forcing
    everything into a single lock queue per route.
    """

    __slots__ = (
        'limit',
        'remaining',
        'outgoing',
        'reset_after',
        'expires',
        'dirty',
        '_last_request',
        '_max_ratelimit_timeout',
        '_loop',
        '_pending_requests',
        '_sleeping',
    )

    def __init__(self, max_ratelimit_timeout: Optional[float]) -> None:
        self.limit: int = 1
        self.remaining: int = self.limit
        self.outgoing: int = 0
        self.reset_after: float = 0.0
        self.expires: Optional[float] = None
        self.dirty: bool = False
        self._max_ratelimit_timeout: Optional[float] = max_ratelimit_timeout
        self._loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        self._pending_requests: deque[asyncio.Future[Any]] = deque()
        # Only a single rate limit object should be sleeping at a time.
        # The object that is sleeping is ultimately responsible for freeing the semaphore
        # for the requests currently pending.
        self._sleeping: asyncio.Lock = asyncio.Lock()
        self._last_request: float = self._loop.time()

    def __repr__(self) -> str:
        return (
            f'<RateLimitBucket limit={self.limit} remaining={self.remaining} pending_requests={len(self._pending_requests)}>'
        )

    def reset(self):
        self.remaining = self.limit - self.outgoing
        self.expires = None
        self.reset_after = 0.0
        self.dirty = False

    def update(self, response: aiohttp.ClientResponse, *, use_clock: bool = False) -> None:
        headers = response.headers
        self.limit = int(headers.get('X-Ratelimit-Limit', 1))

        if self.dirty:
            self.remaining = min(int(headers.get('X-Ratelimit-Remaining', 0)), self.limit - self.outgoing)
        else:
            self.remaining = int(headers.get('X-Ratelimit-Remaining', 0))
            self.dirty = True

        reset_after = headers.get('X-Ratelimit-Reset-After')
        if use_clock or not reset_after:
            utc = datetime.timezone.utc
            now = datetime.datetime.now(utc)
            reset = datetime.datetime.fromtimestamp(float(headers['X-Ratelimit-Reset']), utc)
            self.reset_after = (reset - now).total_seconds()
        else:
            self.reset_after = float(reset_after)

        self.expires = self._loop.time() + self.reset_after

    def _wake_next(self) -> None:
        while self._pending_requests:
            future = self._pending_requests.popleft()
            if not future.done():
                future.set_result(None)
                break

    def _wake(self, count: int = 1, *, exception: Optional[RateLimited] = None) -> None:
        awaken = 0
        while self._pending_requests:
            future = self._pending_requests.popleft()
            if not future.done():
                if exception:
                    future.set_exception(exception)
                else:
                    future.set_result(None)
                awaken += 1

            if awaken >= count:
                break

    async def _refresh(self) -> None:
        error = self._max_ratelimit_timeout and self.reset_after > self._max_ratelimit_timeout
        exception = RateLimited(self.reset_after) if error else None
        async with self._sleeping:
            if not error:
                await asyncio.sleep(self.reset_after)

        self.reset()
        self._wake(self.remaining, exception=exception)

    def is_expired(self) -> bool:
        return self.expires is not None and self._loop.time() > self.expires

    def is_inactive(self) -> bool:
        delta = self._loop.time() - self._last_request
        return delta >= 300 and self.outgoing == 0 and len(self._pending_requests) == 0

    async def acquire(self) -> None:
        self._last_request = self._loop.time()
        if self.is_expired():
            self.reset()

        if self._max_ratelimit_timeout is not None and self.expires is not None:
            # Check if we can pre-emptively block this request for having too large of a timeout
            current_reset_after = self.expires - self._loop.time()
            if current_reset_after > self._max_ratelimit_timeout:
                raise RateLimited(current_reset_after)

        while self.remaining <= 0:
            future = self._loop.create_future()
            self._pending_requests.append(future)
            try:
                await future
            except:
                future.cancel()
                if self.remaining > 0 and not future.cancelled():
                    self._wake_next()
                raise

        self.remaining -= 1
        self.outgoing += 1

    async def __aenter__(self) -> Self:
        await self.acquire()
        return self

    async def __aexit__(self, type: Type[BE], value: BE, traceback: TracebackType) -> None:
        self.outgoing -= 1
        tokens = self.remaining - self.outgoing
        # Check whether the rate limit needs to be pre-emptively slept on
        # Note that this is a Lock to prevent multiple rate limit objects from sleeping at once
        if not self._sleeping.locked():
            if tokens <= 0:
                await self._refresh()
            elif self._pending_requests:
                exception = (
                    RateLimited(self.reset_after)
                    if self._max_ratelimit_timeout and self.reset_after > self._max_ratelimit_timeout
                    else None
                )
                self._wake(tokens, exception=exception)


# For some reason, the Discord voice websocket expects this header to be
# completely lowercase while aiohttp respects spec and does it as case-insensitive
aiohttp.hdrs.WEBSOCKET = 'websocket'  # type: ignore


class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Discord API."""

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        connector: Optional[aiohttp.BaseConnector] = None,
        *,
        impersonate: Impersonate,
        proxy: Optional[str] = None,
        proxy_auth: Optional[aiohttp.BasicAuth] = None,
        unsync_clock: bool = True,
        http_trace: Optional[aiohttp.TraceConfig] = None,
        max_ratelimit_timeout: Optional[float] = None,
    ) -> None:
        self.loop: asyncio.AbstractEventLoop = loop
        self.connector: aiohttp.BaseConnector = connector or MISSING
        self.__session: aiohttp.ClientSession = MISSING  # filled in static_login
        # Route key -> Bucket hash
        self._bucket_hashes: Dict[str, str] = {}
        # Bucket Hash + Major Parameters -> Rate limit
        # or
        # Route key + Major Parameters -> Rate limit
        # When the key is the latter, it is used for temporary
        # one shot requests that don't have a bucket hash
        # When this reaches 256 elements, it will try to evict based off of expiry
        self._buckets: Dict[str, Ratelimit] = {}
        self._global_over: asyncio.Event = MISSING
        self.token: Optional[str] = None
        self.proxy: Optional[str] = proxy
        self.proxy_auth: Optional[aiohttp.BasicAuth] = proxy_auth
        self.http_trace: Optional[aiohttp.TraceConfig] = http_trace
        self.use_clock: bool = not unsync_clock
        self.max_ratelimit_timeout: Optional[float] = max(30.0, max_ratelimit_timeout) if max_ratelimit_timeout else None
        self.impersonate: Impersonate = impersonate

    def clear(self) -> None:
        if self.__session and self.__session.closed:
            self.__session = MISSING

    async def ws_connect(
        self, url: str, *, compress: int = 0, params: Optional[Dict[str, Any]] = None
    ) -> aiohttp.ClientWebSocketResponse:

        initial_headers = self.impersonate.get_websocket_initial_headers()
        if isawaitable(initial_headers):
            initial_headers = await initial_headers

        headers: CIMultiDict[str] = CIMultiDict(initial_headers)
        if 'User-Agent' not in headers:
            user_agent = self.impersonate.get_websocket_user_agent()
            if isawaitable(user_agent):
                user_agent = await user_agent
            headers['User-Agent'] = user_agent

        kwargs = {
            'proxy_auth': self.proxy_auth,
            'proxy': self.proxy,
            'max_msg_size': 0,
            'timeout': 30.0,
            'autoclose': False,
            'headers': headers,
            'compress': compress,
        }

        if params is not None:
            kwargs['params'] = params

        return await self.__session.ws_connect(url, **kwargs)

    def _try_clear_expired_ratelimits(self) -> None:
        if len(self._buckets) < 256:
            return

        keys = [key for key, bucket in self._buckets.items() if bucket.is_inactive()]
        for key in keys:
            del self._buckets[key]

    def get_ratelimit(self, key: str) -> Ratelimit:
        try:
            value = self._buckets[key]
        except KeyError:
            self._buckets[key] = value = Ratelimit(self.max_ratelimit_timeout)
            self._try_clear_expired_ratelimits()
        return value

    async def request(
        self,
        route: Route,
        *,
        files: Optional[Sequence[File]] = None,
        form: Optional[Iterable[Dict[str, Any]]] = None,
        **kwargs: Any,
    ) -> Any:
        method = route.method
        url = route.url
        route_key = route.key

        bucket_hash = None
        try:
            bucket_hash = self._bucket_hashes[route_key]
        except KeyError:
            key = f'{route_key}:{route.major_parameters}'
        else:
            key = f'{bucket_hash}:{route.major_parameters}'

        ratelimit = self.get_ratelimit(key)

        # header creation

        initial_headers = self.impersonate.get_http_initial_headers()
        if isawaitable(initial_headers):
            initial_headers = await initial_headers

        headers: CIMultiDict[str] = CIMultiDict(initial_headers)
        if 'User-Agent' not in headers:
            user_agent = self.impersonate.get_http_user_agent()
            if isawaitable(user_agent):
                user_agent = await user_agent
            headers['User-Agent'] = user_agent

        if 'X-Super-Properties' not in headers:
            xsp = self.impersonate.get_client_properties_base64()
            if isawaitable(xsp):
                xsp = await xsp

            if xsp is not None:
                headers['X-Super-Properties'] = xsp

        supplemental_headers = kwargs.pop('supplemental_headers', None)
        if supplemental_headers:
            headers.update(supplemental_headers)

        if self.token is not None:
            headers['Authorization'] = 'Bearer ' + self.token
        # some checking if it's a JSON request
        if 'json' in kwargs:
            headers['Content-Type'] = 'application/json'
            kwargs['data'] = _to_json(kwargs.pop('json'))

        try:
            reason = kwargs.pop('reason')
        except KeyError:
            pass
        else:
            if reason:
                headers['X-Audit-Log-Reason'] = _uriquote(reason, safe='/ ')

        kwargs['headers'] = headers

        # Proxy support
        if self.proxy is not None:
            kwargs['proxy'] = self.proxy
        if self.proxy_auth is not None:
            kwargs['proxy_auth'] = self.proxy_auth

        if not self._global_over.is_set():
            # wait until the global lock is complete
            await self._global_over.wait()

        response: Optional[aiohttp.ClientResponse] = None
        data: Optional[Union[Dict[str, Any], str]] = None
        async with ratelimit:
            for tries in range(5):
                if files:
                    for f in files:
                        f.reset(seek=tries)

                if form:
                    # with quote_fields=True '[' and ']' in file field names are escaped, which discord does not support
                    form_data = aiohttp.FormData(quote_fields=False)
                    for params in form:
                        form_data.add_field(**params)
                    kwargs['data'] = form_data

                try:
                    async with self.__session.request(method, url, **kwargs) as response:
                        _log.debug('%s %s with %s has returned %s', method, url, kwargs.get('data'), response.status)

                        # even errors have text involved in them so this is safe to call
                        data = await json_or_text(response)

                        # Update and use rate limit information if the bucket header is present
                        discord_hash = response.headers.get('X-Ratelimit-Bucket')
                        # I am unsure if X-Ratelimit-Bucket is always available
                        # However, X-Ratelimit-Remaining has been a consistent cornerstone that worked
                        has_ratelimit_headers = 'X-Ratelimit-Remaining' in response.headers
                        if discord_hash is not None:
                            # If the hash Discord has provided is somehow different from our current hash something changed
                            if bucket_hash != discord_hash:
                                if bucket_hash is not None:
                                    # If the previous hash was an actual Discord hash then this means the
                                    # hash has changed sporadically.
                                    # This can be due to two reasons
                                    # 1. It's a sub-ratelimit which is hard to handle
                                    # 2. The rate limit information genuinely changed
                                    # There is no good way to discern these, Discord doesn't provide a way to do so.
                                    # At best, there will be some form of logging to help catch it.
                                    # Alternating sub-ratelimits means that the requests oscillate between
                                    # different underlying rate limits -- this can lead to unexpected 429s
                                    # It is unavoidable.
                                    fmt = 'A route (%s) has changed hashes: %s -> %s.'
                                    _log.debug(fmt, route_key, bucket_hash, discord_hash)

                                    self._bucket_hashes[route_key] = discord_hash
                                    recalculated_key = discord_hash + route.major_parameters
                                    self._buckets[recalculated_key] = ratelimit
                                    self._buckets.pop(key, None)
                                elif route_key not in self._bucket_hashes:
                                    fmt = '%s has found its initial rate limit bucket hash (%s).'
                                    _log.debug(fmt, route_key, discord_hash)
                                    self._bucket_hashes[route_key] = discord_hash
                                    self._buckets[discord_hash + route.major_parameters] = ratelimit

                        if has_ratelimit_headers:
                            if response.status != 429:
                                ratelimit.update(response, use_clock=self.use_clock)
                                if ratelimit.remaining == 0:
                                    _log.debug(
                                        'A rate limit bucket (%s) has been exhausted. Pre-emptively rate limiting...',
                                        discord_hash or route_key,
                                    )

                        # the request was successful so just return the text/json
                        if 300 > response.status >= 200:
                            _log.debug('%s %s has received %s', method, url, data)
                            return data

                        # we are being rate limited
                        if response.status == 429:
                            if not response.headers.get('Via') or isinstance(data, str):
                                # Banned by Cloudflare more than likely.
                                raise HTTPException(response, data)

                            if ratelimit.remaining > 0:
                                # According to night
                                # https://github.com/discord/discord-api-docs/issues/2190#issuecomment-816363129
                                # Remaining > 0 and 429 means that a sub ratelimit was hit.
                                # It is unclear what should happen in these cases other than just using the retry_after
                                # value in the body.
                                _log.debug(
                                    '%s %s received a 429 despite having %s remaining requests. This is a sub-ratelimit.',
                                    method,
                                    url,
                                    ratelimit.remaining,
                                )

                            retry_after: float = data['retry_after']
                            if self.max_ratelimit_timeout and retry_after > self.max_ratelimit_timeout:
                                _log.warning(
                                    'We are being rate limited. %s %s responded with 429. Timeout of %.2f was too long, erroring instead.',
                                    method,
                                    url,
                                    retry_after,
                                )
                                raise RateLimited(retry_after)

                            fmt = 'We are being rate limited. %s %s responded with 429. Retrying in %.2f seconds.'
                            _log.warning(fmt, method, url, retry_after)

                            _log.debug(
                                'Rate limit is being handled by bucket hash %s with %r major parameters',
                                bucket_hash,
                                route.major_parameters,
                            )

                            # check if it's a global rate limit
                            is_global = data.get('global', False)
                            if is_global:
                                _log.warning('Global rate limit has been hit. Retrying in %.2f seconds.', retry_after)
                                self._global_over.clear()

                            await asyncio.sleep(retry_after)
                            _log.debug('Done sleeping for the rate limit. Retrying...')

                            # release the global lock now that the
                            # global rate limit has passed
                            if is_global:
                                self._global_over.set()
                                _log.debug('Global rate limit is now over.')

                            continue

                        # we've received a 500, 502, 504, or 524, unconditional retry
                        if response.status in {500, 502, 504, 524}:
                            await asyncio.sleep(1 + tries * 2)
                            continue

                        # the usual error cases
                        if response.status == 403:
                            raise Forbidden(response, data)
                        elif response.status == 404:
                            raise NotFound(response, data)
                        elif response.status >= 500:
                            raise DiscordServerError(response, data)
                        else:
                            raise HTTPException(response, data)

                # This is handling exceptions from the request
                except OSError as e:
                    # Connection reset by peer
                    if tries < 4 and e.errno in (54, 10054):
                        await asyncio.sleep(1 + tries * 2)
                        continue
                    raise

            if response is not None:
                # We've run out of retries, raise.
                if response.status >= 500:
                    raise DiscordServerError(response, data)

                raise HTTPException(response, data)

            raise RuntimeError('Unreachable code in HTTP handling')

    async def get_from_cdn(self, url: str) -> bytes:
        kwargs = {}

        # Proxy support
        if self.proxy is not None:
            kwargs['proxy'] = self.proxy
        if self.proxy_auth is not None:
            kwargs['proxy_auth'] = self.proxy_auth

        async with self.__session.get(url, **kwargs) as resp:
            if resp.status == 200:
                return await resp.read()
            elif resp.status == 404:
                raise NotFound(resp, 'asset not found')
            elif resp.status == 403:
                raise Forbidden(resp, 'cannot retrieve asset')
            else:
                raise HTTPException(resp, 'failed to get asset')

        raise RuntimeError('Unreachable')

    async def get_preferred_voice_regions(self) -> List[guild.RTCRegion]:
        initial_headers = self.impersonate.get_http_initial_headers()
        if isawaitable(initial_headers):
            initial_headers = await initial_headers

        headers: CIMultiDict[str] = CIMultiDict(initial_headers)
        if 'User-Agent' not in headers:
            user_agent = self.impersonate.get_http_user_agent()
            if isawaitable(user_agent):
                user_agent = await user_agent
            headers['User-Agent'] = user_agent

        async with self.__session.get('https://latency.media.gaming-sdk.com/rtc', headers=headers) as resp:
            if resp.status == 200:
                return await resp.json()
            elif resp.status == 404:
                raise NotFound(resp, 'RTC regions not found')
            elif resp.status == 403:
                raise Forbidden(resp, 'Cannot retrieve rtc regions')
            else:
                raise HTTPException(resp, 'Failed to get rtc regions')

    # state management

    async def close(self) -> None:
        if self.__session:
            await self.__session.close()

    # login management

    async def startup(self) -> None:
        # Necessary to get aiohttp to stop complaining about session creation
        if self.__session is not MISSING:
            return

        if self.connector is MISSING:
            self.connector = aiohttp.TCPConnector(limit=0)

        self.__session = aiohttp.ClientSession(
            connector=self.connector,
            ws_response_class=DiscordClientWebSocketResponse,
            trace_configs=None if self.http_trace is None else [self.http_trace],
            cookie_jar=aiohttp.DummyCookieJar(),
        )
        self._global_over = asyncio.Event()
        self._global_over.set()

    async def static_login(self, token: str) -> user.User:
        await self.startup()

        old_token = self.token
        self.token = token

        try:
            data = await self.get_me()
        except HTTPException as exc:
            self.token = old_token
            if exc.status == 401:
                raise LoginFailure('Improper token has been passed.') from exc
            raise

        return data

    # Authentication

    def get_fingerprint(self) -> Response[Dict[Literal['fingerprint'], str]]:
        return self.request(Route('GET', '/auth/fingerprint'))

    def get_current_authorization_information(
        self,
    ) -> Response[oauth2.GetCurrentAuthorizationInformationResponseBody]:
        return self.request(Route('GET', '/oauth2/@me'))

    def get_openid_connect_keys(self) -> Response[List[Any]]:
        return self.request(Route('GET', '/oauth2/keys'))

    def get_openid_user_information(self) -> Response[oauth2.GetOpenIDUserInformationResponseBody]:
        return self.request(Route('GET', '/oauth2/userinfo'))

    def get_oauth2_device_code(
        self, payload: oauth2.GetOAuth2DeviceCodeRequestBody
    ) -> Response[oauth2.GetOAuth2DeviceCodeResponseBody]:
        return self.request(Route('POST', '/oauth2/authorize/device'), data=aiohttp.FormData(payload))

    def get_oauth2_token(self, payload: oauth2.GetOAuth2TokenRequestBody) -> Response[oauth2.OAuth2AccessToken]:
        return self.request(Route('POST', '/oauth2/token'), data=aiohttp.FormData(payload))

    def revoke_oauth2_token(self, payload: oauth2.RevokeOAuth2TokenRequestBody) -> Response[None]:
        return self.request(Route('POST', '/oauth2/token/revoke'), data=aiohttp.FormData(payload))

    def get_provisional_account_token(
        self,
        payload: oauth2.GetProvisionalAccountTokenRequestBody,
    ) -> Response[oauth2.OAuth2AccessToken]:
        return self.request(Route('POST', '/partner-sdk/token'), json=payload)

    def unmerge_provisional_account(
        self,
        payload: oauth2.UnmergeProvisionalAccountRequestBody,
    ) -> Response[None]:
        return self.request(Route('POST', '/partner-sdk/provisional-accounts/unmerge'), json=payload)

    # Self user

    def get_me(self) -> Response[user.User]:
        return self.request(Route('GET', '/users/@me'))

    def get_guild_me(self, guild_id: Snowflake) -> Response[member.Member]:
        return self.request(Route('GET', '/users/@me/guilds/{guild_id}/member', guild_id=guild_id))

    def modify_audio_settings(
        self,
        context: settings.AudioContext,
        target_id: int,  # Currently called user_id on backend, but who knows...
        /,
        **payload,
    ) -> Response[None]:
        # This endpoint fails with invalid JSON string if payload is empty?
        route = Route(
            'PATCH',
            '/users/@me/audio-settings/{context}/{target_id}',
            context=context,
            target_id=target_id,
        )
        return self.request(route, json=payload)

    # Group functionality

    # def start_group(self, user_id: Snowflake, recipients: List[int]) -> Response[channel.GroupDMChannel]:
    #     payload = {
    #         'recipients': recipients,
    #     }

    #     return self.request(Route('POST', '/users/{user_id}/channels', user_id=user_id), json=payload)

    def get_linked_accounts(
        self,
        channel_id: Snowflake,
        *,
        user_ids: Optional[List[Snowflake]] = None,
    ) -> Response[channel.LinkedAccounts]:
        params = {}
        if user_ids is not None:
            params['user_ids'] = user_ids
        route = Route('GET', '/channels/{channel_id}/linked-accounts', channel_id=channel_id)
        return self.request(route, params=params)

    # Message management

    def start_private_message(self, user_id: Snowflake) -> Response[channel.DMChannel]:
        return self.request(Route('GET', '/users/@me/dms/{user_id}', user_id=user_id))

    def send_lobby_message(
        self,
        lobby_id: Snowflake,
        params: MultipartParameters,
    ) -> Response[message.Message]:
        r = Route('POST', '/lobbies/{lobby_id}/messages', lobby_id=lobby_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def send_user_message(
        self,
        user_id: Snowflake,
        params: MultipartParameters,
    ) -> Response[message.Message]:
        r = Route('POST', '/users/{user_id}/messages', user_id=user_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def send_message(
        self,
        channel_id: Snowflake,
        params: MultipartParameters,
    ) -> Response[message.Message]:
        r = Route('POST', '/channels/{channel_id}/messages', channel_id=channel_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def send_typing(self, channel_id: Snowflake) -> Response[None]:
        return self.request(Route('POST', '/channels/{channel_id}/typing', channel_id=channel_id))

    def delete_message(
        self, channel_id: Snowflake, message_id: Snowflake, *, reason: Optional[str] = None
    ) -> Response[None]:
        # Special case certain sub-rate limits
        # https://github.com/discord/discord-api-docs/issues/1092
        # https://github.com/discord/discord-api-docs/issues/1295
        difference = utcnow() - snowflake_time(int(message_id))
        metadata: Optional[str] = None
        if difference <= datetime.timedelta(seconds=10):
            metadata = 'sub-10-seconds'
        elif difference >= datetime.timedelta(days=14):
            metadata = 'older-than-two-weeks'
        r = Route(
            'DELETE',
            '/channels/{channel_id}/messages/{message_id}',
            channel_id=channel_id,
            message_id=message_id,
            metadata=metadata,
        )
        return self.request(r, reason=reason)

    def delete_user_message(
        self, user_id: Snowflake, message_id: Snowflake, *, reason: Optional[str] = None
    ) -> Response[None]:
        # Special case certain sub-rate limits
        # https://github.com/discord/discord-api-docs/issues/1092
        # https://github.com/discord/discord-api-docs/issues/1295
        difference = utcnow() - snowflake_time(int(message_id))
        metadata: Optional[str] = None
        if difference <= datetime.timedelta(seconds=10):
            metadata = 'sub-10-seconds'
        elif difference >= datetime.timedelta(days=14):
            metadata = 'older-than-two-weeks'
        r = Route(
            'DELETE',
            '/users/{user_id}/messages/{message_id}',
            user_id=user_id,
            message_id=message_id,
            metadata=metadata,
        )
        return self.request(r, reason=reason)

    def edit_user_message(
        self, user_id: Snowflake, message_id: Snowflake, *, params: MultipartParameters
    ) -> Response[message.Message]:
        r = Route('PATCH', '/users/{user_id}/messages/{message_id}', user_id=user_id, message_id=message_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def edit_message(
        self, channel_id: Snowflake, message_id: Snowflake, *, params: MultipartParameters
    ) -> Response[message.Message]:
        r = Route('PATCH', '/channels/{channel_id}/messages/{message_id}', channel_id=channel_id, message_id=message_id)
        if params.files:
            return self.request(r, files=params.files, form=params.multipart)
        else:
            return self.request(r, json=params.payload)

    def get_message(self, channel_id: Snowflake, message_id: Snowflake) -> Response[message.Message]:
        r = Route('GET', '/channels/{channel_id}/messages/{message_id}', channel_id=channel_id, message_id=message_id)
        return self.request(r)

    def logs_from(
        self,
        channel_id: Snowflake,
        limit: int,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        around: Optional[Snowflake] = None,
    ) -> Response[List[message.Message]]:
        params: Dict[str, Any] = {
            'limit': limit,
        }

        if before is not None:
            params['before'] = before
        if after is not None:
            params['after'] = after
        if around is not None:
            params['around'] = around

        return self.request(Route('GET', '/channels/{channel_id}/messages', channel_id=channel_id), params=params)

    def edit_profile(self, payload: Dict[str, Any]) -> Response[user.User]:
        return self.request(Route('PATCH', '/users/@me/account'), json=payload)

    # Guild management

    def get_guilds(
        self,
        limit: int,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        with_counts: bool = True,
    ) -> Response[List[guild.Guild]]:
        params: Dict[str, Any] = {
            'limit': limit,
            'with_counts': int(with_counts),
        }

        if before:
            params['before'] = before
        if after:
            params['after'] = after

        return self.request(Route('GET', '/users/@me/guilds'), params=params)

    def get_template(self, code: str) -> Response[template.Template]:
        return self.request(Route('GET', '/guilds/templates/{code}', code=code))

    def get_all_guild_channels(self, guild_id: Snowflake) -> Response[List[guild.GuildChannel]]:
        return self.request(Route('GET', '/guilds/{guild_id}/channels', guild_id=guild_id))

    def get_widget(self, guild_id: Snowflake) -> Response[widget.Widget]:
        return self.request(Route('GET', '/guilds/{guild_id}/widget.json', guild_id=guild_id))

    # Invite management

    def get_invite(
        self,
        invite_id: str,
        *,
        with_counts: bool = True,
        guild_scheduled_event_id: Optional[Snowflake] = None,
    ) -> Response[invite.Invite]:
        params: Dict[str, Any] = {
            'with_counts': int(with_counts),
        }

        if guild_scheduled_event_id:
            params['guild_scheduled_event_id'] = guild_scheduled_event_id

        return self.request(Route('GET', '/invites/{invite_id}', invite_id=invite_id), params=params)

    # Application commands
    # TODO: Global app commands (excluding deleting and editing ofc)

    def get_guild_application_commands(
        self, application_id: Snowflake, guild_id: Snowflake
    ) -> Response[List[commands.ApplicationCommand]]:
        r = Route(
            'GET',
            '/applications/{application_id}/guilds/{guild_id}/commands',
            application_id=application_id,
            guild_id=guild_id,
        )
        return self.request(r)

    def get_guild_application_command(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
        command_id: Snowflake,
    ) -> Response[commands.ApplicationCommand]:
        r = Route(
            'GET',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
            application_id=application_id,
            guild_id=guild_id,
            command_id=command_id,
        )
        return self.request(r)

    def create_guild_application_command(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
        payload: commands.ApplicationCommandCreateRequestBody,
    ) -> Response[commands.ApplicationCommand]:
        r = Route(
            'POST',
            '/applications/{application_id}/guilds/{guild_id}/commands',
            application_id=application_id,
            guild_id=guild_id,
        )
        return self.request(r, json=payload)

    def edit_guild_command(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
        command_id: Snowflake,
        payload: commands.ApplicationCommandUpdateRequestBody,
    ) -> Response[commands.ApplicationCommand]:
        r = Route(
            'PATCH',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
            application_id=application_id,
            guild_id=guild_id,
            command_id=command_id,
        )
        return self.request(r, json=payload)

    def delete_guild_application_command(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
        command_id: Snowflake,
    ) -> Response[None]:
        r = Route(
            'DELETE',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}',
            application_id=application_id,
            guild_id=guild_id,
            command_id=command_id,
        )
        return self.request(r)

    def bulk_upsert_guild_application_commands(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
        payload: List[commands.UpdateApplicationCommand],
    ) -> Response[List[commands.ApplicationCommand]]:
        r = Route(
            'PUT',
            '/applications/{application_id}/guilds/{guild_id}/commands',
            application_id=application_id,
            guild_id=guild_id,
        )
        return self.request(r, json=payload)

    def get_guild_application_commands_permissions(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
    ) -> Response[List[commands.GuildApplicationCommandPermissions]]:
        r = Route(
            'GET',
            '/applications/{application_id}/guilds/{guild_id}/commands/permissions',
            application_id=application_id,
            guild_id=guild_id,
        )
        return self.request(r)

    def get_guild_application_command_permissions(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
        command_id: Snowflake,
    ) -> Response[commands.GuildApplicationCommandPermissions]:
        r = Route(
            'GET',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=application_id,
            guild_id=guild_id,
            command_id=command_id,
        )
        return self.request(r)

    def edit_application_command_permissions(
        self,
        application_id: Snowflake,
        guild_id: Snowflake,
        command_id: Snowflake,
        payload: Dict[str, Any],
    ) -> Response[None]:
        r = Route(
            'PUT',
            '/applications/{application_id}/guilds/{guild_id}/commands/{command_id}/permissions',
            application_id=application_id,
            guild_id=guild_id,
            command_id=command_id,
        )
        return self.request(r, json=payload)

    # SKU

    def get_application_entitlements(
        self,
        application_id: Snowflake,
        *,
        user_id: Optional[Snowflake] = None,
        sku_ids: Optional[List[Snowflake]] = None,
        guild_id: Optional[Snowflake] = None,
        exclude_ended: Optional[bool] = None,
        exclude_deleted: Optional[bool] = None,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        limit: Optional[int] = None,
    ) -> Response[List[entitlements.Entitlement]]:
        params = {}

        if user_id is not None:
            params['user_id'] = user_id

        if sku_ids is not None:
            params['sku_ids'] = sku_ids

        if guild_id is not None:
            params['guild_id'] = guild_id

        if exclude_ended is not None:
            params['exclude_ended'] = str(exclude_ended).lower()

        if exclude_deleted is not None:
            params['exclude_deleted'] = str(exclude_deleted).lower()

        if before is not None:
            params['before'] = before

        if after is not None:
            params['after'] = after

        if limit is not None:
            params['limit'] = limit

        route = Route(
            'GET',
            '/applications/{application_id}/entitlements',
            application_id=application_id,
        )
        return self.request(route, params=params)

    def get_application_entitlement(
        self,
        application_id: Snowflake,
        entitlement_id: Snowflake,
    ) -> Response[entitlements.Entitlement]:
        route = Route(
            'GET',
            '/applications/{application_id}/entitlements/{entitlement_id}',
            application_id=application_id,
            entitlement_id=entitlement_id,
        )
        return self.request(route)

    def consume_application_entitlement(
        self,
        application_id: Snowflake,
        entitlement_id: Snowflake,
    ) -> Response[None]:
        route = Route(
            'POST',
            '/applications/{application_id}/entitlements/{entitlement_id}/consume',
            application_id=application_id,
            entitlement_id=entitlement_id,
        )
        return self.request(route)

    def delete_application_entitlement(
        self,
        application_id: Snowflake,
        entitlement_id: Snowflake,
    ) -> Response[None]:
        route = Route(
            'DELETE',
            '/applications/{application_id}/entitlements/{entitlement_id}',
            application_id=application_id,
            entitlement_id=entitlement_id,
        )
        return self.request(route)

    def get_gift(
        self, code: str, *, with_application: Optional[bool] = None, with_subscription_plan: Optional[bool] = None
    ) -> Response[entitlements.GiftCode]:
        params = {}

        if with_application is not None:
            params['with_application'] = str(with_application).lower()

        if with_subscription_plan is not None:
            params['with_subscription_plan'] = str(with_subscription_plan).lower()

        route = Route(
            'GET',
            '/entitlements/gift-codes/{gift_code}',
            gift_code=code,
        )
        return self.request(route)

    # Following endpoints work for OAuth2:
    # - GET /applications/{application.id}/entitlements
    # - GET /applications/{application.id}/entitlements/{entitlement.id}
    # - DELETE /applications/{application.id}/entitlements/{entitlement.id}
    # - POST /applications/{application.id}/entitlements/{entitlement.id}/consume
    # - GET /applications/{application.id}/skus
    # - POST /store/skus
    # - GET /oauth2/applications/{application.id}/assets
    # - GET /store/applications/{application.id}/assets
    # - POST /store/applications/{application.id}/assets
    # - DELETE /store/applications/{application.id}/assets/{asset.id}
    # - GET /activities/statistics/applications/{application.id}
    # - GET /activities
    # - GET /applications/{application_id}/manifest-labels
    # - GET /applications/{application_id}/branches
    # - GET /applications/{application_id}/branches/{branch_id}/builds
    # - GET /applications/{application_id}/branches/{branch_id}/builds/{build_id}
    # - GET /applications/{application_id}/branches/{branch_id}/builds/latest
    # - GET /applications/{application_id}/branches/{branch_id}/builds/live
    # - POST /applications/{application_id}/branches/{branch_id}/builds/{build_id}/size
    # - POST /applications/{application_id}/download-signatures
    # - GET /store/listings/{listing.id}
    # - GET /store/published-listings/skus/{sku_id}
    # - GET /store/skus/{sku.id}/listings
    # - GET /store/published-listings/skus
    # - GET /store/published-listings/applications/{application_id}
    # - GET /store/published-listings/applications
    # - POST /store/listings
    # - PATCH /store/listings/{listing.id}
    # - GET /store/skus/{sku.id}
    # - PATCH /store/skus/{sku.id}
    # - GET /store/eulas/{eula.id}
    # - POST /applications/{application.id}/achievements
    # - GET /applications/{application.id}/achievements
    # - GET /applications/{application.id}/achievements/{achievement.id}
    # - PATCH /applications/{application.id}/achievements/{achievement.id}
    # - PUT /users/{user.id}/applications/{application.id}/achievements/{achievement.id}
    # - DELETE /applications/{application.id}/achievements/{achievement.id}
    # - GET /entitlements/gift-codes/{gift.code} (actually unauthenticated)
    # - GET /oauth2/authorize (also unauthenticated)
    # - GET /skus/{sku.id}/subscriptions
    # - GET /skus/{sku.id}/subscriptions/{subscription.id}

    # Subscriptions

    def list_sku_subscriptions(
        self,
        sku_id: Snowflake,
        before: Optional[Snowflake] = None,
        after: Optional[Snowflake] = None,
        limit: Optional[int] = None,
        user_id: Optional[Snowflake] = None,
    ) -> Response[List[subscription.Subscription]]:
        params = {}

        if before is not None:
            params['before'] = before

        if after is not None:
            params['after'] = after

        if limit is not None:
            params['limit'] = limit

        if user_id is not None:
            params['user_id'] = user_id

        return self.request(
            Route(
                'GET',
                '/skus/{sku_id}/subscriptions',
                sku_id=sku_id,
            ),
            params=params,
        )

    def get_sku_subscription(self, sku_id: Snowflake, subscription_id: Snowflake) -> Response[subscription.Subscription]:
        return self.request(
            Route(
                'GET',
                '/skus/{sku_id}/subscriptions/{subscription_id}',
                sku_id=sku_id,
                subscription_id=subscription_id,
            )
        )

    # POST https://gaming-sdk.com/api/v9/oauth2/token
    # No Authorization here
    # Content-Type: application/x-www-form-urlencoded

    # body:

    # client_id=1169421761859833997
    # grant_type=authorization_code
    # code=code
    # redirect_uri=redirectUri
    # code_verifier=codeVerifier
    # external_auth_token=balls
    # external_auth_type=UNITY_SERVICES_ID_TOKEN

    # Calls
    def get_ringability(self, channel_id: Snowflake) -> Response[channel.CallEligibility]:
        return self.request(Route('GET', '/channels/{channel_id}/call', channel_id=channel_id))

    def ring(self, channel_id: Snowflake, *recipients: Snowflake) -> Response[None]:
        payload = {'recipients': recipients or None}
        return self.request(Route('POST', '/channels/{channel_id}/call/ring', channel_id=channel_id), json=payload)

    def stop_ringing(self, channel_id: Snowflake, *recipients: Snowflake) -> Response[None]:
        payload = {'recipients': recipients}
        return self.request(Route('POST', '/channels/{channel_id}/call/stop-ringing', channel_id=channel_id), json=payload)

    def change_call_voice_region(self, channel_id: int, voice_region: str) -> Response[None]:
        payload = {'region': voice_region}
        return self.request(Route('PATCH', '/channels/{channel_id}/call', channel_id=channel_id), json=payload)

    def get_user_harvest(self) -> Response[Optional[Union[Literal[''], harvest.Harvest]]]:
        return self.request(Route('GET', '/users/@me/harvest'))

    def create_user_harvest(self, *, email: str) -> Response[harvest.Harvest]:
        payload = {'email': email}
        return self.request(Route('POST', '/users/@me/harvest'), json=payload)

    # Lobbies
    def create_or_join_lobby(
        self,
        *,
        secret: str,
        lobby_metadata: Optional[Dict[str, str]] = None,
        member_metadata: Optional[Dict[str, str]] = None,
        idle_timeout_seconds: Optional[int] = None,
    ) -> Response[lobby.Lobby]:
        payload = {
            'secret': secret,
            'lobby_metadata': lobby_metadata,
            'member_metadata': member_metadata,
        }
        if idle_timeout_seconds is not None:
            payload['idle_timeout_seconds'] = idle_timeout_seconds

        return self.request(Route('PUT', '/lobbies'), json=payload)

    def leave_lobby(self, lobby_id: Snowflake) -> Response[None]:
        return self.request(Route('DELETE', '/lobbies/{lobby_id}/members/@me', lobby_id=lobby_id))

    def set_linked_lobby(self, lobby_id: Snowflake, *, channel_id: Optional[Snowflake]) -> Response[lobby.Lobby]:
        payload = {
            'channel_id': channel_id,
        }
        route = Route('PATCH', '/lobbies/{lobby_id}/channel-linking', lobby_id=lobby_id)

        return self.request(route, json=payload)

    # Relationships
    def get_relationships(self, *, with_implicit: Optional[bool] = None) -> Response[List[user.Relationship]]:
        params = {}
        if with_implicit is not None:
            params['with_implicit'] = int(with_implicit)
        return self.request(Route('GET', '/users/@me/relationships'), params=params)

    def remove_relationship(self, user_id: Snowflake) -> Response[None]:
        return self.request(Route('DELETE', '/users/@me/relationships/{user_id}', user_id=user_id))

    def add_relationship(
        self,
        user_id: Snowflake,
        type: Optional[int] = None,
        *,
        friend_token: Optional[str] = None,
        from_friend_suggestion: Optional[bool] = None,
    ) -> Response[None]:
        payload = {}
        if type is not None:
            payload['type'] = type
        if friend_token:
            payload['friend_token'] = friend_token
        if from_friend_suggestion is not None:
            payload['from_friend_suggestion'] = from_friend_suggestion

        return self.request(Route('PUT', '/users/@me/relationships/{user_id}', user_id=user_id), json=payload)

    def send_friend_request(self, username: str, discriminator: Optional[Union[int, str]] = None) -> Response[None]:
        payload = {
            'username': username,
            'discriminator': None if discriminator is None else int(discriminator) or None,
        }
        # This endpoint throws 400/403 and 80000 code if target user didn't authorize app the friend request coming from?
        return self.request(Route('POST', '/users/@me/relationships'), json=payload)

    # Game Relationships
    def get_game_relationships(self) -> Response[List[user.GameRelationship]]:
        return self.request(Route('GET', '/users/@me/game-relationships'))

    def send_game_friend_request(self, username: str) -> Response[None]:
        payload = {'username': username}
        return self.request(Route('POST', '/users/@me/game-relationships'), json=payload)

    def add_game_relationship(
        self,
        user_id: Snowflake,
        type: Optional[int] = None,
    ) -> Response[None]:
        payload = {}
        if type is not None:
            payload['type'] = type

        return self.request(Route('PUT', '/users/@me/game-relationships/{user_id}', user_id=user_id), json=payload)

    def remove_game_relationship(self, user_id: Snowflake) -> Response[None]:
        return self.request(Route('DELETE', '/users/@me/game-relationships/{user_id}', user_id=user_id))

    # Billing

    def popup_bridge_callback(
        self,
        payment_source_type: billing.PaymentSourceType,
        *,
        state: str,
        path: str,
        # Not sure about optionality and nullability of these fields (in client)
        query: Optional[Dict[str, str]] = MISSING,
        insecure: Optional[bool] = MISSING,
    ) -> Response[None]:
        payload: Dict[str, Any] = {
            'state': state,
            'path': path,
        }
        if query is not MISSING:
            payload['query'] = query

        if insecure is not MISSING:
            payload['insecure'] = insecure

        return self.request(
            Route(
                'POST',
                '/billing/popup-bridge/{payment_source_type}/callback',
                payment_source_type=payment_source_type,
            ),
            json=payload,
        )

    # /api/v9/billing/popup-bridge/{payment_source_type}/callback/{state}/{response_type}
    # redirects to https://discord.com/billing/popup-bridge/callback?path=/billing/popup-bridge/{payment_source_type}/callback/{state}/{response_type}&state={state}&response_type={response_type}&payment_source_type={payment_source_type}'

    # Game Invites
    def create_game_invite(
        self,
        recipient_id: Snowflake,
        *,
        launch_parameters: str,  # max 8192 characters
        application_name: str,  # 2-128 characters
        application_icon_url: str,  # max 2048 characters
        fallback_url: Optional[str] = MISSING,
        ttl: Optional[int] = MISSING,  # 300-86400, default 900
    ) -> Response[game_invite.CreateGameInviteResponse]:
        payload: Dict[str, Any] = {
            'recipient_id': str(recipient_id),
            'launch_parameters': launch_parameters,
            'application_name': application_name,
            'application_asset': application_icon_url,
        }

        if fallback_url is not MISSING:
            payload['fallback_url'] = fallback_url

        if ttl is not MISSING:
            payload['ttl'] = ttl

        return self.request(Route('POST', '/game-invite/@me'), json=payload)

    # Misc

    def science(self, properties: Dict[str, Any], *, token: str, type: str, external: bool = False) -> Response[None]:
        payload = {
            'properties': properties,
            'token': token,
            'type': type,
        }

        if external:
            route = Route('POST', '/external/science')
        else:
            route = Route('POST', '/science')

        return self.request(route, json=payload)

    def create_headless_session(
        self,
        activities: List[presences.SendableActivity],
        *,
        token: Optional[str] = None,
    ) -> Response[presences.CreateHeadlessSessionResponseBody]:
        payload: presences.CreateHeadlessSessionRequestBody = {
            'activities': activities,
        }
        if token is not None:
            payload['token'] = token

        route = Route('POST', '/users/@me/headless-sessions')
        return self.request(route, json=payload)

    def delete_headless_session(self, token: str) -> Response[None]:
        payload = {'token': token}
        return self.request(Route('POST', '/users/@me/headless-sessions/delete'), json=payload)

    def get_activity_secret(
        self,
        user_id: Snowflake,
        session_id: str,
        application_id: Snowflake,
        activity_action_type: Literal[1],
        *,
        channel_id: Optional[Snowflake] = None,
        message_id: Optional[Snowflake] = None,
    ) -> Response[presences.GetActivitySecretResponseBody]:
        # Usable in OAuth2 context, unsure what scopes it requires however (perhaps activities.read?)
        params = {}
        if channel_id is not None:
            params['channel_id'] = channel_id
        if message_id is not None:
            params['message_id'] = message_id

        route = Route(
            'GET',
            '/users/{user_id}/sessions/{session_id}/activities/{application_id}/{activity_action_type}',
            user_id=user_id,
            session_id=session_id,
            application_id=application_id,
            activity_action_type=activity_action_type,
        )
        return self.request(route, params=params)

    def get_connections(self) -> Response[list[connections.Connection]]:
        return self.request(Route('GET', '/users/@me/connections'))

    def get_linked_connections(self) -> Response[list[connections.Connection]]:
        return self.request(Route('GET', '/users/@me/linked-connections'))

    def modify_user_settings(self, /, **payload) -> Response[settings.UserSettings]:
        return self.request(Route('PATCH', '/users/@me/settings'), json=payload)

    def upload_stream_preview(self, stream_key: str, thumbnail: str) -> Response[None]:
        payload = {'thumbnail': thumbnail}

        return self.request(
            Route(
                'POST',
                '/streams/{stream_key}/preview',
                stream_key=stream_key,
            ),
            json=payload,
        )

    def upload_video_stream_preview(
        self, stream_key: str, thumbnail: Union[str, bytes, os.PathLike[Any], io.BufferedIOBase]
    ) -> Response[None]:
        file = File(thumbnail)

        return self.request(
            Route(
                'POST',
                '/streams/{stream_key}/preview',
                stream_key=stream_key,
            ),
            files=[file],
            form=[{'name': 'file', 'value': file.fp}],
        )

    async def get_gateway_url(self) -> str:
        try:
            data = await self.request(Route('GET', '/gateway'))
        except HTTPException as exc:
            raise GatewayNotFound() from exc

        return data['url']
