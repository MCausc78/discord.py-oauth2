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

from typing import List, TypedDict
from typing_extensions import NotRequired, Required

from ...types.embed import EmbedType
from ...types.snowflake import Snowflake


class EmbedFooter(TypedDict):
    text: str
    iconURL: NotRequired[str]
    iconProxyURL: NotRequired[str]


class EmbedAuthor(TypedDict):
    name: str
    url: NotRequired[str]
    iconURL: NotRequired[str]
    iconProxyURL: NotRequired[str]


class EmbedProvider(TypedDict, total=False):
    name: str
    url: str


class EmbedMedia(TypedDict, total=False):
    url: Required[str]
    proxyURL: str
    width: int
    height: int
    placeholder: str
    placeholderVersion: int
    description: str
    srcIsAnimated: Required[bool]
    flags: Required[int]


class EmbedField(TypedDict):
    name: str
    value: str
    inline: NotRequired[bool]


class Embed(TypedDict, total=False):
    id: Required[str]
    url: str
    type: Required[EmbedType]  # Spec says this is always provided
    rawTitle: str
    rawDescription: str
    referenceId: Snowflake
    flags: int
    contentScanVersion: int
    timestamp: str  # ISO8601 timestamp
    color: str  # CSS color, like "hsla(240, calc(var(--saturation-factor, 1) * 100%), 69.4%, 1)"
    image: EmbedMedia
    thumbnail: EmbedMedia
    video: EmbedMedia
    fields: Required[List[EmbedField]]  # Should be required most of time:tm:
