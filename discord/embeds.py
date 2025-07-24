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

import datetime
from typing import Any, Dict, List, Mapping, Optional, Protocol, TYPE_CHECKING, Tuple, TypeVar, Union

from .color import Color
from .flags import AttachmentFlags, EmbedFlags, MediaScanFlags
from .utils import _get_as_snowflake, parse_time

# fmt: off
__all__ = (
    'Embed',
)
# fmt: on


class EmbedProxy:
    def __init__(self, layer: Dict[str, Any]):
        self.__dict__.update(layer)

    def __len__(self) -> int:
        return len(self.__dict__)

    def __repr__(self) -> str:
        inner = ', '.join((f'{k}={getattr(self, k)!r}' for k in dir(self) if not k.startswith('_')))
        return f'EmbedProxy({inner})'

    def __getattr__(self, attr: str) -> None:
        return None

    def __eq__(self, other: object) -> bool:
        return isinstance(other, EmbedProxy) and self.__dict__ == other.__dict__


class EmbedMediaProxy(EmbedProxy):
    def __init__(self, layer: Dict[str, Any]):
        super().__init__(layer)
        
        raw_content_scan_metadata = self.__dict__.pop('content_scan_metadata', None)

        self._flags = self.__dict__.pop('flags', 0)
        self._animated = self.__dict__.pop('_animated', None)
        self.description = self.__dict__.pop('description', '')
        self.content_type = self.__dict__.pop('content_type', '')
        
        if raw_content_scan_metadata is None:
            self.content_scan_version = None
            self._content_scan_flags = 0
        else:
            self.content_scan_version = raw_content_scan_metadata['version']
            self._content_scan_flags = raw_content_scan_metadata['flags']

        self.placeholder_version = self.__dict__.pop('placeholder_version', None)
        self.placeholder = self.__dict__.pop('placeholder', '')

    @property
    def flags(self) -> AttachmentFlags:
        return AttachmentFlags._from_value(self._flags or 0)

    @property
    def animated(self) -> bool:
        if self._animated is None:
            return bool(self._flags & AttachmentFlags.animated.flag)
        return self._animated

    @property
    def content_scan_flags(self) -> MediaScanFlags:
        return MediaScanFlags._from_value(self._content_scan_flags)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .rpc.types.embed import (
        EmbedMedia as RPCEmbedMediaPayload,
        Embed as RPCEmbedPayload,
    )
    from .types.embed import (
        EmbedMedia as EmbedMediaPayload,
        Embed as EmbedData,
        EmbedType,
    )

    T = TypeVar('T')

    class _EmbedFooterProxy(Protocol):
        text: Optional[str]
        icon_url: Optional[str]

    class _EmbedFieldProxy(Protocol):
        name: Optional[str]
        value: Optional[str]
        inline: bool

    class _EmbedMediaProxy(Protocol):
        url: Optional[str]
        proxy_url: Optional[str]
        height: Optional[int]
        width: Optional[int]
        flags: AttachmentFlags
        description: str
        content_type: str
        content_scan_version: Optional[int]
        content_scan_flags: int
        placeholder_version: Optional[int]
        placeholder: str

    class _EmbedProviderProxy(Protocol):
        name: Optional[str]
        url: Optional[str]

    class _EmbedAuthorProxy(Protocol):
        name: Optional[str]
        url: Optional[str]
        icon_url: Optional[str]
        proxy_icon_url: Optional[str]

def _transform_rpc_embed_media_to_api(data: RPCEmbedMediaPayload) -> Tuple[bool, EmbedMediaPayload]:
    transformed_data: EmbedMediaPayload = {
        'url': data['url'],
        'flags': data['flags'],
    }
    if 'proxyURL' in data:
        transformed_data['proxy_url'] = data['proxyURL']
    if 'width' in data:
        transformed_data['width'] = data['width']
    if 'height' in data:
        transformed_data['height'] = data['height']
    if 'placeholder' in data:
        transformed_data['placeholder'] = data['placeholder']
    if 'placeholderVersion' in data:
        transformed_data['placeholder_version'] = data['placeholderVersion']
    if 'description' in data:
        transformed_data['description'] = data['description']
    return data['srcIsAnimated'], transformed_data

class Embed:
    """Represents a Discord embed.

    .. container:: operations

        .. describe:: len(x)

            Returns the total size of the embed.
            Useful for checking if it's within the 6000 character limit.

        .. describe:: bool(b)

            Returns whether the embed has any data set.

            .. versionadded:: 2.0

        .. describe:: x == y

            Checks if two embeds are equal.

            .. versionadded:: 2.0

    For ease of use, all parameters that expect a :class:`str` are implicitly
    casted to :class:`str` for you.

    .. versionchanged:: 2.0
        ``Embed.Empty`` has been removed in favour of ``None``.

    Attributes
    ----------
    id: :class:`str`
        The ID of the embed.
        This attribute won't be empty if received from RPC.
        
        .. versionadded:: 3.0
    title: Optional[:class:`str`]
        The title of the embed.
        This can be set during initialization.
        Can only be up to 256 characters.
    type: :class:`str`
        The type of embed. Usually "rich".
        This can be set during initialization.
        Possible strings for embed types can be found on discord's
        :ddocs:`api docs <resources/message#embed-object-embed-types>`
    description: Optional[:class:`str`]
        The description of the embed.
        This can be set during initialization.
        Can only be up to 4096 characters.
    url: Optional[:class:`str`]
        The URL of the embed.
        This can be set during initialization.
    timestamp: Optional[:class:`datetime.datetime`]
        The timestamp of the embed content. This is an aware datetime.
        If a naive datetime is passed, it is converted to an aware
        datetime with the local timezone.
    color: Optional[Union[:class:`Color`, :class:`int`]]
        The color code of the embed. Aliased to ``colour`` as well.
        This can be set during initialization.

        .. note::

            If the embed was received over RPC, :attr:`css_color` should be used instead.
    css_color: Optional[:class:`str`]
        The CSS color of the embed. Aliased to ``css_colour`` as well.

        .. versionadded:: 3.0
    reference_id: Optional[:class:`int`]
        The message's ID this embed was generated from.

        .. versionadded:: 3.0
    content_scan_version: Optional[:class:`int`]
        The version of the explicit content scan filter this embed was scanned with.

        .. versionadded:: 3.0
    """

    __slots__ = (
        'id',
        'title',
        'url',
        'type',
        '_timestamp',
        '_color',
        'css_color',
        '_footer',
        '_image',
        '_thumbnail',
        '_video',
        '_provider',
        '_author',
        '_fields',
        'description',
        'reference_id',
        'content_scan_version',
        '_flags',
    )

    def __init__(
        self,
        *,
        color: Optional[Union[int, Color]] = None,
        colour: Optional[Union[int, Color]] = None,
        title: Optional[Any] = None,
        type: EmbedType = 'rich',
        url: Optional[Any] = None,
        description: Optional[Any] = None,
        timestamp: Optional[datetime.datetime] = None,
    ) -> None:
        self.id: str = ''
        self.color = colour if color is None else color
        self.css_color: Optional[str] = None
        self.title: Optional[str] = title
        self.type: EmbedType = type
        self.url: Optional[str] = url
        self.description: Optional[str] = description
        self.reference_id: Optional[int] = None
        self.content_scan_version: Optional[int] = None
        self._flags: int = 0

        if self.title is not None:
            self.title = str(self.title)

        if self.description is not None:
            self.description = str(self.description)

        if self.url is not None:
            self.url = str(self.url)

        if timestamp is not None:
            self.timestamp = timestamp

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Self:
        """Converts a :class:`dict` to a :class:`Embed` provided it is in the
        format that Discord expects it to be in.

        You can find out about this format in the :userdoccers:`Discord Userdoccers <resources/message#embed-object>`.

        Parameters
        ----------
        data: :class:`dict`
            The dictionary to convert into an embed.
        """
        # we are bypassing __init__ here since it doesn't apply here
        self = cls.__new__(cls)

        # fill in the basic fields

        self.id = ''
        self.title = data.get('title')
        self.type = data.get('type', 'rich')
        self.description = data.get('description', None)
        self.url = data.get('url')
        self.reference_id = _get_as_snowflake(data, 'reference_id')
        self.content_scan_version = data.get('content_scan_version')
        self._flags = data.get('flags', 0)

        if self.title is not None:
            self.title = str(self.title)

        if self.description is not None:
            self.description = str(self.description)

        if self.url is not None:
            self.url = str(self.url)

        # try to fill in the more rich fields

        try:
            self._color = Color(value=data['color'])
        except KeyError:
            pass
            
        self.css_color = None

        try:
            self._timestamp = parse_time(data['timestamp'])
        except KeyError:
            pass

        for attr in ('thumbnail', 'video', 'provider', 'author', 'fields', 'image', 'footer'):
            try:
                value = data[attr]
            except KeyError:
                continue
            else:
                setattr(self, '_' + attr, value)

        return self

    @classmethod
    def _from_rpc(cls, data: RPCEmbedPayload) -> Self:
        transformed_data: EmbedData = {'type': data['type']}

        if 'url' in data:
            transformed_data['url'] = data['url']
        
        if 'rawTitle' in data:
            transformed_data['title'] = data['rawTitle']
        
        if 'rawDescription' in data:
            transformed_data['description'] = data['rawDescription']
        
        if 'referenceId' in data:
            transformed_data['reference_id'] = data['referenceId']

        if 'flags' in data:
            transformed_data['flags'] = data['flags']
        
        if 'contentScanVersion' in data:
            transformed_data['content_scan_version'] = data['contentScanVersion']
        
        if 'timestamp' in data:
            transformed_data['timestamp'] = data['timestamp']
        
        raw_image = data.get('image')
        raw_thumbnail = data.get('thumbnail')
        raw_video = data.get('video')

        if raw_image is None:
            raw_image_animated = None
        else:
            raw_image_animated, transformed_image = _transform_rpc_embed_media_to_api(raw_image)
            transformed_data['image'] = transformed_image

        if raw_thumbnail is None:
            raw_thumbnail_animated = None
        else:
            raw_thumbnail_animated, transformed_thumbnail = _transform_rpc_embed_media_to_api(raw_thumbnail)
            transformed_data['thumbnail'] = transformed_thumbnail

        if raw_video is None:
            raw_video_animated = None
        else:
            raw_video_animated, transformed_video = _transform_rpc_embed_media_to_api(raw_video)
            transformed_data['video'] = transformed_video

        self = cls.from_dict(transformed_data)
        self.id = data['id']
        self.css_color = data.get('color')

        if raw_image_animated is not None and getattr(self, '_image', None) is not None:
            self._image['_animated'] = raw_image_animated  # type: ignore

        if raw_thumbnail_animated is not None and getattr(self, '_thumbnail', None) is not None:
            self._thumbnail['_animated'] = raw_thumbnail_animated  # type: ignore

        if raw_video_animated is not None and getattr(self, '_video', None) is not None:
            self._video['_animated'] = raw_video_animated

        return self

    def copy(self) -> Self:
        """Returns a shallow copy of the embed."""
        return self.__class__.from_dict(self.to_dict())

    def __len__(self) -> int:
        total = len(self.title or '') + len(self.description or '')
        for field in getattr(self, '_fields', []):
            total += len(field['name']) + len(field['value'])

        try:
            footer_text = self._footer['text']
        except (AttributeError, KeyError):
            pass
        else:
            total += len(footer_text)

        try:
            author = self._author
        except AttributeError:
            pass
        else:
            total += len(author['name'])

        return total

    def __bool__(self) -> bool:
        return any(
            (
                self.title,
                self.url,
                self.description,
                self.color,
                self.fields,
                self.timestamp,
                self.author,
                self.thumbnail,
                self.footer,
                self.image,
                self.provider,
                self.video,
                self.reference_id,
                self.content_scan_version,
            )
        )

    def __eq__(self, other: Embed) -> bool:
        return isinstance(other, Embed) and (
            self.type == other.type
            and self.title == other.title
            and self.url == other.url
            and self.description == other.description
            and self.color == other.color
            and self.fields == other.fields
            and self.timestamp == other.timestamp
            and self.author == other.author
            and self.thumbnail == other.thumbnail
            and self.footer == other.footer
            and self.image == other.image
            and self.provider == other.provider
            and self.video == other.video
            and self.reference_id == other.reference_id
            and self.content_scan_version == other.content_scan_version
            and self._flags == other._flags
        )

    @property
    def flags(self) -> EmbedFlags:
        """:class:`EmbedFlags`: The flags of this embed.

        .. versionadded:: 2.5
        """
        return EmbedFlags._from_value(self._flags or 0)

    @property
    def color(self) -> Optional[Color]:
        return getattr(self, '_color', None)

    @color.setter
    def color(self, value: Optional[Union[int, Color]]) -> None:
        if value is None:
            self._color = None
        elif isinstance(value, Color):
            self._color = value
        elif isinstance(value, int):
            self._color = Color(value=value)
        else:
            raise TypeError(f'Expected discord.Color, int, or None but received {value.__class__.__name__} instead.')

    colour = color

    @property
    def css_colour(self) -> Optional[str]:
        return self.css_color

    @property
    def timestamp(self) -> Optional[datetime.datetime]:
        return getattr(self, '_timestamp', None)

    @timestamp.setter
    def timestamp(self, value: Optional[datetime.datetime]) -> None:
        if isinstance(value, datetime.datetime):
            if value.tzinfo is None:
                value = value.astimezone()
            self._timestamp = value
        elif value is None:
            self._timestamp = None
        else:
            raise TypeError(f"Expected datetime.datetime or None received {value.__class__.__name__} instead")

    @property
    def footer(self) -> _EmbedFooterProxy:
        """Returns an ``EmbedProxy`` denoting the footer contents.

        See :meth:`set_footer` for possible values you can access.

        If the attribute has no value then ``None`` is returned.
        """
        # Lying to the type checker for better developer UX.
        return EmbedProxy(getattr(self, '_footer', {}))  # type: ignore

    def set_footer(self, *, text: Optional[Any] = None, icon_url: Optional[Any] = None) -> Self:
        """Sets the footer for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        text: :class:`str`
            The footer text. Can only be up to 2048 characters.
        icon_url: :class:`str`
            The URL of the footer icon. Only HTTP(S) is supported.
            Inline attachment URLs are also supported, see :ref:`local_image`.
        """

        self._footer = {}
        if text is not None:
            self._footer['text'] = str(text)

        if icon_url is not None:
            self._footer['icon_url'] = str(icon_url)

        return self

    def remove_footer(self) -> Self:
        """Clears embed's footer information.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 2.0
        """
        try:
            del self._footer
        except AttributeError:
            pass

        return self

    @property
    def image(self) -> _EmbedMediaProxy:
        """Returns an ``EmbedProxy`` denoting the image contents.

        Possible attributes you can access are:

        - ``url`` for the image URL.
        - ``proxy_url`` for the proxied image URL.
        - ``width`` for the image width.
        - ``height`` for the image height.
        - ``flags`` for the image's attachment flags.

        If the attribute has no value then ``None`` is returned.
        """
        # Lying to the type checker for better developer UX.
        return EmbedMediaProxy(getattr(self, '_image', {}))  # type: ignore

    def set_image(self, *, url: Optional[Any]) -> Self:
        """Sets the image for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        url: Optional[:class:`str`]
            The source URL for the image. Only HTTP(S) is supported.
            If ``None`` is passed, any existing image is removed.
            Inline attachment URLs are also supported, see :ref:`local_image`.
        """

        if url is None:
            try:
                del self._image
            except AttributeError:
                pass
        else:
            self._image: EmbedMediaPayload = {
                'url': str(url),
            }

        return self

    @property
    def thumbnail(self) -> _EmbedMediaProxy:
        """Returns an ``EmbedProxy`` denoting the thumbnail contents.

        Possible attributes you can access are:

        - ``url`` for the thumbnail URL.
        - ``proxy_url`` for the proxied thumbnail URL.
        - ``width`` for the thumbnail width.
        - ``height`` for the thumbnail height.
        - ``flags`` for the thumbnail's attachment flags.

        If the attribute has no value then ``None`` is returned.
        """
        # Lying to the type checker for better developer UX.
        return EmbedMediaProxy(getattr(self, '_thumbnail', {}))  # type: ignore

    def set_thumbnail(self, *, url: Optional[Any]) -> Self:
        """Sets the thumbnail for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        url: Optional[:class:`str`]
            The source URL for the thumbnail. Only HTTP(S) is supported.
            If ``None`` is passed, any existing thumbnail is removed.
            Inline attachment URLs are also supported, see :ref:`local_image`.
        """

        if url is None:
            try:
                del self._thumbnail
            except AttributeError:
                pass
        else:
            self._thumbnail: EmbedMediaPayload = {
                'url': str(url),
            }

        return self

    @property
    def video(self) -> _EmbedMediaProxy:
        """Returns an ``EmbedProxy`` denoting the video contents.

        Possible attributes include:

        - ``url`` for the video URL.
        - ``proxy_url`` for the proxied video URL.
        - ``height`` for the video height.
        - ``width`` for the video width.
        - ``flags`` for the video's attachment flags.

        If the attribute has no value then ``None`` is returned.
        """
        # Lying to the type checker for better developer UX.
        return EmbedMediaProxy(getattr(self, '_video', {}))  # type: ignore

    @property
    def provider(self) -> _EmbedProviderProxy:
        """Returns an ``EmbedProxy`` denoting the provider contents.

        The only attributes that might be accessed are ``name`` and ``url``.

        If the attribute has no value then ``None`` is returned.
        """
        # Lying to the type checker for better developer UX.
        return EmbedProxy(getattr(self, '_provider', {}))  # type: ignore

    @property
    def author(self) -> _EmbedAuthorProxy:
        """Returns an ``EmbedProxy`` denoting the author contents.

        See :meth:`set_author` for possible values you can access.

        If the attribute has no value then ``None`` is returned.
        """
        # Lying to the type checker for better developer UX.
        return EmbedProxy(getattr(self, '_author', {}))  # type: ignore

    def set_author(self, *, name: Any, url: Optional[Any] = None, icon_url: Optional[Any] = None) -> Self:
        """Sets the author for the embed content.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        name: :class:`str`
            The name of the author. Can only be up to 256 characters.
        url: :class:`str`
            The URL for the author.
        icon_url: :class:`str`
            The URL of the author icon. Only HTTP(S) is supported.
            Inline attachment URLs are also supported, see :ref:`local_image`.
        """

        self._author = {
            'name': str(name),
        }

        if url is not None:
            self._author['url'] = str(url)

        if icon_url is not None:
            self._author['icon_url'] = str(icon_url)

        return self

    def remove_author(self) -> Self:
        """Clears embed's author information.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionadded:: 1.4
        """
        try:
            del self._author
        except AttributeError:
            pass

        return self

    @property
    def fields(self) -> List[_EmbedFieldProxy]:
        """List[``EmbedProxy``]: Returns a :class:`list` of ``EmbedProxy`` denoting the field contents.

        See :meth:`add_field` for possible values you can access.

        If the attribute has no value then ``None`` is returned.
        """
        # Lying to the type checker for better developer UX.
        return [EmbedProxy(d) for d in getattr(self, '_fields', [])]  # type: ignore

    def add_field(self, *, name: Any, value: Any, inline: bool = True) -> Self:
        """Adds a field to the embed object.

        This function returns the class instance to allow for fluent-style
        chaining. Can only be up to 25 fields.

        Parameters
        ----------
        name: :class:`str`
            The name of the field. Can only be up to 256 characters.
        value: :class:`str`
            The value of the field. Can only be up to 1024 characters.
        inline: :class:`bool`
            Whether the field should be displayed inline.
        """

        field = {
            'inline': inline,
            'name': str(name),
            'value': str(value),
        }

        try:
            self._fields.append(field)
        except AttributeError:
            self._fields = [field]

        return self

    def insert_field_at(self, index: int, *, name: Any, value: Any, inline: bool = True) -> Self:
        """Inserts a field before a specified index to the embed.

        This function returns the class instance to allow for fluent-style
        chaining. Can only be up to 25 fields.

        .. versionadded:: 1.2

        Parameters
        ----------
        index: :class:`int`
            The index of where to insert the field.
        name: :class:`str`
            The name of the field. Can only be up to 256 characters.
        value: :class:`str`
            The value of the field. Can only be up to 1024 characters.
        inline: :class:`bool`
            Whether the field should be displayed inline.
        """

        field = {
            'inline': inline,
            'name': str(name),
            'value': str(value),
        }

        try:
            self._fields.insert(index, field)
        except AttributeError:
            self._fields = [field]

        return self

    def clear_fields(self) -> Self:
        """Removes all fields from this embed.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. versionchanged:: 2.0
            This function now returns the class instance.
        """
        try:
            self._fields.clear()
        except AttributeError:
            self._fields = []

        return self

    def remove_field(self, index: int) -> Self:
        """Removes a field at a specified index.

        If the index is invalid or out of bounds then the error is
        silently swallowed.

        This function returns the class instance to allow for fluent-style
        chaining.

        .. note::

            When deleting a field by index, the index of the other fields
            shift to fill the gap just like a regular list.

        .. versionchanged:: 2.0
            This function now returns the class instance.

        Parameters
        ----------
        index: :class:`int`
            The index of the field to remove.
        """
        try:
            del self._fields[index]
        except (AttributeError, IndexError):
            pass

        return self

    def set_field_at(self, index: int, *, name: Any, value: Any, inline: bool = True) -> Self:
        """Modifies a field to the embed object.

        The index must point to a valid pre-existing field. Can only be up to 25 fields.

        This function returns the class instance to allow for fluent-style
        chaining.

        Parameters
        ----------
        index: :class:`int`
            The index of the field to modify.
        name: :class:`str`
            The name of the field. Can only be up to 256 characters.
        value: :class:`str`
            The value of the field. Can only be up to 1024 characters.
        inline: :class:`bool`
            Whether the field should be displayed inline.

        Raises
        ------
        IndexError
            An invalid index was provided.
        """

        try:
            field = self._fields[index]
        except (TypeError, IndexError, AttributeError):
            raise IndexError('field index out of range')

        field['name'] = str(name)
        field['value'] = str(value)
        field['inline'] = inline
        return self

    def to_dict(self) -> EmbedData:
        """Converts this embed object into a dict."""

        # add in the raw data into the dict
        # fmt: off
        result = {
            key[1:]: getattr(self, key)
            for key in self.__slots__
            if key[0] == '_' and hasattr(self, key)
        }
        # fmt: on

        # deal with basic convenience wrappers

        try:
            color = result.pop('color')
        except KeyError:
            pass
        else:
            if color:
                result['color'] = color.value

        try:
            timestamp = result.pop('timestamp')
        except KeyError:
            pass
        else:
            if timestamp:
                if timestamp.tzinfo:
                    result['timestamp'] = timestamp.astimezone(tz=datetime.timezone.utc).isoformat()
                else:
                    result['timestamp'] = timestamp.replace(tzinfo=datetime.timezone.utc).isoformat()

        # add in the non raw attribute ones
        if self.type:
            result['type'] = self.type

        if self.description:
            result['description'] = self.description

        if self.url:
            result['url'] = self.url

        if self.title:
            result['title'] = self.title

        if self.reference_id:
            result['reference_id'] = str(self.reference_id)

        if self.content_scan_version is not None:
            result['content_scan_version'] = self.content_scan_version

        return result  # type: ignore # This payload is equivalent to the EmbedData type
