"""
The MIT License (MIT)

Copyright (c) 2015-present Rapptz

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

from typing import Any, List, Optional, TYPE_CHECKING

from .guild import Guild
from .utils import parse_time

# fmt: off
__all__ = (
    'Template',
)
# fmt: on

if TYPE_CHECKING:
    from datetime import datetime
    from typing_extensions import Self

    from .rpc.types.template import Template as RPCTemplatePayload
    from .state import BaseConnectionState
    from .types.template import Template as TemplatePayload
    from .user import User


class Template:
    """Represents a Discord template.

    .. versionadded:: 1.4

    Attributes
    ----------
    code: :class:`str`
        The template code.
    uses: :class:`int`
        How many times the template has been used.
    name: :class:`str`
        The name of the template.
    description: :class:`str`
        The description of the template.
    creator: :class:`User`
        The creator of the template.
    created_at: :class:`datetime`
        An aware datetime in UTC representing when the template was created.
    updated_at: :class:`datetime`
        An aware datetime in UTC representing when the template was last updated.
        This is referred to as "last synced" in the official Discord client.
    source_guild: :class:`Guild`
        The guild snapshot that represents the data that this template currently holds.
    is_dirty: Optional[:class:`bool`]
        Whether the template has unsynced changes.

        .. versionadded:: 2.0
    """

    __slots__ = (
        'code',
        'uses',
        'name',
        'description',
        'creator',
        'created_at',
        'updated_at',
        'source_guild',
        'is_dirty',
        '_state',
    )

    def __init__(self, *, data: TemplatePayload, state: BaseConnectionState) -> None:
        self._state: BaseConnectionState = state
        self._store(data)

    def _store(self, data: TemplatePayload) -> None:
        creator_data = data.get('creator')
        source_serialized = data['serialized_source_guild']
        source_serialized['id'] = int(data['source_guild_id'])

        self.code: str = data['code']
        self.uses: int = data['usage_count']
        self.name: str = data['name']
        self.description: Optional[str] = data['description']
        self.creator: Optional[User] = None if creator_data is None else self._state.create_user(creator_data)
        self.created_at: Optional[datetime] = parse_time(data.get('created_at'))
        self.updated_at: Optional[datetime] = parse_time(data.get('updated_at'))
        self.source_guild = Guild(data=source_serialized, state=self._state)
        self.is_dirty: Optional[bool] = data.get('is_dirty')

    @classmethod
    def _from_rpc(cls, data: RPCTemplatePayload, state: BaseConnectionState) -> Self:
        return cls(
            data={
                'code': data['code'],
                'name': data['name'],
                'description': data.get('description'),
                'usage_count': data['usageCount'],
                'creator_id': data['creatorId'],
                'creator': data['creator'],
                'created_at': data['createdAt'],
                'updated_at': data['updatedAt'],
                'source_guild_id': data['sourceGuildId'],
                'serialized_source_guild': data['serializedSourceGuild'],
                'is_dirty': data.get('isDirty'),
            },
            state=state,
        )

    def __repr__(self) -> str:
        return (
            f'<Template code={self.code!r} uses={self.uses} name={self.name!r}'
            f' creator={self.creator!r} source_guild={self.source_guild!r} is_dirty={self.is_dirty}>'
        )

    @property
    def url(self) -> str:
        """:class:`str`: The template url.

        .. versionadded:: 2.0
        """
        return f'https://discord.new/{self.code}'
