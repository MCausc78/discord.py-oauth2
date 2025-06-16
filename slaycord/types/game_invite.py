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

from typing import Any, Dict, TypedDict

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


class GameInvite(TypedDict):
    invite_id: Snowflake
    platform_type: ConnectionType
    launch_parameters: str
    # A JSON string, which decodes as
    # {
    #   titleId: undefined | null | string,
    #   inviteToken: undefined | null | string
    # }
    installed: bool
    joinable: bool
    inviter_id: Snowflake
    created_at: str  # ISO8601 timestamp
    ttl: int  # TTL in seconds
    application_asset: str
    application_name: str
    parsed_launch_parameters: Dict[str, Any]
