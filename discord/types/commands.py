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

from typing import Dict, List, Literal, Optional, TypedDict, Union
from typing_extensions import NotRequired, Required

from .channel import ChannelType
from .interactions import InteractionContextType, InteractionInstallationType
from .snowflake import Snowflake

ApplicationCommandType = Literal[1, 2, 3, 4]


class BaseApplicationCommand(TypedDict, total=False):
    id: Required[Snowflake]
    application_id: Required[Snowflake]
    version: Required[Snowflake]
    default_member_permissions: NotRequired[Optional[str]]
    # This is actually annotation, but black hates it for some reason
    # type_ Required[ApplicationCommandType]
    name: Required[str]
    name_localized: Optional[str]
    name_localizations: Optional[Dict[str, str]]
    description: Required[str]
    description_localized: Optional[str]
    description_localizations: Optional[Dict[str, str]]
    guild_id: Snowflake
    dm_permission: Optional[bool]
    contexts: Optional[List[InteractionContextType]]
    integration_types: Optional[List[InteractionInstallationType]]
    # handler: ApplicationCommandHandler
    # options: List[ApplicationCommandOption]
    nsfw: bool


class SlashCommand(BaseApplicationCommand):
    type: Literal[1]
    options: NotRequired[List[ApplicationCommandOption]]


class UserCommand(BaseApplicationCommand):
    type: Literal[2]


class MessageCommand(BaseApplicationCommand):
    type: Literal[3]


class PrimaryEntryPointCommand(BaseApplicationCommand):
    type: Literal[4]
    handler: NotRequired[ApplicationCommandHandler]


ApplicationCommand = Union[
    SlashCommand,
    UserCommand,
    MessageCommand,
    PrimaryEntryPointCommand,
]

ApplicationCommandHandler = Literal[1, 2]
ApplicationCommandOption = Union[
    'ApplicationCommandSubcommandOption',
    'ApplicationCommandSubcommandGroupOption',
    'ApplicationCommandStringOption',
    'ApplicationCommandIntegerOption',
    'ApplicationCommandBooleanOption',
    'ApplicationCommandUserOption',
    'ApplicationCommandChannelOption',
    'ApplicationCommandRoleOption',
    'ApplicationCommandMentionableOption',
    'ApplicationCommandNumberOption',
    'ApplicationCommandAttachmentOption',
]


class BaseApplicationCommandOption(TypedDict):
    name: str
    name_localized: NotRequired[Optional[str]]
    name_localizations: NotRequired[Optional[Dict[str, str]]]
    description: str
    description_localized: NotRequired[Optional[str]]
    description_localizations: NotRequired[Optional[Dict[str, str]]]
    required: NotRequired[bool]


class ApplicationCommandSubcommandOption(BaseApplicationCommandOption):
    type: Literal[1]
    options: NotRequired[
        List[
            Union[
                ApplicationCommandStringOption,
                ApplicationCommandIntegerOption,
                ApplicationCommandBooleanOption,
                ApplicationCommandUserOption,
                ApplicationCommandChannelOption,
                ApplicationCommandRoleOption,
                ApplicationCommandMentionableOption,
                ApplicationCommandNumberOption,
                ApplicationCommandAttachmentOption,
            ]
        ]
    ]


class ApplicationCommandSubcommandGroupOption(BaseApplicationCommandOption, total=False):
    type: Required[Literal[2]]
    options: List[ApplicationCommandSubcommandOption]


class ApplicationCommandStringOption(BaseApplicationCommandOption, total=False):
    type: Required[Literal[3]]
    autocomplete: bool
    choices: List[ApplicationCommandStringOptionChoice]
    min_length: Optional[int]
    max_length: Optional[int]


class ApplicationCommandStringOptionChoice(TypedDict, total=False):
    name: Required[str]
    name_localized: Optional[str]
    name_localizations: Optional[Dict[str, str]]
    value: Required[str]


class ApplicationCommandIntegerOption(BaseApplicationCommandOption, total=False):
    type: Required[Literal[4]]
    autocomplete: bool
    choices: List[ApplicationCommandIntegerOptionChoice]
    min_value: Optional[int]
    max_value: Optional[int]


class ApplicationCommandIntegerOptionChoice(TypedDict, total=False):
    name: Required[str]
    name_localized: Optional[str]
    name_localizations: Optional[Dict[str, str]]
    value: Required[int]


class ApplicationCommandBooleanOption(BaseApplicationCommandOption):
    type: Literal[5]


class ApplicationCommandUserOption(BaseApplicationCommandOption):
    type: Literal[6]


class ApplicationCommandChannelOption(BaseApplicationCommandOption, total=False):
    type: Required[Literal[7]]
    channel_types: List[ChannelType]


class ApplicationCommandRoleOption(BaseApplicationCommandOption):
    type: Literal[8]


class ApplicationCommandMentionableOption(BaseApplicationCommandOption):
    type: Literal[9]


class ApplicationCommandNumberOption(BaseApplicationCommandOption, total=False):
    type: Required[Literal[10]]
    autocomplete: bool
    choices: List[ApplicationCommandNumberOptionChoice]
    min_value: Optional[float]
    max_value: Optional[float]


class ApplicationCommandNumberOptionChoice(TypedDict, total=False):
    name: Required[str]
    name_localized: Optional[str]
    name_localizations: Optional[Dict[str, str]]
    value: Required[float]


class ApplicationCommandAttachmentOption(BaseApplicationCommandOption):
    type: Literal[11]


# Permissions
ApplicationCommandPermissionType = Literal[1, 2, 3]  # ROLE->1, USER->2, CHANNEL->3


class ApplicationCommandPermission(TypedDict):
    id: Snowflake
    type: ApplicationCommandPermissionType
    permission: bool


class GuildApplicationCommandPermissions(TypedDict):
    id: Snowflake
    application_id: Snowflake
    guild_id: Snowflake
    permissions: List[ApplicationCommandPermission]


# Sendable
class SendableBaseApplicationCommandOption(TypedDict):
    name: str  # 1-32 characters
    name_localizations: NotRequired[Optional[Dict[str, str]]]  # max 34 keys, each value is 1-32 characters
    description: str  # 1-100 characters
    description_localizations: NotRequired[Optional[Dict[str, str]]]  # max 34 keys, each value is 1-100 characters
    required: NotRequired[Optional[bool]]


class SendableApplicationCommandSubcommandOption(SendableBaseApplicationCommandOption):
    type: Literal[1]
    options: NotRequired[
        Optional[
            List[
                Union[
                    SendableApplicationCommandStringOption,
                    SendableApplicationCommandIntegerOption,
                    SendableApplicationCommandBooleanOption,
                    SendableApplicationCommandUserOption,
                    SendableApplicationCommandChannelOption,
                    SendableApplicationCommandRoleOption,
                    SendableApplicationCommandMentionableOption,
                    SendableApplicationCommandNumberOption,
                    SendableApplicationCommandAttachmentOption,
                ]
            ]
        ]
    ]  # max 25


class SendableApplicationCommandSubcommandGroupOption(SendableBaseApplicationCommandOption, total=False):
    type: Required[Literal[2]]
    options: Optional[List[SendableApplicationCommandSubcommandOption]]


class SendableApplicationCommandStringOption(SendableBaseApplicationCommandOption, total=False):
    type: Required[Literal[3]]
    autocomplete: Optional[bool]
    choices: Optional[List[ApplicationCommandStringOptionChoice]]
    min_length: Optional[int]
    max_length: Optional[int]


class SendableApplicationCommandStringOptionChoice(TypedDict):
    name: str  # 1-100 chars
    name_localizations: NotRequired[Optional[Dict[str, str]]]  # max 34 keys, each value is 1-100 characters
    value: str  # max 6000 characters


class SendableApplicationCommandIntegerOption(SendableBaseApplicationCommandOption, total=False):
    type: Required[Literal[4]]
    autocomplete: Optional[bool]
    choices: Optional[List[SendableApplicationCommandIntegerOptionChoice]]
    min_value: Optional[int]
    max_value: Optional[int]


class SendableApplicationCommandIntegerOptionChoice(TypedDict):
    name: str  # 1-100 chars
    name_localizations: NotRequired[Optional[Dict[str, str]]]  # max 34 keys, each value is 1-100 characters
    value: int


class SendableApplicationCommandBooleanOption(SendableBaseApplicationCommandOption):
    type: Literal[5]


class SendableApplicationCommandUserOption(SendableBaseApplicationCommandOption):
    type: Literal[6]


class SendableApplicationCommandChannelOption(SendableBaseApplicationCommandOption, total=False):
    type: Required[Literal[7]]
    channel_types: Optional[List[ChannelType]]


class SendableApplicationCommandRoleOption(SendableBaseApplicationCommandOption):
    type: Literal[8]


class SendableApplicationCommandMentionableOption(SendableBaseApplicationCommandOption):
    type: Literal[9]


class SendableApplicationCommandNumberOption(SendableBaseApplicationCommandOption, total=False):
    type: Required[Literal[10]]
    autocomplete: Optional[bool]
    choices: Optional[List[ApplicationCommandNumberOptionChoice]]  # max 25 items
    min_value: Optional[float]
    max_value: Optional[float]


class SendableApplicationCommandNumberOptionChoice(TypedDict):
    name: str  # 1-100 chars
    name_localizations: NotRequired[Optional[Dict[str, str]]]  # max 34 keys, each value is 1-100 characters
    value: float


class SendableApplicationCommandAttachmentOption(SendableBaseApplicationCommandOption):
    type: Literal[11]


SendableApplicationCommandOption = Union[
    'SendableApplicationCommandSubcommandOption',
    'SendableApplicationCommandSubcommandGroupOption',
    'SendableApplicationCommandStringOption',
    'SendableApplicationCommandIntegerOption',
    'SendableApplicationCommandBooleanOption',
    'SendableApplicationCommandUserOption',
    'SendableApplicationCommandChannelOption',
    'SendableApplicationCommandRoleOption',
    'SendableApplicationCommandMentionableOption',
    'SendableApplicationCommandNumberOption',
    'SendableApplicationCommandAttachmentOption',
]


class ApplicationCommandCreateRequestBody(TypedDict, total=False):
    name: Required[str]  # 1-32 characters
    name_localizations: Optional[Dict[str, str]]  # max 34 keys, each value is 1-32 chars
    description: Optional[str]  # max 100 chars
    description_localizations: Optional[Dict[str, str]]  # max 34 keys, each value is 1-100 chars
    options: Optional[List[SendableApplicationCommandOption]]  # max 25 items
    default_member_permissions: Optional[str]
    dm_permission: Optional[bool]
    contexts: Optional[List[InteractionContextType]]  # min 1 item
    integration_types: Optional[List[InteractionInstallationType]]  # min 1 item
    handler: Optional[ApplicationCommandHandler]
    type: Optional[ApplicationCommandType]


class UpdateApplicationCommand(TypedDict, total=False):
    id: Snowflake
    name: Required[str]  # 1-32 characters
    name_localizations: Optional[Dict[str, str]]  # max 34 keys, each value is 1-32 chars
    description: Optional[str]  # max 100 chars
    description_localizations: Optional[Dict[str, str]]  # max 34 keys, each value is 1-100 chars
    options: Optional[List[SendableApplicationCommandOption]]  # max 25 items
    default_member_permissions: Optional[str]
    dm_permission: Optional[bool]
    contexts: Optional[List[InteractionContextType]]  # min 1 item
    integration_types: Optional[List[InteractionInstallationType]]  # min 1 item
    handler: Optional[ApplicationCommandHandler]
    type: Optional[ApplicationCommandType]


class ApplicationCommandUpdateRequestBody(TypedDict, total=False):
    name: str  # 1-32 characters
    name_localizations: Optional[Dict[str, str]]  # max 34 keys, each value is 1-32 chars
    description: Optional[str]  # max 100 chars
    description_localizations: Optional[Dict[str, str]]  # max 34 keys, each value is 1-100 chars
    options: Optional[List[SendableApplicationCommandOption]]  # max 25 items
    default_member_permissions: Optional[str]
    dm_permission: Optional[bool]
    contexts: Optional[List[InteractionContextType]]  # min 1 item
    integration_types: Optional[List[InteractionInstallationType]]  # min 1 item
    handler: Optional[ApplicationCommandHandler]
    type: Optional[ApplicationCommandType]
