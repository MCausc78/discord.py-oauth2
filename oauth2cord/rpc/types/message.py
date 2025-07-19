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

from typing import List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired, Required

from ...types.message import Attachment
from ...types.snowflake import Snowflake
from .embed import Embed
from .user import User

OriginalMatch = TypedDict(
    'OriginalMatch',
    {
        'index': NotRequired[int],
        '0': str,
        '1': str,
        '2': str,
        '3': str,
        '4': str,
        '5': str,
        '6': str,
        '7': str,
        '8': str,
        '9': str,
        '10': str,
        # 10 matches should be enough :clueless:
    },
)


class TextComponent(TypedDict):
    type: Literal['text']
    content: str
    originalMatch: OriginalMatch


class SubTextComponent(TypedDict):
    type: Literal['subtext']
    content: str


class StrongComponent(TypedDict):
    type: Literal['strong']
    content: List[ContentComponent]


class ItailcComponent(TypedDict):
    type: Literal['em']
    content: List[ContentComponent]


class UnderlineComponent(TypedDict):
    type: Literal['u']
    content: List[ContentComponent]


class StrikethroughComponent(TypedDict):
    type: Literal['s']
    content: List[ContentComponent]


class BreakComponent(TypedDict):
    type: Literal['br']


class EmojiComponent(TypedDict, total=False):
    type: Required[Literal['emoji']]
    name: Required[str]  # like ":skull:" or ":gw_m_doglol:"

    # Unicode
    originalMatch: OriginalMatch
    src: str  # URL like "https://canary.discord.com/assets/ead410f7f5d404c3.svg"
    surrogate: str

    # Custom
    animated: bool
    emojiId: Snowflake


class MentionComponent(TypedDict, total=False):
    type: Required[Literal['mention']]
    content: Required[List[ContentComponent]]
    channelId: Required[Snowflake]
    guildId: Snowflake  # not sure about NotRequired

    # Roles
    color: int  # hex color
    colorString: str  # like "#RRGGBB"
    roleColor: int
    roleColors: None  # idk whats inside
    roleId: Snowflake
    roleName: str  # like "@admin"
    # If everyone/here is mentioned, then only roleName is present

    # Users
    parsedUserId: Snowflake

    # Both
    roleName: str  # (? unsure on that one)
    viewingChannelId: Snowflake  # idk what thats for


class InlineCodeComponent(TypedDict):
    type: Literal['inlineCode']
    content: str


class CodeBlockComponent(TypedDict):
    type: Literal['codeBlock']
    lang: str
    content: str
    inQuote: bool  # ???


class ChannelComponent(TypedDict):
    type: Literal['channel']
    content: List[ContentComponent]
    channelType: int
    iconType: Literal[
        'text',
        'voice',
        'voice-locked',
        'stage',
        'stage-locked',
        'post',
        'thread',
        'media',
        'forum',
    ]


class ChannelMentionComponent(TypedDict):
    type: Literal['channelMention']
    channelId: Snowflake
    messageId: Optional[Snowflake]
    inContent: None  # idk
    content: List[ChannelComponent]


ContentComponent = Union[
    TextComponent,
    SubTextComponent,
    StrongComponent,
    ItailcComponent,
    UnderlineComponent,
    StrikethroughComponent,
    BreakComponent,
    EmojiComponent,
    MentionComponent,
    InlineCodeComponent,
    CodeBlockComponent,
    ChannelMentionComponent,
]


class Message(TypedDict):
    id: Snowflake
    blocked: bool  # true if author is blocked
    bot: bool  # always false?
    content: str
    content_parsed: NotRequired[List[ContentComponent]]
    nick: NotRequired[str]
    author_color: NotRequired[str]  # string like #RRGGBB
    edited_timestamp: Optional[str]  # ISO8601 timestamp
    timestamp: str  # also ISO8601 timestamp
    tts: bool
    mentions: List[Snowflake]
    mention_everyone: bool
    mention_roles: List[Snowflake]
    embeds: List[Embed]
    attachments: List[Attachment]
    author: NotRequired[User]  # :clueless:
    pinned: bool
    type: int
