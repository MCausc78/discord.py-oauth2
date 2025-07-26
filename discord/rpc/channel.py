from __future__ import annotations

from typing import List, Optional, TYPE_CHECKING, Union

from ..enums import try_enum, ChannelType
from ..mixins import Hashable
from .message import Message
from .voice_state import VoiceState

if TYPE_CHECKING:
    from .guild import Guild
    from .state import RPCConnectionState
    from .types.channel import (
        PartialChannel as PartialChannelPayload,
        GuildChannel as GuildChannelPayload,
    )

__all__ = (
    'PartialChannel',
    'GuildChannel',
)


class PartialChannel(Hashable):
    """Represents a partial Discord channel.

    .. versionadded:: 3.0

    Attributes
    ----------
    id: :class:`int`
        The channel's ID.
    guild_id: :class:`int`
        The guild's ID that this channel belongs to (or zero if the channel is a private channel).
    type: :class:`discord.ChannelType`
        The channel's type.
    name: :class:`str`
        The channel's name. Empty for DM channels.
    """

    __slots__ = (
        '_state',
        'id',
        'guild_id',
        'type',
        'name',
    )

    def __init__(
        self, *, data: Union[PartialChannelPayload, GuildChannelPayload], guild_id: int, state: RPCConnectionState
    ) -> None:
        self._state: RPCConnectionState = state
        self.id = int(data['id'])
        self.guild_id: int = guild_id
        self._update(data)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} id={self.id!r} type={self.type!r} name={self.name!r}>'

    def _update(self, data: Union[PartialChannelPayload, GuildChannelPayload]) -> None:
        self.type: ChannelType = try_enum(ChannelType, data['type'])
        self.name: str = data['name']

    @property
    def guild(self) -> Optional[Guild]:
        """Optional[:class:`Guild`]: The guild that this channel belongs to."""
        return self._state.get_rpc_guild(self.guild_id)


class GuildChannel(PartialChannel):
    """Represents a Discord guild channel.

    This inherits from :class:`PartialChannel`.

    .. versionadded:: 3.0

    Attributes
    ----------
    topic: :class:`str`
        The channel's topic.
    bitrate: :class:`int`
        The channel's preferred audio bitrate in bits per second.
        Only applicable if the channel is vocal (voice or stage) channel.
    user_limit: :class:`int`
        The channel's limit for number of members that can be in a vocal channel.
        Only applicable if the channel is vocal (voice or stage) channel.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0. e.g. the
        top channel is position 0.
    messages: List[:class:`Message`]
        A list of messages in channel. May be empty if the user have not visited the channel.
    voice_states: List[:class:`VoiceState`]
        A list of voice states that belong to this channel.
        Only applicable if the channel is vocal (voice or stage) channel.
    """

    __slots__ = (
        'topic',
        'bitrate',
        'user_limit',
        'position',
        'messages',
        'voice_states',
    )

    def __init__(
        self, *, data: Union[PartialChannelPayload, GuildChannelPayload], guild_id: int = 0, state: RPCConnectionState
    ) -> None:
        super().__init__(data=data, guild_id=int(data.get('guild_id', guild_id)), state=state)

    def _update(self, data: GuildChannelPayload) -> None:
        super()._update(data)
        state = self._state

        self.topic: str = data.get('topic', '')
        self.bitrate: int = data.get('bitrate', 0)
        self.user_limit: int = data.get('user_limit', 0)
        self.position: int = data.get('position', 0)
        self.messages: List[Message] = [Message(data=d, channel=self, state=state) for d in data.get('messages', ())]
        self.voice_states: List[VoiceState] = [VoiceState(data=d, state=state) for d in data.get('voice_states', ())]
