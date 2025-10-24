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

from copy import copy
import inspect
import logging
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from ..activity import ActivityInvite
from ..enums import try_enum, ChannelType
from ..entitlements import Entitlement
from ..relationship import Relationship
from ..state import BaseConnectionState
from ..user import ClientUser
from ..utils import _get_as_snowflake
from .activities import ActivityParticipant
from .channel import PartialChannel
from .enums import JoinIntent, LayoutMode, OrientationLockState, ThermalState
from .guild import PartialGuild
from .member import Member
from .message import Message
from .notification import Notification
from .quests import QuestEnrollmentStatus
from .settings import VoiceSettings
from .voice_connection_status import VoiceConnectionStatus
from .voice_state import VoiceState

if TYPE_CHECKING:
    from ..http import HTTPClient
    from .guild import Guild
    from .types.events import (
        ReadyEvent as ReadyEventPayload,
        CurrentUserUpdateEvent as CurrentUserUpdateEventPayload,
        CurrentGuildMemberUpdateEvent as CurrentGuildMemberUpdateEventPayload,
        GuildStatusEvent as GuildStatusEventPayload,
        GuildCreateEvent as GuildCreateEventPayload,
        ChannelCreateEvent as ChannelCreateEventPayload,
        RelationshipUpdateEvent as RelationshipUpdateEventPayload,
        VoiceChannelSelectEvent as VoiceChannelSelectEventPayload,
        VoiceStateCreateEvent as VoiceStateCreateEventPayload,
        VoiceStateUpdateEvent as VoiceStateUpdateEventPayload,
        VoiceStateDeleteEvent as VoiceStateDeleteEventPayload,
        VoiceSettingsUpdateEvent as VoiceSettingsUpdateEventPayload,
        VoiceConnectionStatusEvent as VoiceConnectionStatusEventPayload,
        SpeakingStartEvent as SpeakingStartEventPayload,
        SpeakingStopEvent as SpeakingStopEventPayload,
        GameJoinEvent as GameJoinEventPayload,
        ActivityJoinEvent as ActivityJoinEventPayload,
        ActivityJoinRequestEvent as ActivityJoinRequestEventPayload,
        ActivityInviteEvent as ActivityInviteEventPayload,
        ActivityPipModeUpdateEvent as ActivityPipModeUpdateEventPayload,
        ActivityLayoutModeUpdateEvent as ActivityLayoutModeUpdateEventPayload,
        ThermalStateUpdateEvent as ThermalStateUpdateEventPayload,
        OrientationUpdateEvent as OrientationUpdateEventPayload,
        ActivityInstanceParticipantsUpdateEvent as ActivityInstanceParticipantsUpdateEventPayload,
        NotificationCreateEvent as NotificationCreateEventPayload,
        MessageCreateEvent as MessageCreateEventPayload,
        MessageUpdateEvent as MessageUpdateEventPayload,
        MessageDeleteEvent as MessageDeleteEventPayload,
        EntitlementCreateEvent as EntitlementCreateEventPayload,
        EntitlementDeleteEvent as EntitlementDeleteEventPayload,
        ScreenshareStateUpdateEvent as ScreenshareStateUpdateEventPayload,
        VideoStateUpdateEvent as VideoStateUpdateEventPayload,
        AuthorizeRequestEvent as AuthorizeRequestEventPayload,
        QuestEnrollmentStatusUpdateEvent as QuestEnrollmentStatusUpdateEventPayload,
    )

_log = logging.getLogger(__name__)


class RPCConnectionState(BaseConnectionState):
    __slots__ = (
        'dispatch',
        'parsers',
        'version',
        'cdn_host',
        'api_endpoint',
        'environment',
        'user',
    )

    def __init__(self, *, dispatch: Callable[..., None], http: HTTPClient) -> None:
        super().__init__(dispatch=dispatch, http=http)
        self.parsers: Dict[str, Callable[[Any], None]]
        self.parsers = parsers = {}
        for attr, func in inspect.getmembers(self):
            if attr.startswith('parse_'):
                parsers[attr[6:].upper()] = func

        self.clear()

    def clear(self) -> None:
        self.version: int = 0
        self.cdn_host: str = ''
        self.api_endpoint: str = ''
        self.environment: str = 'production'
        self.user: Optional[ClientUser] = None

    async def close(self) -> None:
        pass

    def parse_ready(self, data: ReadyEventPayload) -> None:
        config_data = data['config']
        user_data = data.get('user')

        self.version = data['v']
        self.cdn_host = config_data['cdn_host']
        self.api_endpoint = config_data['api_endpoint']
        self.environment = config_data['environment']
        self.user = ClientUser._from_rpc(user_data, self) if user_data else None

        if self.user is not None and self.user.id == 1045800378228281345:
            _log.warning('Detected arRPC. Most of functions will not work!')

        self.dispatch('ready')

    def parse_current_user_update(self, data: CurrentUserUpdateEventPayload) -> None:
        if self.user is None:
            self.user = ClientUser._from_rpc(data, self)
            self.dispatch('current_user_update', None, self.user)
        else:
            old = copy(self.user)
            self.user._update_from_rpc(data)
            self.dispatch('current_user_update', old, self.user)

    def parse_current_guild_member_update(self, data: CurrentGuildMemberUpdateEventPayload) -> None:
        self.dispatch('current_member_update', Member(data=data, state=self))

    def parse_guild_status(self, data: GuildStatusEventPayload) -> None:
        guild = PartialGuild(data=data['guild'], state=self)

        self.dispatch('guild_update', guild)

    def parse_guild_create(self, data: GuildCreateEventPayload) -> None:
        guild = PartialGuild(data=data, state=self)

        self.dispatch('guild_join', guild)

    def parse_channel_create(self, data: ChannelCreateEventPayload) -> None:
        channel = PartialChannel(data=data, guild_id=0, state=self)

        if channel.type in (
            ChannelType.private,
            ChannelType.group,
            ChannelType.ephemeral_dm,
        ):
            event = 'private_channel_create'
        else:
            event = 'guild_channel_create'

        self.dispatch(event, channel)

    def parse_relationship_update(self, data: RelationshipUpdateEventPayload) -> None:
        relationship = Relationship._from_rpc(data, self)

        self.dispatch('relationship_update', relationship)

    def parse_voice_channel_select(self, data: VoiceChannelSelectEventPayload) -> None:
        channel_id = _get_as_snowflake(data, 'channel_id')
        guild_id = _get_as_snowflake(data, 'guild_id')  # Always seems to be absent when channel_id is null?
        self.dispatch('voice_channel_select', channel_id, guild_id)

    def parse_voice_state_create(self, data: VoiceStateCreateEventPayload) -> None:
        voice_state = VoiceState(data=data, state=self)

        self.dispatch('voice_state_create', voice_state)

    def parse_voice_state_update(self, data: VoiceStateUpdateEventPayload) -> None:
        voice_state = VoiceState(data=data, state=self)

        self.dispatch('voice_state_update', voice_state)

    def parse_voice_state_delete(self, data: VoiceStateDeleteEventPayload) -> None:
        voice_state = VoiceState(data=data, state=self)

        self.dispatch('voice_state_delete', voice_state)

    def parse_voice_settings_update(self, data: VoiceSettingsUpdateEventPayload) -> None:
        self.dispatch('voice_settings_update', VoiceSettings(data=data, state=self))

    def parse_voice_connection_status(self, data: VoiceConnectionStatusEventPayload) -> None:
        self.dispatch('voice_connection_status_update', VoiceConnectionStatus(data))

    def parse_speaking_start(self, data: SpeakingStartEventPayload) -> None:
        channel_id = int(data['channel_id'])
        user_id = int(data['user_id'])

        self.dispatch('speaking_start', channel_id, user_id)

    def parse_speaking_stop(self, data: SpeakingStopEventPayload) -> None:
        channel_id = int(data['channel_id'])
        user_id = int(data['user_id'])

        self.dispatch('speaking_stop', channel_id, user_id)

    def parse_game_join(self, data: GameJoinEventPayload) -> None:
        intent = data.get('intent')

        self.dispatch('game_join', data['secret'], None if intent is None else try_enum(JoinIntent, intent))

    def parse_activity_join(self, data: ActivityJoinEventPayload) -> None:
        intent = data.get('intent')

        self.dispatch('activity_join', data['secret'], None if intent is None else try_enum(JoinIntent, intent))

    def parse_activity_join_request(self, data: ActivityJoinRequestEventPayload) -> None:
        self.dispatch('activity_invite', ActivityInvite.from_rpc(data, self))

    def parse_activity_invite(self, data: ActivityInviteEventPayload) -> None:
        self.dispatch('activity_invite', ActivityInvite.from_rpc(data, self))

    def parse_activity_pip_mode_update(self, data: ActivityPipModeUpdateEventPayload) -> None:
        self.dispatch('pip_mode_update', data['is_pip_mode'])

    def parse_activity_layout_mode_update(self, data: ActivityLayoutModeUpdateEventPayload) -> None:
        self.dispatch('layout_mode_update', try_enum(LayoutMode, data['layout_mode']))

    def parse_thermal_state_update(self, data: ThermalStateUpdateEventPayload) -> None:
        self.dispatch('thermal_state_update', try_enum(ThermalState, data['thermal_state']))

    def parse_orientation_update(self, data: OrientationUpdateEventPayload) -> None:
        self.dispatch('orientation_update', try_enum(OrientationLockState, data['screen_orientation']))

    def parse_activity_instance_participants_update(self, data: ActivityInstanceParticipantsUpdateEventPayload) -> None:
        participants = [ActivityParticipant._from_rpc(d, self) for d in data['participants']]

        self.dispatch('raw_activity_instance_participants_update', participants)

    def parse_notification_create(self, data: NotificationCreateEventPayload) -> None:
        self.dispatch('notification', Notification(data=data, state=self))

    def parse_message_create(self, data: MessageCreateEventPayload) -> None:
        channel_id = int(data['channel_id'])
        message = Message(data=data['message'], channel_id=channel_id, state=self)

        self.dispatch('message', message)

    def parse_message_update(self, data: MessageUpdateEventPayload) -> None:
        channel_id = int(data['channel_id'])
        message = Message(data=data['message'], channel_id=channel_id, state=self)

        self.dispatch('message_edit', message)

    def parse_message_delete(self, data: MessageDeleteEventPayload) -> None:
        channel_id = int(data['channel_id'])
        message_id = int(data['message']['id'])

        self.dispatch('message_delete', channel_id, message_id)

    def parse_entitlement_create(self, data: EntitlementCreateEventPayload) -> None:
        entitlement = Entitlement(data=data, state=self)

        self.dispatch('entitlement_create', entitlement)

    def parse_entitlement_delete(self, data: EntitlementDeleteEventPayload) -> None:
        entitlement = Entitlement(data=data, state=self)

        self.dispatch('entitlement_delete', entitlement)

    def parse_screenshare_state_update(self, data: ScreenshareStateUpdateEventPayload) -> None:
        application = data.get('application')
        if application is None:
            application_name = None
        else:
            application_name = application.get('name')

        self.dispatch('screenshare_state_update', data['active'], data.get('pid'), application_name)

    def parse_video_state_update(self, data: VideoStateUpdateEventPayload) -> None:
        self.dispatch('video_state_update', data['active'])

    def parse_authorize_request(self, data: AuthorizeRequestEventPayload) -> None:
        self.dispatch('authorize_request')

    def parse_quest_enrollment_status_update(self, data: QuestEnrollmentStatusUpdateEventPayload) -> None:
        self.dispatch('quest_enrollment_status_update', QuestEnrollmentStatus(data))

    # Overrides
    def get_rpc_guild(self, guild_id: Optional[int]) -> Optional[Guild]:
        return None
