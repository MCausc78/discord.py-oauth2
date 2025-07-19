from __future__ import annotations

from typing import Any, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from ...types.message import MessageActivityType
from ...types.presences import ReceivableActivity
from ...types.snowflake import Snowflake
from .user import User


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


# CURRENT_USER_UPDATE


class CurrentGuildMemberUpdateEventRequest(TypedDict):
    guild_id: Snowflake


# CURRENT_GUILD_MEMBER_UPDATE
# GUILD_STATUS
# GUILD_CREATE
# CHANNEL_CREATE
# RELATIONSHIP_UPDATE


class VoiceChannelSelectEventRequest(TypedDict):
    pass


class VoiceChannelSelectEvent(TypedDict):
    channel_id: Optional[Snowflake]
    guild_id: Optional[Snowflake]


# VOICE_STATE_CREATE
# VOICE_STATE_DELETE
# VOICE_STATE_UPDATE
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
    #   "hostname":"rotterdam11336.oauth2cord.media",
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
    activity: ReceivableActivity
    type: MessageActivityType
    channel_id: Snowflake
    message_id: Snowflake


# ACTIVITY_SPECTATE (deprecated and appears to never fire based on client code)


class ActivityInviteRequestEventRequest(TypedDict):
    pass


class ActivityInviteRequestEvent(TypedDict):
    user: User
    activity: ReceivableActivity
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


# THERMAL_STATE_UPDATE
# ORIENTATION_UPDATE
# ACTIVITY_INSTANCE_PARTICIPANTS_UPDATE
# NOTIFICATION_CREATE
# MESSAGE_CREATE
# MESSAGE_UPDATE
# MESSAGE_DELETE


class OverlayEventRequest(TypedDict):
    pass


class OverlayEvent(TypedDict):
    pass


# OVERLAY_UPDATE
# ENTITLEMENT_CREATE
# ENTITLEMENT_DELETE
# VOICE_CHANNEL_EFFECT_SEND
# VOICE_CHANNEL_EFFECT_RECENT_EMOJI
# VOICE_CHANNEL_EFFECT_TOGGLE_ANIMATION_TYPE
# SCREENSHARE_STATE_UPDATE
# VIDEO_STATE_UPDATE
