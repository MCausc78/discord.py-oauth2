from __future__ import annotations

from typing import Any, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from ...types.entitlements import Entitlement
from ...types.message import MessageActivity, MessageActivityType
from ...types.snowflake import Snowflake
from .channel import PartialGuildChannel
from .guild import PartialGuild
from .message import Message
from .user import User, Relationship


class IncomingPacket(TypedDict):
    cmd: str
    data: Any
    nonce: Optional[str]
    evt: Optional[str]


class OutgoingPacket(TypedDict):
    cmd: str
    args: Any
    nonce: str
    evt: NotRequired[str]


class ReadyEventConfig(TypedDict):
    cdn_host: str  # like 'cdn.discordapp.com'
    api_endpoint: str  # like '//canary.discord.com/api'
    environment: str  # like 'production'


class ReadyEvent(TypedDict):
    v: int
    config: ReadyEventConfig
    user: NotRequired[User]


class CurrentUserUpdateEventRequest(TypedDict):
    pass


# TODO: CURRENT_USER_UPDATE response


class CurrentGuildMemberUpdateEventRequest(TypedDict):
    guild_id: Snowflake


# TODO: CURRENT_GUILD_MEMBER_UPDATE response


class GuildStatusEventRequest(TypedDict):
    guild_id: Snowflake


class GuildStatusEvent(TypedDict):
    guild: PartialGuild
    online: Literal[0]  # Deprecated


class GuildCreateEventRequest(TypedDict):
    pass


GuildCreateEvent = PartialGuild


class ChannelCreateEventRequest(TypedDict):
    pass


ChannelCreateEvent = PartialGuildChannel


class RelationshipUpdateEventRequest(TypedDict):
    pass


RelationshipUpdateEvent = Relationship


class VoiceChannelSelectEventRequest(TypedDict):
    pass


class VoiceChannelSelectEvent(TypedDict):
    channel_id: Optional[Snowflake]
    guild_id: Optional[Snowflake]


class VoiceStateCreateEventRequest(TypedDict):
    channel_id: Snowflake


class VoiceStateUpdateEventRequest(TypedDict):
    channel_id: Snowflake


class VoiceStateDeleteEventRequest(TypedDict):
    channel_id: Snowflake


# VOICE_STATE_CREATE
# VOICE_STATE_DELETE
# VOICE_STATE_UPDATE


class VoiceSettingsUpdateEventRequest(TypedDict):
    pass


class VoiceSettingsUpdate2EventRequest(TypedDict):
    pass


# VOICE_SETTINGS_UPDATE
# VOICE_SETTINGS_UPDATE_2


class VoiceConnectionStatusEventRequest(TypedDict):
    pass


class VoiceConnectionStatusEventPing(TypedDict):
    time: int  # in ms
    value: int  # latency in ms


class VoiceConnectionStatusEvent(TypedDict):
    # {
    #   "state":"VOICE_CONNECTED",
    #   "hostname":"rotterdam11336.discord.media",
    #   "pings":[{"time":1750679009463,"value":44},
    #            {"time":1750679014461,"value":43},
    #            {"time":1750679019462,"value":43},
    #            {"time":1750679024463,"value":43}
    #   ],
    #   "average_ping":43.25,
    #   "last_ping":43}'
    state: Literal[
        'DISCONNECTED',
        'AWAITING_ENDPOINT',
        'AUTHENTICATING',
        'CONNECTING',
        'RTC_DISCONNECTED',
        'RTC_CONNECTING',
        'RTC_CONNECTED',
        'NO_ROUTE',
        'ICE_CHECKING',
        'DTLS_CONNECTING',
    ]
    hostname: str  # ''
    pings: List[VoiceConnectionStatusEventPing]  # []
    average_ping: int  # 0 if disconnected, in ms
    last_ping: NotRequired[int]  # undefined if disconnected, in ms


class SpeakingStartEventRequest(TypedDict):
    channel_id: Optional[Snowflake]


class SpeakingStartEvent(TypedDict):
    channel_id: Snowflake
    user_id: Snowflake


class SpeakingStopEventRequest(TypedDict):
    channel_id: Optional[Snowflake]


class GameJoinEventRequest(TypedDict):
    pass


class GameJoinEvent(TypedDict):
    secret: str


# GAME_SPECTATE (deprecated and appears to never fire based on client code)


class ActivityJoinEventRequest(TypedDict):
    pass


class ActivityJoinEvent(TypedDict):
    secret: str


class ActivityJoinRequestEventRequest(TypedDict):
    pass


class ActivityJoinRequestEvent(TypedDict):
    user: User
    activity: MessageActivity
    type: MessageActivityType
    channel_id: Snowflake
    message_id: Snowflake


# ACTIVITY_SPECTATE (deprecated and appears to never fire based on client code)


class ActivityInviteEventRequest(TypedDict):
    pass


class ActivityInviteEvent(TypedDict):
    user: User
    activity: MessageActivity
    type: MessageActivityType
    channel_id: Snowflake
    message_id: Snowflake


class ActivityPipModeUpdateEventRequest(TypedDict):
    pass


class ActivityPipModeUpdateEvent(TypedDict):
    is_pip_mode: bool  # layout_mode != FOCUSED


class ActivityLayoutModeUpdateEventRequest(TypedDict):
    pass


class ActivityLayoutModeUpdateEvent(TypedDict):
    layout_mode: Literal[0, 1, 2]  # {FOCUSED: 0, PIP: 1, GRID: 2}


class ThermalStateUpdateEventRequest(TypedDict):
    pass


class ThermalStateUpdateEvent(TypedDict):
    thermal_state: Literal[
        -1,  # UNHANDLED
        0,  # NOMINAL
        1,  # FAIR
        2,  # SERIOUS
        3,  # CRITICAL
    ]


class OrientationUpdateEventRequest(TypedDict):
    pass


class OrientationUpdateEvent(TypedDict):
    # Unsure how the enum is called in client, but it is Orientation in embedded app sdk
    screen_orientation: Literal[
        1,  # UNLOCKED
        2,  # PORTRAIT
        3,  # LANDSCAPE
    ]


class ActivityInstanceParticipantsUpdateEventRequest(TypedDict):
    pass


class ActivityInstanceParticipantsUpdateEvent(TypedDict):
    participants: List[User]


class NotificationCreateEventRequest(TypedDict):
    pass


class NotificationCreateEvent(TypedDict):
    channel_id: Snowflake
    message: Snowflake
    icon_url: Optional[str]
    title: str
    body: str


class MessageCreateEventRequest(TypedDict):
    channel_id: Snowflake


class MessageCreateEvent(TypedDict):
    channel_id: Snowflake
    message: Message


class MessageUpdateEventRequest(TypedDict):
    channel_id: Snowflake


class MessageUpdateEvent(TypedDict):
    channel_id: Snowflake
    message: Message


class MessageDeleteEventRequest(TypedDict):
    channel_id: Snowflake


class PartialMessage(TypedDict):
    id: Snowflake


class MessageDeleteEvent(TypedDict):
    channel_id: Snowflake
    message: PartialMessage


# TODO: Overlay commands/events
class OverlayEventRequest(TypedDict):
    pass


class OverlayEvent(TypedDict):
    pass


class EntitlementCreateEventRequest(TypedDict):
    pass


EntitlementCreateEvent = Entitlement


class EntitlementDeleteEventRequest(TypedDict):
    pass


EntitlementDeleteEvent = Entitlement

# VOICE_CHANNEL_EFFECT_SEND
# VOICE_CHANNEL_EFFECT_RECENT_EMOJI
# VOICE_CHANNEL_EFFECT_TOGGLE_ANIMATION_TYPE


class ScreenshareStateUpdateEventRequest(TypedDict):
    pass


class ScreenshareStateUpdateEventApplication(TypedDict):
    name: str


class ScreenshareStateUpdateEvent(TypedDict):
    active: bool
    pid: Optional[int]
    application: Optional[ScreenshareStateUpdateEventApplication]


class VideoStateUpdateEventRequest(TypedDict):
    pass


class VideoStateUpdateEvent(TypedDict):
    active: bool
