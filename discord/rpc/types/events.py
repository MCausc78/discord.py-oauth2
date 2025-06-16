from __future__ import annotations

from typing import Any, Optional, TypedDict
from typing_extensions import NotRequired


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
# VOICE_CHANNEL_SELECT
# VOICE_STATE_CREATE
# VOICE_STATE_DELETE
# VOICE_STATE_UPDATE
# VOICE_SETTINGS_UPDATE
# VOICE_SETTINGS_UPDATE_2
# VOICE_CONNECTION_STATUS
# SPEAKING_START
# SPEAKING_STOP
# GAME_JOIN
# GAME_SPECTATE
# ACTIVITY_JOIN
# ACTIVITY_JOIN_REQUEST
# ACTIVITY_SPECTATE
# ACTIVITY_INVITE
# ACTIVITY_PIP_MODE_UPDATE
# ACTIVITY_LAYOUT_MODE_UPDATE
# THERMAL_STATE_UPDATE
# ORIENTATION_UPDATE
# ACTIVITY_INSTANCE_PARTICIPANTS_UPDATE
# NOTIFICATION_CREATE
# MESSAGE_CREATE
# MESSAGE_UPDATE
# MESSAGE_DELETE
# OVERLAY
# OVERLAY_UPDATE
# ENTITLEMENT_CREATE
# ENTITLEMENT_DELETE
# VOICE_CHANNEL_EFFECT_SEND
# VOICE_CHANNEL_EFFECT_RECENT_EMOJI
# VOICE_CHANNEL_EFFECT_TOGGLE_ANIMATION_TYPE
# SCREENSHARE_STATE_UPDATE
# VIDEO_STATE_UPDATE
