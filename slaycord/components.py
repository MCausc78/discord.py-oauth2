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

from typing import Any, ClassVar, Generic, List, Literal, Optional, TYPE_CHECKING, Tuple, TypeVar, Union, overload

from .asset import AssetMixin
from .color import Color
from .enums import (
    try_enum,
    ButtonStyle,
    ChannelType,
    ComponentType,
    MediaItemLoadingState,
    SelectDefaultValueType,
    SeparatorSpacingSize,
    TextStyle,
)
from .flags import AttachmentFlags, MediaScanFlags
from .partial_emoji import PartialEmoji, _EmojiTag
from .utils import MISSING, _get_as_snowflake, get_slots

if TYPE_CHECKING:
    from typing_extensions import Self, TypeAlias

    from .abc import Snowflake
    from .emoji import Emoji
    from .state import ConnectionState
    from .types.components import (
        Component as ComponentPayload,
        ActionRow as ActionRowPayload,
        Button as ButtonPayload,
        SelectDefaultValues as SelectDefaultValuesPayload,
        SelectMenu as SelectMenuPayload,
        SelectOption as SelectOptionPayload,
        TextInput as TextInputPayload,
        Section as SectionPayload,
        TextDisplay as TextDisplayPayload,
        UnfurledMediaItem as UnfurledMediaItemPayload,
        Thumbnail as ThumbnailPayload,
        MediaGalleryItem as MediaGalleryItemPayload,
        MediaGallery as MediaGalleryPayload,
        FileComponent as FileComponentPayload,
        Separator as SeparatorPayload,
        ContentInventoryEntry as ContentInventoryEntryPayload,
        Container as ContainerPayload,
    )

    MessageActionRowChildComponent = Union['Button', 'SelectMenu', 'TextInput']
    ContainerActionRowChildComponent = Union[
        MessageActionRowChildComponent,
        'Section',
        'TextDisplay',
        'MediaGallery',
        'FileComponent',
        'Separator',
    ]
    SectionChildComponent: TypeAlias = 'TextDisplay'
    SectionAccessoryComponent = Union['Button', 'Thumbnail']
    MessageComponent = Union[
        'ActionRow[MessageActionRowChildComponent]',
        'Section',
        'TextDisplay',
        'MediaGallery',
        'FileComponent',
        'Separator',
        'ContentInventoryEntry',
        'Container',
    ]


__all__ = (
    'Component',
    'ActionRow',
    'Button',
    'SelectMenu',
    'SelectOption',
    'TextInput',
    'SelectDefaultValue',
)

T = TypeVar('T', bound='Component')


class Component:
    """Represents a Discord Bot UI Kit Component.

    The components supported by Discord are:

    - :class:`ActionRow`
    - :class:`Button`
    - :class:`SelectMenu`
    - :class:`TextInput`
    - :class:`Section`
    - :class:`TextDisplay`
    - :class:`Thumbnail`
    - :class:`MediaGallery`
    - :class:`FileComponent`
    - :class:`Separator`
    - :class:`Container`

    This class is abstract and cannot be instantiated.

    .. versionadded:: 2.0
    """

    __slots__: Tuple[str, ...] = ()

    __repr_info__: ClassVar[Tuple[str, ...]]

    def __repr__(self) -> str:
        attrs = ' '.join(f'{key}={getattr(self, key)!r}' for key in self.__repr_info__)
        return f'<{self.__class__.__name__} {attrs}>'

    @property
    def type(self) -> ComponentType:
        """:class:`ComponentType`: The type of component."""
        raise NotImplementedError

    @classmethod
    def _raw_construct(cls, **kwargs) -> Self:
        self = cls.__new__(cls)
        for slot in get_slots(cls):
            try:
                value = kwargs[slot]
            except KeyError:
                pass
            else:
                setattr(self, slot, value)
        return self

    def to_dict(self) -> ComponentPayload:
        raise NotImplementedError


class ActionRow(Component, Generic[T]):
    """Represents a Discord Bot UI Kit Action Row.

    This is a component that holds up to 5 children components in a row.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 3.0
    children: List[Union[:class:`Button`, :class:`SelectMenu`, :class:`TextInput`]]
        The children components that this holds, if any.
    """

    __slots__: Tuple[str, ...] = (
        'id',
        'children',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ActionRowPayload, state: Optional[ConnectionState]) -> None:
        self.id: Optional[int] = data.get('id')
        self.children: List[T] = []

        for component_data in data.get('components', ()):
            component = _component_factory(component_data, state)

            if component is not None:
                self.children.append(component)  # type: ignore

    @property
    def type(self) -> Literal[ComponentType.action_row]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.action_row

    def to_dict(self) -> ActionRowPayload:
        return {
            'type': self.type.value,
            'components': [child.to_dict() for child in self.children],  # type: ignore
        }


class Button(Component):
    """Represents a button from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 3.0
    style: :class:`.ButtonStyle`
        The style of the button.
    custom_id: Optional[:class:`str`]
        The ID of the button that gets received during an interaction.
        If this button is for a URL, it does not have a custom ID.
    url: Optional[:class:`str`]
        The URL this button sends you to.
    disabled: :class:`bool`
        Whether the button is disabled or not.
    label: Optional[:class:`str`]
        The label of the button, if any.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji of the button, if available.
    sku_id: Optional[:class:`int`]
        The SKU ID this button sends you to, if available.

        .. versionadded:: 2.4
    """

    __slots__: Tuple[str, ...] = (
        'id',
        'style',
        'custom_id',
        'url',
        'disabled',
        'label',
        'emoji',
        'sku_id',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: ButtonPayload, /) -> None:
        self.id: Optional[int] = data.get('id')
        self.style: ButtonStyle = try_enum(ButtonStyle, data['style'])
        self.custom_id: Optional[str] = data.get('custom_id')
        self.url: Optional[str] = data.get('url')
        self.disabled: bool = data.get('disabled', False)
        self.label: Optional[str] = data.get('label')
        self.emoji: Optional[PartialEmoji]
        try:
            self.emoji = PartialEmoji.from_dict(data['emoji'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            self.emoji = None

        try:
            self.sku_id: Optional[int] = int(data['sku_id'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            self.sku_id = None

    @property
    def type(self) -> Literal[ComponentType.button]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.button

    def to_dict(self) -> ButtonPayload:
        payload: ButtonPayload = {
            'type': 2,
            'style': self.style.value,
            'disabled': self.disabled,
        }

        if self.sku_id:
            payload['sku_id'] = str(self.sku_id)

        if self.label:
            payload['label'] = self.label

        if self.custom_id:
            payload['custom_id'] = self.custom_id

        if self.url:
            payload['url'] = self.url

        if self.emoji:
            payload['emoji'] = self.emoji.to_dict()

        return payload


class SelectMenu(Component):
    """Represents a select menu from the Discord Bot UI Kit.

    A select menu is functionally the same as a dropdown, however
    on mobile it renders a bit differently.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 3.0
    type: :class:`ComponentType`
        The type of component.
    custom_id: Optional[:class:`str`]
        The ID of the select menu that gets received during an interaction.
    placeholder: Optional[:class:`str`]
        The placeholder text that is shown if nothing is selected, if any.
    min_values: :class:`int`
        The minimum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 0 and 25.
    max_values: :class:`int`
        The maximum number of items that must be chosen for this select menu.
        Defaults to 1 and must be between 1 and 25.
    options: List[:class:`SelectOption`]
        A list of options that can be selected in this menu.
    disabled: :class:`bool`
        Whether the select is disabled or not.
    channel_types: List[:class:`.ChannelType`]
        A list of channel types that are allowed to be chosen in this select menu.
    """

    __slots__: Tuple[str, ...] = (
        'id',
        'type',
        'custom_id',
        'placeholder',
        'min_values',
        'max_values',
        'options',
        'disabled',
        'channel_types',
        'default_values',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SelectMenuPayload, /) -> None:
        self.id: Optional[int] = data.get('id')
        self.type: ComponentType = try_enum(ComponentType, data['type'])
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self.min_values: int = data.get('min_values', 1)
        self.max_values: int = data.get('max_values', 1)
        self.options: List[SelectOption] = [SelectOption.from_dict(option) for option in data.get('options', ())]
        self.disabled: bool = data.get('disabled', False)
        self.channel_types: List[ChannelType] = [try_enum(ChannelType, t) for t in data.get('channel_types', ())]
        self.default_values: List[SelectDefaultValue] = [
            SelectDefaultValue.from_dict(d) for d in data.get('default_values', ())
        ]

    def to_dict(self) -> SelectMenuPayload:
        payload: SelectMenuPayload = {
            'type': self.type.value,  # type: ignore # We know this is a select menu
            'custom_id': self.custom_id,
            'min_values': self.min_values,
            'max_values': self.max_values,
            'disabled': self.disabled,
        }
        if self.placeholder:
            payload['placeholder'] = self.placeholder
        if self.options:
            payload['options'] = [op.to_dict() for op in self.options]
        if self.channel_types:
            payload['channel_types'] = [t.value for t in self.channel_types]  # type: ignore
        if self.default_values:
            payload['default_values'] = [v.to_dict() for v in self.default_values]

        return payload


class SelectOption:
    """Represents a select menu's option.

    While these can be created by users, it's not very useful since user accounts can not send any components.

    .. versionadded:: 2.0

    Parameters
    ----------
    label: :class:`str`
        The label of the option. This is displayed to users.
        Can only be up to 100 characters.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the label.
        Can only be up to 100 characters.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
        Can only be up to 100 characters.
    emoji: Optional[Union[:class:`str`, :class:`Emoji`, :class:`PartialEmoji`]]
        The emoji of the option, if available.
    default: :class:`bool`
        Whether this option is selected by default.

    Attributes
    ----------
    label: :class:`str`
        The label of the option. This is displayed to users.
    value: :class:`str`
        The value of the option. This is not displayed to users.
        If not provided when constructed then it defaults to the
        label.
    description: Optional[:class:`str`]
        An additional description of the option, if any.
    default: :class:`bool`
        Whether this option is selected by default.
    """

    __slots__: Tuple[str, ...] = (
        'label',
        'value',
        'description',
        '_emoji',
        'default',
    )

    def __init__(
        self,
        *,
        label: str,
        value: str = MISSING,
        description: Optional[str] = None,
        emoji: Optional[Union[str, Emoji, PartialEmoji]] = None,
        default: bool = False,
    ) -> None:
        self.label: str = label
        self.value: str = label if value is MISSING else value
        self.description: Optional[str] = description

        self.emoji = emoji
        self.default: bool = default

    def __repr__(self) -> str:
        return (
            f'<SelectOption label={self.label!r} value={self.value!r} description={self.description!r} '
            f'emoji={self.emoji!r} default={self.default!r}>'
        )

    def __str__(self) -> str:
        if self.emoji:
            base = f'{self.emoji} {self.label}'
        else:
            base = self.label

        if self.description:
            return f'{base}\n{self.description}'
        return base

    @property
    def emoji(self) -> Optional[PartialEmoji]:
        """Optional[:class:`.PartialEmoji`]: The emoji of the option, if available."""
        return self._emoji

    @emoji.setter
    def emoji(self, value: Optional[Union[str, Emoji, PartialEmoji]]) -> None:
        if value is not None:
            if isinstance(value, str):
                self._emoji = PartialEmoji.from_str(value)
            elif isinstance(value, _EmojiTag):
                self._emoji = value._to_partial()
            else:
                raise TypeError(f'expected str, Emoji, or PartialEmoji, received {value.__class__.__name__} instead')
        else:
            self._emoji = None

    @classmethod
    def from_dict(cls, data: SelectOptionPayload) -> SelectOption:
        try:
            emoji = PartialEmoji.from_dict(data['emoji'])  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            emoji = None

        return cls(
            label=data['label'],
            value=data['value'],
            description=data.get('description'),
            emoji=emoji,
            default=data.get('default', False),
        )

    def to_dict(self) -> SelectOptionPayload:
        payload: SelectOptionPayload = {
            'label': self.label,
            'value': self.value,
            'default': self.default,
        }

        if self.emoji:
            payload['emoji'] = self.emoji.to_dict()

        if self.description:
            payload['description'] = self.description

        return payload


class TextInput(Component):
    """Represents a text input from the Discord Bot UI Kit.

    .. versionadded:: 2.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.

        .. versionadded:: 3.0
    custom_id: Optional[:class:`str`]
        The ID of the text input that gets received during an interaction.
    label: :class:`str`
        The label to display above the text input.
    style: :class:`TextStyle`
        The style of the text input.
    placeholder: Optional[:class:`str`]
        The placeholder text to display when the text input is empty.
    value: Optional[:class:`str`]
        The default value of the text input.
    required: :class:`bool`
        Whether the text input is required.
    min_length: Optional[:class:`int`]
        The minimum length of the text input.
    max_length: Optional[:class:`int`]
        The maximum length of the text input.
    """

    __slots__: Tuple[str, ...] = (
        'id',
        'style',
        'label',
        'custom_id',
        'placeholder',
        'value',
        'required',
        'min_length',
        'max_length',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: TextInputPayload, /) -> None:
        self.id: Optional[int] = data.get('id')
        self.style: TextStyle = try_enum(TextStyle, data['style'])
        self.label: str = data['label']
        self.custom_id: str = data['custom_id']
        self.placeholder: Optional[str] = data.get('placeholder')
        self.value: Optional[str] = data.get('value')
        self.required: bool = data.get('required', True)
        self.min_length: Optional[int] = data.get('min_length')
        self.max_length: Optional[int] = data.get('max_length')

    @property
    def type(self) -> Literal[ComponentType.text_input]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.text_input

    def to_dict(self) -> TextInputPayload:
        payload: TextInputPayload = {
            'type': self.type.value,
            'style': self.style.value,
            'label': self.label,
            'custom_id': self.custom_id,
            'required': self.required,
        }

        if self.placeholder:
            payload['placeholder'] = self.placeholder

        if self.value:
            payload['value'] = self.value

        if self.min_length:
            payload['min_length'] = self.min_length

        if self.max_length:
            payload['max_length'] = self.max_length

        return payload

    @property
    def default(self) -> Optional[str]:
        """Optional[:class:`str`]: The default value of the text input.

        This is an alias to :attr:`value`.
        """
        return self.value


class SelectDefaultValue:
    """Represents a select menu's default value.

    These can be created by users.

    .. versionadded:: 2.4

    Parameters
    ----------
    id: :class:`int`
        The ID of a role, user, or channel.
    type: :class:`SelectDefaultValueType`
        The type of value that ``id`` represents.
    """

    def __init__(
        self,
        *,
        id: int,
        type: SelectDefaultValueType,
    ) -> None:
        self.id: int = id
        self._type: SelectDefaultValueType = type

    @property
    def type(self) -> SelectDefaultValueType:
        """:class:`SelectDefaultValueType`: The type of value that ``id`` represents."""
        return self._type

    @type.setter
    def type(self, value: SelectDefaultValueType) -> None:
        if not isinstance(value, SelectDefaultValueType):
            raise TypeError(f'expected SelectDefaultValueType, received {value.__class__.__name__} instead')

        self._type = value

    def __repr__(self) -> str:
        return f'<SelectDefaultValue id={self.id!r} type={self.type!r}>'

    @classmethod
    def from_dict(cls, data: SelectDefaultValuesPayload) -> SelectDefaultValue:
        return cls(
            id=data['id'],
            type=try_enum(SelectDefaultValueType, data['type']),
        )

    def to_dict(self) -> SelectDefaultValuesPayload:
        return {
            'id': self.id,
            'type': self._type.value,
        }

    @classmethod
    def from_channel(cls, channel: Snowflake, /) -> Self:
        """Creates a :class:`SelectDefaultValue` with the type set to :attr:`~SelectDefaultValueType.channel`.

        Parameters
        ----------
        channel: :class:`~slaycord.abc.Snowflake`
            The channel to create the default value for.

        Returns
        -------
        :class:`SelectDefaultValue`
            The default value created with the channel.
        """
        return cls(
            id=channel.id,
            type=SelectDefaultValueType.channel,
        )

    @classmethod
    def from_role(cls, role: Snowflake, /) -> Self:
        """Creates a :class:`SelectDefaultValue` with the type set to :attr:`~SelectDefaultValueType.role`.

        Parameters
        ----------
        role: :class:`~slaycord.abc.Snowflake`
            The role to create the default value for.

        Returns
        -------
        :class:`SelectDefaultValue`
            The default value created with the role.
        """
        return cls(
            id=role.id,
            type=SelectDefaultValueType.role,
        )

    @classmethod
    def from_user(cls, user: Snowflake, /) -> Self:
        """Creates a :class:`SelectDefaultValue` with the type set to :attr:`~SelectDefaultValueType.user`.

        Parameters
        ----------
        user: :class:`~slaycord.abc.Snowflake`
            The user to create the default value for.

        Returns
        -------
        :class:`SelectDefaultValue`
            The default value created with the user.
        """
        return cls(
            id=user.id,
            type=SelectDefaultValueType.user,
        )


class Section(Component):
    """Represents a section from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    components: List[:class:`TextDisplay`]
        The components on this section.

        .. warn::

            The types of children components are subject to change (but not removed).
            Never assume this will contain only :class:`TextDisplay`\\'s.
    accessory: Union[:class:`Button`, :class:`Thumbnail`]
        The section accessory.

        .. warn::

            The types of children components are subject to change (but not removed).
            Never assume this will be only :class:`Button` or :class:`Thumbnail`.
    """

    __slots__: Tuple[str, ...] = (
        'id',
        'components',
        'accessory',
    )

    __repr_info__: ClassVar[Tuple[str, ...]] = __slots__

    def __init__(self, data: SectionPayload, state: Optional[ConnectionState]) -> None:
        self.id: Optional[int] = data.get('id')
        self.components: List[SectionChildComponent] = []

        for component_data in data['components']:
            component = _component_factory(component_data, state)

            if component is not None:
                self.components.append(component)

        accessory = _component_factory(data['accessory'], state)

        self.accessory: SectionAccessoryComponent
        if accessory is not None:
            self.accessory = accessory  # type: ignore
        else:
            # I wish I didn't had to do bullshit like this,
            # but this is a signal for _component_factory to return None
            self.accessory = MISSING

    @property
    def type(self) -> Literal[ComponentType.section]:
        """:class:`ComponentType`: The type of component."""
        return ComponentType.section

    def to_dict(self) -> SectionPayload:
        payload: SectionPayload = {
            'type': 9,
            'components': [c.to_dict() for c in self.components],
            'accessory': self.accessory.to_dict(),
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload


class TextDisplay(Component):
    """Represents a text display from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    content: :class:`str`
        The content that this display shows.
    """

    __slots__ = (
        'id',
        'content',
    )

    __repr_info__ = __slots__

    def __init__(self, data: TextDisplayPayload) -> None:
        self.id: Optional[int] = data.get('id')
        self.content: str = data['content']

    @property
    def type(self) -> Literal[ComponentType.text_display]:
        return ComponentType.text_display

    def to_dict(self) -> TextDisplayPayload:
        payload: TextDisplayPayload = {
            'type': self.type.value,
            'content': self.content,
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload


class UnfurledMediaItem(AssetMixin):
    """Represents an unfurled media item.

    .. versionadded:: 3.0

    Parameters
    ----------
    url: :class:`str`
        The URL of this media item. This can be an arbitrary url or a reference to a local
        file uploaded as an attachment within the message, which can be accessed with the
        ``attachment://<filename>`` format.

    Attributes
    ----------
    url: :class:`str`
        The URL of this media item.
    proxy_url: Optional[:class:`str`]
        The proxy URL. This is a cached version of the :attr:`url` in the
        case of images. When the message is deleted, this URL might be valid for a few minutes
        or not valid at all.
    height: Optional[:class:`int`]
        The media item's height, in pixels. Only applicable to images and videos.
    width: Optional[:class:`int`]
        The media item's width, in pixels. Only applicable to images and videos.
    content_type: :class:`str`
        The media item's `content type <https://en.wikipedia.org/wiki/Media_type>`_.
    placeholder: Optional[:class:`str`]
        The media item's placeholder.
    loading_state: Optional[:class:`MediaItemLoadingState`]
        The loading state of this media item.
    content_scan_version: Optiona[:class:`int`]
        The version of the content scan filter.
    attachment_id: Optional[:class:`int`]
        The ID of the attachment this media item points to,
        only available if the URL points to a local file
        uploaded within the component message.
    """

    __slots__ = (
        '_state',
        'url',
        'proxy_url',
        'height',
        'width',
        'placeholder',
        'placeholder_version',
        'content_type',
        'loading_state',
        'content_scan_version',
        '_content_scan_flags',
        '_flags',
        'attachment_id',
    )

    def __init__(self, url: str) -> None:
        self._state: Optional[ConnectionState] = None
        self.url: str = url
        self.proxy_url: Optional[str] = None
        self.height: Optional[int] = None
        self.width: Optional[int] = None
        self.placeholder: Optional[str] = None
        self.placeholder_version: Optional[int] = None
        self.content_type: str = ''
        self.loading_state: Optional[MediaItemLoadingState] = None
        self.content_scan_version: Optional[int] = None
        self._content_scan_flags: int = 0
        self._flags: int = 0
        self.attachment_id: Optional[int] = None

    @property
    def content_scan_flags(self) -> MediaScanFlags:
        """:class:`MediaScanFlags`: The media scan flags."""
        return MediaScanFlags._from_value(self._content_scan_flags)

    @property
    def flags(self) -> AttachmentFlags:
        """:class:`AttachmentFlags`: This media item's flags."""
        return AttachmentFlags._from_value(self._flags)

    @classmethod
    def _from_data(cls, data: UnfurledMediaItemPayload, state: Optional[ConnectionState]):
        self = cls(data['url'])
        self._state = state
        self._partial_update(data)
        return self

    def _update(self, data: UnfurledMediaItemPayload) -> None:
        self.url = data['url']
        self._partial_update(data)

    def _partial_update(self, data: UnfurledMediaItemPayload) -> None:
        raw_loading_state = data.get('loading_state')

        self.proxy_url = data.get('proxy_url')
        self.height = data.get('height')
        self.width = data.get('width')
        self.placeholder = data.get('placeholder')
        self.placeholder_version = data.get('placeholder_version')
        self.content_type = data.get('content_type', '')

        if raw_loading_state is None:
            self.loading_state = None
        else:
            self.loading_state = try_enum(MediaItemLoadingState, raw_loading_state)

        content_scan_metadata_data = data.get('content_scan_metadata')
        if content_scan_metadata_data is None:
            self.content_scan_version = None
            self._content_scan_flags = 0
        else:
            self.content_scan_version = content_scan_metadata_data['version']
            self._content_scan_flags = content_scan_metadata_data['flags']

        self._flags = data.get('flags', 0)
        self.attachment_id = _get_as_snowflake(data, 'attachment_id')

    def __repr__(self) -> str:
        return f'<UnfurledMediaItem url={self.url}>'

    def to_dict(self) -> UnfurledMediaItemPayload:
        return {
            'url': self.url,
        }


class MediaGalleryItem:
    """Represents a :class:`MediaGalleryComponent` media item.

    .. versionadded:: 3.0

    Attributes
    ----------
    media: Union[:class:`str`, :class:`UnfurledMediaItem`]
        The media item data. This can be a string representing a local
        file uploaded as an attachment in the message, which can be accessed
        using the ``attachment://<filename>`` format, or an arbitrary url.
    description: Optional[:class:`str`]
        The description to show within this item. Up to 256 characters. Defaults
        to ``None``.
    spoiler: :class:`bool`
        Whether this item is flagged as a spoiler.
    """

    __slots__ = (
        'media',
        'description',
        'spoiler',
        '_state',
    )

    def __init__(
        self,
        media: Union[str, UnfurledMediaItem],
        *,
        description: Optional[str] = None,
        spoiler: bool = False,
    ) -> None:
        self._state: Optional[ConnectionState] = None
        self.media: UnfurledMediaItem = UnfurledMediaItem(media) if isinstance(media, str) else media
        self.description: Optional[str] = description
        self.spoiler: bool = spoiler

    def __repr__(self) -> str:
        return f'<MediaGalleryItem media={self.media!r}>'

    @classmethod
    def _from_data(cls, data: MediaGalleryItemPayload, state: Optional[ConnectionState]) -> MediaGalleryItem:
        media = data['media']
        self = cls(
            media=UnfurledMediaItem._from_data(media, state),
            description=data.get('description'),
            spoiler=data.get('spoiler', False),
        )
        self._state = state
        return self

    @classmethod
    def _from_gallery(
        cls,
        items: List[MediaGalleryItemPayload],
        state: Optional[ConnectionState],
    ) -> List[MediaGalleryItem]:
        return [cls._from_data(item, state) for item in items]

    def to_dict(self) -> MediaGalleryItemPayload:
        payload: MediaGalleryItemPayload = {
            'media': self.media.to_dict(),
            'spoiler': self.spoiler,
        }

        if self.description:
            payload['description'] = self.description

        return payload


class Thumbnail(Component):
    """Represents a thumbnail from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    media: :class:`UnfurledMediaItem`
        The media item data.
    description: Optional[:class:`str`]
        The description to show within this item. Up to 256 characters.
    spoiler: :class:`bool`
        Whether this item is flagged as a spoiler.
    """

    __slots__ = (
        'id',
        'media',
        'description',
        'spoiler',
    )

    __repr_info__ = __slots__

    def __init__(
        self,
        data: ThumbnailPayload,
        state: Optional[ConnectionState],
    ) -> None:
        self.id: Optional[int] = data.get('id')
        self.media: UnfurledMediaItem = UnfurledMediaItem._from_data(data['media'], state)
        self.description: Optional[str] = data.get('description')
        self.spoiler: bool = data.get('spoiler', False)

    @property
    def type(self) -> Literal[ComponentType.thumbnail]:
        return ComponentType.thumbnail

    def to_dict(self) -> ThumbnailPayload:
        payload: ThumbnailPayload = {
            'type': self.type.value,
            'media': self.media.to_dict(),
        }

        if self.description is not None:
            payload['description'] = self.description

        payload['spoiler'] = self.spoiler

        if self.id is not None:
            payload['id'] = self.id

        return payload


class MediaGallery(Component):
    """Represents a media gallery from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    items: List[:class:`MediaGalleryItem`]
        The items in this media gallery.
    """

    __slots__ = (
        'id',
        'items',
    )

    __repr_info__ = __slots__

    def __init__(
        self,
        data: MediaGalleryPayload,
        state: Optional[ConnectionState],
    ) -> None:
        self.id: Optional[int] = data.get('id')
        self.items: List[MediaGalleryItem] = MediaGalleryItem._from_gallery(data['items'], state)

    @property
    def type(self) -> Literal[ComponentType.media_gallery]:
        return ComponentType.media_gallery

    def to_dict(self) -> MediaGalleryPayload:
        payload: MediaGalleryPayload = {
            'type': self.type.value,
            'items': [item.to_dict() for item in self.items],
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload


class FileComponent(Component):
    """Represents a file from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    media: :class:`UnfurledMediaItem`
        The unfurled attachment contents of the file.
    spoiler: :class:`bool`
        Whether this file is flagged as a spoiler.
    name: :class:`str`
        The displayed file name.
    size: :class:`int`
        The file size in MiB.
    """

    __slots__ = (
        'id',
        'media',
        'spoiler',
        'name',
        'size',
    )

    __repr_info__ = __slots__

    def __init__(
        self,
        data: FileComponentPayload,
        state: Optional[ConnectionState],
    ) -> None:
        self.id: Optional[int] = data.get('id')
        self.media: UnfurledMediaItem = UnfurledMediaItem._from_data(data['file'], state)
        self.spoiler: bool = data.get('spoiler', False)
        self.name: str = data.get('name', '')
        self.size: int = data.get('size', 0)

    @property
    def type(self) -> Literal[ComponentType.file]:
        return ComponentType.file

    def to_dict(self) -> FileComponentPayload:
        payload: FileComponentPayload = {
            'type': self.type.value,
            'file': self.media.to_dict(),
            'spoiler': self.spoiler,
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload


class Separator(Component):
    """Represents a Separator from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    visible: :class:`bool`
        Whether this separator is visible and shows a divider.
    spacing: :class:`SeparatorSpacing`
        The spacing size of the separator.
    """

    __slots__ = (
        'id',
        'visible',
        'spacing',
    )

    __repr_info__ = __slots__

    def __init__(
        self,
        data: SeparatorPayload,
    ) -> None:
        self.id: Optional[int] = data.get('id')
        self.spacing: SeparatorSpacingSize = try_enum(SeparatorSpacingSize, data.get('spacing', 1))
        self.visible: bool = data.get('divider', True)

    @property
    def type(self) -> Literal[ComponentType.separator]:
        return ComponentType.separator

    def to_dict(self) -> SeparatorPayload:
        payload: SeparatorPayload = {
            'type': self.type.value,
            'divider': self.visible,
            'spacing': self.spacing.value,
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload


class ContentInventoryEntry(Component):
    """Represents an activity feed entry.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    """

    __slots__ = ('id',)

    __repr_info__ = ('id',)

    def __init__(self, data: ContentInventoryEntryPayload) -> None:
        self.id: Optional[int] = data.get('id')

    @property
    def type(self) -> Literal[ComponentType.content_inventory_entry]:
        return ComponentType.content_inventory_entry

    def to_dict(self) -> ContentInventoryEntryPayload:
        payload: ContentInventoryEntryPayload = {
            'type': self.type.value,
        }

        if self.id is not None:
            payload['id'] = self.id

        return payload


class Container(Component, Generic[T]):
    """Represents a Container from the Discord Bot UI Kit.

    This inherits from :class:`Component`.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`int`]
        The ID of this component.
    children: List[:class:`Component`]
        This container's children.
    spoiler: :class:`bool`
        Whether this container is flagged as a spoiler.
    """

    __slots__ = (
        'id',
        'children',
        '_accent_color',
        'spoiler',
    )

    __repr_info__ = (
        'id',
        'children',
        'accent_color',
        'spoiler',
    )

    def __init__(self, data: ContainerPayload, state: Optional[ConnectionState]) -> None:
        self.id: Optional[int] = data.get('id')
        self.children: List[T] = []

        for child in data['components']:
            component = _component_factory(child, state)

            if component is not None:
                self.children.append(component)  # type: ignore

        self._accent_color: Optional[int] = data.get('accent_color')
        self.spoiler: bool = data.get('spoiler', False)

    @property
    def accent_color(self) -> Optional[Color]:
        """Optional[:class:`Color`]: The container's accent color."""
        if self._accent_color is None:
            return None

        return Color(self._accent_color)

    accent_colour = accent_color

    @property
    def type(self) -> Literal[ComponentType.container]:
        return ComponentType.container

    def to_dict(self) -> ContainerPayload:
        payload: ContainerPayload = {
            'type': self.type.value,
            'components': [c.to_dict() for c in self.children],  # type: ignore
            'spoiler': self.spoiler,
        }

        if self._accent_color is not None:
            payload['accent_color'] = self._accent_color

        if self.id is not None:
            payload['id'] = self.id

        return payload


@overload
def _component_factory(data: ActionRowPayload, state: Optional[ConnectionState]) -> ActionRow[Any]:
    ...


@overload
def _component_factory(data: ButtonPayload, state: Optional[ConnectionState]) -> Button:
    ...


@overload
def _component_factory(data: TextInputPayload, state: Optional[ConnectionState]) -> TextInput:
    ...


@overload
def _component_factory(data: SelectMenuPayload, state: Optional[ConnectionState]) -> SelectMenu:
    ...


@overload
def _component_factory(data: SectionPayload, state: Optional[ConnectionState]) -> Section:
    ...


@overload
def _component_factory(data: TextDisplayPayload, state: Optional[ConnectionState]) -> TextDisplay:
    ...


@overload
def _component_factory(data: ThumbnailPayload, state: Optional[ConnectionState]) -> Thumbnail:
    ...


@overload
def _component_factory(data: MediaGalleryPayload, state: Optional[ConnectionState]) -> MediaGallery:
    ...


@overload
def _component_factory(data: FileComponentPayload, state: Optional[ConnectionState]) -> FileComponent:
    ...


@overload
def _component_factory(data: SeparatorPayload, state: Optional[ConnectionState]) -> Separator:
    ...


@overload
def _component_factory(data: ContentInventoryEntryPayload, state: Optional[ConnectionState]) -> ContentInventoryEntry:
    ...


@overload
def _component_factory(data: ContainerPayload, state: Optional[ConnectionState]) -> Container:
    ...


@overload
def _component_factory(data: ComponentPayload, state: Optional[ConnectionState]) -> Optional[Component]:
    ...


def _component_factory(data: ComponentPayload, state: Optional[ConnectionState]) -> Optional[Component]:
    if data['type'] == 1:
        return ActionRow(data, state)
    elif data['type'] == 2:
        return Button(data)
    elif data['type'] == 4:
        return TextInput(data)
    elif data['type'] == 9:
        section = Section(data, state)
        if section.accessory is MISSING:
            return None
        return section
    elif data['type'] == 10:
        return TextDisplay(data)
    elif data['type'] == 11:
        return Thumbnail(data, state)
    elif data['type'] == 12:
        return MediaGallery(data, state)
    elif data['type'] == 13:
        return FileComponent(data, state)
    elif data['type'] == 14:
        return Separator(data)
    elif data['type'] == 16:
        return ContentInventoryEntry(data)
    elif data['type'] == 17:
        return Container(data, state)
    elif data['type'] in (3, 5, 6, 7, 8):
        return SelectMenu(data)
