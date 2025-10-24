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

from typing import Optional, TYPE_CHECKING

from ..asset import Asset
from ..utils import _get_as_snowflake

if TYPE_CHECKING:
    from .state import RPCConnectionState
    from .types.events import CurrentGuildMemberUpdateEvent as MemberPayload
    from .types.user import AvatarDecorationData as AvatarDecorationDataPayload

# fmt: off
__all__ = (
    'Member',
)
# fmt: on


class Member:
    __slots__ = (
        '_state',
        'guild_id',
        'user_id',
        'nick',
        '_avatar',
        '_avatar_decoration_data',
        '_banner',
        'bio',
        'pronouns',
        'color_string',
    )

    def __init__(self, *, data: MemberPayload, state: RPCConnectionState) -> None:
        self._state: RPCConnectionState = state
        self.guild_id: int = int(data['guild_id'])
        self.user_id: int = int(data['user_id'])
        self.nick: Optional[str] = data.get('nick')
        self._avatar: Optional[str] = data.get('avatar')
        self._avatar_decoration_data: Optional[AvatarDecorationDataPayload] = data.get('avatar_decoration_data')
        self._banner: Optional[str] = data.get('banner')
        self.bio: Optional[str] = data.get('bio')
        self.pronouns: Optional[str] = data.get('pronouns')
        self.color_string: Optional[str] = data.get('color_string')

    @property
    def guild_avatar(self) -> Optional[Asset]:
        """Optional[:class:`~discord.Asset`]: Returns an :class:`~discord.Asset` for the guild avatar
        the member has. If unavailable, ``None`` is returned.
        """
        if self._avatar is None:
            return None
        return Asset._from_guild_avatar(self._state, self.guild_id, self.user_id, self._avatar)

    @property
    def guild_avatar_decoration(self) -> Optional[Asset]:
        """Optional[:class:`~discord.`]: Returns an :class:`~discord.Asset` for the avatar decoration the member has.

        If the member has not set an avatar decoration, ``None`` is returned.
        """
        if self._avatar_decoration_data is not None:
            return Asset._from_avatar_decoration(self._state, self._avatar_decoration_data['asset'])
        return None

    @property
    def guild_avatar_decoration_sku_id(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns the SKU ID of the avatar decoration the member has.

        If the member has not set an avatar decoration, ``None`` is returned.
        """
        if self._avatar_decoration_data is not None:
            return _get_as_snowflake(self._avatar_decoration_data, 'skuId')
        return None

    @property
    def guild_banner(self) -> Optional[Asset]:
        """Optional[:class:`~discord.Asset`]: Returns an :class:`~discord.Asset` for the guild banner
        the member has. If unavailable, ``None`` is returned.
        """
        if self._banner is None:
            return None
        return Asset._from_guild_banner(self._state, self.guild_id, self.user_id, self._banner)
