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

from typing import Optional, TypedDict
from typing_extensions import NotRequired

from .connections import ConnectionType
from .snowflake import Snowflake

# This seems enough to trigger a fake game invite:
# GatewaySocket._handleDispatch({
#     invite_id: SnowflakeUtils.fromTimestamp(Date.now()),
#     platform_type: "xbox",
#     launch_parameters: JSON.stringify({ titleId: "title ID", inviteToken: "invite token" }),
#     installed: true,
#     joinable: true,
#     inviter_id: UserStore.getCurrentUser().id,
#     created_at: new Date().toISOString(),
#     ttl: 86400,
#     application_asset: "https://cdn.discordapp.com/embed/avatars/1.png",
#     application_name: "SentinelGameInvite",
#     parsed_launch_parameters: { titleId: "title ID", inviteToken: "invite token" },
# }, "GAME_INVITE_CREATE", null);

# And here's a real game invite:
# {
#   't': 'GAME_INVITE_CREATE',
#   's': 11,
#   'op': 0,
#   'd': {
#     'ttl': 900,
#     'recipient_id': '1169421761859833997',
#     'platform_type': 'xbox',
#     'launch_parameters': '',
#     'inviter_id': '1073325901825187841',
#     'invite_id': '1385215083558342749',
#     'fallback_url': None,
#     'created_at': '2025-06-19T11:10:11.976253+00:00',
#     'application_name': 'GTA 5',
#     'application_asset': 'https://images-ext-1.discordapp.net/external/GyQicPLz_zQO15bOMtiGTtC4Kud7JjQbs1Ecuz7RrtU/https/cdn.discordapp.com/embed/avatars/1.png?format=png'
#   }
# }


class GameInvite(TypedDict):
    ttl: int  # TTL in seconds
    recipient_id: Snowflake
    platform_type: ConnectionType
    launch_parameters: str
    # launch_parameters is a JSON string, which decodes as
    # {
    #   titleId: undefined | null | string,
    #   inviteToken: undefined | null | string
    # }
    # However it is arbitrary string, meaning it should be treated as untrusted data
    inviter_id: Snowflake
    invite_id: Snowflake
    fallback_url: Optional[str]
    created_at: str  # ISO8601 timestamp
    installed: NotRequired[bool]
    joinable: NotRequired[bool]
    application_name: str
    application_asset: str


class CreateGameInviteResponse(TypedDict):
    invite_id: Snowflake
