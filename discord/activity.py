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

from copy import copy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple, Union, overload

from .asset import Asset
from .color import Color
from .enums import (
    try_enum,
    ActivityActionType,
    ActivityPartyPrivacy,
    ActivityPlatform,
    ActivityType,
    ClientType,
    OperatingSystem,
    Status,
)
from .flags import (
    ActivityFlags,
    ActivityPlatforms,
)
from .partial_emoji import PartialEmoji
from .utils import MISSING, _get_as_snowflake, cached_slot_property, find, parse_time

__all__ = (
    'BaseActivity',
    '_activity_asset_url',
    'ActivityAssets',
    'ActivityButton',
    'ActivityParty',
    'ActivitySecrets',
    'Activity',
    'Game',
    'Streaming',
    'Spotify',
    'CustomActivity',
    'Session',
    'HeadlessSession',
    'ActivityInvite',
)

if TYPE_CHECKING:
    from typing_extensions import Self

    from .message import MessageApplication, Message
    from .state import ConnectionState
    from .types.presences import (
        SendableActivity as SendableActivityPayload,
        ReceivableActivity as ReceivableActivityPayload,
        ActivityTimestamps,
        ActivityParty as ActivityPartyPayload,
        ActivityAssets as ActivityAssetsPayload,
        ActivitySecrets as ActivitySecretsPayload,
    )
    from .types.gateway import (
        Session as SessionPayload,
        ActivityInviteCreateEvent as ActivityInviteCreateEventPayload,
    )
    from .types.message import MessageActivity as MessageActivityPayload
    from .types.settings import (
        UserSettingsCustomStatus as UserSettingsCustomStatusPayload,
    )
    from .user import User


class BaseActivity:
    """The base activity that all user-settable activities inherit from.
    An user-settable activity is one that can be used in :meth:`Client.change_presence`.

    The following types currently count as user-settable:

    - :class:`Activity`
    - :class:`Game`
    - :class:`Streaming`
    - :class:`CustomActivity`

    Note that although these types are considered user-settable by the library,
    Discord typically ignores certain combinations of activity depending on
    what is currently set. This behavior may change in the future so there are
    no guarantees on whether Discord will actually let you set these types.

    .. versionadded:: 1.3

    Attributes
    ----------
    id: :class:`str`
        The activity's ID. Only unique per user.
    """

    __slots__ = (
        'id',
        '_created_at',
    )

    def __init__(self, **kwargs: Any) -> None:
        self.id: str = kwargs.get('id', '')
        self._created_at: Optional[float] = kwargs.get('created_at')

    @property
    def created_at(self) -> Optional[datetime]:
        """Optional[:class:`~datetime.datetime`]: When the user started doing this activity in UTC.

        .. versionadded:: 1.3
        """
        if self._created_at is not None:
            return datetime.fromtimestamp(self._created_at / 1000, tz=timezone.utc)

    def to_dict(
        self, *, application_id: Optional[int] = MISSING, session_id: Optional[str] = MISSING, state: ConnectionState
    ) -> Optional[SendableActivityPayload]:
        raise NotImplementedError


def _activity_asset_url(image: Optional[str] = None, *, application_id: Optional[int] = None) -> Optional[str]:
    if image is None:
        return None
    elif image.startswith('mp:'):
        return f'https://media.discordapp.net/{image[3:]}'
    elif application_id is not None:
        return Asset.BASE + f'/app-assets/{application_id}/{image}.png'


class ActivityAssets:
    """Represents assets within in :class:`Game` activity.

    .. versionadded:: 3.0

    Attributes
    ----------
    large_image: Optional[:class:`str`]
        An arbitrary string representing the large activity asset image.

        You can find out about format of this string in the :userdoccers:`Discord Userdoccers <resources/presence#activity-asset-image>`.
    large_image_text: Optional[:class:`str`]
        The large image asset hover text of this activity, if applicable.
    small_image: Optional[:class:`str`]
        An arbitrary string representing the small activity asset image.

        You can find out about format of this string in the :userdoccers:`Discord Userdoccers <resources/presence#activity-asset-image>`.
    small_image_text: Optional[:class:`str`]
        The small image asset hover text of this activity, if applicable.
    """

    __slots__ = (
        '_application_id',
        'large_image',
        'large_image_text',
        'small_image',
        'small_image_text',
    )

    def __init__(
        self,
        *,
        large_image: Optional[str] = None,
        large_image_text: Optional[str] = None,
        small_image: Optional[str] = None,
        small_image_text: Optional[str] = None,
    ) -> None:
        self._application_id: Optional[int] = None
        self.large_image: Optional[str] = large_image
        self.large_image_text: Optional[str] = large_image_text
        self.small_image: Optional[str] = small_image
        self.small_image_text: Optional[str] = small_image_text

    @classmethod
    def from_dict(cls, data: ActivityAssetsPayload, application_id: Optional[int] = None) -> Self:
        self = cls(
            large_image=data.get('large_image'),
            large_image_text=data.get('large_text'),
            small_image=data.get('small_image'),
            small_image_text=data.get('small_text'),
        )
        self._application_id = application_id
        return self

    def to_dict(self) -> ActivityAssetsPayload:
        payload: ActivityAssetsPayload = {}

        if self.large_image is not None:
            payload['large_image'] = self.large_image

        if self.large_image_text is not None:
            payload['large_text'] = self.large_image_text

        if self.small_image is not None:
            payload['small_image'] = self.small_image

        if self.small_image_text is not None:
            payload['small_text'] = self.small_image_text

        return payload

    @property
    def large_image_url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns an URL pointing to the large image asset of this activity, if applicable."""
        return _activity_asset_url(self.large_image, application_id=self._application_id)

    @property
    def small_image_url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns an URL pointing to the small image asset of this activity, if applicable."""
        return _activity_asset_url(self.small_image, application_id=self._application_id)


class ActivityButton:
    """A button in :class:`Game` activity.

    .. versionadded:: 3.0

    Attributes
    ----------
    label: :class:`str`
        The button's label.
    url: :class:`str`
        The button's URL.
    """

    __slots__ = (
        'label',
        'url',
    )

    def __init__(self, *, label: str, url: str) -> None:
        self.label: str = label
        self.url: str = url


class ActivityParty:
    """Represents an activity party.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`str`]
        The party's ID.
    current_size: Optional[:class:`int`]
        The party's current size.
    max_size: Optional[:class:`int`]
        The party's max size.
    privacy: Optional[:class:`ActivityPartyPrivacy`]
        The party's privacy level.
    """

    __slots__ = (
        'id',
        'current_size',
        'max_size',
        'privacy',
    )

    def __init__(
        self,
        *,
        id: Optional[str] = None,
        current_size: Optional[int] = None,
        max_size: Optional[int] = None,
        privacy: Optional[ActivityPartyPrivacy] = None,
    ) -> None:
        self.id: Optional[str] = id
        self.current_size: Optional[int] = current_size
        self.max_size: Optional[int] = max_size
        self.privacy: Optional[ActivityPartyPrivacy] = privacy

    @classmethod
    def from_dict(cls, data: ActivityPartyPayload) -> Self:
        current_size = None
        max_size = None

        raw_size = data.get('size')
        if raw_size:
            current_size, max_size, *_ = raw_size

        raw_privacy = data.get('privacy')
        if raw_privacy is None:
            privacy = None
        else:
            privacy = try_enum(ActivityPartyPrivacy, raw_privacy)

        return cls(
            id=data.get('id'),
            current_size=current_size,
            max_size=max_size,
            privacy=privacy,
        )

    def to_dict(self) -> ActivityPartyPayload:
        payload: ActivityPartyPayload = {}

        if self.id is not None:
            payload['id'] = self.id

        if self.current_size is not None and self.max_size is not None:
            payload['size'] = (self.current_size, self.max_size)

        if self.privacy is not None:
            payload['privacy'] = self.privacy.value

        return payload


class ActivitySecrets:
    """Represents secrets of a Discord :class:`Game`.

    .. versionadded:: 3.0

    Attributes
    -----------
    join: Optional[:class:`str`]
        The secret for joining a party. Can be only up to 128 characters.
    spectate: Optional[:class:`str`]
        The secret for spectating a game. Can be only up to 128 characters.

        .. deprecated:: 3.0

            Spectating has been removed from official clients and no longer supported.
    match: Optional[:class:`str`]
        The secret for a specific instanced match. Can be only up to 128 characters.

        .. deprecated:: 3.0
    """

    __slots__ = (
        'join',
        'spectate',
        'match',
    )

    def __init__(self, join: Optional[str], *, spectate: Optional[str] = None, match: Optional[str] = None) -> None:
        self.join: Optional[str] = join
        self.spectate: Optional[str] = spectate
        self.match: Optional[str] = match

    @classmethod
    def from_dict(cls, data: ActivitySecretsPayload) -> Self:
        return cls(
            join=data.get('join'),
            spectate=data.get('spectate'),
            match=data.get('match'),
        )

    def to_dict(self) -> ActivitySecretsPayload:
        payload: ActivitySecretsPayload = {}

        if self.join is not None:
            payload['join'] = self.join

        if self.spectate is not None:
            payload['spectate'] = self.spectate

        if self.match is not None:
            payload['match'] = self.match

        return payload


class Activity(BaseActivity):
    """Represents an activity in Discord.

    This could be an activity such as streaming, playing, listening
    or watching.

    For memory optimization purposes, some activities are offered in slimmed
    down versions:

    - :class:`Game`
    - :class:`Streaming`

    Attributes
    ----------
    name: Optional[:class:`str`]
        The name of the activity.
    type: :class:`ActivityType`
        The type of activity currently being done.
    url: Optional[:class:`str`]
        A stream URL that the activity could be doing.
    session_id: Optional[:class:`str`]
        The ID of the Gateway session the activity is attached to.
    platform: Optional[:class:`ActivityPlatform`]
        The user's current platform.

        .. versionadded:: 2.4

        .. versionchanged:: 3.0

            The type was changed from :class:`str` to :class:`ActivityPlatform`.
    start_timestamp: Optional[:class:`int`]
        Corresponds to when the user started doing the
        activity in milliseconds since Unix epoch.
    end_timestamp: Optional[:class:`int`]:
        Corresponds to when the user will finish doing the
        activity in milliseconds since Unix epoch.
    application_id: Optional[:class:`int`]
        The application ID of the game.
    details: Optional[:class:`str`]
        The detail of the user's current activity.
    state: Optional[:class:`str`]
        The user's current state. For example, "In Game".
    sync_id: Optional[:class:`str`]
        The ID of the synced activity (for example, a Spotify song ID).
    button_labels: List[:class:`str`]
        A list of strings representing the labels of custom buttons shown in a rich presence.

        .. versionadded:: 2.0

        .. versionchanged:: 3.0

            The attribute was renamed from ``buttons`` to ``button_labels``.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji that belongs to this activity.
    party: Optional[:class:`ActivityParty`]
        The party of the activity.
    assets: Optional[:class:`ActivityAssets`]
        The images and their hover text of an activity.
    metadata: Dict[:class:`str`, Any]
        A dictionary representing the activity metadata.


        It contains the following optional keys:

        - ``button_urls``: A list representing URLs correpresenting to the custom buttons shown in Rich Presence.
        - ``artist_ids``: A list representing the Spotify IDs of artists.
        - ``album_id``: A string representing the ID of album of the song being played.
        - ``context_uri``: A string representing the Spotify URI of the current player context.
        - ``type``: A string representing the type of Spotify being played, generally ``track`` or ``episode``.

        See more details on :userdoccers:`Discord Userdoccers <resources/presence#activity-metadata-object>`.

        .. danger::

            Contents inside this attribute are NOT sanitized and can have technically anything. Treat data carefully.
    """

    __slots__ = (
        'id',
        'name',
        'type',
        'url',
        'session_id',
        'platform',
        '_supported_platforms',
        'start_timestamp',
        'end_timestamp',
        'application_id',
        'details',
        'state',
        'sync_id',
        '_flags',
        'button_labels',
        'emoji',
        'party',
        'assets',
        'metadata',
    )

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        activity_type = kwargs.get('type', -1)
        platform = kwargs.get('platform')
        supported_platforms = kwargs.get('supported_platforms')
        timestamps = kwargs.get('timestamps')
        emoji = kwargs.get('emoji')

        self.id: str = kwargs.get('id', '')
        self.name: Optional[str] = kwargs.get('name')
        self.type: ActivityType = (
            activity_type if isinstance(activity_type, ActivityType) else try_enum(ActivityType, activity_type)
        )
        self.url: Optional[str] = kwargs.get('url')
        self.session_id: Optional[str] = kwargs.get('session_id')

        if platform is None:
            self.platform: Optional[ActivityPlatform] = None
        elif isinstance(platform, ActivityPlatform):
            self.platform = platform
        else:
            self.platform = try_enum(ActivityPlatform, platform)

        if supported_platforms is None:
            self._supported_platforms: Optional[int] = None
        elif isinstance(supported_platforms, ActivityPlatforms):
            self._supported_platforms = supported_platforms.value
        else:
            self._supported_platforms = supported_platforms

        if timestamps:
            self.start_timestamp: Optional[int] = timestamps.get('start')
            self.end_timestamp: Optional[int] = timestamps.get('end')
        else:
            self.start_timestamp = None
            self.end_timestamp = None

        self.application_id: Optional[int] = _get_as_snowflake(kwargs, 'application_id')
        self.details: Optional[str] = kwargs.get('details')
        self.state: Optional[str] = kwargs.get('state')
        self.sync_id: Optional[str] = kwargs.get('sync_id')
        self._flags: int = kwargs.get('flags', 0)

        try:
            self.button_labels: List[str] = kwargs['buttons']
        except KeyError:
            self.button_labels = []

        self.emoji: Optional[PartialEmoji] = None if emoji is None else PartialEmoji.from_dict(emoji)
        self.party: Optional[ActivityParty] = kwargs.get('party')
        self.assets: Optional[ActivityAssets] = kwargs.get('assets')

        try:
            self.metadata: Dict[str, Any] = kwargs['metadata']
        except KeyError:
            self.metadata = {}

    def __repr__(self) -> str:
        attrs = (
            ('name', self.name),
            ('type', self.type),
            ('url', self.url),
            ('session_id', self.session_id),
            ('platform', self.platform),
            ('application_id', self.application_id),
            ('details', self.details),
            ('emoji', self.emoji),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<Activity {inner}>'

    def to_dict(
        self, *, application_id: Optional[int] = MISSING, session_id: Optional[str] = MISSING, state: ConnectionState
    ) -> Optional[SendableActivityPayload]:
        ret: Dict[str, Any] = {}
        for attr in self.__slots__:
            value = getattr(self, attr, None)
            if value is None:
                continue

            if isinstance(value, dict) and len(value) == 0:
                continue

            if attr.startswith('_'):
                attr = attr[1:]

            if hasattr(value, 'to_dict'):
                value = value.to_dict()  # type: ignore

            ret[attr] = value

        ret['type'] = int(self.type)
        if self.emoji:
            ret['emoji'] = self.emoji.to_dict()

        return ret  # type: ignore

    @property
    def start(self) -> Optional[datetime]:
        """Optional[:class:`~datetime.datetime`]: When the user started doing this activity in UTC, if applicable."""
        if self.start_timestamp:
            timestamp = self.start_timestamp / 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return None

    @property
    def end(self) -> Optional[datetime]:
        """Optional[:class:`~datetime.datetime`]: When the user will stop doing this activity in UTC, if applicable."""
        if self.end_timestamp:
            timestamp = self.end_timestamp
            return datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return None

    @property
    def large_image_url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns a URL pointing to the large image asset of this activity, if applicable."""
        if self.assets:
            return self.assets.large_image_url
        return None

    @property
    def small_image_url(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns a URL pointing to the small image asset of this activity, if applicable."""
        if self.assets:
            return self.assets.small_image_url
        return None

    @property
    def large_image_text(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the large image asset hover text of this activity, if applicable."""
        if self.assets:
            return self.assets.large_image_text
        return None

    @property
    def small_image_text(self) -> Optional[str]:
        """Optional[:class:`str`]: Returns the small image asset hover text of this activity, if applicable."""
        if self.assets:
            return self.assets.small_image_text
        return None


class Game(BaseActivity):
    """A slimmed down version of :class:`Activity` that represents a Discord game.

    This is typically displayed via **Playing** on the official Discord client.

    The parameters are mostly same as attributes, with additional ones detailed below.

    .. container:: operations

        .. describe:: x == y

            Checks if two games are equal.

        .. describe:: x != y

            Checks if two games are not equal.

        .. describe:: hash(x)

            Returns the game's hash.

        .. describe:: str(x)

            Returns the game's name.

    Parameters
    ----------
    supported_platforms: Optional[:class:`ActivityPlatforms`]
        The platforms the game is supported on.

    Attributes
    ----------
    name: :class:`str`
        The game's name.
    session_id: Optional[:class:`str`]
        The ID of the Gateway session the activity is attached to.
    platform: Optional[:class:`ActivityPlatform`]
        Where the user is playing from (ie. PS5, Xbox).

        .. versionadded:: 2.4

        .. versionchanged:: 3.0

            The type was changed from :class:`str` to :class:`ActivityPlatform`.
    application_id: Optional[:class:`int`]
        The game's application ID.
    parent_application_id: Optional[:class:`int`]
        The game's parent application ID.
    details: Optional[:class:`str`]
        The game's details.
    state: Optional[:class:`str`]
        The game's state.
    button_labels: List[:class:`str`]
        A list of strings representing the labels of custom buttons shown in a rich presence.

        .. versionadded:: 2.0

        .. versionchanged:: 3.0

            The attribute was renamed from ``buttons`` to ``button_labels``.
    party: Optional[:class:`ActivityParty`]
        The party of the activity.
    assets: Optional[:class:`ActivityAssets`]
        The images and their hover text of an activity.
    secrets: Optional[:class:`ActivitySecrets`]
        The secrets for joining/spectating a game.
    metadata: Dict[:class:`str`, Any]
        A dictionary representing the activity metadata.

        It contains the following optional keys:

        - ``button_urls``: A list representing URLs correpresenting to the custom buttons shown in Rich Presence.
        - ``artist_ids``: A list representing the Spotify IDs of artists.
        - ``album_id``: A string representing the ID of album of the song being played.
        - ``context_uri``: A string representing the Spotify URI of the current player context.
        - ``type``: A string representing the type of Spotify being played, generally ``track`` or ``episode``.

        See more details on :userdoccers:`Discord Userdoccers <resources/presence#activity-metadata-object>`.

        .. danger::

            Contents inside this attribute are NOT sanitized and can have technically anything. Treat data carefully."
    """

    __slots__ = (
        'name',
        'session_id',
        'platform',
        '_supported_platforms',
        'start_timestamp',
        'end_timestamp',
        'application_id',
        'parent_application_id',
        'details',
        'state',
        '_flags',
        'button_labels',
        'party',
        'assets',
        'secrets',
        'metadata',
    )

    def __init__(self, details: Optional[str] = None, **extra: Any) -> None:
        super().__init__(**extra)

        platform = extra.get('platform')
        supported_platforms = extra.get('supported_platforms')
        timestamps = extra.get('timestamps')

        self.name: str = extra.get('name', '')
        self.session_id: Optional[str] = extra.get('session_id')

        if platform is None:
            self.platform: Optional[ActivityPlatform] = None
        elif isinstance(platform, ActivityPlatform):
            self.platform = platform
        else:
            self.platform = try_enum(ActivityPlatform, platform)

        if supported_platforms is None:
            self._supported_platforms: Optional[int] = None
        elif isinstance(supported_platforms, ActivityPlatforms):
            self._supported_platforms = supported_platforms.value
        else:
            self._supported_platforms = supported_platforms

        if timestamps:
            self.start_timestamp: int = timestamps.get('start', 0)
            self.end_timestamp: int = timestamps.get('end', 0)
        else:
            self.start_timestamp = 0
            self.end_timestamp = 0

        self.application_id: Optional[int] = _get_as_snowflake(extra, 'application_id')
        self.parent_application_id: Optional[int] = _get_as_snowflake(extra, 'parent_application_id')
        self.details: Optional[str] = details
        self.state: Optional[str] = extra.get('state')
        self._flags: int = extra.get('flags', 0)

        try:
            self.button_labels: List[str] = extra['buttons']
        except KeyError:
            self.button_labels = []

        self.party: Optional[ActivityParty] = extra.get('party')
        self.assets: Optional[ActivityAssets] = extra.get('assets')
        self.secrets: Optional[ActivitySecrets] = extra.get('secrets')

        try:
            self.metadata: Dict[str, Any] = extra['metadata']
        except KeyError:
            self.metadata = {}

    @property
    def supported_platforms(self) -> Optional[ActivityPlatforms]:
        """Optional[:class:`ActivityPlatforms`]: The platforms the game is supported on."""
        if self._supported_platforms is not None:
            return ActivityPlatforms._from_value(self._supported_platforms)

    @property
    def flags(self) -> ActivityFlags:
        """:class:`ActivityFlags`: The activity's flags."""
        return ActivityFlags._from_value(self._flags)

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the game's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.playing`.
        """
        return ActivityType.playing

    @property
    def start(self) -> Optional[datetime]:
        """Optional[:class:`~datetime.datetime`]: When the user started playing this game in UTC, if applicable."""
        if self.start_timestamp:
            return datetime.fromtimestamp(self.start_timestamp / 1000, tz=timezone.utc)
        return None

    @property
    def end(self) -> Optional[datetime]:
        """Optional[:class:`~datetime.datetime`]: When the user will stop playing this game in UTC, if applicable."""
        if self.end_timestamp:
            return datetime.fromtimestamp(self.end_timestamp / 1000, tz=timezone.utc)
        return None

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return f'<Game name={self.name!r}>'

    def add_button(self, label: str, *, url: str) -> Self:
        """Adds a button.

        Parameters
        ----------
        label: :class:`str`
            The label of the button.
        url: :class:`str`
            The URL of the button.

        Returns
        -------
        :class:`Game`
            The current instance, for chaining.
        """

        self.button_labels.append(label)

        try:
            button_urls = self.metadata['button_urls']
        except KeyError:
            self.metadata['button_urls'] = [url]
        else:
            button_urls.append(url)

        return self

    def to_dict(
        self, *, application_id: Optional[int] = MISSING, session_id: Optional[str] = MISSING, state: ConnectionState
    ) -> Optional[SendableActivityPayload]:
        # {"d":{"activities":[{
        #   "application_id":1169421761859833997,"flags":0,"name":"Hackplug",
        #   "session_id":"e7a6641eb5889041e7618e6b76111620","type":0}],"afk":false,"since":"0","status":"idle"},"op":3}

        if application_id is MISSING:
            if self.application_id is None:
                application_id = state.application_id
            else:
                application_id = self.application_id

        if session_id is MISSING:
            session = state.current_session
            if session:
                session_id = session.id
            else:
                session_id = None

        timestamps: ActivityTimestamps = {}

        if self.start_timestamp:
            timestamps['start'] = self.start_timestamp
        if self.end_timestamp:
            timestamps['end'] = self.end_timestamp

        payload: Dict[str, Any] = {
            'application_id': application_id,
        }
        if self.assets:
            payload['assets'] = self.assets

        if self.button_labels:
            payload['buttons'] = self.button_labels

        # if self.buttons:
        #     payload['buttons'] = [button.label for button in self.buttons]
        #     metadata = {'button_urls': [button.url for button in self.buttons]}

        if self.details is not None:
            payload['details'] = self.details

        payload['flags'] = self._flags
        if self.metadata:
            payload['metadata'] = self.metadata

        payload['name'] = self.name or state.application_name or ''
        if self.parent_application_id:
            payload['parent_application_id'] = self.parent_application_id

        if self.party:
            party = self.party.to_dict()
            if party:
                payload['party'] = party

        if self.platform:
            payload['platform'] = self.platform.value

        if session_id is not None:
            payload['session_id'] = session_id

        if self.state is not None:
            payload['state'] = self.state

        if self._supported_platforms is not None:
            payload['supported_platforms'] = ActivityPlatforms._from_value(self._supported_platforms).to_string_array()

        payload['type'] = self.type.value
        return payload  # type: ignore

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Game) and other.name == self.name

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)


class Streaming(BaseActivity):
    """A slimmed down version of :class:`Activity` that represents a Discord streaming status.

    This is typically displayed via **Streaming** on the official Discord client.

    .. container:: operations

        .. describe:: x == y

            Checks if two streams are equal.

        .. describe:: x != y

            Checks if two streams are not equal.

        .. describe:: hash(x)

            Returns the stream's hash.

        .. describe:: str(x)

            Returns the stream's name.

    Attributes
    ----------
    platform: Optional[:class:`str`]
        Where the user is streaming from (ie. YouTube, Twitch).

        .. versionadded:: 1.3

    name: Optional[:class:`str`]
        The stream's name.
    details: Optional[:class:`str`]
        An alias for :attr:`name`.
    game: Optional[:class:`str`]
        The game being streamed.

        .. versionadded:: 1.3

    url: :class:`str`
        The stream's URL.
    assets: :class:`ActivityAssets`
    """

    # assets is used to be documented as "A dictionary comprising of similar keys than those in :attr:`Activity.assets`."

    __slots__ = (
        'platform',
        'name',
        'game',
        'url',
        'details',
        'state',
        'assets',
    )

    def __init__(self, *, name: Optional[str], url: str, **extra: Any) -> None:
        super().__init__(**extra)
        self.platform: Optional[str] = name
        self.name: Optional[str] = extra.get('details', name)
        self.game: Optional[str] = extra.get('state', None)
        self.url: str = url
        self.details: Optional[str] = extra.get('details', self.name)  # compatibility
        self.state: Optional[str] = extra.get('state')

        raw_assets = extra.get('assets')
        self.assets: ActivityAssets

        if raw_assets:
            if isinstance(raw_assets, ActivityAssets):
                self.assets = raw_assets
            else:
                self.assets = ActivityAssets.from_dict(raw_assets, None)
        else:
            self.assets = ActivityAssets()

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the game's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.streaming`.
        """
        return ActivityType.streaming

    def __str__(self) -> str:
        return str(self.name)

    def __repr__(self) -> str:
        return f'<Streaming name={self.name!r}>'

    @property
    def twitch_name(self) -> Optional[str]:
        """Optional[:class:`str`]: If provided, the Twitch name of the user streaming.

        This corresponds to the ``large_image`` key of the :attr:`Streaming.assets`
        dictionary if it starts with ``twitch:``. Typically set by the Discord client.
        """

        name = self.assets.large_image
        if name and name[:7] == 'twitch:':
            return name[7:]

        return None

    def to_dict(
        self, *, application_id: Optional[int] = MISSING, session_id: Optional[str] = MISSING, state: ConnectionState
    ) -> Optional[SendableActivityPayload]:
        # Reconstructed from async _checkTwitch(e){

        payload: Dict[str, Any] = {
            'type': ActivityType.streaming.value,
            'url': str(self.url),
            'name': str(self.name),
            'assets': self.assets.to_dict(),
        }
        if self.details:
            payload['details'] = self.details
        if self.state:
            payload['state'] = self.state

        return payload  # type: ignore

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Streaming) and other.name == self.name and other.url == self.url

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.name)


# TODO: Spotify class really needs a refactor too...
class Spotify:
    """Represents a Spotify listening activity from Discord. This is a special case of
    :class:`Activity` that makes it easier to work with the Spotify integration.

    .. container:: operations

        .. describe:: x == y

            Checks if two activities are equal.

        .. describe:: x != y

            Checks if two activities are not equal.

        .. describe:: hash(x)

            Returns the activity's hash.

        .. describe:: str(x)

            Returns the string 'Spotify'.
    """

    __slots__ = ('_state', '_details', '_timestamps', '_assets', '_party', '_sync_id', '_session_id', '_created_at')

    def __init__(self, **data: Any) -> None:
        self._state: str = data.get('state', '')
        self._details: str = data.get('details', '')
        self._timestamps: ActivityTimestamps = data.get('timestamps') or {}
        self._assets: ActivityAssetsPayload = data.get('assets') or {}
        self._party: ActivityPartyPayload = data.get('party') or {}
        self._sync_id: str = data.get('sync_id', '')
        self._session_id: Optional[str] = data.get('session_id', None)
        self._created_at: Optional[float] = data.get('created_at', None)

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the activity's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.listening`.
        """
        return ActivityType.listening

    @property
    def created_at(self) -> Optional[datetime]:
        """Optional[:class:`~datetime.datetime`]: When the user started listening in UTC.

        .. versionadded:: 1.3
        """
        if self._created_at is not None:
            return datetime.fromtimestamp(self._created_at / 1000, tz=timezone.utc)

    @property
    def color(self) -> Color:
        """:class:`Color`: Returns the Spotify integration color, as a :class:`Color`.

        There is an alias for this named :attr:`colour`.
        """
        return Color(0x1DB954)

    @property
    def colour(self) -> Color:
        """:class:`Colour`: Returns the Spotify integration colour, as a :class:`Colour`.

        This is an alias of :attr:`color`.
        """
        return self.color

    def to_dict(
        self, *, application_id: Optional[int] = MISSING, session_id: Optional[str] = MISSING, state: ConnectionState
    ) -> Optional[SendableActivityPayload]:
        return {
            'name': 'Spotify',
            'assets': self._assets,
            'details': self._details,
            'state': self._state,
            'timestamps': self._timestamps,  # always sent as {start: f, end: f + c}
            'party': self._party,  # always sent as {id: n}
            # if !is_local, then insert these fields:
            'sync_id': self._sync_id,
            'flags': 48,  # PLAY | SYNC
            # 'metadata': {
            #   'context_uri': NotRequired[str],
            #   'album_id': str,
            #   'artist_ids': List[str],
            #   'type': ???,
            #   'button_urls': [],
            # },
        }

    @property
    def name(self) -> str:
        """:class:`str`: The activity's name. This will always return "Spotify"."""
        return 'Spotify'

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Spotify)
            and other._session_id == self._session_id
            and other._sync_id == self._sync_id
            and other.start == self.start
        )

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self._session_id)

    def __str__(self) -> str:
        return 'Spotify'

    def __repr__(self) -> str:
        return f'<Spotify title={self.title!r} artist={self.artist!r} track_id={self.track_id!r}>'

    @property
    def title(self) -> str:
        """:class:`str`: The title of the song being played."""
        return self._details

    @property
    def artists(self) -> List[str]:
        """List[:class:`str`]: The artists of the song being played."""
        return self._state.split('; ')

    @property
    def artist(self) -> str:
        """:class:`str`: The artist of the song being played.

        This does not attempt to split the artist information into
        multiple artists. Useful if there's only a single artist.
        """
        return self._state

    @property
    def album(self) -> str:
        """:class:`str`: The album that the song being played belongs to."""
        return self._assets.get('large_text', '')

    @property
    def album_cover_url(self) -> str:
        """:class:`str`: The album cover image URL from Spotify's CDN."""
        large_image = self._assets.get('large_image', '')
        if large_image[:8] != 'spotify:':
            return ''
        album_image_id = large_image[8:]
        return 'https://i.scdn.co/image/' + album_image_id

    @property
    def track_id(self) -> str:
        """:class:`str`: The track ID used by Spotify to identify this song."""
        return self._sync_id

    @property
    def track_url(self) -> str:
        """:class:`str`: The track URL to listen on Spotify.

        .. versionadded:: 2.0
        """
        return f'https://open.spotify.com/track/{self.track_id}'

    @property
    def start(self) -> datetime:
        """:class:`~datetime.datetime`: When the user started playing this song in UTC."""
        # the start key will be present here
        return datetime.fromtimestamp(self._timestamps['start'] / 1000, tz=timezone.utc)  # type: ignore

    @property
    def end(self) -> datetime:
        """:class:`~datetime.datetime`: When the user will stop playing this song in UTC."""
        # the end key will be present here
        return datetime.fromtimestamp(self._timestamps['end'] / 1000, tz=timezone.utc)  # type: ignore

    @property
    def duration(self) -> timedelta:
        """:class:`~datetime.timedelta`: The duration of the song being played."""
        return self.end - self.start

    @property
    def party_id(self) -> str:
        """:class:`str`: The party ID of the listening party."""
        return self._party.get('id', '')


class CustomActivity(BaseActivity):
    """Represents a custom activity from Discord.

    .. container:: operations

        .. describe:: x == y

            Checks if two activities are equal.

        .. describe:: x != y

            Checks if two activities are not equal.

        .. describe:: hash(x)

            Returns the activity's hash.

        .. describe:: str(x)

            Returns the custom status text.

    .. versionadded:: 1.3

    Attributes
    ----------
    name: Optional[:class:`str`]
        The custom activity's name.
    emoji: Optional[:class:`PartialEmoji`]
        The emoji to pass to the activity, if any.
    expires_at: Optional[:class:`~datetime.datetime`]
        When the custom activity will expire. This is only available from :attr:`UserSettings.custom_activity`.
    """

    __slots__ = ('name', 'emoji', 'state', 'expires_at')

    def __init__(
        self,
        name: Optional[str],
        *,
        emoji: Optional[Union[PartialEmoji, Dict[str, Any], str]] = None,
        state: Optional[str] = None,
        expires_at: Optional[datetime] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if name == 'Custom Status':
            name = state
        self.name: Optional[str] = name
        self.expires_at: Optional[datetime] = expires_at

        self.emoji: Optional[PartialEmoji]
        if emoji is None:
            self.emoji = emoji
        elif isinstance(emoji, dict):
            self.emoji = PartialEmoji.from_dict(emoji)
        elif isinstance(emoji, str):
            self.emoji = PartialEmoji(name=emoji)
        elif isinstance(emoji, PartialEmoji):
            self.emoji = emoji
        else:
            raise TypeError(f'Expected str, PartialEmoji, or None, received {type(emoji)!r} instead.')

    @property
    def type(self) -> ActivityType:
        """:class:`ActivityType`: Returns the activity's type. This is for compatibility with :class:`Activity`.

        It always returns :attr:`ActivityType.custom`.
        """
        return ActivityType.custom

    @classmethod
    def from_user_settings_payload(cls, data: UserSettingsCustomStatusPayload) -> Optional[Self]:
        emoji_id = _get_as_snowflake(data, 'emoji_id')
        emoji_name = data.get('emoji_name')

        if emoji_id is None and emoji_name is None:
            emoji = None
        else:
            emoji = PartialEmoji(
                name=emoji_name or '',
                id=emoji_id,
            )

        text = data.get('text')
        if text is None and emoji is None:
            return None

        expires_at = parse_time(data.get('expires_at'))

        return cls(
            text,
            emoji=emoji,
            expires_at=expires_at,
        )

    def to_user_settings_payload(self) -> UserSettingsCustomStatusPayload:
        payload: Dict[str, Any] = {
            'text': self.name,
        }
        if self.emoji is not None:
            emoji_payload = {}

            emoji_id = self.emoji.id
            emoji_name = self.emoji.name
            if emoji_id is not None and emoji_id != 0:
                emoji_payload['id'] = str(emoji_id)
            if emoji_name is not None and len(emoji_name):
                emoji_payload['name'] = emoji_name
            payload['emoji'] = emoji_payload

        if self.expires_at is not None:
            payload['expires_at'] = self.expires_at.isoformat()

        return payload  # type: ignore

    def to_dict(
        self, *, application_id: Optional[int] = MISSING, session_id: Optional[str] = MISSING, state: ConnectionState
    ) -> Optional[SendableActivityPayload]:
        if not self.name:
            return None

        o = {
            'flags': 0,
            'name': 'Custom Status',
            'state': self.name,  # :(
            'type': ActivityType.custom.value,
        }
        # For some reason, SDK doesn't send emoji here, so we won't send it too :(
        # if self.emoji:
        #    o['emoji'] = self.emoji.to_dict()
        return o  # type: ignore

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, CustomActivity)
            and other.name == self.name
            and other.emoji == self.emoji
            and other.expires_at == self.expires_at
        )

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash((self.name, str(self.emoji)))

    def __str__(self) -> str:
        if self.emoji:
            if self.name:
                return f'{self.emoji} {self.name}'
            return str(self.emoji)
        else:
            return str(self.name)

    def __repr__(self) -> str:
        return f'<CustomActivity name={self.name!r} emoji={self.emoji!r}>'


class Session:
    """Represents a connected Discord gateway session.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two sessions are equal.

        .. describe:: x != y

            Checks if two sessions are not equal.

        .. describe:: hash(x)

            Returns the session's hash.

    Attributes
    ----------
    id: :class:`str`
        The session ID.
    active: :class:`bool`
        Whether the session is active.
    os: :class:`OperatingSystem`
        The operating system the session is running on.
    client: :class:`ClientType`
        The client the session is running on.
    version: :class:`int`
        The version of the client the session is running on (used for differentiating between e.g. PS4/PS5).
    status: :class:`Status`
        The status of the session.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The activities the session is currently doing.
    hidden_activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`]]
        The hidden activities the session is currently doing.
    """

    __slots__ = (
        '_state',
        'id',
        'active',
        'os',
        'client',
        'version',
        'status',
        'activities',
        'hidden_activities',
    )

    def __init__(self, *, data: SessionPayload, state: ConnectionState):
        self._state = state
        client_info = data['client_info']

        self.id: str = data['session_id']
        self.os: OperatingSystem = OperatingSystem.from_string(client_info['os'])
        self.client: ClientType = try_enum(ClientType, client_info['client'])
        self.version: int = client_info.get('version', 0)
        self._update(data)

    def _update(self, data: SessionPayload):
        state = self._state

        # Only these should ever change
        self.active: bool = data.get('active', False)
        self.status: Status = try_enum(Status, data['status'])
        self.activities: Tuple[ActivityTypes, ...] = tuple(
            create_activity(activity, state) for activity in data.get('activities', ())
        )
        self.hidden_activities: Tuple[ActivityTypes, ...] = tuple(
            create_activity(activity, state) for activity in data.get('hidden_activities', ())
        )

    def __repr__(self) -> str:
        return f'<Session id={self.id!r} active={self.active!r} status={self.status!r} activities={self.activities!r}>'

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Session) and self.id == other.id

    def __ne__(self, other: object) -> bool:
        if isinstance(other, Session):
            return self.id != other.id
        return True

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def _fake_all(cls, *, state: ConnectionState, data: SessionPayload) -> Self:
        self = cls.__new__(cls)
        self._state = state
        self.id = 'all'
        self.os = OperatingSystem.unknown
        self.client = ClientType.unknown
        self.version = 0
        self._update(data)
        return self

    def is_overall(self) -> bool:
        """:class:`bool`: Whether the session represents the overall presence across all platforms.

        .. note::

            If this is ``True``, then :attr:`id`, :attr:`os`, and :attr:`client` will not be real values.
        """
        return self.id == 'all'

    def is_headless(self) -> bool:
        """:class:`bool`: Whether the session is headless."""
        return self.id.startswith('h:')

    def is_current(self) -> bool:
        """:class:`bool`: Whether the session is the current session."""
        ws = self._state._get_websocket()
        return False if ws is None else self.id == ws.session_id


class HeadlessSession:
    """Represents a headless session.

    A headless session is a session that does not have Gateway connection (nor requires it) and primarily used to set Rich Presence.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: Optional[:class:`str`]
        The ID of the headless session.
    token: :class:`str`
        The session's token.
    activities: Tuple[Union[:class:`BaseActivity`, :class:`Spotify`], ...]
        The activities.
    """

    __slots__ = (
        '_state',
        'id',
        'token',
        'activities',
    )

    def __init__(self, *, token: str, activities: Tuple[ActivityTypes, ...], state: ConnectionState) -> None:
        self._state: ConnectionState = state

        # Headless session IDs are generally in following format: ``h:733035e1465e89eee843bdc1c240``
        session_id = None
        for activity in activities:
            if hasattr(activity, 'session_id'):
                session_id = activity.session_id  # type: ignore
                if session_id is not None:
                    break

        self.id: Optional[str] = session_id
        self.token: str = token
        self.activities: Tuple[ActivityTypes, ...] = activities

    async def delete(self) -> None:
        """|coro|

        Deletes the headless session.

        Raises
        ------
        HTTPException
            The session token is invalid, or deleting the headless session failed.
        """
        await self._state.http.delete_headless_session(self.token)

    async def edit(
        self, *, activities: List[ActivityTypes] = MISSING, application_id: Optional[int] = MISSING
    ) -> HeadlessSession:
        """|coro|

        Edits the headless session.

        All parameters are optional. If no parameters were passed, a HTTP request will be not done;
        instead, this method will return ``copy(self)``.

        Parameters
        ----------
        activities: List[Union[:class:`BaseActivity`, :class:`Spotify`], ...]
            The new activities. This must contain exactly single activity.

        Raises
        ------
        HTTPException
            The session token is invalid, or editing the headless session failed.

        Returns
        -------
        :class:`HeadlessSession`
            The newly updated session.
        """
        if activities is MISSING:
            return copy(self)

        state = self._state
        activities_data = []
        for a in activities:
            activity_data = a.to_dict(application_id=application_id, session_id=None, state=state)
            if activity_data is not None:
                activities_data.append(activity_data)

        data = await state.http.create_headless_session(
            activities=activities_data,
            token=self.token,
        )
        return HeadlessSession(
            token=data['token'],
            activities=tuple(create_activity(d, state) for d in data['activities']),
            state=state,
        )


class ActivityInvite:
    """Represents an activity invite.

    .. versionadded:: 3.0

    Attributes
    ----------
    channel_id: Optional[:class:`int`]
        The ID of the channel the message was sent in.
    message_id: Optional[:class:`int`]
        The ID of the message associated with this invite.
    author: Optional[:class:`User`]
        The user who created this invite.
    application: Optional[:class:`MessageApplication`]
        The application associated with this invite.
    activity: Optional[:class:`dict`]
        The activity associated with this invite.

        This is a dictionary with the following optional keys:

        - ``type``: An integer denoting the type of message activity being requested.
        - ``party_id``: The party ID associated with the party.
    """

    __slots__ = (
        '_state',
        '_message',
        'channel_id',
        'message_id',
        'author',
        'application',
        'activity',
    )

    def __init__(
        self,
        *,
        channel_id: Optional[int],
        message: Optional[Message] = None,
        message_id: Optional[int] = None,
        author: Optional[User] = None,
        application: Optional[MessageApplication] = None,
        activity: Optional[MessageActivityPayload] = None,
        state: ConnectionState,
    ) -> None:
        self._state: ConnectionState = state
        self._message: Optional[Message] = message
        self.channel_id: Optional[int] = channel_id
        self.message_id: Optional[int] = message_id
        self.author: Optional[User] = author
        self.application: Optional[MessageApplication] = application
        self.activity: Optional[MessageActivityPayload] = activity

    @cached_slot_property('_cs_message')
    def message(self) -> Optional[Message]:
        """Optional[:class:`~discord.Message`]: The message associated with this Rich Presence invite."""
        return self._message or self._state._get_message(self.message_id)

    @classmethod
    def from_event(cls, data: ActivityInviteCreateEventPayload, state: ConnectionState) -> Self:
        from .message import MessageApplication

        raw_author = data.get('author')
        raw_application = data.get('application')

        if raw_author is None:
            author = None
        else:
            author = state.store_user(raw_author, cache=False)

        if raw_application is None:
            application = None
        else:
            application = MessageApplication(data=raw_application, state=state)

        return cls(
            channel_id=_get_as_snowflake(data, 'channel_id'),
            message=None,
            message_id=_get_as_snowflake(data, 'message_id'),
            author=author,
            application=application,
            activity=data.get('activity'),
            state=state,
        )

    @classmethod
    def from_message(cls, message: Message) -> Self:
        from .member import Member

        state = message._state

        if isinstance(message.author, Member):
            # Downgrade Member to User
            author = message.author._user
        else:
            author = message.author

        return cls(
            channel_id=message.channel.id,
            message=message,
            message_id=message.id,
            author=author,
            application=message.application,
            activity=message.activity,
            state=state,
        )

    async def accept_activity_invite(
        self, *, application_id: Optional[int] = MISSING, session_id: Optional[str] = MISSING, state: ConnectionState
    ) -> str:
        """|coro|

        Accepts an activity invite.

        Parameters
        ----------
        session_id: Optional[:class:`str`]
            The session ID. Only required if user presence
            is unavailable (e.g. due to being not connected to Gateway).

        Raises
        ------
        Forbidden
            You are not allowed to accept activity invites.
        HTTPException
            Accepting activity invite failed.
        """
        activity = self.activity
        if not activity:
            raise TypeError('Invite does not have activity')

        application = self.application
        if not application:
            raise TypeError('Application is unavailable for some reason')

        author_id = 0
        if session_id is None:
            if self.author is None:
                raise TypeError('Please set session ID manually')
            author_id = self.author.id

            r = self.author.relationship
            if r is None:
                raise TypeError('Cannot get user activities')
            activities = r.activities

            a = find(
                lambda a, /: (
                    isinstance(a, Game) and a.application_id == application.id and a.party == activity['party_id']
                ),
                activities,
            )
            if a is None:
                raise TypeError('Invite is invalid')

            assert isinstance(a, Game), 'Invite is not game invite'
            session_id = a.session_id or ''

        data = await self._state.http.get_activity_secret(
            author_id,
            session_id,
            application.id,
            ActivityActionType.join.value,
            channel_id=self.channel_id or 0,
            message_id=self.message_id or 0,
        )
        return data['secret']


ActivityTypes = Union[Activity, Game, CustomActivity, Streaming, Spotify]


@overload
def create_activity(
    data: Union[ReceivableActivityPayload, SendableActivityPayload], state: ConnectionState
) -> ActivityTypes:
    ...


@overload
def create_activity(data: None, state: ConnectionState) -> None:
    ...


def create_activity(
    data: Optional[Union[ReceivableActivityPayload, SendableActivityPayload]], state: ConnectionState
) -> Optional[ActivityTypes]:
    if not data:
        return None

    game_type = try_enum(ActivityType, data.get('type', -1))
    if game_type is ActivityType.playing and 'application_id' not in data and 'session_id' not in data:
        cls = Game
    elif game_type is ActivityType.custom and 'name' in data:
        ret = CustomActivity(**data)  # type: ignore
        if isinstance(ret.emoji, PartialEmoji):
            ret.emoji._state = state
        return ret
    elif game_type is ActivityType.streaming and 'url' in data:
        # The URL won't be None here
        return Streaming(**data)  # type: ignore
    elif game_type is ActivityType.listening and 'sync_id' in data and 'session_id' in data:
        return Spotify(**data)
    else:
        cls = Activity

    transformed_kwargs: Optional[Dict[str, Any]] = None

    raw_supported_platforms = data.get('supported_platforms')
    raw_party = data.get('party')
    raw_assets = data.get('assets')

    if raw_supported_platforms is not None:
        supported_platforms = ActivityPlatforms.from_string_array(raw_supported_platforms).value

        if transformed_kwargs is None:
            transformed_kwargs = {'supported_platforms': supported_platforms}
        else:
            transformed_kwargs['supported_platforms'] = supported_platforms

    if raw_party is not None:
        party = ActivityParty.from_dict(raw_party)

        if transformed_kwargs is None:
            transformed_kwargs = {'party': party}
        else:
            transformed_kwargs['party'] = party

    if raw_assets is not None:
        assets = ActivityAssets.from_dict(raw_assets)

        if transformed_kwargs is None:
            transformed_kwargs = {'assets': assets}
        else:
            transformed_kwargs['assets'] = assets

    if transformed_kwargs:
        transformed_kwargs = {**data, **transformed_kwargs}
        ret = cls(**transformed_kwargs)
    else:
        ret = cls(**data)  # type: ignore

    if hasattr(ret, 'emoji') and isinstance(ret.emoji, PartialEmoji):  # type: ignore
        ret.emoji._state = state  # type: ignore

    return ret
