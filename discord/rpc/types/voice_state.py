from __future__ import annotations

from typing import TypedDict

from .user import User


class InnerVoiceState(TypedDict):
    mute: bool
    deaf: bool
    self_mute: bool
    self_deaf: bool
    suppress: bool


class Pan(TypedDict):
    left: float  # min 0, max 1
    right: float  # min 0, max 1


class VoiceState(TypedDict):
    nick: str
    mute: bool
    volume: float
    pan: Pan  # Defaults to {left: 1, right: 1}
    voice_state: InnerVoiceState
    user: User
