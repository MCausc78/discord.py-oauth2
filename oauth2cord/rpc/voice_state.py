from __future__ import annotations

from typing import TYPE_CHECKING

from ..user import User

if TYPE_CHECKING:
    from .state import RPCConnectionState
    from .types.voice_state import (
        InnerVoiceState as InnerVoiceStatePayload,
        Pan as PanPayload,
        VoiceState as VoiceStatePayload,
    )

__all__ = ('VoiceState',)


class VoiceState:
    """Represents a Discord user's voice state.

    Unlike :class:`oauth2cord.VoiceState`, these are received from RPC.

    .. versionadded:: 3.0

    Attributes
    ----------
    user: :class:`oauth2cord.User`
        The user this voice state is for.
    mute: :class:`bool`
        Indicates if the user is currently muted by the guild.
    deaf: :class:`bool`
        Indicates if the user is currently deafened by the guild.
    self_mute: :class:`bool`
        Indicates if the user is currently muted by their own accord.
    self_deaf: :class:`bool`
        Indicates if the user is currently deafened by their own accord.
    suppress: :class:`bool`
        Indicates if the user is suppressed from speaking.

        Only applies to stage channels.
    nick: :class:`str`
        The nick of the user.
    local_mute: :class:`bool`
        Indicates if the user is currently muted locally in the Discord client.
    local_volume: :class:`float`
        The user's volume, set locally.
    left_pan: :class:`float`
        The left pan of user, set locally. Can be only between ``0.0`` and ``1.0``.
    right_pan: :class:`float`
        The right pan of user, set locally. Can be only between ``0.0`` and ``1.0``.
    """

    __slots__ = (
        '_state',
        'user',
        'mute',
        'deaf',
        'self_mute',
        'self_deaf',
        'suppress',
        'nick',
        'local_mute',
        'local_volume',
        'left_pan',
        'right_pan',
    )

    if TYPE_CHECKING:
        _state: RPCConnectionState
        user: User
        mute: bool
        deaf: bool
        self_mute: bool
        self_deaf: bool
        suppress: bool
        nick: str
        local_mute: bool
        local_volume: float
        left_pan: float
        right_pan: float

    def __init__(self, *, data: VoiceStatePayload, state: RPCConnectionState) -> None:
        self._state = state
        self._update(data)

    def _update_pan(self, data: PanPayload) -> None:
        self.left_pan = data['left']
        self.right_pan = data['right']

    def _update_inner(self, data: InnerVoiceStatePayload) -> None:
        self.mute = data['mute']
        self.deaf = data['deaf']
        self.self_deaf = data['self_deaf']
        self.self_mute = data['self_mute']
        self.suppress = data['suppress']

    def _update(self, data: VoiceStatePayload) -> None:
        self._update_pan(data['pan'])
        self._update_inner(data['voice_state'])

        self.user = User._from_rpc(data['user'], self._state)
        self.nick = data['nick']
        self.local_mute = data['mute']
        self.local_volume = data['volume']
