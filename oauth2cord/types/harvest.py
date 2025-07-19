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

from typing import Dict, Literal, Optional, TypedDict

from .snowflake import Snowflake


class Harvest(TypedDict):
    harvest_id: Snowflake
    user_id: Snowflake
    email: str
    state: HarvestState
    status: HarvestStatus
    created_at: str
    completed_at: Optional[str]
    polled_at: Optional[str]
    backends: Dict[HarvestBackendType, HarvestBackendState]
    updated_at: str
    shadow_run: bool
    harvest_metadata: HarvestMetadata


class HarvestMetadata(TypedDict, total=False):
    user_is_staff: bool
    is_provisional: bool
    sla_email_sent: bool
    bypass_cooldown: bool


HarvestState = Literal['INCOMPLETE', 'DELIVERED', 'CANCELLED']
HarvestStatus = Literal[0, 1, 2, 3, 4]
HarvestBackendType = Literal[
    'users',
    'analytics',
    'activities_e',
    'activities_w',
    'messages',
    'hubspot',
    'guilds',
    'ads',
]
HarvestBackendState = Literal['INITIAL', 'RUNNING', 'EXTRACTED']
