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

from typing import Dict, List, Literal, TypedDict, Union
from typing_extensions import NotRequired

from .integration import IntegrationAccount, IntegrationGuild, IntegrationType
from .snowflake import Snowflake

ConnectionType = Literal[
    'amazon-music',
    'battlenet',
    'bluesky',
    'bungie',
    'contacts',
    'crunchyroll',
    'domain',
    'ebay',
    'epicgames',
    'facebook',
    'github',
    'instagram',
    'leagueoflegends',
    'mastodon',
    'paypal',
    'playstation',
    'playstation-stg',
    'reddit',
    'riotgames',
    'roblox',
    'samsung',
    'skype',
    'spotify',
    'soundcloud',
    'steam',
    'tiktok',
    'twitch',
    'twitter',
    'xbox',
    'youtube',
]
VisibilityType = Literal[0, 1]


class PartialConnection(TypedDict):
    id: str
    type: ConnectionType
    name: str
    verified: bool
    metadata: NotRequired[Dict[str, str]]


class ConnectionIntegration(TypedDict):
    id: Union[Literal['twitch-partners'], Snowflake]
    type: IntegrationType
    account: IntegrationAccount
    guild: IntegrationGuild


class Connection(PartialConnection):
    metadata_visibility: VisibilityType
    revoked: bool
    integrations: List[ConnectionIntegration]
    friend_sync: bool
    show_activity: bool
    two_way_link: bool
    visibility: VisibilityType
    access_token: NotRequired[str]


ConsoleHandoffType = Literal[
    'CREATE_NEW_CALL',
    'TRANSFER_EXISTING_CALL',
]


class ConnectRequestProperties(TypedDict):
    handoff_type: ConsoleHandoffType


class ConnectionRequest(TypedDict):
    analytics_properties: ConnectRequestProperties
