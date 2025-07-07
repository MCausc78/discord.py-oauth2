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

from typing import Dict, List, Literal, Optional, Tuple, TypedDict, Union
from typing_extensions import NotRequired

from .appinfo import PartialApplication
from .snowflake import Snowflake
from .user import PartialUser


class PresenceUser(TypedDict):
    id: Snowflake


class Presence(TypedDict):
    user: Union[PresenceUser, PartialUser]
    guild_id: NotRequired[Snowflake]
    status: StatusType
    # Not truly NotRequired, just for sanity
    activities: NotRequired[List[ReceivableActivity]]
    hidden_activities: NotRequired[List[ReceivableActivity]]
    client_status: ClientStatus


class Session(TypedDict):
    session_id: str
    client_info: ClientInfo
    status: StatusType
    # Not truly NotRequired, just for sanity
    activities: NotRequired[List[ReceivableActivity]]
    hidden_activities: NotRequired[List[ReceivableActivity]]
    active: NotRequired[bool]


class ClientInfo(TypedDict):
    version: int
    os: Literal['windows', 'osx', 'linux', 'android', 'ios', 'playstation', 'xbox', 'other', 'unknown']
    client: ClientType


ClientType = Literal['desktop', 'web', 'mobile', 'embedded', 'unknown']
OperatingSystemType = Literal[
    'windows',
    'osx',
    'linux',
    'android',
    'ios',
    'playstation',
    'xbox',
    'unknown',
]
ClientStatus = Dict[ClientType, 'StatusType']
StatusType = Literal['online', 'dnd', 'idle', 'invisible', 'offline', 'unknown']

# Activities
class _BaseActivity(TypedDict, total=False):
    name: str
    type: ActivityType
    url: Optional[str]
    platform: ActivityPlatformType
    supported_platforms: List[ActivityPlatformType]
    timestamps: ActivityTimestamps
    application_id: Snowflake
    details: Optional[str]
    state: Optional[str]
    sync_id: str
    flags: int
    buttons: List[str]
    emoji: Optional[ActivityEmoji]
    party: ActivityParty
    assets: ActivityAssets


class SendableActivity(_BaseActivity, total=False):
    secrets: ActivitySecrets
    metadata: ActivityMetadata


class ReceivableActivity(_BaseActivity, total=False):
    id: str
    created_at: int
    session_id: Optional[str]


ActivityType = Literal[0, 1, 2, 4, 5]
ActivityPlatformType = Literal[
    'desktop',
    'xbox',
    'samsung',
    'ios',
    'android',
    'embedded',
    'ps4',
    'ps5',
]
ActivityActionType = Literal[1, 2, 3, 4, 5]


class ActivityTimestamps(TypedDict, total=False):
    start: int
    end: int


class ActivityEmoji(TypedDict):
    name: str
    id: NotRequired[Snowflake]
    animated: NotRequired[bool]


class ActivityAssets(TypedDict, total=False):
    large_image: str  # 1-256 characters
    large_text: str  # 2-128 characters
    small_image: str  # 1-256 characters
    small_text: str  # 2-128 characters


class ActivityParty(TypedDict, total=False):
    id: str  # 2-128 characters
    size: Tuple[int, int]  # Both elements must be positive


class ActivitySecrets(TypedDict, total=False):
    match: str  # 2-128 characters
    join: str  # 2-128
    spectate: str  # 2-128 characters


class ActivityMetadata(TypedDict, total=False):
    button_urls: List[str]
    artist_ids: List[str]
    album_id: str
    context_uri: str
    type: str


# HTTP
class Presences(TypedDict):
    guilds: List[VoiceGuild]
    presences: List[Presence]
    applications: List[PartialApplication]


class VoiceGuild(TypedDict):
    guild_id: Snowflake
    guild_name: str
    guild_icon: Optional[str]
    voice_channels: List[VoiceChannel]


class VoiceChannel(TypedDict):
    channel_id: Snowflake
    channel_name: str
    users: List[Snowflake]
    streams: NotRequired[List[VoiceStream]]


class VoiceStream(TypedDict):
    user_id: Snowflake


class XboxPresences(Presences):
    connected_account_ids: List[ConnectedAccount]


class ConnectedAccount(TypedDict):
    user_id: Snowflake
    provider_ids: List[str]


class UpdatePresenceRequestBody(TypedDict):
    package_name: str
    update: NotRequired[PresenceUpdateType]


PresenceUpdateType = Literal['START', 'UPDATE', 'STOP']


class GlobalActivityStatistics(TypedDict):
    user_id: Snowflake
    user: NotRequired[PartialUser]
    application_id: Snowflake
    application: NotRequired[PartialApplication]
    updated_at: str
    duration: int


class ApplicationActivityStatistics(TypedDict):
    user_id: Snowflake
    last_played_at: str
    total_duration: int


class UserApplicationActivityStatistics(TypedDict):
    application_id: str
    last_played_at: str
    first_played_at: NotRequired[str]
    total_duration: int
    total_discord_sku_duration: int


class CreateHeadlessSessionRequestBody(TypedDict):
    activities: List[SendableActivity]
    token: NotRequired[str]


class CreateHeadlessSessionResponseBody(TypedDict):
    activities: List[ReceivableActivity]
    token: str


class DeleteHeadlessSessionRequestBody(TypedDict):
    token: str


class GetActivitySecretResponseBody(TypedDict):
    secret: str


class UpdateActivitySubscriptionsRequestBodt(TypedDict):
    subscriptions: List[ActivitySubscription]


class ActivitySubscription(TypedDict):
    user_id: Snowflake
    application_id: Snowflake
    party_id: str
    message_id: Snowflake
    channel_id: Snowflake
