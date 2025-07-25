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
from typing_extensions import NotRequired, Required

from ...types.billing import PaymentSourceType
from ...types.connections import ConnectionType
from ...types.entitlements import Entitlement, GiftCode
from ...types.interactions import InteractionInstallationType
from ...types.invite import Invite, InviteWithCounts
from ...types.oauth2 import GetCurrentAuthorizationInformationResponseBody
from ...types.sku import SKU
from ...types.snowflake import Snowflake
from ...types.soundboard import SoundboardSound

from .channel import PartialGuildChannel, GuildChannel
from .guild import PartialGuild
from .presence import Activity
from .settings import PartialShortcutKeyCombo, VoiceSettingsModeType, VoiceSettings
from .template import Template
from .user import User, Relationship
from .voice_state import Pan


class SetConfigRequest(TypedDict):
    use_interactive_pip: bool


class SetConfigResponse(TypedDict):
    use_interactive_pip: bool


class AuthorizeRequest(TypedDict, total=False):
    client_id: Required[Snowflake]
    response_type: Literal['code', 'token']  # While the API accepts 'token' here, the client rejects it
    scopes: List[str]  # This takes priority over scope
    scope: List[str]  # Deprecated I think?

    code_challenge: str
    code_challenge_method: Literal['S256']
    state: str
    nonce: str
    permissions: str
    guild_id: Snowflake
    channel_id: Snowflake
    prompt: Literal['none', 'consent']  # Defaults to consent
    disable_guild_select: bool  # Defaults to false
    integration_type: InteractionInstallationType
    pid: int

    # {
    #   client_id: u,
    #   response_type: y="code",
    #   redirect_uri: v,
    #   code_challenge: C,
    #   code_challenge_method: S,
    #   state: N,
    #   nonce: T,
    #   scope: P,
    #   permissions: j,
    #   guild_id: A,
    #   channel_id: Z,
    #   prompt: x,
    #   disable_guild_select: L,
    #   integration_type: w,
    #   pid: R, (does nothing)
    #   signal: D (doesn't work)
    # }


class AuthorizeResponse(TypedDict):
    code: str


class AuthenticateRequest(TypedDict):
    access_token: str


class AuthenticateResponse(GetCurrentAuthorizationInformationResponseBody):
    access_token: str


class GetGuildRequest(TypedDict):
    guild_id: Snowflake
    timeout: int  # min 0, max 60


class GetGuildResponse(PartialGuild):
    members: List[Any]
    vanity_url_code: Optional[str]


class GetGuildsResponse(TypedDict):
    guilds: List[PartialGuild]


class GetChannelRequest(TypedDict):
    channel_id: Snowflake


GetChannelResponse = GuildChannel


class GetChannelsRequest(TypedDict):
    guild_id: Snowflake


class GetChannelsResponse(TypedDict):
    channels: List[PartialGuildChannel]


class GetChannelPermissionsRequest(TypedDict):
    pass


class GetChannelPermissionsResponse(TypedDict):
    permissions: str  # Stringified BigInt


class CreateChannelInviteRequest(TypedDict):
    channel_id: Snowflake


CreateChannelInviteResponse = Invite


class GetRelationshipsRequest(TypedDict):
    pass


class GetRelationshipsResponse(TypedDict):
    relationships: List[Relationship]


class GetUserRequest(TypedDict):
    id: Snowflake


GetUserResponse = Optional[User]

SubscribeRequest = Any


class SubscribeResponse(TypedDict):
    evt: str


UnsubscribeRequest = Any  # Remove subscription with these args and provided event name


class UnsubscribeResponse(TypedDict):
    evt: str


class SetUserVoiceSettingsRequest(TypedDict):
    user_id: Snowflake
    pan: NotRequired[Pan]
    volume: NotRequired[float]
    mute: NotRequired[bool]


class SetUserVoiceSettingsResponse(TypedDict):
    user_id: Snowflake
    pan: Pan
    volume: float
    mute: bool


class SetUserVoiceSettings2Request(TypedDict):  # No idea why this exists...
    user_id: Snowflake
    volume: NotRequired[float]
    mute: NotRequired[bool]


SetUserVoiceSettings2Response = None


class PushToTalkRequest(TypedDict):
    active: NotRequired[bool]


PushToTalkResponse = None


class SelectVoiceChannelRequest(TypedDict):
    channel_id: Optional[Snowflake]
    timeout: NotRequired[float]  # 0-60
    force: NotRequired[bool]
    navigate: NotRequired[bool]


SelectVoiceChannelResponse = Optional[GuildChannel]


class GetSelectedVoiceChannelRequest(TypedDict):
    pass


GetSelectedVoiceChannelResponse = Optional[GuildChannel]


class SelectTextChannelRequest(TypedDict):
    channel_id: Optional[Snowflake]
    timeout: NotRequired[float]  # 0-60


SelectTextChannelResponse = Optional[GuildChannel]


class GetVoiceSettingsRequest(TypedDict):
    pass


GetVoiceSettingsResponse = VoiceSettings


class SetVoiceSettings2RequestInputMode(TypedDict):
    type: VoiceSettingsModeType
    shortcut: str


class SetVoiceSettings2Request(TypedDict, total=False):
    input_mode: SetVoiceSettings2RequestInputMode
    self_mute: bool
    self_deaf: bool


SetVoiceSettings2Response = None


class SetVoiceSettingsRequestIO(TypedDict):
    device_id: str
    volume: NotRequired[float]  # 0-200


class SetVoiceSettingsRequestMode(TypedDict):
    type: VoiceSettingsModeType
    auto_threshold: NotRequired[bool]
    threshold: NotRequired[int]  # min -100, max 0
    shortcut: NotRequired[List[PartialShortcutKeyCombo]]
    delay: NotRequired[float]  # min -0, max 2000


class SetVoiceSettingsRequest(TypedDict, total=False):
    input: SetVoiceSettingsRequestIO
    output: SetVoiceSettingsRequestIO
    mode: SetVoiceSettingsRequestMode
    automatic_gain_control: bool
    echo_cancellation: bool
    noise_suppression: bool
    qos: bool
    silence_warning: bool
    deaf: bool
    mute: bool


SetVoiceSettingsResponse = VoiceSettings


class SetActivityRequest(TypedDict):
    pid: int
    activity: Optional[Activity]


SetActivityResponse = Optional[Activity]


class SendActivityJoinInviteRequest(TypedDict):
    user_id: Snowflake
    pid: int


SendActivityJoinInviteResponse = None


class CloseActivityJoinRequest(TypedDict):
    user_id: Snowflake


CloseActivityJoinResponse = None


class ActivityInviteUserRequest(TypedDict):
    user_id: Snowflake
    type: Literal[1]  # JOIN
    content: NotRequired[str]  # 0-1024 characters
    pid: int  # min 0


ActivityInviteUserResponse = None


class AcceptActivityInviteRequest(TypedDict):
    type: Literal[1]  # JOIN
    user_id: Snowflake
    session_id: str
    channel_id: Snowflake
    message_id: Snowflake
    application_id: NotRequired[Snowflake]


AcceptActivityInviteResponse = None


class OpenInviteDialogRequest(TypedDict):
    pass


OpenInviteDialogResponse = None


class OpenShareMomentDialogRequest(TypedDict):
    mediaUrl: str


class OpenShareMomentDialogResponse(TypedDict):
    pass


class ShareInteractionRequestOption(TypedDict):
    name: str
    value: str


class ShareInteractionRequestPreviewImage(TypedDict):
    height: int
    url: str
    width: int


class ShareInteractionRequestComponentButton(TypedDict):
    type: Literal[2]
    style: Literal[1, 2, 3, 4, 5]
    label: NotRequired[str]  # max 80
    custom_id: NotRequired[str]  # max 100


class ShareInteractionRequestComponent(TypedDict):
    type: Literal[1]
    components: List[ShareInteractionRequestComponentButton]  # max 5


class ShareInteractionRequest(TypedDict):
    command: str
    options: List[ShareInteractionRequestOption]
    content: str  # max 2000
    require_launch_channel: NotRequired[bool]
    preview_image: NotRequired[ShareInteractionRequestPreviewImage]
    components: NotRequired[ShareInteractionRequestComponent]
    pid: NotRequired[int]


class ShareInteractionResponse(TypedDict):
    success: bool


class InitiateImageUploadRequest(TypedDict):
    pass


class InitiateImageUploadResponse(TypedDict):
    image_url: str


class ShareLinkRequest(TypedDict):
    custom_id: str  # max 64 characters
    message: str  # max 1000 characters
    link_id: str  # max 64 characters


class ShareLinkResponse(TypedDict):
    success: bool
    didCopyLink: bool
    didSendMessage: bool


class InviteBrowserRequest(TypedDict):
    code: str


class InviteBrowserResponse(TypedDict):
    code: str
    invite: InviteWithCounts


class DeepLinkRequest(TypedDict):
    type: Literal[
        'USER_SETTINGS',
        'CHANGELOG',
        'LIBRARY',
        'STORE_HOME',
        'STORE_LISTING',
        'PICK_GUILD_SETTINGS',
        'CHANNEL',
        'QUEST_HOME',
        'DISCOVERY_GAME_RESULTS',
        'OAUTH2',
        'SHOP',
        'FEATURES',
        'ACTIVITIES',
    ]


DeepLinkResponse = Optional[bool]


class ConnectionsCallbackRequest(TypedDict):
    providerType: ConnectionType
    code: str
    openid_params: NotRequired[str]
    iss: NotRequired[str]
    state: str


ConnectionsCallbackResponse = None


class BillingPopupBridgeCallbackRequest(TypedDict):
    state: str
    path: str
    query: NotRequired[Dict[str, str]]
    payment_source_type: PaymentSourceType


BillingPopupBridgeCallbackResponse = Any  # Gives result of await RestAPI.post(...) as is lol


class BraintreePopupBridgeCallbackRequest(TypedDict):
    # Identical to BillingPopupBridgeCallbackRequest but the only difference is hard-coded PayPal paymentSourceType
    state: str
    path: str
    query: NotRequired[Dict[str, str]]


BraintreePopupBridgeCallbackResponse = Any  # Gives result of await RestAPI.post(...) as is lol


class GiftCodeBrowserRequest(TypedDict):
    code: str


class GiftCodeBrowserResponse(TypedDict):
    giftCode: GiftCode


class GuildTemplateBrowserRequest(TypedDict):
    code: str


class GuildTemplateBrowserResponse(TypedDict):
    guildTemplate: Template
    code: str


class OpenMessageRequest(TypedDict):
    guild_id: NotRequired[Optional[Snowflake]]
    channel_id: Snowflake
    message_id: Snowflake
    pid: int


OpenMessageResponse = None


class SetSuppressNotificationsRequest(TypedDict):
    suppress_notifications: bool
    target_user_id: Snowflake


class OverlayRequest(TypedDict):
    token: str


OverlayResponse = None


class BrowserHandoffRequest(TypedDict):
    handoffToken: str
    fingerprint: str


BrowserHandoffResponse = None


class CertifiedDeviceVendor(TypedDict):
    name: str  # min 1 character
    url: str  # min 1 character


class CertifiedDeviceModel(TypedDict):
    name: str  # min 1 character
    url: str  # min 1 character


class CertifiedDevice(TypedDict):
    type: Literal[
        'audioinput',
        'audiooutput',
        'videoinput',
    ]
    id: str  # min 1 character
    vendor: CertifiedDeviceVendor
    model: CertifiedDeviceModel
    related: NotRequired[List[str]]  # min 1 characters
    echo_cancellation: NotRequired[bool]
    noise_suppression: NotRequired[bool]
    automatic_gain_control: NotRequired[bool]
    hardware_mute: NotRequired[bool]


class SetCertifiedDevicesRequest(TypedDict):
    devices: List[CertifiedDevice]


SetCertifiedDevicesResponse = None


class GetImageRequest(TypedDict):
    type: Literal['image']
    id: str
    format: Literal['png', 'webp', 'jpg']
    size: Literal[16, 32, 64, 128, 256, 512, 1024]


class GetImageResponse(TypedDict):
    data_url: str


class SetOverlayLockedRequest(TypedDict):
    locked: bool
    pid: int  # min 0


SetOverlayLockedResponse = None


class OpenOverlayActivityInviteRequest(TypedDict):
    type: Literal[1]
    pid: int  # min 0


OpenOverlayActivityInviteResponse = None


class OpenOverlayGuildInviteRequest(TypedDict):
    code: str
    pid: int  # min 0


OpenOverlayGuildInviteResponse = None  # Times out...


class OpenOverlayVoiceSettingsRequest(TypedDict):
    pid: int  # min 0


OpenOverlayVoiceSettingsResponse = None


class ValidateApplicationRequest(TypedDict):
    pass


# TODO: Verify this
ValidateApplicationResponse = Optional[bool]  # I guess thats correct


class GetEntitlementTicketRequest(TypedDict):
    pass


class GetEntitlementTicketResponse(TypedDict):
    ticket: str


class GetApplicationTicketRequest(TypedDict):
    pass


class GetApplicationTicketResponse(TypedDict):
    ticket: str


class StartPurchaseRequest(TypedDict):
    sku_id: Snowflake
    pid: int  # min 0


StartPurchaseResponse = List[Entitlement]  # Hope that's correct


class StartPremiumPurchaseRequest(TypedDict):
    pid: int  # min 0


StartPremiumPurchaseResponse = None


class GetSKUsRequest(TypedDict):
    pass


GetSKUsResponse = List[SKU]


class GetEntitlementsRequest(TypedDict):
    pass


GetEntitlementsResponse = List[Entitlement]


class GetSKUsEmbeddedRequest(TypedDict):
    pass


class GetSKUsEmbeddedResponse(TypedDict):
    skus: List[SKU]


class GetEntitlementsEmbeddedResponse(TypedDict):
    entitlements: List[Entitlement]


class GetNetworkingConfigRequest(TypedDict):
    pass


class GetNetworkingConfigResponse(TypedDict):
    address: str
    token: str


NetworkingSystemMetricsRequest = Any
NetworkingSystemMetricsResponse = None

NetworkingPeerMetricsRequest = Any
NetworkingPeerMetricsResponse = Any


class NetworkingCreateTokenRequest(TypedDict):
    pass


class NetworkingCreateTokenResponse(TypedDict):
    token: str  # No clue whats this token is for


class UserSettingsGetLocaleRequest(TypedDict):
    pass


class UserSettingsGetLocaleResponse(TypedDict):
    locale: str


# SEND_GENERIC_EVENT is deprecated and always throws an error

# SEND_ANALYTICS_EVENT can be used only from post_message transport
class SendAnalyticsEventRequest(TypedDict):
    event_name: str
    event_properties: Dict[str, Any]


SendAnalyticsEventResponse = None


class OpenExternalLinkRequest(TypedDict):
    url: str


class OpenExternalLinkResponse(TypedDict):
    opened: bool


class CaptureLogRequest(TypedDict):
    level: Literal[
        'log',
        'warn',
        'debug',
        'info',
        'error',
    ]  # max 10 characters
    message: str  # max 1000 characters


CaptureLogResponse = None


class EncourageHwAccelerationRequest(TypedDict):
    pass


class EncourageHwAccelerationResponse(TypedDict):
    enabled: bool


class SetOrientationLockStateRequest(TypedDict):
    lock_state: Literal[1, 2, 3]
    picture_in_picture_lock_state: NotRequired[Optional[Literal[1, 2, 3]]]
    grid_lock_state: NotRequired[Optional[Literal[1, 2, 3]]]


SetOrientationLockStateResponse = None


class GetPlatformBehaviorsRequest(TypedDict):
    pass


class GetPlatformBehaviorsResponse(TypedDict):
    iosKeyboardResizesView: bool


GetSoundboardSounds = List[SoundboardSound]


class PlaySoundboardSoundRequest(TypedDict):
    guild_id: NotRequired[Snowflake]
    sound_id: NotRequired[Snowflake]


PlaySoundboardSoundResponse = None


class ToggleVideoRequest(TypedDict):
    pass


ToggleVideoResponse = None


class ToggleScreenshareRequest(TypedDict):
    pid: NotRequired[int]  # min 0


class GetActivityInstanceConnectedParticipantsRequest(TypedDict):
    pass


class GetActivityInstanceConnectedParticipantsResponse(TypedDict):
    participants: List[User]


class GetProviderAccessTokenRequest(TypedDict):
    provider: str
    connection_redirect: NotRequired[str]


class GetProviderAccessTokenResponse(TypedDict):
    access_token: str


class MaybeGetProviderAccessTokenRequest(TypedDict):
    provider: str


class MaybeGetProviderAccessTokenResponse(TypedDict):
    refresh_token: str


class NavigateToConnectionsRequest(TypedDict):
    pass


NavigateToConnectionsResponse = None


class InviteUserEmbeddedRequest(TypedDict):
    user_id: Snowflake
    content: NotRequired[str]  # min 0-1024 characters


InviteUserEmbeddedResponse = None
