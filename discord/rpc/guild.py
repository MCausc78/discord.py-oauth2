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

import re
from typing import Optional, TYPE_CHECKING

from ..guild import PartialGuild as _PartialGuild

if TYPE_CHECKING:
    from .state import RPCConnectionState
    from .types.commands import GetGuildResponse as GetGuildResponsePayload
    from .types.guild import (
        PartialGuild as PartialGuildPayload,
    )

__all__ = (
    '_get_icon_hash_from_url',
    'PartialGuild',
    'Guild',
)


def _get_icon_hash_from_url(url: str) -> str:
    # Is this terrible? Yes.
    # Does it work? Yes.
    # Does Discord provide required data in payload? No.
    # That's why I have to do this dirty thing :(
    match = re.search(r'/icons/\d+/(\w+)\.', url)
    if match is None:
        return ''

    return match.group(1)


class PartialGuild(_PartialGuild):
    """Represents a Discord guild.

    This inherits from :class:`discord.PartialGuild`,
    and unlike the inherited class, these are received over RPC and will have following attributes filled in:

    - :attr:`~PartialGuild.id`
    - :attr:`~PartialGuild.name`
    - :attr:`~PartialGuild.icon`
    """

    __slots__ = ()

    if TYPE_CHECKING:
        _state: RPCConnectionState

    def __init__(self, *, data: PartialGuildPayload, state: RPCConnectionState) -> None:
        icon_url = data.get('icon_url')

        if icon_url:
            icon_hash = _get_icon_hash_from_url(icon_url) or None
        else:
            icon_hash = None

        super().__init__(
            id=int(data['id']),
            name=data['name'],
            icon_hash=icon_hash,
            features=[],
            state=state,
        )


class Guild(PartialGuild):
    """Represents a Discord guild.

    This inherits from :class:`PartialGuild`.

    Attributes
    ----------
    vanity_url_code: Optional[:class:`str`]
        The guild's vanity URL code, if any.
    """

    __slots__ = ('vanity_url_code',)

    def __init__(self, *, data: GetGuildResponsePayload, state: RPCConnectionState) -> None:
        super().__init__(data=data, state=state)
        self.vanity_url_code: Optional[str] = data.get('vanity_url_code')
