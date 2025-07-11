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

from typing import List, Literal, Optional, TypedDict
from typing_extensions import NotRequired, Required

from .appinfo import PartialApplication
from .guild import Guild
from .snowflake import Snowflake
from .user import User
from .webhook import Webhook


class OAuth2AccessToken(TypedDict):
    token_type: Literal['Bearer']
    access_token: str
    id_token: NotRequired[str]
    scope: str
    expires_in: int
    refresh_token: NotRequired[str]
    guild: NotRequired[Guild]
    webhook: NotRequired[Webhook]


class GetCurrentAuthorizationInformationResponseBody(TypedDict):
    application: PartialApplication
    scopes: List[str]
    expires: str
    user: NotRequired[User]


class GetOpenIDUserInformationResponseBody(TypedDict):
    sub: Snowflake
    email: Optional[str]
    email_verified: bool
    preferred_username: str
    nickname: Optional[str]
    picture: str
    locale: str


class GetOAuth2DeviceCodeRequestBody(TypedDict):
    client_id: NotRequired[Snowflake]
    client_secret: NotRequired[str]
    scope: NotRequired[str]


class GetOAuth2DeviceCodeResponseBody(TypedDict):
    device_code: str
    user_code: str
    verification_uri: str
    verification_uri_complete: str
    expires_in: int
    interval: int


class GetOAuth2TokenRequestBody(TypedDict, total=False):
    grant_type: Required[
        Literal[
            'authorization_code',
            'refresh_token',
            'client_credentials',
            'urn:ietf:params:oauth:grant-type:device_code',
        ]
    ]  # sob
    client_id: Snowflake
    client_secret: str
    code: str
    code_verifier: str
    redirect_uri: str
    refresh_token: str
    device_code: str
    scope: str
    external_auth_type: ExternalProviderAuthenticationType
    external_auth_token: str


class RevokeOAuth2TokenRequestBody(TypedDict):
    token: str
    client_id: NotRequired[Snowflake]
    client_secret: NotRequired[str]


class GetProvisionalAccountTokenRequestBody(TypedDict):
    client_id: Snowflake
    client_secret: NotRequired[Optional[str]]
    external_auth_type: ExternalProviderAuthenticationType
    external_auth_token: str


ExternalProviderAuthenticationType = Literal[
    'OIDC',
    'EPIC_ONLINE_SERVICES_ACCESS_TOKEN',
    'EPIC_ONLINE_SERVICES_ID_TOKEN',
    'STEAM_SESSION_TICKET',
    'UNITY_SERVICES_ID_TOKEN',
]


class UnmergeProvisionalAccountRequestBody(TypedDict):
    client_id: Snowflake
    client_secret: NotRequired[str]
    external_auth_type: ExternalProviderAuthenticationType
    external_auth_token: str
