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
