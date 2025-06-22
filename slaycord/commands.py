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

from typing import Dict, Generic, List, Literal, Optional, TYPE_CHECKING, TypeVar, Union, overload

from .enums import (
    try_enum,
    AppCommandHandler,
    AppCommandOptionType,
    AppCommandType,
    ChannelType,
    Locale,
)
from .flags import AppCommandContext, AppInstallationType
from .mixins import Hashable
from .permissions import Permissions
from .utils import MISSING, _get_as_snowflake

if TYPE_CHECKING:
    from .guild import Guild
    from .state import ConnectionState
    from .types.commands import (
        SlashCommand as SlashCommandPayload,
        UserCommand as UserCommandPayload,
        MessageCommand as MessageCommandPayload,
        PrimaryEntryPointCommand as PrimaryEntryPointCommandPayload,
        ApplicationCommand as ApplicationCommandPayload,
        ApplicationCommandOption as ApplicationCommandOptionPayload,
        ApplicationCommandStringOptionChoice as ApplicationCommandStringOptionChoicePayload,
        ApplicationCommandIntegerOptionChoice as ApplicationCommandIntegerOptionChoicePayload,
        ApplicationCommandNumberOptionChoice as ApplicationCommandNumberOptionChoicePayload,
        SendableApplicationCommandStringOptionChoice as SendableApplicationCommandStringOptionChoicePayload,
        SendableApplicationCommandIntegerOptionChoice as SendableApplicationCommandIntegerOptionChoicePayload,
        SendableApplicationCommandNumberOptionChoice as SendableApplicationCommandNumberOptionChoicePayload,
        ApplicationCommandUpdateRequestBody as ApplicationCommandUpdateRequestBodyPayload,
    )

    ApplicationCommandParent = Union['SlashCommand', 'SlashCommandGroup']

__all__ = (
    'BaseCommand',
    'SlashCommand',
    'UserCommand',
    'MessageCommand',
    'PrimaryEntryPointCommand',
    'UnknownCommand',
    'Option',
    'SlashCommandGroup',
    'Choice',
    'ApplicationCommand',
    '_command_factory',
)

T = TypeVar('T')


class BaseCommand(Hashable):
    """An ABC that represents an application command.

    The following implement this ABC:

    - :class:`~slaycord.SlashCommand`
    - :class:`~slaycord.UserCommand`
    - :class:`~slaycord.MessageCommand`
    - :class:`~slaycord.UnknownCommand`

    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The command's ID.
    application_id: :class:`int`
        The ID of the application this command belongs to.
    version: :class:`int`
        The command's version.
    type: :class:`~slaycord.AppCommandType`
        The type of application command.
    name: :class:`str`
        The command's name.
    name_localized: Optional[:class:`str`]
        The localized command's name.
    name_localizations: Dict[:class:`Locale`, :class:`str`]
        The localized names of the application command. Used for display purposes.
    description: :class:`str`
        The command's description.
    description_localized: :class:`str`
        The localized command's description.
    description_localizations: Dict[:class:`Locale`, :class:`str`]
        The localized descriptions of the application command. Used for display purposes.
    guild_id: Optional[:class:`int`]
        The ID of the guild this command is registered in. A value of ``None``
        denotes that it is a global command.
    dm_permission: :class:`bool`
        A boolean that indicates whether this command can be run in direct messages.
    allowed_contexts: Optional[:class:`~slaycord.AppCommandContext`]
        The contexts that this command is allowed to be used in. Overrides the ``dm_permission`` attribute.
    allowed_installs: Optional[:class:`~slaycord.AppInstallationType`]
        The installation contexts that this command is allowed to be installed in.
    nsfw: :class:`bool`
        Whether the command is NSFW and should only work in NSFW channels.
    """

    __slots__ = (
        '_state',
        'id',
        'application_id',
        'version',
        '_default_member_permissions',
        'type',
        'name',
        'name_localized',
        'name_localizations',
        'description',
        'description_localized',
        'description_localizations',
        'guild_id',
        'dm_permission',
        'allowed_contexts',
        'allowed_installs',
        # 'handler',
        'nsfw',
    )

    if TYPE_CHECKING:
        _state: ConnectionState

        id: int
        application_id: int
        version: int
        _default_member_permissions: Optional[int]
        # This is actually annotation, but black hates it for some reason
        # type_ AppCommandType
        name: str
        name_localized: Optional[str]
        name_localizations: Dict[Locale, str]
        description: str
        description_localized: Optional[str]
        description_localizations: Dict[Locale, str]
        guild_id: Optional[int]
        dm_permission: bool
        allowed_contexts: Optional[AppCommandContext]
        allowed_installs: Optional[AppInstallationType]
        # handler: AppCommandHandler
        nsfw: bool

    def __init__(self, *, data: ApplicationCommandPayload, state: ConnectionState) -> None:
        self._state: ConnectionState = state
        self.id: int = int(data['id'])
        self.application_id: int = int(data['application_id'])
        self._update(data)

    def _update(self, data: ApplicationCommandPayload) -> None:
        dmp = data.get('default_member_permissions')
        dp = data.get('dm_permission')
        c = data.get('contexts')
        it = data.get('integration_types')
        nsfw = data.get('nsfw')

        self.version: int = int(data['version'])
        self._default_member_permissions: Optional[int] = None if dmp is None else int(dmp)
        # self.type: AppCommandType = try_enum(AppCommandType, data['type'])
        self.name: str = data['name']
        self.name_localized: Optional[str] = data.get('name_localized')
        self.name_localizations: Dict[Locale, str] = {
            try_enum(Locale, k): v for k, v in data.get('name_localizations') or {}
        }
        self.description: str = data['description']
        self.description_localized: Optional[str] = data.get('description_localized')
        self.description_localizations: Dict[Locale, str] = {
            try_enum(Locale, k): v for k, v in data.get('description_localizations') or {}
        }
        self.guild_id: Optional[int] = _get_as_snowflake(data, 'guild_id')

        self.dm_permission: bool = True if dp is None else dp
        self.allowed_contexts: Optional[AppCommandContext] = None if c is None else AppCommandContext._from_value(c)
        self.allowed_installs: Optional[AppInstallationType] = None if it is None else AppInstallationType._from_value(it)
        # self.handler: Optional[AppCommandHandler] = None if h is None else try_enum(AppCommandHandler, h)
        self.nsfw: bool = False if nsfw is None else nsfw

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id} name={self.name!r}>'

    def __str__(self) -> str:
        return self.name

    @property
    def default_member_permissions(self) -> Optional[Permissions]:
        """Optional[:class:`~slaycord.Permissions`]: The default permissions required to use this command.

        .. note::
            This may be overrided on a guild-by-guild basis.
        """
        dmp = self._default_member_permissions
        return None if dmp is None else Permissions._from_value(dmp)

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`~slaycord.Guild`]: Returns the guild this command is registered to
        if it exists.
        """
        return self._state._get_guild(self.guild_id)

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the command."""
        return f'</{self.name}:{self.id}>'

    def is_group(self) -> bool:
        """:class:`bool`: Whether this command is a group."""
        return False

    async def delete(self) -> None:
        """|coro|

        Deletes the application command.

        Raises
        ------
        NotFound
            The application command was not found.
        Forbidden
            You do not have permission to delete this application command.
        HTTPException
            Deleting the application command failed.
        TypeError
            The application command was global.
        """
        http = self._state.http

        if not self.guild_id:
            raise TypeError('Cannot delete global commands in OAuth2 context')

        await http.delete_guild_application_command(
            self.application_id,
            self.guild_id,
            self.id,
        )


class SlashCommand(BaseCommand):
    """Represents a slash command.

    This inherits from :class:`~slaycord.BaseCommand`.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.

    Attributes
    ----------
    options: List[Union[:class:`Argument`, :class:`SlashCommandGroup`]]
        A list of options.
    """

    __slots__ = ('options',)

    def _update(self, data: SlashCommandPayload) -> None:
        super()._update(data)
        state = self._state
        self.options: List[Union[Option, SlashCommandGroup]] = [
            app_command_option_factory(
                data=d,
                parent=self,
                state=state,
            )
            for d in data.get('options', ())
        ]

    @property
    def type(self) -> Literal[AppCommandType.chat_input]:
        """:class:`AppCommandType`: The type of application command. This is always :attr:`AppCommandType.chat_input`."""
        return AppCommandType.chat_input

    def is_group(self) -> bool:
        """Query whether this command is a group.

        Returns
        -------
        :class:`bool`
            Whether this command is a group.
        """
        return any(isinstance(o, SlashCommandGroup) for o in self.options)


class UserCommand(BaseCommand):
    """Represents an user command.

    This inherits from :class:`~slaycord.BaseCommand`.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.
    """

    __slots__ = ()

    @property
    def type(self) -> Literal[AppCommandType.user]:
        """:class:`AppCommandType`: The type of application command. This is always :attr:`AppCommandType.user`."""
        return AppCommandType.user

    async def edit(
        self,
        *,
        name: str = MISSING,
        name_localizations: Optional[Dict[Locale, str]] = MISSING,
        description: str = MISSING,
        description_localizations: Optional[Dict[Locale, str]] = MISSING,
        default_member_permissions: Optional[Permissions] = MISSING,
        dm_permission: Optional[bool] = MISSING,
        allowed_contexts: Optional[AppCommandContext] = MISSING,
        allowed_installs: Optional[AppInstallationType] = MISSING,
    ) -> UserCommand:
        """|coro|

        Edits the command.

        Raises
        ------
        NotFound
            The application command was not found.
        Forbidden
            You do not have permission to edit this application command.
        HTTPException
            Editing the application command failed.
        TypeError
            The application command was global.
        """

        if not self.guild_id:
            raise TypeError('Cannot edit global commands in OAuth2 context')

        payload: ApplicationCommandUpdateRequestBodyPayload = {}

        if name is not MISSING:
            payload['name'] = name

        if name_localizations is not MISSING:
            if name_localizations is None:
                payload['name_localizations'] = None
            else:
                payload['name_localizations'] = {k.value: v for k, v in name_localizations.items()}

        if description is not MISSING:
            payload['description'] = description

        if description_localizations is not MISSING:
            if description_localizations is None:
                payload['description_localizations'] = None
            else:
                payload['description_localizations'] = {k.value: v for k, v in description_localizations.items()}

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
                # Should be fine:tm:
                payload['contexts'] = allowed_contexts.to_array()  # type: ignore

        if allowed_installs is not MISSING:
            if allowed_installs is None:
                payload['integration_types'] = None
            else:
                # Should be fine:tm:
                payload['integration_types'] = allowed_installs.to_array()  # type: ignore

        state = self._state
        data = await state.http.edit_guild_command(self.application_id, self.guild_id, self.id, payload)
        return UserCommand(data=data, state=state)


class MessageCommand(BaseCommand):
    """Represents a message command.

    This inherits from :class:`~slaycord.BaseCommand`.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.
    """

    __slots__ = ()

    @property
    def type(self) -> Literal[AppCommandType.message]:
        """:class:`AppCommandType`: The type of application command. This is always :attr:`AppCommandType.message`."""
        return AppCommandType.message


class PrimaryEntryPointCommand(BaseCommand):
    """Represents a primary entry-point command.

    This inherits from :class:`~slaycord.BaseCommand`.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.

    Attributes
    ----------
    handler: Optional[:class:`~slaycord.AppCommandHandler`]
        Determines whether the interaction is handled by the app's interactions handler or by Discord.
    """

    __slots__ = ('handler',)

    def _update(self, data: PrimaryEntryPointCommandPayload) -> None:
        super()._update(data)

        h = data.get('handler')
        self.handler: Optional[AppCommandHandler] = None if h is None else try_enum(AppCommandHandler, h)

    @property
    def type(self) -> Literal[AppCommandType.primary_entry_point]:
        """:class:`AppCommandType`: The type of application command. This is always :attr:`AppCommandType.primary_entry_point`."""
        return AppCommandType.primary_entry_point


class UnknownCommand(BaseCommand):
    """Represents a command that is not recognized by the library.

    This inherits from :class:`~slaycord.BaseCommand`.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two commands are equal.

        .. describe:: x != y

            Checks if two commands are not equal.

        .. describe:: hash(x)

            Return the command's hash.

        .. describe:: str(x)

            Returns the command's name.

    Attributes
    ----------
    raw_type: :class:`int`
        The raw value for the command.
    raw_payload: Dict[:class:`str`, Any]
        The raw data.
    """

    __slots__ = (
        'raw_type',
        'raw_payload',
    )

    def _update(self, data: ApplicationCommandPayload) -> None:
        super()._update(data)

        self.raw_type: int = data['type']
        self.raw_payload: ApplicationCommandPayload = data

    @property
    def type(self) -> Literal[AppCommandType.unknown]:
        """:class:`AppCommandType`: The type of application command. This is always :attr:`AppCommandType.unknown`."""
        return AppCommandType.unknown


class Option:
    """Represents an application command option.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: :class:`~slaycord.AppCommandOptionType`
        The type of option.
    name: :class:`str`
        The name of the option.
    name_localized: Optional[:class:`str`]
        The localized name of the option.
    name_localizations: Dict[:class:`~slaycord.Locale`, :class:`str`]
        The localized names of the option. Used for display purposes.
    description: :class:`str`
        The description of the option.
    description_localized: Optional[:class:`str`]
        The localized description of the option.
    description_localizations: Dict[:class:`~slaycord.Locale`, :class:`str`]
        The localized descriptions of the option. Used for display purposes.
    required: :class:`bool`
        Whether the option is required.
    choices: List[:class:`Choice`]
        A list of choices for the command to choose from for this option.
    parent: Union[:class:`SlashCommand`, :class:`SlashCommandGroup`]
        The parent application command that has this option.
    channel_types: List[:class:`~slaycord.ChannelType`]
        The channel types that are allowed for this option.
    min_value: Optional[Union[:class:`int`, :class:`float`]]
        The minimum supported value for this option.
    max_value: Optional[Union[:class:`int`, :class:`float`]]
        The maximum supported value for this option.
    min_length: Optional[:class:`int`]
        The minimum allowed length for this option.
    max_length: Optional[:class:`int`]
        The maximum allowed length for this option.
    autocomplete: :class:`bool`
        Whether the option has autocomplete.
    """

    __slots__ = (
        '_state',
        'type',
        'name',
        'name_localized',
        'name_localizations',
        'description',
        'description_localized',
        'description_localizations',
        'required',
        'choices',
        'parent',
        'channel_types',
        'min_value',
        'max_value',
        'min_length',
        'max_length',
        'autocomplete',
    )

    def __init__(
        self,
        *,
        data: ApplicationCommandOptionPayload,
        parent: ApplicationCommandParent,
        state: Optional[ConnectionState] = None,
    ) -> None:
        self._state: Optional[ConnectionState] = state
        self.parent: ApplicationCommandParent = parent
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} type={self.type!r} required={self.required}>'

    def _from_data(self, data: ApplicationCommandOptionPayload) -> None:
        self.type: AppCommandOptionType = try_enum(AppCommandOptionType, data['type'])
        self.name: str = data['name']
        self.name_localized: Optional[str] = data.get('name_localized')
        self.name_localizations: Dict[Locale, str] = {
            try_enum(Locale, k): v for k, v in (data.get('name_localizations') or {}).items()
        }
        self.description: str = data['description']
        self.description_localizations: Dict[Locale, str] = {
            try_enum(Locale, k): v for k, v in (data.get('description_localizations') or {}).items()
        }
        self.required: bool = data.get('required', False)
        self.choices: List[Choice[Union[int, float, str]]] = list(map(Choice.from_dict, data.get('choices', ())))
        self.channel_types: List[ChannelType] = [try_enum(ChannelType, d) for d in data.get('channel_types', ())]
        self.min_value: Optional[Union[int, float]] = data.get('min_value')
        self.max_value: Optional[Union[int, float]] = data.get('max_value')
        self.min_length: Optional[int] = data.get('min_length')
        self.max_length: Optional[int] = data.get('max_length')
        self.autocomplete: bool = data.get('autocomplete', False)


class SlashCommandGroup:
    """Represents an application command subcommand.

    .. versionadded:: 3.0

    Attributes
    ----------
    type: :class:`~slaycord.AppCommandOptionType`
        The type of subcommand.
    name: :class:`str`
        The name of the subcommand.
    description: :class:`str`
        The description of the subcommand.
    name_localizations: Dict[:class:`~slaycord.Locale`, :class:`str`]
        The localised names of the subcommand. Used for display purposes.
    description_localizations: Dict[:class:`~slaycord.Locale`, :class:`str`]
        The localised descriptions of the subcommand. Used for display purposes.
    options: List[Union[:class:`Option`, :class:`SlashCommandGroup`]]
        A list of options.
    parent: Union[:class:`SlashCommand`, :class:`SlashCommandGroup`]
        The parent application command.
    """

    __slots__ = (
        '_state',
        'type',
        'name',
        'name_localized',
        'name_localizations',
        'description',
        'description_localized',
        'description_localizations',
        'options',
        'parent',
    )

    def __init__(
        self,
        *,
        data: ApplicationCommandOptionPayload,
        parent: ApplicationCommandParent,
        state: Optional[ConnectionState] = None,
    ) -> None:
        self._state: Optional[ConnectionState] = state
        self.parent: ApplicationCommandParent = parent
        self._from_data(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} name={self.name!r} type={self.type!r}>'

    @property
    def qualified_name(self) -> str:
        """:class:`str`: Returns the fully qualified command name.

        The qualified name includes the parent name as well. For example,
        in a command like ``/foo bar`` the qualified name is ``foo bar``.
        """
        # A B C
        #     ^ self
        #   ^ parent
        # ^ grandparent

        names = [self.name, self.parent.name]
        if isinstance(self.parent, SlashCommandGroup):
            names.append(self.parent.parent.name)

        return ' '.join(reversed(names))

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given SlashCommandGroup."""
        names = [self.name, self.parent.name]

        if isinstance(self.parent, SlashCommandGroup):
            names.append(self.parent.parent.name)

        parent = self.parent
        while isinstance(parent, SlashCommandGroup):
            parent = parent.parent
        command_id = parent.id

        return '</{}:{}>'.format(
            ' '.join(reversed(names)),
            command_id,
        )

    def _from_data(self, data: ApplicationCommandOptionPayload) -> None:
        state = self._state

        self.type: AppCommandOptionType = try_enum(AppCommandOptionType, data['type'])
        self.name: str = data['name']
        self.description: str = data['description']
        self.options: List[Union[Option, SlashCommandGroup]] = [
            app_command_option_factory(data=d, parent=self, state=state) for d in data.get('options', ())
        ]
        self.name_localizations: Dict[Locale, str] = {
            try_enum(Locale, k): v for k, v in (data.get('name_localizations') or {}).items()
        }
        self.description_localizations: Dict[Locale, str] = {
            try_enum(Locale, k): v for k, v in (data.get('description_localizations') or {}).items()
        }


class Choice(Generic[T]):
    """Represents an application command argument choice.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two choices are equal.

        .. describe:: x != y

            Checks if two choices are not equal.

        .. describe:: hash(x)

            Returns the choice's hash.

    Parameters
    ----------
    name: :class:`str`
        The name of the choice. Used for display purposes.
        Can only be up to 100 characters.
    name_localized: Optional[:class:`str`]
        The localized name of the choice.
    name_localizations: Optional[Dict[:class:`~slaycord.Locale`, :class:`str`]]
        The localized names of the choice. Used for display purposes.
    value: Union[:class:`str`, :class:`int`, :class:`float`]
        The value of the choice. If it's a string, it can only be
        up to 100 characters long.
    """

    __slots__ = (
        'name',
        'name_localized',
        'name_localizations',
        'value',
    )

    def __init__(self, *, name: str, name_localizations: Optional[Dict[Locale, str]] = None, value: T):
        self.name: str = name
        self.name_localized: Optional[str] = None
        self.name_localizations: Optional[Dict[Locale, str]] = name_localizations
        self.value: T = value

    @classmethod
    def from_dict(
        cls,
        data: Union[
            ApplicationCommandStringOptionChoicePayload,
            ApplicationCommandIntegerOptionChoicePayload,
            ApplicationCommandNumberOptionChoicePayload,
            SendableApplicationCommandStringOptionChoicePayload,
            SendableApplicationCommandIntegerOptionChoicePayload,
            SendableApplicationCommandNumberOptionChoicePayload,
        ],
    ) -> Choice[T]:
        self = cls.__new__(cls)
        self.name = data['name']
        self.name_localized = data.get('name_localized')
        self.value = data['value']  # type: ignore # This seems to break every other pyright release
        self.name_localizations = {try_enum(Locale, k): v for k, v in (data.get('name_localizations') or {}).items()}
        return self

    def __eq__(self, o: object) -> bool:
        return isinstance(o, Choice) and self.name == o.name and self.value == o.value

    def __hash__(self) -> int:
        return hash((self.name, self.value))

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}(name={self.name!r}, value={self.value!r})'

    def to_dict(
        self,
    ) -> Union[
        SendableApplicationCommandStringOptionChoicePayload,
        SendableApplicationCommandIntegerOptionChoicePayload,
        SendableApplicationCommandNumberOptionChoicePayload,
    ]:
        payload: Union[
            SendableApplicationCommandStringOptionChoicePayload,
            SendableApplicationCommandIntegerOptionChoicePayload,
            SendableApplicationCommandNumberOptionChoicePayload,
        ] = {
            'name': self.name,
            'value': self.value,
        }  # type: ignore

        if self.name_localizations is not None:
            payload['name_localizations'] = {k.value: v for k, v in self.name_localizations.items()}

        return payload


ApplicationCommand = Union[
    SlashCommand,
    UserCommand,
    MessageCommand,
    PrimaryEntryPointCommand,
    UnknownCommand,
]


def app_command_option_factory(
    data: ApplicationCommandOptionPayload,
    parent: ApplicationCommandParent,
    *,
    state: Optional[ConnectionState] = None,
) -> Union[Option, SlashCommandGroup]:
    if data['type'] in (1, 2):
        return SlashCommandGroup(data=data, parent=parent, state=state)
    return Option(data=data, parent=parent, state=state)


@overload
def _command_factory(data: SlashCommandPayload, state: ConnectionState) -> SlashCommand:
    ...


@overload
def _command_factory(data: UserCommandPayload, state: ConnectionState) -> UserCommand:
    ...


@overload
def _command_factory(data: MessageCommandPayload, state: ConnectionState) -> MessageCommand:
    ...


@overload
def _command_factory(data: PrimaryEntryPointCommandPayload, state: ConnectionState) -> PrimaryEntryPointCommand:
    ...


@overload
def _command_factory(data: ApplicationCommandPayload, state: ConnectionState) -> ApplicationCommand:
    ...


def _command_factory(data: ApplicationCommandPayload, state: ConnectionState) -> ApplicationCommand:
    if data['type'] == 1:
        return SlashCommand(data=data, state=state)
    elif data['type'] == 2:
        return UserCommand(data=data, state=state)
    elif data['type'] == 3:
        return MessageCommand(data=data, state=state)
    elif data['type'] == 4:
        return PrimaryEntryPointCommand(data=data, state=state)
    return UnknownCommand(data=data, state=state)
