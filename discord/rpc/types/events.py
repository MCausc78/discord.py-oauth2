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

from typing import Any, Dict, List, Literal, Optional, TypedDict
from typing_extensions import NotRequired

from ...types.entitlements import Entitlement
from ...types.message import MessageActivity, MessageActivityType
from ...types.snowflake import Snowflake
from .channel import PartialChannel
from .commands import ActivityParticipant
from .guild import PartialGuild
from .message import Message
from .settings import VoiceSettings, VoiceInputMode
from .user import AvatarDecorationData, User, Relationship
from .voice_state import VoiceState


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


CurrentUserUpdateEvent = User


class CurrentGuildMemberUpdateEventRequest(TypedDict):
    guild_id: Snowflake


class CurrentGuildMemberUpdateEvent(TypedDict):
    user_id: Snowflake
    nick: Optional[str]
    guild_id: Snowflake
    avatar: Optional[str]
    avatar_decoration_data: Optional[AvatarDecorationData]
    banner: NotRequired[Optional[str]]
    bio: NotRequired[Optional[str]]
    pronouns: NotRequired[Optional[str]]
    color_string: NotRequired[Optional[str]]


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


ChannelCreateEvent = PartialChannel


class RelationshipUpdateEventRequest(TypedDict):
    pass


RelationshipUpdateEvent = Relationship


class VoiceChannelSelectEventRequest(TypedDict):
    pass


class VoiceChannelSelectEvent(TypedDict):
    channel_id: Optional[Snowflake]
    guild_id: NotRequired[Optional[Snowflake]]


class VoiceStateCreateEventRequest(TypedDict):
    channel_id: Snowflake


VoiceStateCreateEvent = VoiceState


class VoiceStateUpdateEventRequest(TypedDict):
    channel_id: Snowflake


VoiceStateUpdateEvent = VoiceState


class VoiceStateDeleteEventRequest(TypedDict):
    channel_id: Snowflake


VoiceStateDeleteEvent = VoiceState


class VoiceSettingsUpdateEventRequest(TypedDict):
    pass


VoiceSettingsUpdateEvent = VoiceSettings


class VoiceSettingsUpdate2EventRequest(TypedDict):
    pass


class VoiceSettingsUpdate2Event(TypedDict):
    input_mode: VoiceInputMode
    local_mutes: List[Snowflake]
    local_volumes: Dict[Snowflake, float]
    self_mute: bool
    self_deaf: bool


# 2025-07-26 22:09:50 DEBUG    discord.rpc.transport For IPC event: 1 b'{
#   "cmd":"DISPATCH",
#   "data":{
#     "input_mode":{"type":"VOICE_ACTIVITY","shortcut":""},
#     "local_mutes":[],
#     "local_volumes":{},
#     "self_mute":false,
#     "self_deaf":false
#   },
#   "evt":"VOICE_SETTINGS_UPDATE_2",
#   "nonce":null
# }'


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


class SpeakingStopEvent(TypedDict):
    channel_id: Snowflake
    user_id: Snowflake


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
    participants: List[ActivityParticipant]


class NotificationCreateEventRequest(TypedDict):
    pass


class NotificationCreateEvent(TypedDict):
    channel_id: Snowflake
    message: Message
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
