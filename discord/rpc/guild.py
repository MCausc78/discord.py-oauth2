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
    and unlike :class:`discord.PartialGuild`, these are received over RPC and will have following attributes filled in:

    - :attr:`id`
    - :attr:`name`
    - :attr:`icon`
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
