from __future__ import annotations

from copy import copy
import inspect
import logging
from typing import Any, Callable, Dict, Optional, TYPE_CHECKING

from ..entitlements import Entitlement
from ..relationship import Relationship
from ..state import BaseConnectionState
from ..user import ClientUser
from .channel import PartialGuildChannel
from .guild import PartialGuild
from .message import Message

if TYPE_CHECKING:
    from ..http import HTTPClient
    from .guild import Guild
    from .types.events import (
        ReadyEvent as ReadyEventPayload,
        CurrentUserUpdateEvent as CurrentUserUpdateEventPayload,
        MessageCreateEvent as MessageCreateEventPayload,
        MessageUpdateEvent as MessageUpdateEventPayload,
        MessageDeleteEvent as MessageDeleteEventPayload,
        GuildStatusEvent as GuildStatusEventPayload,
        GuildCreateEvent as GuildCreateEventPayload,
        ChannelCreateEvent as ChannelCreateEventPayload,
        RelationshipUpdateEvent as RelationshipUpdateEventPayload,
        EntitlementCreateEvent as EntitlementCreateEventPayload,
        EntitlementDeleteEvent as EntitlementDeleteEventPayload,
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

    def parse_guild_status(self, data: GuildStatusEventPayload) -> None:
        guild = PartialGuild(data=data['guild'], state=self)

        self.dispatch('guild_update', guild)

    def parse_guild_create(self, data: GuildCreateEventPayload) -> None:
        guild = PartialGuild(data=data, state=self)

        self.dispatch('guild_join', guild)

    def parse_channel_create(self, data: ChannelCreateEventPayload) -> None:
        channel = PartialGuildChannel(data=data, guild_id=0, state=self)

        self.dispatch('guild_channel_create', channel)

    def parse_relationship_update(self, data: RelationshipUpdateEventPayload) -> None:
        relationship = Relationship._from_rpc(data, self)

        self.dispatch('relationship_update', relationship)

    def parse_entitlement_create(self, data: EntitlementCreateEventPayload) -> None:
        entitlement = Entitlement(data=data, state=self)

        self.dispatch('entitlement_create', entitlement)

    def parse_entitlement_delete(self, data: EntitlementDeleteEventPayload) -> None:
        entitlement = Entitlement(data=data, state=self)

        self.dispatch('entitlement_delete', entitlement)

    # Overrides
    def get_rpc_guild(self, guild_id: Optional[int]) -> Optional[Guild]:
        return None
