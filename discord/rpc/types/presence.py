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
from typing_extensions import NotRequired

from ...types.presences import (
    StatusType,
    ReceivableActivity as APIActivity,
    ActivityTimestamps,
    ActivityAssets,
    ActivityParty as APIActivityParty,
    ActivitySecrets,
)


class RelationshipPresence(TypedDict):
    status: StatusType
    activity: Optional[APIActivity]  # Activity that is associated with authorized application


class ActivityParty(APIActivityParty):
    privacy: NotRequired[Literal[0, 1]]  # PRIVATE | PUBLIC


class ActivityButton(TypedDict):
    label: str  # 1-32 characters
    url: str  # 1-512


class Activity(TypedDict, total=False):
    state: str  # 2-128 characters
    details: str  # 2-128 characters
    timestamps: ActivityTimestamps
    assets: ActivityAssets
    secrets: ActivitySecrets
    buttons: List[ActivityButton]  # 1-2 elements (0 elements aren't permitted; omit this if you want no buttons)
    instance: bool
    supported_platforms: List[str]  # 1-32 characters, 1-3 elements
    type: Literal[0, 2, 3, 5]
