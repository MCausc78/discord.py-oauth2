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

from typing import Optional, TypedDict
from typing_extensions import NotRequired

from ...types.snowflake import Snowflake
from ...types.user import RelationshipType
from .presence import RelationshipPresence


class AvatarDecorationData(TypedDict):
    asset: str
    skuId: NotRequired[Snowflake]
    expiresAt: NotRequired[int]


class User(TypedDict):
    id: Snowflake
    username: str
    discriminator: str
    global_name: Optional[str]
    avatar: Optional[str]
    avatar_decoration_data: Optional[AvatarDecorationData]
    bot: bool
    flags: int
    premium_type: int


class Relationship(TypedDict):
    type: RelationshipType
    user: User
    presence: RelationshipPresence
