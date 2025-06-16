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

from typing import List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired, Required

from .channel import ChannelType
from .emoji import PartialEmoji
from .snowflake import Snowflake

ComponentType = Literal[1, 2, 3, 4]
ButtonStyle = Literal[1, 2, 3, 4, 5, 6]
TextStyle = Literal[1, 2]
DefaultValueType = Literal['user', 'role', 'channel']


class BaseComponent(TypedDict):
    id: NotRequired[int]


class ActionRowBase(BaseComponent):
    type: Literal[1]


class MessageActionRow(ActionRowBase):
    components: List[MessageActionRowChildComponent]


class ContainerActionRow(ActionRowBase):
    components: List[ContainerActionRowChildComponent]


class Button(BaseComponent):
    type: Literal[2]
    style: ButtonStyle
    custom_id: NotRequired[str]
    url: NotRequired[str]
    disabled: NotRequired[bool]
    emoji: NotRequired[PartialEmoji]
    label: NotRequired[str]
    sku_id: NotRequired[str]


class SelectOption(TypedDict):
    label: str
    value: str
    default: bool
    description: NotRequired[str]
    emoji: NotRequired[PartialEmoji]


class Select(BaseComponent):
    custom_id: str
    placeholder: NotRequired[str]
    min_values: NotRequired[int]
    max_values: NotRequired[int]
    disabled: NotRequired[bool]


class SelectDefaultValues(TypedDict):
    id: int
    type: DefaultValueType


class StringSelect(Select):
    type: Literal[3]
    options: NotRequired[List[SelectOption]]


class UserSelect(Select):
    type: Literal[5]
    default_values: NotRequired[List[SelectDefaultValues]]


class RoleSelect(Select):
    type: Literal[6]
    default_values: NotRequired[List[SelectDefaultValues]]


class MentionableSelect(Select):
    type: Literal[7]
    default_values: NotRequired[List[SelectDefaultValues]]


class ChannelSelect(Select):
    type: Literal[8]
    channel_types: NotRequired[List[ChannelType]]
    default_values: NotRequired[List[SelectDefaultValues]]


class TextInput(BaseComponent):
    type: Literal[4]
    custom_id: str
    style: TextStyle
    label: str
    placeholder: NotRequired[str]
    value: NotRequired[str]
    required: NotRequired[bool]
    min_length: NotRequired[int]
    max_length: NotRequired[int]


class SelectMenu(Select):
    type: Literal[3, 5, 6, 7, 8]
    options: NotRequired[List[SelectOption]]
    channel_types: NotRequired[List[ChannelType]]
    default_values: NotRequired[List[SelectDefaultValues]]


class Section(BaseComponent):
    type: Literal[9]
    components: List[TextDisplay]
    accessory: Union[Thumbnail, Button]


class TextDisplay(BaseComponent):
    type: Literal[10]
    content: str


MediaItemLoadingState = Literal[
    0,  # UNKNOWN
    1,  # LOADING
    2,  # LOADED_SUCCESS
    3,  # LOADED_NOT_FOUND
]


class MediaItemScanMetadata(TypedDict):
    version: int
    flags: int  # EXPLICIT = 1 << 0, GORE = 1 << 1


class UnfurledMediaItem(TypedDict, total=False):
    url: Required[str]
    proxy_url: str
    height: Optional[int]
    width: Optional[int]
    placeholder: Optional[str]
    placeholder_version: Optional[int]
    content_type: str
    loading_state: MediaItemLoadingState
    content_scan_metadata: Optional[MediaItemScanMetadata]
    flags: int
    attachment_id: Snowflake


class Thumbnail(BaseComponent):
    type: Literal[11]
    media: UnfurledMediaItem
    description: NotRequired[str]
    spoiler: NotRequired[bool]


class MediaGalleryItem(TypedDict):
    # Similar to Thumbnail...
    media: UnfurledMediaItem
    description: NotRequired[str]
    spoiler: NotRequired[bool]


class MediaGallery(BaseComponent):
    type: Literal[12]
    items: List[MediaGalleryItem]


class FileComponent(BaseComponent):
    type: Literal[13]
    file: UnfurledMediaItem
    spoiler: NotRequired[bool]
    name: NotRequired[str]  # Always provided by the API
    size: NotRequired[int]  # Always provided by the API


SeparatorSpacingSize = Literal[1, 2]


class Separator(BaseComponent):
    type: Literal[14]
    divider: NotRequired[bool]
    spacing: NotRequired[SeparatorSpacingSize]


# 15 is reserved


class ContentInventoryEntry(BaseComponent):
    type: Literal[16]


class Container(BaseComponent):
    type: Literal[17]
    components: List[Union[ContainerActionRow, Section, TextDisplay, MediaGallery, FileComponent, Separator]]
    accent_color: NotRequired[Optional[int]]
    spoiler: NotRequired[bool]


MessageActionRowChildComponent = Union[Button, SelectMenu, TextInput]
ContainerActionRowChildComponent = Union[
    MessageActionRowChildComponent,
    Section,
    TextDisplay,
    MediaGallery,
    FileComponent,
    Separator,
]
MessageComponent = Union[
    MessageActionRow,
    Section,
    TextDisplay,
    MediaGallery,
    FileComponent,
    Separator,
    ContentInventoryEntry,
    Container,
]
ActionRow = Union[MessageActionRow, ContainerActionRow]
Component = Union[
    ActionRow,
    Button,
    SelectMenu,
    TextInput,
    Section,
    TextDisplay,
    Thumbnail,
    MediaGallery,
    FileComponent,
    Separator,
    ContentInventoryEntry,
    Container,
]
