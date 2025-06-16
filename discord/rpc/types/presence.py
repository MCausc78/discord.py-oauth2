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

from typing import List, Literal, Optional, Tuple, TypedDict

from ...types.activity import StatusType, Activity as APIActivity


class RelationshipPresence(TypedDict):
    status: StatusType
    activity: Optional[APIActivity]  # Activity that is associated with authorized application


class ActivityTimestamps(TypedDict, total=False):
    start: int
    end: int


class ActivityAssets(TypedDict, total=False):
    large_image: str  # 1-256 characters
    large_text: str  # 2-128 characters
    small_image: str  # 1-256 characters
    small_text: str  # 2-128 characters


class ActivityParty(TypedDict, total=False):
    id: str  # 2-128 characters
    size: Tuple[int, int]  # Both elements must be positive
    privacy: Literal[0, 1]  # PRIVATE | PUBLIC


class ActivitySecrets(TypedDict, total=False):
    match: str  # 2-128 characters
    join: str  # 2-128
    spectate: str  # 2-128 characters


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
