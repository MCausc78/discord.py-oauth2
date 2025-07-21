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
import datetime
from typing import (
    Any,
    ClassVar,
    Dict,
    List,
    Literal,
    NamedTuple,
    Optional,
    Sequence,
    Set,
    TYPE_CHECKING,
    Tuple,
    Union,
    overload,
)

from .asset import Asset
from .channel import *
from .channel import _guild_channel_factory
from .commands import (
    SlashCommand,
    UserCommand,
    MessageCommand,
    Option,
    SlashCommandGroup,
    _command_factory,
)
from .emoji import Emoji
from .errors import MissingApplicationID
from .enums import (
    try_enum,
    AppCommandType,
    ContentFilter,
    MFALevel,
    NSFWLevel,
    NotificationLevel,
    Locale,
    VerificationLevel,
)
from .flags import AppCommandContext, AppInstallationType, SystemChannelFlags
from .invite import Invite
from .member import Member, VoiceState
from .mixins import Hashable
from .role import Role
from .scheduled_event import ScheduledEvent
from .soundboard import SoundboardSound
from .stage_instance import StageInstance
from .sticker import GuildSticker
from .threads import Thread
from .utils import (
    DEFAULT_FILE_SIZE_LIMIT_BYTES,
    MISSING,
    SequenceProxy,
    _get_as_snowflake,
    find,
    parse_time,
    snowflake_time,
    utcnow,
)
from .widget import Widget


__all__ = (
    'PartialGuild',
    'UserGuild',
    'Guild',
)

MISSING = MISSING

if TYPE_CHECKING:
    from .abc import Snowflake
    from .channel import VoiceChannel, StageChannel, TextChannel, ForumChannel, CategoryChannel
    from .permissions import Permissions
    from .state import ConnectionState
    from .types.commands import (
        SlashCommand as SlashCommandPayload,
        UserCommand as UserCommandPayload,
        MessageCommand as MessageCommandPayload,
        ApplicationCommandCreateRequestBody as ApplicationCommandCreateRequestBodyPayload,
    )
    from .types.guild import (
        Guild as GuildPayload,
        GuildFeature,
        IncidentData,
    )
    from .types.threads import (
        Thread as ThreadPayload,
    )
    from .types.voice import BaseVoiceState as VoiceStatePayload
    from .voice_client import VoiceProtocol

    VocalGuildChannel = Union[VoiceChannel, StageChannel]
    GuildChannel = Union[VocalGuildChannel, ForumChannel, TextChannel, CategoryChannel]
    ByCategoryItem = Tuple[Optional[CategoryChannel], List[GuildChannel]]


class _GuildLimit(NamedTuple):
    emoji: int
    stickers: int
    bitrate: float
    filesize: int


class PartialGuild(Hashable):
    """Represents a very partial guild.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    id: :class:`int`
        The guild's ID.
    name: :class:`str`
        The guild's name.
    features: List[:class:`str`]
        A list of features that the guild has. The features that a guild can have are
        subject to arbitrary change by Discord. A list of guild features can be found
        in :userdoccers:`Discord Userdoccers <resources/guild#guild-features>`.
    """

    __slots__ = (
        '_state',
        'id',
        'name',
        '_icon',
        'features',
    )

    def __init__(
        self, *, id: int, name: str, icon_hash: Optional[str] = None, features: List[GuildFeature], state: ConnectionState
    ) -> None:
        self._state: ConnectionState = state
        self.id: int = id
        self.name: str = name
        self._icon: Optional[str] = icon_hash
        self.features: List[GuildFeature] = features

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r} features={self.features!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return snowflake_time(self.id)

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's icon asset, if available."""
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @overload
    async def create_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        options: List[Union[Option, SlashCommandGroup]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
        type: Literal[AppCommandType.chat_input],
    ) -> SlashCommand:
        ...

    @overload
    async def create_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
        type: Literal[AppCommandType.user],
    ) -> UserCommand:
        ...

    @overload
    async def create_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
        type: Literal[AppCommandType.message],
    ) -> MessageCommand:
        ...

    @overload
    async def create_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        options: List[Union[Option, SlashCommandGroup]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
        type: AppCommandType = ...,
    ) -> Union[SlashCommand, UserCommand, MessageCommand]:
        ...
    
    async def create_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        options: List[Union[Option, SlashCommandGroup]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
        type: AppCommandType = AppCommandType.chat_input,
    ) -> Union[SlashCommand, UserCommand, MessageCommand]:
        """|coro|
        
        Creates an application command for the guild.

        .. versionadded:: 3.0

        Parameters
        ----------
        name: :class:`str`
            The name for the slash command. Must be between 1 and 32 characters long.
        name_localizations: Optional[Dict[:class:`~discord.Locale`, :class:`str`]]
            The name localizations for the slash command.

            Each value must be between 1 and 32 characters.
        description: Optional[:class:`str`]
            The description for the slash command. Can be only up to 100 characters.
        description_localizations: Optional[Dict[:class:`~discord.Locale`, :class:`str`]]
            The description localizations for the slash command.

            Each value can be only up to 100 characters.
        options: List[Union[:class:`Option`, :class:`SlashCommandGroup`]]
            The options for the slash command.
        default_member_permissions: Optional[:class:`~discord.Permissions`]
            The default permissions needed to use this application command.
            Pass value of ``None`` to remove any permission requirements.
        dm_permission: :class:`bool`
            Indicates if the application command can be used in DMs.

            .. deprecated:: 3.0

                Edit ``allowed_contexts`` instead.
        allowed_contexts: Optional[:class:`AppCommandContext`]
            The contexts that this command should be allowed to be used in.
            Overrides the ``dm_permission`` parameter.
        allowed_installs: Optional[:class:`AppInstallationType`]
            The installation contexts that this command should be allowed to be installed in.
        type: :class:`AppCommandType`
            The type for the application command. Defaults to :attr:`~AppCommandType.chat_input`.
        
        Raises
        ------
        Forbidden
            You do not have permission to create application command.
        HTTPException
            Creating the application command failed.

        Returns
        --------
        Union[:class:`SlashCommand`, :class:`UserCommand`, :class:`MessageCommand`]
            The application command created.
        """
        
        payload: ApplicationCommandCreateRequestBodyPayload = {
            'name': name,
        }

        if name_localizations is not MISSING:
            if name_localizations is None:
                payload['name_localizations'] = None
            else:
                payload['name_localizations'] = {
                    k.value: v
                    for k, v in name_localizations.items()
                }
        
        if description is not MISSING:
            payload['description'] = description
        
        if description_localizations is not MISSING:
            if description_localizations is None:
                payload['description_localizations'] = None
            else:
                payload['description_localizations'] = {
                    k.value: v
                    for k, v in description_localizations.items()
                }
        
        if options is not MISSING:
            if options is None:
                payload['options'] = None
            else:
                payload['options'] = [o.to_dict() for o in options]
        
        if default_member_permissions is not MISSING:
            if default_member_permissions is None:
                payload['default_member_permissions'] = '0'
            else:
                payload['default_member_permissions'] = str(default_member_permissions.value)
        
        if dm_permission is not MISSING:
            payload['dm_permission'] = dm_permission
        
        if allowed_contexts is not MISSING:
            if allowed_contexts is None:
                payload['contexts'] = None
            else:
                payload['contexts'] = allowed_contexts.to_array()  # type: ignore
        
        if allowed_installs is not MISSING:
            if allowed_installs is None:
                payload['integration_types'] = None
            else:
                payload['integration_types'] = allowed_installs.to_array()  # type: ignore
        
        if type is not MISSING:
            payload['type'] = type.value  # type: ignore
        
        state = self._state
        application_id = state.application_id
        
        if application_id is None:
            raise MissingApplicationID
        
        data = await state.http.create_guild_application_command(application_id, self.id, payload)
        return _command_factory(data, state)  # type: ignore
    
    async def create_message_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
    ) -> MessageCommand:
        """|coro|
        
        Creates a message command for the guild.

        The parameters are same as :meth:`~PartialGuild.create_command` except ``options`` is removed.

        .. versionadded:: 3.0

        Raises
        ------
        Forbidden
            You do not have permission to create application command.
        HTTPException
            Creating the application command failed.

        Returns
        --------
        :class:`MessageCommand`
            The message command created.
        """
        return await self.create_command(
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            default_member_permissions=default_member_permissions,
            dm_permission=dm_permission,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
            type=AppCommandType.message,
        )

    async def create_slash_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        options: List[Union[Option, SlashCommandGroup]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
    ) -> SlashCommand:
        """|coro|
        
        Creates a slash command for the guild.

        The parameters are same as :meth:`~PartialGuild.create_command`.

        .. versionadded:: 3.0

        Raises
        ------
        Forbidden
            You do not have permission to create application command.
        HTTPException
            Creating the application command failed.

        Returns
        --------
        :class:`SlashCommand`
            The slash command created.
        """
        return await self.create_command(
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            options=options,
            default_member_permissions=default_member_permissions,
            dm_permission=dm_permission,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
            type=AppCommandType.chat_input,
        )

    async def create_user_command(
        self,
        name: str,
        *,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: Optional[str] = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: bool = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
    ) -> UserCommand:
        """|coro|
        
        Creates an user command for the guild.

        The parameters are same as :meth:`~PartialGuild.create_command` except ``options`` is removed.

        .. versionadded:: 3.0

        Raises
        ------
        Forbidden
            You do not have permission to create application command.
        HTTPException
            Creating the application command failed.

        Returns
        --------
        :class:`UserCommand`
            The user command created.
        """
        return await self.create_command(
            name=name,
            name_localizations=name_localizations,
            description=description,
            description_localizations=description_localizations,
            default_member_permissions=default_member_permissions,
            dm_permission=dm_permission,
            allowed_contexts=allowed_contexts,
            allowed_installs=allowed_installs,
            type=AppCommandType.user,
        )

    async def fetch_command(self, id: int, /) -> List[Union[SlashCommand, UserCommand, MessageCommand]]:
        """|coro|

        Fetches an application command from the application.

        Parameters
        ----------
        id: :class:`int`
            The ID of the command to fetch.

        Raises
        ------
        HTTPException
            Fetching the command failed.
        MissingApplicationID
            The application ID could not be found.
        NotFound
            The application command was not found. This could also be because the command is a global command.

        Returns
        -------
        Union[:class:`SlashCommand`, :class:`UserCommand`, :class:`MessageCommand`, :class:`UnknownCommand`]
            The retrieved command.
        """
        state = self._state

        application_id = state.application_id
        if application_id is None:
            raise MissingApplicationID

        data = await state.http.get_guild_application_command(application_id, self.id, id)
        return _command_factory(data, state)  # type: ignore

    async def fetch_commands(self) -> List[Union[SlashCommand, UserCommand, MessageCommand]]:
        """|coro|

        Fetches the application's current commands.

        Raises
        ------
        HTTPException
            Fetching the commands failed.
        MissingApplicationID
            The application ID could not be found.

        Returns
        -------
        List[Union[:class:`SlashCommand`, :class:`UserCommand`, :class:`MessageCommand`, :class:`UnknownCommand`]]
            The application's commands.
        """
        state = self._state

        application_id = state.application_id

        if application_id is None:
            raise MissingApplicationID

        data = await state.http.get_guild_application_commands(application_id, self.id)
        return [_command_factory(d, state) for d in data]  # type: ignore

    async def fetch_me(self) -> Member:
        """|coro|

        Retrieve member version of yourself for this guild.

        Similar to :meth:`Client.fetch_me` except returns :class:`Member`.
        This is essentially used to get the member version of yourself.

        Raises
        ------
        Forbidden
            You do not have proper permissions to fetch member version of yourself for this guild.
        HTTPException
            Retrieving member version of yourself failed.

        Returns
        -------
        :class:`Member`
            The member version of yourself.
        """
        state = self._state
        data = await state.http.get_guild_me(self.id)

        if isinstance(self, Guild):
            guild = self
        else:
            guild = state._get_or_create_unavailable_guild(
                self.id,
                data={
                    'name': self.name,
                    'icon': self._icon,
                    'banner': getattr(self, '_banner', None),
                    'owner_id': state.self_id if getattr(self, 'is_owner', False) else 0,
                    'features': self.features,
                    'approximate_presence_count': getattr(self, 'approximate_presence_count', None),
                    'approximate_member_count': getattr(self, 'approximate_member_count', None),
                    'unavailable': True,
                },
            )

        return Member(data=data, guild=guild, state=state)  # type: ignore

    async def widget(self) -> Widget:
        """|coro|

        Returns the widget of the guild.

        .. note::

            The guild must have the widget enabled to get this information.

        Raises
        ------
        Forbidden
            The widget for this guild is disabled.
        HTTPException
            Retrieving the widget failed.

        Returns
        -------
        :class:`Widget`
            The guild's widget.
        """
        data = await self._state.http.get_widget(self.id)

        return Widget(state=self._state, data=data)

    async def change_voice_state(
        self,
        *,
        channel: Optional[Snowflake],
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
    ) -> None:
        """|coro|

        Changes client's voice state in the guild.

        .. versionadded:: 1.4

        Parameters
        ----------
        channel: Optional[:class:`abc.Snowflake`]
            Channel the client wants to join. You must explicitly pass ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        self_video: :class:`bool`
            Indicates if the client should show camera.
        """

        ws = self._state._get_websocket()
        channel_id = channel.id if channel else None
        await ws.voice_state(
            guild_id=self.id,
            channel_id=channel_id,
            self_mute=self_mute,
            self_deaf=self_deaf,
            self_video=self_video,
        )

    def get_partial_slash_command(self, id: int, /, *, application_id: Optional[int] = None) -> SlashCommand:
        """Retrieve a very partial slash command that can be used to edit or delete the guild command.

        Parameters
        ----------
        id: :class:`int`
            The ID of the command.
        application_id: Optional[:class:`int`]
            The ID of the application the command belongs to. This generally should be automatically filled in.

        Raises
        ------
        MissingApplicationID
            The ID of the application was not found.

        Returns
        -------
        :class:`SlashCommand`
            The partial slash command.

            .. warn::

                Most of attributes will be fake, except for :attr:`~SlashCommand.id`,
                :attr:`~SlashCommand.application_id`, and :attr:`~SlashCommand.guild_id`.
        """
        state = self._state

        if application_id is None:
            application_id = state.application_id

        if application_id is None:
            raise MissingApplicationID

        fake_payload: SlashCommandPayload = {
            'type': 1,
            'id': id,
            'application_id': application_id,
            'version': 0,
            'name': '',
            'name_localized': None,
            'name_localizations': {},
            'description': '',
            'description_localized': None,
            'description_localizations': {},
            'guild_id': self.id,
            'dm_permission': True,
            'contexts': [0, 1, 2],
            'integration_types': [0],
            'nsfw': False,
            'options': [],
        }
        return SlashCommand(data=fake_payload, state=state)

    def get_partial_user_command(self, id: int, /, *, application_id: Optional[int] = None) -> UserCommand:
        """Retrieve a very partial user command that can be used to edit or delete the guild command.

        Parameters
        ----------
        id: :class:`int`
            The ID of the command.
        application_id: Optional[:class:`int`]
            The ID of the application the command belongs to. This generally should be automatically filled in.

        Raises
        ------
        MissingApplicationID
            The ID of the application was not found.

        Returns
        -------
        :class:`UserCommand`
            The partial user command.

            .. warn::

                Most of attributes will be fake, except for :attr:`~UserCommand.id`,
                :attr:`~UserCommand.application_id`, and :attr:`~UserCommand.guild_id`.
        """
        state = self._state

        if application_id is None:
            application_id = state.application_id

        if application_id is None:
            raise MissingApplicationID

        fake_payload: UserCommandPayload = {
            'type': 2,
            'id': id,
            'application_id': application_id,
            'version': 0,
            'name': '',
            'name_localized': None,
            'name_localizations': {},
            'description': '',
            'description_localized': None,
            'description_localizations': {},
            'guild_id': self.id,
            'dm_permission': True,
            'contexts': [0, 1, 2],
            'integration_types': [0],
            'nsfw': False,
        }
        return UserCommand(data=fake_payload, state=state)

    def get_partial_message_command(self, id: int, /, *, application_id: Optional[int] = None) -> MessageCommand:
        """Retrieve a very partial message command that can be used to edit or delete the guild command.

        Parameters
        ----------
        id: :class:`int`
            The ID of the command.
        application_id: Optional[:class:`int`]
            The ID of the application the command belongs to. This generally should be automatically filled in.

        Raises
        ------
        MissingApplicationID
            The ID of the application was not found.

        Returns
        -------
        :class:`MessageCommand`
            The partial message command.

            .. warn::

                Most of attributes will be fake, except for :attr:`~MessageCommand.id`,
                :attr:`~MessageCommand.application_id`, and :attr:`~MessageCommand.guild_id`.
        """
        state = self._state

        if application_id is None:
            application_id = state.application_id

        if application_id is None:
            raise MissingApplicationID

        fake_payload: MessageCommandPayload = {
            'type': 3,
            'id': id,
            'application_id': application_id,
            'version': 0,
            'name': '',
            'name_localized': None,
            'name_localizations': {},
            'description': '',
            'description_localized': None,
            'description_localizations': {},
            'guild_id': self.id,
            'dm_permission': True,
            'contexts': [0, 1, 2],
            'integration_types': [0],
            'nsfw': False,
        }
        return MessageCommand(data=fake_payload, state=state)

class UserGuild(PartialGuild):
    """Represents a Discord partial guild.

    This is referred to as a "server" in the official Discord UI.

    This inherits from :class:`UserGuild`.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    owner: :class:`bool`
        Whether you own the guild.
    approximate_member_count: Optional[:class:`int`]
        The approximate number of members in the guild. This is ``None`` unless the guild is obtained
        using :meth:`Client.fetch_guild` or :meth:`Client.fetch_guilds` with ``with_counts=True``.
    approximate_presence_count: Optional[:class:`int`]
        The approximate number of members currently active in the guild.
        Offline members are excluded. This is ``None`` unless the guild is obtained using
        :meth:`Client.fetch_guild` or :meth:`Client.fetch_guilds` with ``with_counts=True``.
    """

    __slots__ = (
        '_banner',
        'is_owner',
        'features',
        '_permissions',
        'approximate_member_count',
        'approximate_presence_count',
    )

    def __init__(self, *, data: GuildPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.name: str = data['name']
        self._icon: Optional[str] = data.get('icon')
        self._banner: Optional[str] = data.get('banner')
        self.is_owner: bool = data.get('owner', False)
        self.features: List[GuildFeature] = data.get('features', [])
        self._permissions: int = int(data.get('permissions', 0))
        self.approximate_member_count: Optional[int] = data.get('approximate_member_count')
        self.approximate_presence_count: Optional[int] = data.get('approximate_presence_count')

    def __str__(self) -> str:
        return self.name or ''

    @property
    def icon(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's icon asset, if available."""
        if self._icon is None:
            return None
        return Asset._from_guild_icon(self._state, self.id, self._icon)

    @property
    def banner(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's banner asset, if available."""
        if self._banner is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._banner, path='banners')


class Guild(UserGuild):
    """Represents a Discord guild.

    This is referred to as a "server" in the official Discord UI.

    This inherits from :class:`UserGuild`.

    .. container:: operations

        .. describe:: x == y

            Checks if two guilds are equal.

        .. describe:: x != y

            Checks if two guilds are not equal.

        .. describe:: hash(x)

            Returns the guild's hash.

        .. describe:: str(x)

            Returns the guild's name.

    Attributes
    ----------
    emojis: Tuple[:class:`Emoji`, ...]
        All emojis that the guild owns.
    stickers: Tuple[:class:`GuildSticker`, ...]
        All stickers that the guild owns.

        .. versionadded:: 2.0
    afk_timeout: :class:`int`
        The number of seconds until someone is moved to the AFK channel.
    owner_id: :class:`int`
        The guild owner's ID. Use :attr:`Guild.owner` instead.
    unavailable: :class:`bool`
        Indicates if the guild is unavailable. If this is ``True`` then the
        reliability of other attributes outside of :attr:`Guild.id` is slim and they might
        all be ``None``. It is best to not do anything with the guild if it is unavailable.

        Check the :func:`on_guild_unavailable` and :func:`on_guild_available` events.
    max_presences: Optional[:class:`int`]
        The maximum amount of presences for the guild.
    max_members: Optional[:class:`int`]
        The maximum amount of members for the guild.

        .. note::

            This attribute is only available via :meth:`.Client.fetch_guild`.
    max_video_channel_users: Optional[:class:`int`]
        The maximum amount of users in a video channel.

        .. versionadded:: 1.4
    description: Optional[:class:`str`]
        The guild's description.
    verification_level: :class:`VerificationLevel`
        The guild's verification level.
    vanity_url_code: Optional[:class:`str`]
        The guild's vanity url code, if any

        .. versionadded:: 2.0
    explicit_content_filter: :class:`ContentFilter`
        The guild's explicit content filter.
    default_notifications: :class:`NotificationLevel`
        The guild's notification settings.
    premium_tier: :class:`int`
        The premium tier for this guild. Corresponds to "Nitro Server" in the official UI.
        The number goes from 0 to 3 inclusive.
    premium_subscription_count: :class:`int`
        The number of "boosts" this guild currently has.
    preferred_locale: :class:`Locale`
        The preferred locale for the guild. Used when filtering Server Discovery
        results to a specific language.

        .. versionchanged:: 2.0
            This field is now an enum instead of a :class:`str`.
    nsfw_level: :class:`NSFWLevel`
        The guild's NSFW level.

        .. versionadded:: 2.0

    mfa_level: :class:`MFALevel`
        The guild's Multi-Factor Authentication requirement level.

        .. versionchanged:: 2.0
            This field is now an enum instead of an :class:`int`.

    premium_progress_bar_enabled: :class:`bool`
        Indicates if the guild has premium AKA server boost level progress bar enabled.

        .. versionadded:: 2.0
    widget_enabled: :class:`bool`
        Indicates if the guild has widget enabled.

        .. versionadded:: 2.0
    max_stage_video_users: Optional[:class:`int`]
        The maximum amount of users in a stage video channel.

        .. versionadded:: 2.3
    """

    __slots__ = (
        'afk_timeout',
        'unavailable',
        'owner_id',
        'emojis',
        'stickers',
        'verification_level',
        'explicit_content_filter',
        'default_notifications',
        'description',
        'max_presences',
        'max_members',
        'max_video_channel_users',
        'premium_tier',
        'premium_subscription_count',
        'preferred_locale',
        'nsfw_level',
        'mfa_level',
        'vanity_url_code',
        'widget_enabled',
        '_widget_channel_id',
        '_afk_channel_id',
        '_members',
        '_channels',
        '_roles',
        '_member_count',
        '_large',
        '_splash',
        '_voice_states',
        '_system_channel_id',
        '_system_channel_flags',
        '_discovery_splash',
        '_rules_channel_id',
        '_public_updates_channel_id',
        '_stage_instances',
        '_scheduled_events',
        '_threads',
        'premium_progress_bar_enabled',
        '_safety_alerts_channel_id',
        'max_stage_video_users',
        '_incidents_data',
        '_soundboard_sounds',
    )

    _PREMIUM_GUILD_LIMITS: ClassVar[Dict[Optional[int], _GuildLimit]] = {
        None: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=DEFAULT_FILE_SIZE_LIMIT_BYTES),
        0: _GuildLimit(emoji=50, stickers=5, bitrate=96e3, filesize=DEFAULT_FILE_SIZE_LIMIT_BYTES),
        1: _GuildLimit(emoji=100, stickers=15, bitrate=128e3, filesize=DEFAULT_FILE_SIZE_LIMIT_BYTES),
        2: _GuildLimit(emoji=150, stickers=30, bitrate=256e3, filesize=52428800),
        3: _GuildLimit(emoji=250, stickers=60, bitrate=384e3, filesize=104857600),
    }

    def __init__(self, *, data: GuildPayload, state: ConnectionState) -> None:
        self._channels: Dict[int, GuildChannel] = {}
        self._members: Dict[int, Member] = {}
        self._voice_states: Dict[int, VoiceState] = {}
        self._threads: Dict[int, Thread] = {}
        self._stage_instances: Dict[int, StageInstance] = {}
        self._scheduled_events: Dict[int, ScheduledEvent] = {}
        self._soundboard_sounds: Dict[int, SoundboardSound] = {}
        self._state: ConnectionState = state
        self._member_count: Optional[int] = None
        self._from_data(data)

    def _add_channel(self, channel: GuildChannel, /) -> None:
        self._channels[channel.id] = channel

    def _remove_channel(self, channel: Snowflake, /) -> None:
        self._channels.pop(channel.id, None)

    def _voice_state_for(self, user_id: int, /) -> Optional[VoiceState]:
        return self._voice_states.get(user_id)

    def _add_member(self, member: Member, /) -> None:
        self._members[member.id] = member

    def _store_thread(self, payload: ThreadPayload, /) -> Thread:
        thread = Thread(guild=self, state=self._state, data=payload)
        self._threads[thread.id] = thread
        return thread

    def _remove_member(self, member: Snowflake, /) -> None:
        self._members.pop(member.id, None)

    def _add_thread(self, thread: Thread, /) -> None:
        self._threads[thread.id] = thread

    def _remove_thread(self, thread: Snowflake, /) -> None:
        self._threads.pop(thread.id, None)

    def _clear_threads(self) -> None:
        self._threads.clear()

    def _remove_threads_by_channel(self, channel_id: int) -> List[Thread]:
        to_remove = [t for t in self._threads.values() if t.parent_id == channel_id]
        for thread in to_remove:
            del self._threads[thread.id]
        return to_remove

    def _filter_threads(self, channel_ids: Set[int]) -> Dict[int, Thread]:
        to_remove: Dict[int, Thread] = {k: t for k, t in self._threads.items() if t.parent_id in channel_ids}
        for k in to_remove:
            del self._threads[k]
        return to_remove

    def _add_soundboard_sound(self, sound: SoundboardSound, /) -> None:
        self._soundboard_sounds[sound.id] = sound

    def _remove_soundboard_sound(self, sound: SoundboardSound, /) -> None:
        self._soundboard_sounds.pop(sound.id, None)

    def __repr__(self) -> str:
        attrs = (
            ('id', self.id),
            ('name', self.name),
            ('chunked', self.chunked),
            ('member_count', self._member_count),
        )
        inner = ' '.join('%s=%r' % t for t in attrs)
        return f'<Guild {inner}>'

    def _update_voice_state(
        self, data: VoiceStatePayload, channel_id: Optional[int]
    ) -> Tuple[Optional[Member], VoiceState, VoiceState]:
        cache_flags = self._state.member_cache_flags
        user_id = int(data['user_id'])
        channel: Optional[VocalGuildChannel] = self.get_channel(channel_id)  # type: ignore # this will always be a voice channel
        try:
            # Check if we should remove the voice state from cache
            if channel is None:
                after = self._voice_states.pop(user_id)
            else:
                after = self._voice_states[user_id]

            before = copy(after)
            after._update(data, channel)
        except KeyError:
            # If we're here then add it into the cache
            after = VoiceState(data=data, channel=channel)
            before = VoiceState(data=data, channel=None)
            self._voice_states[user_id] = after

        member = self.get_member(user_id)
        if member is None:
            try:
                member = Member(data=data['member'], state=self._state, guild=self)  # type: ignore
            except KeyError:
                member = None

            if member is not None and cache_flags.voice:
                self._add_member(member)

        return member, before, after

    def _add_role(self, role: Role, /) -> None:
        self._roles[role.id] = role

    def _remove_role(self, role_id: int, /) -> Role:
        # this raises KeyError if it fails..
        return self._roles.pop(role_id)

    @classmethod
    def _create_unavailable(cls, *, state: ConnectionState, guild_id: int, data: Optional[Dict[str, Any]]) -> Guild:
        if data is None:
            data = {'unavailable': True}
        data.update(id=guild_id)
        return cls(state=state, data=data)  # type: ignore

    def _from_data(self, guild: GuildPayload) -> None:
        from .presences import Presence

        try:
            self._member_count = guild['member_count']  # pyright: ignore[reportTypedDictNotRequiredAccess]
        except KeyError:
            pass

        self.name: str = guild.get('name', '')
        self.verification_level: VerificationLevel = try_enum(VerificationLevel, guild.get('verification_level', 0))
        self.default_notifications: NotificationLevel = try_enum(
            NotificationLevel, guild.get('default_message_notifications', -1)
        )
        self.explicit_content_filter: ContentFilter = try_enum(ContentFilter, guild.get('explicit_content_filter', 0))
        self.afk_timeout: int = guild.get('afk_timeout', 0)
        self._icon: Optional[str] = guild.get('icon')
        self._banner: Optional[str] = guild.get('banner')
        self.unavailable: bool = guild.get('unavailable', False)
        self.id: int = int(guild['id'])
        self._roles: Dict[int, Role] = {}
        state = self._state  # speed up attribute access
        for r in guild.get('roles', ()):
            role = Role(guild=self, data=r, state=state)
            self._roles[role.id] = role

        self.emojis: Tuple[Emoji, ...] = (
            tuple(map(lambda d: state.store_emoji(self, d), guild.get('emojis', ())))
            if state.cache_guild_expressions
            else ()
        )
        self.stickers: Tuple[GuildSticker, ...] = (
            tuple(map(lambda d: state.store_sticker(self, d), guild.get('stickers', ())))
            if state.cache_guild_expressions
            else ()
        )
        self.features: List[GuildFeature]
        if 'features' in guild:
            self.features = guild['features']
        elif not hasattr(self, 'features'):
            self.features = []
        self._splash: Optional[str] = guild.get('splash')
        self._system_channel_id: Optional[int] = _get_as_snowflake(guild, 'system_channel_id')
        self.description: Optional[str] = guild.get('description')
        self.max_presences: Optional[int] = guild.get('max_presences')
        self.max_members: Optional[int] = guild.get('max_members')
        self.max_video_channel_users: Optional[int] = guild.get('max_video_channel_users')
        self.max_stage_video_users: Optional[int] = guild.get('max_stage_video_channel_users')
        self.premium_tier: int = guild.get('premium_tier', 0)
        self.premium_subscription_count: int = guild.get('premium_subscription_count') or 0
        self.vanity_url_code: Optional[str] = guild.get('vanity_url_code')
        self.widget_enabled: bool = guild.get('widget_enabled', False)
        self._widget_channel_id: Optional[int] = _get_as_snowflake(guild, 'widget_channel_id')
        self._system_channel_flags: int = guild.get('system_channel_flags', 0)
        self.preferred_locale: Locale = try_enum(Locale, guild.get('preferred_locale', 'en-US'))
        self._discovery_splash: Optional[str] = guild.get('discovery_splash')
        self._rules_channel_id: Optional[int] = _get_as_snowflake(guild, 'rules_channel_id')
        self._public_updates_channel_id: Optional[int] = _get_as_snowflake(guild, 'public_updates_channel_id')
        self._safety_alerts_channel_id: Optional[int] = _get_as_snowflake(guild, 'safety_alerts_channel_id')
        self.nsfw_level: NSFWLevel = try_enum(NSFWLevel, guild.get('nsfw_level', 0))
        self.mfa_level: MFALevel = try_enum(MFALevel, guild.get('mfa_level', 0))
        self.approximate_presence_count: Optional[int] = guild.get('approximate_presence_count')
        self.approximate_member_count: Optional[int] = guild.get('approximate_member_count')
        self.premium_progress_bar_enabled: bool = guild.get('premium_progress_bar_enabled', False)
        self.owner_id: Optional[int] = _get_as_snowflake(guild, 'owner_id')
        self.is_owner: bool = self.owner_id == state.self_id
        self._large: Optional[bool] = None if self._member_count is None else self._member_count >= 250
        self._afk_channel_id: Optional[int] = _get_as_snowflake(guild, 'afk_channel_id')
        self._incidents_data: Optional[IncidentData] = guild.get('incidents_data')

        if 'channels' in guild:
            channels = guild['channels']
            for c in channels:
                factory, ch_type = _guild_channel_factory(c['type'])
                if factory:
                    self._add_channel(factory(guild=self, data=c, state=self._state))  # type: ignore

        for obj in guild.get('voice_states', ()):
            self._update_voice_state(obj, int(obj['channel_id']))  # type: ignore

        cache_joined = self._state.member_cache_flags.joined
        cache_voice = self._state.member_cache_flags.voice
        self_id = self._state.self_id
        for mdata in guild.get('members', ()):
            member = Member(data=mdata, guild=self, state=self._state)  # type: ignore # Members will have the 'user' key in this scenario
            if cache_joined or member.id == self_id or (cache_voice and member.id in self._voice_states):
                self._add_member(member)

        empty_tuple = ()
        for presence in guild.get('presences', ()):
            raw_presence = Presence(data=presence, state=self._state)
            member = self.get_member(raw_presence.user_id)

            if member is not None:
                member._presence_update(raw_presence, empty_tuple)  # type: ignore

        if 'threads' in guild:
            threads = guild['threads']
            for thread in threads:
                self._add_thread(Thread(guild=self, state=self._state, data=thread))

        if 'stage_instances' in guild:
            for s in guild['stage_instances']:
                stage_instance = StageInstance(guild=self, data=s, state=self._state)
                self._stage_instances[stage_instance.id] = stage_instance

        if 'guild_scheduled_events' in guild:
            for s in guild['guild_scheduled_events']:
                scheduled_event = ScheduledEvent(data=s, state=self._state)
                self._scheduled_events[scheduled_event.id] = scheduled_event

        if 'soundboard_sounds' in guild:
            for s in guild['soundboard_sounds']:
                soundboard_sound = SoundboardSound(guild=self, data=s, state=self._state)
                self._add_soundboard_sound(soundboard_sound)

    @property
    def channels(self) -> Sequence[GuildChannel]:
        """Sequence[:class:`abc.GuildChannel`]: A list of channels that belongs to this guild."""
        return SequenceProxy(self._channels.values())

    @property
    def threads(self) -> Sequence[Thread]:
        """Sequence[:class:`Thread`]: A list of threads that you have permission to view.

        .. versionadded:: 2.0
        """
        return SequenceProxy(self._threads.values())

    @property
    def large(self) -> bool:
        """:class:`bool`: Indicates if the guild is a 'large' guild.

        A large guild is defined as having more than ``large_threshold`` count
        members, which for this library is set to the maximum of 250.
        """
        if self._large is None:
            if self._member_count is not None:
                return self._member_count >= 250
            return len(self._members) >= 250
        return self._large

    @property
    def voice_channels(self) -> List[VoiceChannel]:
        """List[:class:`VoiceChannel`]: A list of voice channels that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, VoiceChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def stage_channels(self) -> List[StageChannel]:
        """List[:class:`StageChannel`]: A list of stage channels that belongs to this guild.

        .. versionadded:: 1.7

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, StageChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def me(self) -> Member:
        """:class:`Member`: Similar to :attr:`Client.user` except an instance of :class:`Member`.
        This is essentially used to get the member version of yourself.
        """
        self_id = self._state.user.id  # type: ignore # state.user won't be None if we're logged in
        # The self member is *always* cached
        return self.get_member(self_id)  # type: ignore

    @property
    def voice_client(self) -> Optional[VoiceProtocol]:
        """Optional[:class:`VoiceProtocol`]: Returns the :class:`VoiceProtocol` associated with this guild, if any."""
        return self._state._get_voice_client(self.id)

    @property
    def text_channels(self) -> List[TextChannel]:
        """List[:class:`TextChannel`]: A list of text channels that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, TextChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def categories(self) -> List[CategoryChannel]:
        """List[:class:`CategoryChannel`]: A list of categories that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, CategoryChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    @property
    def forums(self) -> List[ForumChannel]:
        """List[:class:`ForumChannel`]: A list of forum channels that belongs to this guild.

        This is sorted by the position and are in UI order from top to bottom.
        """
        r = [ch for ch in self._channels.values() if isinstance(ch, ForumChannel)]
        r.sort(key=lambda c: (c.position, c.id))
        return r

    def by_category(self) -> List[ByCategoryItem]:
        """Returns every :class:`CategoryChannel` and their associated channels.

        These channels and categories are sorted in the official Discord UI order.

        If the channels do not have a category, then the first element of the tuple is
        ``None``.

        Returns
        -------
        List[Tuple[Optional[:class:`CategoryChannel`], List[:class:`abc.GuildChannel`]]]:
            The categories and their associated channels.
        """
        grouped: Dict[Optional[int], List[GuildChannel]] = {}
        for channel in self._channels.values():
            if isinstance(channel, CategoryChannel):
                grouped.setdefault(channel.id, [])
                continue

            try:
                grouped[channel.category_id].append(channel)
            except KeyError:
                grouped[channel.category_id] = [channel]

        def key(t: ByCategoryItem) -> Tuple[Tuple[int, int], List[GuildChannel]]:
            k, v = t
            return ((k.position, k.id) if k else (-1, -1), v)

        _get = self._channels.get
        as_list: List[ByCategoryItem] = [(_get(k), v) for k, v in grouped.items()]  # type: ignore
        as_list.sort(key=key)
        for _, channels in as_list:
            channels.sort(key=lambda c: (c._sorting_bucket, c.position, c.id))
        return as_list

    def _resolve_channel(self, id: Optional[int], /) -> Optional[Union[GuildChannel, Thread]]:
        if id is None:
            return

        return self._channels.get(id) or self._threads.get(id)

    def get_channel_or_thread(self, channel_id: int, /) -> Optional[Union[Thread, GuildChannel]]:
        """Returns a channel or thread with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[Union[:class:`Thread`, :class:`.abc.GuildChannel`]]
            The returned channel or thread or ``None`` if not found.
        """
        return self._channels.get(channel_id) or self._threads.get(channel_id)

    def get_channel(self, channel_id: Optional[int], /) -> Optional[GuildChannel]:
        """Returns a channel with the given ID.

        .. note::

            This does *not* search for threads.

        .. versionchanged:: 2.0

            ``channel_id`` parameter is now positional-only.

        Parameters
        ----------
        channel_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`.abc.GuildChannel`]
            The returned channel or ``None`` if not found.
        """
        if channel_id is None:
            return None

        return self._channels.get(channel_id)

    def get_thread(self, thread_id: int, /) -> Optional[Thread]:
        """Returns a thread with the given ID.

        .. note::

            This does not always retrieve archived threads, as they are not retained in the internal
            cache. Use :func:`fetch_channel` instead.

        .. versionadded:: 2.0

        Parameters
        ----------
        thread_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Thread`]
            The returned thread or ``None`` if not found.
        """
        return self._threads.get(thread_id)

    def get_emoji(self, emoji_id: int, /) -> Optional[Emoji]:
        """Returns an emoji with the given ID.

        .. versionadded:: 2.3

        Parameters
        ----------
        emoji_id: int
            The ID to search for.

        Returns
        -------
        Optional[:class:`Emoji`]
            The returned Emoji or ``None`` if not found.
        """
        emoji = self._state.get_emoji(emoji_id)
        if emoji and emoji.guild == self:
            return emoji
        return None

    @property
    def afk_channel(self) -> Optional[VocalGuildChannel]:
        """Optional[Union[:class:`VoiceChannel`, :class:`StageChannel`]]: The channel that denotes the AFK channel.

        If no channel is set, then this returns ``None``.
        """
        return self.get_channel(self._afk_channel_id)  # type: ignore

    @property
    def system_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Returns the guild's channel used for system messages.

        If no channel is set, then this returns ``None``.
        """
        channel_id = self._system_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def system_channel_flags(self) -> SystemChannelFlags:
        """:class:`SystemChannelFlags`: Returns the guild's system channel settings."""
        return SystemChannelFlags._from_value(self._system_channel_flags)

    @property
    def rules_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Return's the guild's channel used for the rules.
        The guild must be a Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.3
        """
        channel_id = self._rules_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def public_updates_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Return's the guild's channel where admins and
        moderators of the guilds receive notices from Discord. The guild must be a
        Community guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 1.4
        """
        channel_id = self._public_updates_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def safety_alerts_channel(self) -> Optional[TextChannel]:
        """Optional[:class:`TextChannel`]: Return's the guild's channel used for safety alerts, if set.

        For example, this is used for the raid protection setting. The guild must have the ``COMMUNITY`` feature.

        .. versionadded:: 2.3
        """
        channel_id = self._safety_alerts_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def widget_channel(self) -> Optional[Union[TextChannel, ForumChannel, VoiceChannel, StageChannel]]:
        """Optional[Union[:class:`TextChannel`, :class:`ForumChannel`, :class:`VoiceChannel`, :class:`StageChannel`]]: Returns
        the widget channel of the guild.

        If no channel is set, then this returns ``None``.

        .. versionadded:: 2.3
        """
        channel_id = self._widget_channel_id
        return channel_id and self._channels.get(channel_id)  # type: ignore

    @property
    def emoji_limit(self) -> int:
        """:class:`int`: The maximum number of emoji slots this guild has."""
        more_emoji = 200 if 'MORE_EMOJI' in self.features else 50
        return max(more_emoji, self._PREMIUM_GUILD_LIMITS[self.premium_tier].emoji)

    @property
    def sticker_limit(self) -> int:
        """:class:`int`: The maximum number of sticker slots this guild has.

        .. versionadded:: 2.0
        """
        more_stickers = 60 if 'MORE_STICKERS' in self.features else 0
        return max(more_stickers, self._PREMIUM_GUILD_LIMITS[self.premium_tier].stickers)

    @property
    def bitrate_limit(self) -> float:
        """:class:`float`: The maximum bitrate for voice channels this guild can have."""
        vip_guild = self._PREMIUM_GUILD_LIMITS[1].bitrate if 'VIP_REGIONS' in self.features else 96e3
        return max(vip_guild, self._PREMIUM_GUILD_LIMITS[self.premium_tier].bitrate)

    @property
    def filesize_limit(self) -> int:
        """:class:`int`: The maximum number of bytes files can have when uploaded to this guild."""
        return self._PREMIUM_GUILD_LIMITS[self.premium_tier].filesize

    @property
    def members(self) -> Sequence[Member]:
        """Sequence[:class:`Member`]: A list of members that belong to this guild."""
        return SequenceProxy(self._members.values())

    def get_member(self, user_id: int, /) -> Optional[Member]:
        """Returns a member with the given ID.

        .. versionchanged:: 2.0

            ``user_id`` parameter is now positional-only.

        Parameters
        ----------
        user_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Member`]
            The member or ``None`` if not found.
        """
        return self._members.get(user_id)

    @property
    def premium_subscribers(self) -> List[Member]:
        """List[:class:`Member`]: A list of members who have "boosted" this guild."""
        return [member for member in self.members if member.premium_since is not None]

    @property
    def roles(self) -> Sequence[Role]:
        """Sequence[:class:`Role`]: Returns a sequence of the guild's roles in hierarchy order.

        The first element of this sequence will be the lowest role in the
        hierarchy.
        """
        return SequenceProxy(self._roles.values(), sorted=True)

    def get_role(self, role_id: int, /) -> Optional[Role]:
        """Returns a role with the given ID.

        .. versionchanged:: 2.0

            ``role_id`` parameter is now positional-only.

        Parameters
        ----------
        role_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`Role`]
            The role or ``None`` if not found.
        """
        return self._roles.get(role_id)

    @property
    def default_role(self) -> Role:
        """:class:`Role`: Gets the @everyone role that all members have by default."""
        # The @everyone role is *always* given
        return self.get_role(self.id)  # type: ignore

    @property
    def premium_subscriber_role(self) -> Optional[Role]:
        """Optional[:class:`Role`]: Gets the premium subscriber role, AKA "boost" role, in this guild.

        .. versionadded:: 1.6
        """
        for role in self._roles.values():
            if role.is_premium_subscriber():
                return role
        return None

    @property
    def self_role(self) -> Optional[Role]:
        """Optional[:class:`Role`]: Gets the role associated with this client's user, if any.

        .. versionadded:: 1.6
        """
        self_id = self._state.self_id
        for role in self._roles.values():
            tags = role.tags
            if tags and tags.bot_id == self_id:
                return role
        return None

    @property
    def stage_instances(self) -> Sequence[StageInstance]:
        """Sequence[:class:`StageInstance`]: Returns a sequence of the guild's stage instances that
        are currently running.

        .. versionadded:: 2.0
        """
        return SequenceProxy(self._stage_instances.values())

    def get_stage_instance(self, stage_instance_id: int, /) -> Optional[StageInstance]:
        """Returns a stage instance with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        stage_instance_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`StageInstance`]
            The stage instance or ``None`` if not found.
        """
        return self._stage_instances.get(stage_instance_id)

    @property
    def scheduled_events(self) -> Sequence[ScheduledEvent]:
        """Sequence[:class:`ScheduledEvent`]: Returns a sequence of the guild's scheduled events.

        .. versionadded:: 2.0
        """
        return SequenceProxy(self._scheduled_events.values())

    def get_scheduled_event(self, scheduled_event_id: int, /) -> Optional[ScheduledEvent]:
        """Returns a scheduled event with the given ID.

        .. versionadded:: 2.0

        Parameters
        ----------
        scheduled_event_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`ScheduledEvent`]
            The scheduled event or ``None`` if not found.
        """
        return self._scheduled_events.get(scheduled_event_id)

    @property
    def soundboard_sounds(self) -> Sequence[SoundboardSound]:
        """Sequence[:class:`SoundboardSound`]: Returns a sequence of the guild's soundboard sounds.

        .. versionadded:: 2.5
        """
        return SequenceProxy(self._soundboard_sounds.values())

    def get_soundboard_sound(self, sound_id: int, /) -> Optional[SoundboardSound]:
        """Returns a soundboard sound with the given ID.

        .. versionadded:: 2.5

        Parameters
        ----------
        sound_id: :class:`int`
            The ID to search for.

        Returns
        -------
        Optional[:class:`SoundboardSound`]
            The soundboard sound or ``None`` if not found.
        """
        return self._soundboard_sounds.get(sound_id)

    def _resolve_soundboard_sound(self, id: Optional[int], /) -> Optional[SoundboardSound]:
        if id is None:
            return

        return self._soundboard_sounds.get(id)

    @property
    def owner(self) -> Optional[Member]:
        """Optional[:class:`Member`]: The member that owns the guild."""
        return self.get_member(self.owner_id)  # type: ignore

    @property
    def splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's invite splash asset, if available."""
        if self._splash is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._splash, path='splashes')

    @property
    def discovery_splash(self) -> Optional[Asset]:
        """Optional[:class:`Asset`]: Returns the guild's discovery splash asset, if available."""
        if self._discovery_splash is None:
            return None
        return Asset._from_guild_image(self._state, self.id, self._discovery_splash, path='discovery-splashes')

    @property
    def member_count(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns the member count if available.

        .. warning::

            Due to a Discord limitation, in order for this attribute to remain up-to-date and
            accurate, it requires :attr:`Intents.members` to be specified.

        .. versionchanged:: 2.0

            Now returns an ``Optional[int]``.
        """
        return self._member_count

    @property
    def chunked(self) -> bool:
        """:class:`bool`: Returns a boolean indicating if the guild is "chunked".

        A chunked guild means that :attr:`member_count` is equal to the
        number of members stored in the internal :attr:`members` cache.

        If this value returns ``False``, then you should request for
        offline members.
        """
        count = self._member_count
        if count is None:
            return False
        return count == len(self._members)

    @property
    def created_at(self) -> datetime.datetime:
        """:class:`datetime.datetime`: Returns the guild's creation time in UTC."""
        return snowflake_time(self.id)

    def get_member_named(self, name: str, /) -> Optional[Member]:
        """Returns the first member found that matches the name provided.

        The name is looked up in the following order:

        - Username#Discriminator (deprecated)
        - Username#0 (deprecated, only gets users that migrated from their discriminator)
        - Nickname
        - Global name
        - Username

        If no member is found, ``None`` is returned.

        .. versionchanged:: 2.0

            ``name`` parameter is now positional-only.

        .. deprecated:: 2.3

            Looking up users via discriminator due to Discord API change.

        Parameters
        ----------
        name: :class:`str`
            The name of the member to lookup.

        Returns
        -------
        Optional[:class:`Member`]
            The member in this guild with the associated name. If not found
            then ``None`` is returned.
        """

        members = self.members

        username, _, discriminator = name.rpartition('#')

        # If # isn't found then "discriminator" actually has the username
        if not username:
            discriminator, username = username, discriminator

        if discriminator == '0' or (len(discriminator) == 4 and discriminator.isdigit()):
            return find(lambda m: m.name == username and m.discriminator == discriminator, members)

        def pred(m: Member) -> bool:
            return m.nick == name or m.global_name == name or m.name == name

        return find(pred, members)

    @property
    def vanity_url(self) -> Optional[str]:
        """Optional[:class:`str`]: The Discord vanity invite URL for this guild, if available.

        .. versionadded:: 2.0
        """
        if self.vanity_url_code is None:
            return None
        return f'{Invite.BASE}/{self.vanity_url_code}'

    @property
    def invites_paused_until(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: If invites are paused, returns when
        invites will get enabled in UTC, otherwise returns None.

        .. versionadded:: 2.4
        """
        if not self._incidents_data:
            return None

        return parse_time(self._incidents_data.get('invites_disabled_until'))

    @property
    def dms_paused_until(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: If DMs are paused, returns when DMs
        will get enabled in UTC, otherwise returns None.

        .. versionadded:: 2.4
        """
        if not self._incidents_data:
            return None

        return parse_time(self._incidents_data.get('dms_disabled_until'))

    @property
    def dm_spam_detected_at(self) -> Optional[datetime.datetime]:
        """:class:`datetime.datetime`: Returns the time when DM spam was detected in the guild.

        .. versionadded:: 2.5
        """
        if not self._incidents_data:
            return None

        return parse_time(self._incidents_data.get('dm_spam_detected_at'))

    @property
    def raid_detected_at(self) -> Optional[datetime.datetime]:
        """Optional[:class:`datetime.datetime`]: Returns the time when a raid was detected in the guild.

        .. versionadded:: 2.5
        """
        if not self._incidents_data:
            return None

        return parse_time(self._incidents_data.get('raid_detected_at'))

    def invites_paused(self) -> bool:
        """:class:`bool`: Whether invites are paused in the guild.

        .. versionadded:: 2.4
        """
        if not self.invites_paused_until:
            return 'INVITES_DISABLED' in self.features

        return self.invites_paused_until > utcnow()

    def dms_paused(self) -> bool:
        """:class:`bool`: Whether DMs are paused in the guild.

        .. versionadded:: 2.4
        """
        if not self.dms_paused_until:
            return False

        return self.dms_paused_until > utcnow()

    def is_dm_spam_detected(self) -> bool:
        """:class:`bool`: Whether DM spam was detected in the guild.

        .. versionadded:: 2.5
        """
        if not self.dm_spam_detected_at:
            return False

        return self.dm_spam_detected_at > utcnow()

    def is_raid_detected(self) -> bool:
        """:class:`bool`: Whether a raid was detected in the guild.

        .. versionadded:: 2.5
        """
        if not self.raid_detected_at:
            return False

        return self.raid_detected_at > utcnow()

    async def change_voice_state(
        self,
        *,
        channel: Optional[Snowflake],
        self_mute: bool = False,
        self_deaf: bool = False,
        self_video: bool = False,
    ) -> None:
        """|coro|

        Changes client's voice state in the guild.

        .. versionadded:: 1.4

        Parameters
        -----------
        channel: Optional[:class:`abc.Snowflake`]
            Channel the client wants to join. Use ``None`` to disconnect.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        self_video: :class:`bool`
            Indicates if the client is using video. Do not use.
        """
        state = self._state
        ws = state._get_websocket()
        channel_id = channel.id if channel else None

        await ws.voice_state(self.id, channel_id, self_mute, self_deaf, self_video)
