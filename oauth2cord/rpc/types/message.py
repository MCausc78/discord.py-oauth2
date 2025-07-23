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
        'index': Required[int],
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
    total=False,
)


class TextComponent(TypedDict):
    type: Literal['text']
    content: str
    originalMatch: NotRequired[OriginalMatch]


class StrikethroughComponent(TypedDict):
    type: Literal['s']
    content: List[ContentComponent]


class UnderlineComponent(TypedDict):
    type: Literal['u']
    content: List[ContentComponent]


class StrongComponent(TypedDict):
    type: Literal['strong']
    content: List[ContentComponent]


class ItailcComponent(TypedDict):
    type: Literal['em']
    content: List[ContentComponent]


# e.IMAGE = "image",


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


# e.CUSTOM_EMOJI = "customEmoji", # ???


class LinkComponent(TypedDict):
    type: Literal['link']
    content: List[ContentComponent]
    target: str
    title: NotRequired[str]


# e.URL = "url",
# e.AUTOLINK = "autolink",


class HighlightComponent(TypedDict):
    type: Literal['highlight']
    content: List[ContentComponent]


# e.PARAGRAPH = "paragraph",


class BreakComponent(TypedDict):
    type: Literal['br']


# e.NEWLINE = "newline",
# e.ESCAPE = "escape",


class SpoilerComponent(TypedDict):
    type: Literal['spoiler']
    channelId: Snowflake
    content: List[ContentComponent]


class BlockQuoteComponent(TypedDict):
    type: Literal['blockQuote']
    content: List[ContentComponent]


class InlineCodeComponent(TypedDict):
    type: Literal['inlineCode']
    content: str


class CodeBlockComponent(TypedDict):
    type: Literal['codeBlock']
    lang: str
    content: str
    inQuote: bool  # True if in blockQuote


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


# {
# "type": "channelMention",
# "channelId": "YYY",
# "guildId": "XXX",
# "messageId": "ZZZ",
# "originalLink": "https://canary.discord.com/channels/XXX/YYY/ZZZ",
# "inContent": [{
#  "type": "channel",
#  "content": [{
#   "type": "text",
#   "content": "garbage-collector-1"
#  }],
#  "channelType": 0,
#  "iconType": "text"
# }],
# "content": [{
#  "type": "channel",
#  "content": [{
#   "type": "text",
#   "content": ""
#  }],
#  "iconType": "message"
# }]
class ChannelMentionComponent(TypedDict):
    type: Literal['channelMention']
    channelId: Snowflake
    guildId: NotRequired[Optional[Union[Snowflake, Literal['@me']]]]  # Always provided actually
    messageId: Optional[Snowflake]
    inContent: Optional[List[ChannelComponent]]  # idk
    content: List[ChannelComponent]


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


class GuildComponent(TypedDict):
    type: Literal['guild']
    guildId: Snowflake
    content: str
    icon: NotRequired[str]


class AttachmentLinkComponent(TypedDict):
    type: Literal['attachmentLink']
    content: List[TextComponent]
    attachmentUrl: str
    attachmentName: str


class ShopLinkComponent(TypedDict):
    type: Literal['shopLink']
    content: List[TextComponent]
    shopLink: str
    skuId: Snowflake


class SoundboardComponent(TypedDict):
    type: Literal['soundboard']
    guildId: Snowflake
    soundId: Snowflake


class StaticRouteLinkComponent(TypedDict):
    type: Literal['staticRouteLink']
    content: List[TextComponent]
    mainContent: List[TextComponent]
    itemContent: Optional[List[TextComponent]]
    itemId: NotRequired[Snowflake]  # only applicable if id is linked-roles
    id: str  # GuildNavigationType
    gulidId: Snowflake
    channelId: str  # GuildNavigationType


class RoleMentionComponent(TypedDict):
    type: Literal['roleMention']
    id: Snowflake


class CommandMentionComponent(TypedDict):
    type: Literal['commandMention']
    channelId: Snowflake
    commandId: Snowflake
    commandName: str
    commandKey: str  # {id}\x00{name}
    content: List[ContentComponent]


class TimestampComponent(TypedDict):
    type: Literal['timestamp']
    timestamp: str  # unix timestamp
    format: NotRequired[str]  # single char, one of tTdDfFR
    parsed: str  # ISO8601 timestamp
    full: str
    formatted: str  # How it's rendered in client


# e.LIST = "list",
# e.HEADING = "heading",
class SubTextComponent(TypedDict):
    type: Literal['subtext']
    content: str


class SilentPrefixComponent(TypedDict):
    type: Literal['silentPrefix']
    content: str  # Literal['@silent'] # lol


# ...

ContentComponent = Union[
    TextComponent,
    StrikethroughComponent,
    UnderlineComponent,
    StrongComponent,
    ItailcComponent,
    EmojiComponent,
    LinkComponent,
    HighlightComponent,
    BreakComponent,
    SpoilerComponent,
    BlockQuoteComponent,
    InlineCodeComponent,
    CodeBlockComponent,
    MentionComponent,
    ChannelMentionComponent,
    ChannelComponent,
    GuildComponent,
    AttachmentLinkComponent,
    ShopLinkComponent,
    SoundboardComponent,
    StaticRouteLinkComponent,
    RoleMentionComponent,
    CommandMentionComponent,
    TimestampComponent,
    SubTextComponent,
    SilentPrefixComponent,
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
