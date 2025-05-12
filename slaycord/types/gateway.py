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

from typing import Dict, List, Literal, Optional, TypedDict, Tuple, Union
from typing_extensions import NotRequired, Required

from .activity import StatusType, PartialPresenceUpdate, Activity
from .appinfo import GatewayAppInfo, PartialAppInfo
from .audit_log import AuditLogEntry
from .automod import AutoModerationAction, AutoModerationRuleTriggerType
from .channel import ChannelType, DMChannel, GroupDMChannel, StageInstance, VoiceChannelEffect
from .emoji import Emoji, PartialEmoji
from .game_invite import GameInvite
from .guild import Guild, UnavailableGuild
from .integration import BaseIntegration, IntegrationApplication
from .interactions import Interaction
from .invite import InviteTargetType
from .lobby import LobbyMember, LobbyVoiceState, Lobby
from .member import MemberWithUser
from .message import Message, LobbyMessage, ReactionType
from .role import Role
from .scheduled_event import GuildScheduledEvent
from .settings import GatewayUserSettings, AudioContext, AudioSettings
from .sku import Entitlement
from .snowflake import Snowflake
from .soundboard import SoundboardSound
from .sticker import GuildSticker
from .stream import *
from .subscription import Subscription
from .threads import Thread, ThreadMember
from .user import (
    User,
    AvatarDecorationData,
    RelationshipType,
    Relationship,
    GameRelationshipType,
    GameRelationship,
    RecentUserActivity,
)
from .voice import GuildVoiceState, VoiceState


class SessionStartLimit(TypedDict):
    total: int
    remaining: int
    reset_after: int
    max_concurrency: int


class Gateway(TypedDict):
    url: str


class GatewayBot(Gateway):
    shards: int
    session_start_limit: SessionStartLimit


class CreateHeadlessSessionResponse(TypedDict):
    activities: List[Activity]
    token: str


class GatewayFeatureFlags(TypedDict):
    disabled_gateway_events: List[str]
    disabled_functions: List[str]


class ReadyEvent(TypedDict):
    v: int
    user_settings: GatewayUserSettings
    users: List[User]
    user: User
    session_id: str
    sessions: List[Session]
    scopes: List[str]
    resume_gateway_url: str
    relationships: NotRequired[List[Relationship]]
    private_channels: NotRequired[List[Union[DMChannel, GroupDMChannel]]]
    guilds: List[Guild]
    game_relationships: List[GameRelationship]
    feature_flags: GatewayFeatureFlags
    av_sf_protocol_floor: int
    application: GatewayAppInfo
    analytics_token: str


class SupplementalGuild(TypedDict):
    id: int
    voice_states: NotRequired[List[GuildVoiceState]]


class ClientInfo(TypedDict):
    version: int
    os: Literal['windows', 'osx', 'linux', 'android', 'ios', 'playstation', 'unknown']
    client: Literal['web', 'desktop', 'mobile', 'unknown']


class Session(TypedDict):
    session_id: str
    active: NotRequired[bool]
    client_info: ClientInfo
    status: StatusType
    # Not truly not required, just for sanity
    activities: NotRequired[List[Activity]]
    hidden_activities: NotRequired[List[Activity]]


class MergedPresences(TypedDict):
    friends: List[PartialPresenceUpdate]
    guilds: List[List[PartialPresenceUpdate]]


class ReadySupplementalEvent(TypedDict):
    guilds: List[SupplementalGuild]
    merged_members: List[List[MemberWithUser]]
    merged_presences: MergedPresences
    lazy_private_channels: List[Union[DMChannel, GroupDMChannel]]
    disclose: List[str]
    game_invites: List[GameInvite]
    user_activities: List[RecentUserActivity]


ResumedEvent = Literal[None]

MessageCreateEvent = Message


class MessageDeleteEvent(TypedDict):
    id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class MessageDeleteBulkEvent(TypedDict):
    ids: List[Snowflake]
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


MessageUpdateEvent = MessageCreateEvent


class MessageReactionAddEvent(TypedDict):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji
    member: NotRequired[MemberWithUser]
    guild_id: NotRequired[Snowflake]
    message_author_id: NotRequired[Snowflake]
    burst: bool
    burst_colors: NotRequired[List[str]]
    type: ReactionType


class MessageReactionRemoveEvent(TypedDict):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    emoji: PartialEmoji
    guild_id: NotRequired[Snowflake]
    burst: bool
    type: ReactionType


class MessageReactionRemoveAllEvent(TypedDict):
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


class MessageReactionRemoveEmojiEvent(TypedDict):
    emoji: PartialEmoji
    message_id: Snowflake
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]


InteractionCreateEvent = Interaction


PresenceUpdateEvent = PartialPresenceUpdate


UserUpdateEvent = User


class InviteCreateEvent(TypedDict):
    channel_id: Snowflake
    code: str
    created_at: str
    max_age: int
    max_uses: int
    temporary: bool
    uses: Literal[0]
    guild_id: NotRequired[Snowflake]
    inviter: NotRequired[User]
    target_type: NotRequired[InviteTargetType]
    target_user: NotRequired[User]
    target_application: NotRequired[PartialAppInfo]


class InviteDeleteEvent(TypedDict):
    channel_id: Snowflake
    code: str
    guild_id: NotRequired[Snowflake]


class _ChannelEvent(TypedDict):
    id: Snowflake
    type: ChannelType


class PartialChannelUpdate(TypedDict):
    id: Snowflake
    last_message_id: Optional[Snowflake]
    last_pin_timestamp: NotRequired[Optional[str]]


ChannelCreateEvent = ChannelUpdateEvent = ChannelDeleteEvent = _ChannelEvent
ChannelUpdatePartialEvent = PartialChannelUpdate


class ChannelRecipientEvent(TypedDict):
    channel_id: Snowflake
    user: User
    nick: str


class ChannelPinsUpdateEvent(TypedDict):
    channel_id: Snowflake
    guild_id: NotRequired[Snowflake]
    last_pin_timestamp: NotRequired[Optional[str]]


class ThreadCreateEvent(Thread, total=False):
    newly_created: bool
    members: List[ThreadMember]


ThreadUpdateEvent = Thread


class ThreadDeleteEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    parent_id: Snowflake
    type: ChannelType


class ThreadListSyncEvent(TypedDict):
    guild_id: Snowflake
    threads: List[Thread]
    members: List[ThreadMember]
    channel_ids: NotRequired[List[Snowflake]]


class ThreadMemberUpdate(ThreadMember):
    guild_id: Snowflake


class ThreadMembersUpdate(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    member_count: int
    added_members: NotRequired[List[ThreadMember]]
    removed_member_ids: NotRequired[List[Snowflake]]


class GuildMemberAddEvent(MemberWithUser):
    guild_id: Snowflake


class GuildMemberRemoveEvent(TypedDict):
    guild_id: Snowflake
    user: User


class GuildMemberUpdateEvent(TypedDict):
    guild_id: Snowflake
    roles: List[Snowflake]
    user: User
    avatar: Optional[str]
    joined_at: Optional[str]
    flags: int
    nick: NotRequired[str]
    premium_since: NotRequired[Optional[str]]
    deaf: NotRequired[bool]
    mute: NotRequired[bool]
    pending: NotRequired[bool]
    communication_disabled_until: NotRequired[str]
    avatar_decoration_data: NotRequired[AvatarDecorationData]


class GuildEmojisUpdateEvent(TypedDict):
    guild_id: Snowflake
    emojis: List[Emoji]


class GuildStickersUpdateEvent(TypedDict):
    guild_id: Snowflake
    stickers: List[GuildSticker]


GuildCreateEvent = GuildUpdateEvent = Guild
GuildDeleteEvent = UnavailableGuild


class _GuildBanEvent(TypedDict):
    guild_id: Snowflake
    user: User


GuildBanAddEvent = GuildBanRemoveEvent = _GuildBanEvent


class _GuildRoleEvent(TypedDict):
    guild_id: Snowflake
    role: Role


class GuildRoleDeleteEvent(TypedDict):
    guild_id: Snowflake
    role_id: Snowflake


GuildRoleCreateEvent = GuildRoleUpdateEvent = _GuildRoleEvent


class GuildMembersChunkEvent(TypedDict):
    guild_id: Snowflake
    members: List[MemberWithUser]
    chunk_index: int
    chunk_count: int
    not_found: NotRequired[List[Snowflake]]
    presences: NotRequired[List[PresenceUpdateEvent]]
    nonce: NotRequired[str]


class GuildIntegrationsUpdateEvent(TypedDict):
    guild_id: Snowflake


class _IntegrationEvent(BaseIntegration, total=False):
    guild_id: Required[Snowflake]
    role_id: Optional[Snowflake]
    enable_emoticons: bool
    subscriber_count: int
    revoked: bool
    application: IntegrationApplication


IntegrationCreateEvent = IntegrationUpdateEvent = _IntegrationEvent


class IntegrationDeleteEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    application_id: NotRequired[Snowflake]


class WebhooksUpdateEvent(TypedDict):
    guild_id: Snowflake
    channel_id: Snowflake


StageInstanceCreateEvent = StageInstanceUpdateEvent = StageInstanceDeleteEvent = StageInstance

GuildScheduledEventCreateEvent = GuildScheduledEventUpdateEvent = GuildScheduledEventDeleteEvent = GuildScheduledEvent


class _GuildScheduledEventUsersEvent(TypedDict):
    guild_scheduled_event_id: Snowflake
    user_id: Snowflake
    guild_id: Snowflake


GuildScheduledEventUserAdd = GuildScheduledEventUserRemove = _GuildScheduledEventUsersEvent

VoiceStateUpdateEvent = GuildVoiceState
VoiceChannelEffectSendEvent = VoiceChannelEffect

GuildSoundBoardSoundCreateEvent = GuildSoundBoardSoundUpdateEvent = SoundboardSound


class GuildSoundBoardSoundsUpdateEvent(TypedDict):
    guild_id: Snowflake
    soundboard_sounds: List[SoundboardSound]


class GuildSoundBoardSoundDeleteEvent(TypedDict):
    sound_id: Snowflake
    guild_id: Snowflake


class VoiceServerUpdateEvent(TypedDict):
    token: str
    guild_id: Optional[Snowflake]
    channel_id: NotRequired[Snowflake]
    endpoint: Optional[str]


class TypingStartEvent(TypedDict):
    channel_id: Snowflake
    user_id: Snowflake
    timestamp: int
    guild_id: NotRequired[Snowflake]
    member: NotRequired[MemberWithUser]


class AutoModerationActionExecution(TypedDict):
    guild_id: Snowflake
    action: AutoModerationAction
    rule_id: Snowflake
    rule_trigger_type: AutoModerationRuleTriggerType
    user_id: Snowflake
    channel_id: NotRequired[Snowflake]
    message_id: NotRequired[Snowflake]
    alert_system_message_id: NotRequired[Snowflake]
    content: str
    matched_keyword: Optional[str]
    matched_content: Optional[str]


class GuildAuditLogEntryCreate(AuditLogEntry):
    guild_id: Snowflake


class VoiceChannelStatusUpdateEvent(TypedDict):
    id: Snowflake
    guild_id: Snowflake
    status: Optional[str]


EntitlementCreateEvent = EntitlementUpdateEvent = EntitlementDeleteEvent = Entitlement


class PollVoteActionEvent(TypedDict):
    user_id: Snowflake
    channel_id: Snowflake
    message_id: Snowflake
    guild_id: NotRequired[Snowflake]
    answer_id: int


SubscriptionCreateEvent = SubscriptionUpdateEvent = SubscriptionDeleteEvent = Subscription


class CallCreateEvent(TypedDict):
    channel_id: Snowflake
    message_id: Snowflake
    embedded_activities: List[dict]
    region: str
    ringing: List[Snowflake]
    voice_states: List[VoiceState]
    unavailable: NotRequired[bool]


class CallUpdateEvent(TypedDict):
    channel_id: Snowflake
    guild_id: Optional[Snowflake]  # ???
    message_id: Snowflake
    region: str
    ringing: List[Snowflake]


class CallDeleteEvent(TypedDict):
    channel_id: Snowflake
    unavailable: NotRequired[bool]


LobbyCreateEvent = LobbyUpdateEvent = Lobby


class LobbyDeleteEvent(TypedDict):
    id: Snowflake
    reason: str


class _LobbyMembersEvent(TypedDict):
    member: LobbyMember
    lobby_id: Snowflake
    application_id: Snowflake


LobbyMemberAddEvent = LobbyMemberUpdateEvent = LobbyMemberRemoveEvent = _LobbyMembersEvent


class LobbyMemberConnectEvent(TypedDict):
    member: LobbyMember
    lobby_id: Snowflake


class LobbyMemberDisconnectEvent(TypedDict):
    member: LobbyMember
    lobby_id: Snowflake


LobbyMessageCreateEvent = LobbyMessage


class LobbyMessageDeleteEvent(TypedDict):
    id: Snowflake
    lobby_id: Snowflake


LobbyMessageUpdateEvent = LobbyMessageCreateEvent


class LobbyVoiceServerUpdateEvent(TypedDict):
    token: str
    lobby_id: Snowflake
    endpoint: Optional[str]


LobbyVoiceStateUpdateEvent = LobbyVoiceState


class UpdateLobbyVoiceState(TypedDict):
    lobby_id: Snowflake
    self_mute: bool
    self_deaf: bool


GameInviteCreateEvent = GameInvite


class GameInviteDeleteEvent(TypedDict):
    invite_id: Snowflake


class GameInviteDeleteManyEvent(TypedDict):
    invite_ids: List[Snowflake]


class RelationshipAddEvent(Relationship):
    should_notify: NotRequired[bool]


class RelationshipEvent(TypedDict):
    id: Snowflake
    type: RelationshipType
    nickname: Optional[str]


GameRelationshipAddEvent = GameRelationship


class GameRelationshipRemoveEvent(TypedDict):
    id: Snowflake
    application_id: Snowflake
    type: GameRelationshipType
    since: str
    dm_access_type: int
    user_id: Snowflake


SessionsReplaceEvent = Union[List[Session], Tuple[Session, ...]]

AudioSettingsUpdateEvent = Dict[AudioContext, Dict[Snowflake, AudioSettings]]


class UserMergeOperationCompletedEvent(TypedDict):
    merge_operation_id: Snowflake
    source_user_id: Snowflake


UserSettingsUpdateEvent = GatewayUserSettings

StreamCreateEvent = StreamUpdateEvent = Stream


class StreamDeleteEvent(TypedDict):
    stream_key: str
    reason: Literal[
        'user_requested',
        'stream_ended',
        'stream_full',
        'unauthorized',
        'safety_guild_rate_limited',
        'parse_failed',
        'invalid_channel',
    ]
    unavailable: NotRequired[bool]
