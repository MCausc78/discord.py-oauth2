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
