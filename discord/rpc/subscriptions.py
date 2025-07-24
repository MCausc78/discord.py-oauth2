from __future__ import annotations

from typing import Any, Dict, Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Self


class EventSubscription:
    """Represents an event subscription.

    .. versionadded:: 3.0
    """

    __slots__ = ()

    def get_type(self) -> str:
        return ''

    def get_data(self) -> Dict[str, Any]:
        return {}


class GenericSubscription(EventSubscription):
    """Represents a subscription for a generic event (event that does not require arguments)."""

    __slots__ = ('type',)

    def __init__(self, type: str) -> None:
        self.type: str = type

    def get_type(self) -> str:
        return self.type

    @classmethod
    def current_user_update(cls) -> Self:
        return cls('CURRENT_USER_UPDATE')

    @classmethod
    def guild_join(cls) -> Self:
        return cls('GUILD_CREATE')

    @classmethod
    def channel_create(cls) -> Self:
        return cls('CHANNEL_CREATE')

    @classmethod
    def relationship_update(cls) -> Self:
        return cls('RELATIONSHIP_UPDATE')

    @classmethod
    def voice_channel_select(cls) -> Self:
        return cls('VOICE_CHANNEL_SELECT')

    @classmethod
    def voice_settings_update(cls) -> Self:
        return cls('VOICE_SETTINGS_UPDATE')

    @classmethod
    def voice_settings_update_2(cls) -> Self:
        return cls('VOICE_SETTINGS_UPDATE_2')

    @classmethod
    def voice_connection_status(cls) -> Self:
        return cls('VOICE_CONNECTION_STATUS')

    @classmethod
    def game_join(cls) -> Self:
        return cls('GAME_JOIN')

    @classmethod
    def activity_join(cls) -> Self:
        return cls('ACTIVITY_JOIN')

    @classmethod
    def activity_join_request(cls) -> Self:
        return cls('ACTIVITY_JOIN_REQUEST')

    @classmethod
    def activity_invite(cls) -> Self:
        return cls('ACTIVITY_INVITE')

    @classmethod
    def activity_pip_mode_update(cls) -> Self:
        return cls('ACTIVITY_PIP_MODE_UPDATE')

    @classmethod
    def activity_layout_mode_update(cls) -> Self:
        return cls('ACTIVITY_LAYOUT_MODE_UPDATE')

    @classmethod
    def thermal_state_update(cls) -> Self:
        return cls('THERMAL_STATE_UPDATE')

    @classmethod
    def orientation_update(cls) -> Self:
        return cls('ORIENTATION_UPDATE')

    @classmethod
    def activity_instance_participants_update(cls) -> Self:
        return cls('ACTIVITY_INSTANCE_PARTICIPANTS_UPDATE')

    @classmethod
    def notification_create(cls) -> Self:
        return cls('NOTIFICATION_CREATE')

    @classmethod
    def entitlement_create(cls) -> Self:
        return cls('ENTITLEMENT_CREATE')

    @classmethod
    def entitlement_delete(cls) -> Self:
        return cls('ENTITLEMENT_DELETE')

    @classmethod
    def screenshare_state_update(cls) -> Self:
        return cls('SCREENSHARE_STATE_UPDATE')

    @classmethod
    def video_state_update(cls) -> Self:
        return cls('VIDEO_STATE_UPDATE')


class ChannelSubscription(EventSubscription):
    """Represents a subscription for a channel event (event that happens in a specific channel)."""

    __slots__ = ('type', 'channel_id')

    def __init__(self, type: str, *, channel_id: int) -> None:
        self.type: str = type
        self.channel_id: int = channel_id

    def get_type(self) -> str:
        return self.type

    def get_data(self) -> Dict[str, Any]:
        return {'channel_id': str(self.channel_id)}

    @classmethod
    def voice_state_create(cls, channel_id: int) -> Self:
        return cls('VOICE_STATE_CREATE', channel_id=channel_id)

    @classmethod
    def voice_state_update(cls, channel_id: int) -> Self:
        return cls('VOICE_STATE_UPDATE', channel_id=channel_id)

    @classmethod
    def voice_state_delete(cls, channel_id: int) -> Self:
        return cls('VOICE_STATE_DELETE', channel_id=channel_id)

    @classmethod
    def message_create(cls, channel_id: int) -> Self:
        return cls('MESSAGE_CREATE', channel_id=channel_id)

    @classmethod
    def message_update(cls, channel_id: int) -> Self:
        return cls('MESSAGE_UPDATE', channel_id=channel_id)

    @classmethod
    def message_delete(cls, channel_id: int) -> Self:
        return cls('MESSAGE_DELETE', channel_id=channel_id)


class GuildSubscription(EventSubscription):
    """Represents a subscription for a guild event (event that happens in a specific guild)."""

    __slots__ = ('type', 'guild_id')

    def __init__(self, type: str, *, guild_id: int) -> None:
        self.type: str = type
        self.guild_id: int = guild_id

    def get_type(self) -> str:
        return self.type

    def get_data(self) -> Dict[str, Any]:
        return {'guild_id': str(self.guild_id)}

    @classmethod
    def current_member_update(cls, guild_id: int) -> Self:
        return cls('CURRENT_GUILD_MEMBER_UPDATE', guild_id=guild_id)

    @classmethod
    def guild_status(cls, guild_id: int) -> Self:
        return cls('GUILD_STATUS', guild_id=guild_id)


class SpeakingEventSubscription(EventSubscription):
    __slots__ = (
        'operation',
        'channel_id',
        'user_id',
    )

    def __init__(self, operation: Literal['START', 'STOP'], *, channel_id: int, user_id: int) -> None:
        self.operation = operation
        self.channel_id: int = channel_id
        self.user_id: int = user_id

    def get_type(self) -> str:
        return 'SPEAKING_' + self.operation

    def get_data(self) -> Dict[str, Any]:
        return {
            'channel_id': str(self.channel_id),
            'user_id': str(self.user_id),
        }

    @classmethod
    def start(cls, channel_id: int, user_id: int) -> Self:
        return cls('START', channel_id=channel_id, user_id=user_id)

    @classmethod
    def stop(cls, channel_id: int, user_id: int) -> Self:
        return cls('STOP', channel_id=channel_id, user_id=user_id)
