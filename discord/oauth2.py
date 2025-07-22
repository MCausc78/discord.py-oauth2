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

from asyncio import sleep
from typing import List, Optional, TYPE_CHECKING

from .appinfo import PartialAppInfo
from .errors import HTTPException, LoginFailure
from .guild import Guild
from .user import ClientUser
from .utils import parse_time
from .webhook import Webhook

if TYPE_CHECKING:
    from datetime import datetime

    from .enums import ExternalAuthenticationProviderType
    from .state import BaseConnectionState, ConnectionState
    from .types.oauth2 import (
        OAuth2AccessToken as OAuth2AccessTokenPayload,
        GetCurrentAuthorizationInformationResponseBody as GetCurrentAuthorizationInformationResponseBodyPayload,
        GetOAuth2DeviceCodeResponseBody as GetOAuth2DeviceCodeResponseBodyPayload,
        GetOAuth2TokenRequestBody as GetOAuth2TokenRequestBodyPayload,
    )

__all__ = (
    'OAuth2Authorization',
    'AccessToken',
    'OAuth2DeviceFlow',
)


class OAuth2Authorization:
    """Represents an OAuth2 authorization.

    Attributes
    ----------
    application: :class:`~discord.PartialAppInfo`
        The application the OAuth2 authorization is associated with.
    scopes: List[:class:`str`]
        The scopes that this OAuth2 authorization grants.
    expires_at: :class:`~datetime.datetime`
        When the authorization will expire.
    user: Optional[:class:`~discord.ClientUser`]
        The user that created this OAuth2 authorization.

        This attribute will be ``None`` if ``identify`` scope is not granted.
    """

    __slots__ = (
        '_state',
        'application',
        'scopes',
        'expires_at',
        'user',
    )

    def __init__(self, *, data: GetCurrentAuthorizationInformationResponseBodyPayload, state: BaseConnectionState) -> None:
        raw_user = data.get('user')

        self._state: BaseConnectionState = state
        self.application: PartialAppInfo = PartialAppInfo(data=data['application'], state=state)
        self.scopes: List[str] = data['scopes']
        self.expires_at: datetime = parse_time(data['expires'])
        self.user: Optional[ClientUser] = None if raw_user is None else ClientUser(data=raw_user, state=state)


class AccessToken:
    """Represents an OAuth2 access token.

    Attributes
    ----------
    type: :class:`str`
        The type of the token. This always will be ``Bearer``.
    access_token: :class:`str`
        The access token.
    id_token: :class:`str`
        The ID token. Only applicable when retrieving token for a provisional account.
    scopes: List[:class:`str`]
        The scopes the token has.
    expires_in: :class:`int`
        Duration in seconds, after which the access token expires.
    refresh_token: :class:`str`
        The refresh token for retrieving new access tokens.

        When retrieving token for a provisional account, this is populated only for certain authentication providers.
    guild: Optional[:class:`~discord.Guild`]
        The guild to which the bot was added, if applicable.
    webhook: Optional[:class:`~discord.Webhook`]
        The created webhook, if applicable.
    """

    __slots__ = (
        'type',
        'access_token',
        'id_token',
        'scopes',
        'expires_in',
        'refresh_token',
        'guild',
        'webhook',
    )

    def __init__(self, *, data: OAuth2AccessTokenPayload, state: ConnectionState) -> None:
        guild_data = data.get('guild')
        webhook_data = data.get('webhook')

        self.type: str = data['token_type']
        self.access_token: str = data['access_token']
        self.id_token: str = data.get('id_token', '')
        self.scopes: List[str] = data['scope'].split(' ')
        self.expires_in: int = data['expires_in']
        self.refresh_token: str = data.get('refresh_token', '')
        self.guild: Optional[Guild] = Guild(data=guild_data, state=state) if guild_data else None
        self.webhook: Optional[Webhook] = Webhook.from_state(data=webhook_data, state=state) if webhook_data else None


class OAuth2DeviceFlow:
    """Represents an OAuth2 Device flow.

    Attributes
    ----------
    device_code: :class:`str`
        The internal device code which should be exchanged.
    code: :class:`str`
        The code that should be shown to user.
    verification_uri: :class:`str`
        The verification URI, without ``user_code`` query string parameter.

        You can show this URL and value of ``user_code`` to user.
    complete_verification_uri: :class:`str`
        The verification URI, with an ``user_code`` query string parameter. For example: ``https://discord.com/activate?user_code=ZAW6C586``.

        This generally should be embedded into QR code and shown to user.
    expires_in: :class:`int`
        Duration in seconds after which the flow will be aborted.
    interval: :class:`int`
        The interval in seconds for polling the endpoint.
    """

    def __init__(
        self,
        *,
        data: GetOAuth2DeviceCodeResponseBodyPayload,
        client_id: int,
        client_secret: Optional[str] = None,
        state: ConnectionState,
    ) -> None:
        self._state: ConnectionState = state
        self._client_id: int = client_id
        self._client_secret: Optional[str] = client_secret

        self.device_code: str = data['device_code']
        self.code: str = data['user_code']
        self.verification_uri: str = data['verification_uri']
        self.complete_verification_uri: str = data['verification_uri_complete']
        self.expires_in: int = data['expires_in']
        self.interval: int = data['interval']

    async def poll(
        self,
        *,
        external_auth_token: Optional[str] = None,
        external_auth_type: Optional[ExternalAuthenticationProviderType] = None,
    ) -> AccessToken:
        """|coro|

        Starts polling for an access token.

        Parameters
        ----------
        external_auth_token: Optional[:class:`str`]
            The external authentication token.
            If this is provided, then ``external_auth_type`` must be provided as well.
        external_auth_type: Optional[:class:`ExternalAuthenticationProviderType`]
            The external authentication provider type.
            If this is provided, then ``external_auth_token`` must be provided as well.

        Raises
        ------
        LoginFailure
            The user aborted the process, or the device code expired.
        HTTPException
            Exchanging the token failed for other reasons.

        Returns
        -------
        :class:`~discord.AccessToken`
            The access token.
        """

        payload: GetOAuth2TokenRequestBodyPayload = {
            'grant_type': 'urn:ietf:params:oauth:grant-type:device_code',
            'client_id': self._client_id,
            'device_code': self.device_code,
        }
        if self._client_secret:
            payload['client_secret'] = self._client_secret
        if external_auth_token:
            payload['external_auth_token'] = external_auth_token
        if external_auth_type:
            payload['external_auth_type'] = external_auth_type.value

        interval = self.interval
        state = self._state
        http = state.http

        while True:
            await sleep(interval)

            try:
                data = await http.get_oauth2_token(payload)
            except HTTPException as exc:
                if exc.error_code == 'authorization_pending':
                    continue

                if exc.error_code == 'slow_down':
                    interval = int(interval * 1.5)
                    continue

                if exc.error_code in ('expired_token', 'access_denied'):
                    raise LoginFailure from exc

                raise exc from None

            return AccessToken(data=data, state=state)
