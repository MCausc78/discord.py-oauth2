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

import asyncio
from copy import copy
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Literal,
    Optional,
    Protocol,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

from .enums import ChannelType
from .errors import ClientException
from .file import File
from .http import handle_message_parameters
from .mentions import AllowedMentions
from .object import Object
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .utils import (
    MISSING,
    _get_as_snowflake,
    get,
    snowflake_time,
)
from .voice_client import VoiceClient, VoiceProtocol

__all__ = (
    'Snowflake',
    'User',
    'PrivateChannel',
    'GuildChannel',
    'Messageable',
    'Connectable',
)

T = TypeVar('T', bound=VoiceProtocol)

if TYPE_CHECKING:
    from .asset import Asset
    from .channel import (
        TextChannel,
        DMChannel,
        GroupChannel,
        EphemeralDMChannel,
        PartialMessageable,
        VoiceChannel,
        StageChannel,
        CategoryChannel,
    )
    from .client import Client
    from .guild import Guild
    from .member import Member
    from .message import Message
    from .state import ConnectionState
    from .types.channel import (
        PermissionOverwrite as PermissionOverwritePayload,
        GuildChannel as GuildChannelPayload,
        OverwriteType,
    )
    from .user import ClientUser

    PartialMessageableChannel = Union[TextChannel, DMChannel, EphemeralDMChannel, PartialMessageable]
    MessageableChannel = PartialMessageableChannel
    MessageableDestinationType = Literal['channel', 'lobby', 'user']
    SnowflakeTime = Union["Snowflake", datetime]
    VocalChannel = Union[DMChannel, GroupChannel, VoiceChannel, StageChannel]


@runtime_checkable
class Snowflake(Protocol):
    """An ABC that details the common operations on a Discord model.

    Almost all :ref:`Discord models <discord_api_models>` meet this
    abstract base class.

    If you want to create a snowflake on your own, consider using
    :class:`.Object`.

    Attributes
    ----------
    id: :class:`int`
        The model's unique ID.
    """

    __slots__ = ()

    id: int


@runtime_checkable
class User(Snowflake, Protocol):
    """An ABC that details the common operations on a Discord user.

    The following implement this ABC:

    - :class:`~oauth2cord.User`
    - :class:`~oauth2cord.ClientUser`
    - :class:`~oauth2cord.Member`

    This ABC must also implement :class:`~oauth2cord.abc.Snowflake`.

    Attributes
    ----------
    name: :class:`str`
        The user's username.
    discriminator: :class:`str`
        The user's discriminator. This is a legacy concept that is no longer used.
    global_name: Optional[:class:`str`]
        The user's global nickname.
    bot: :class:`bool`
        If the user is a bot account.
    system: :class:`bool`
        If the user is a system account.
    """

    name: str
    discriminator: str
    global_name: Optional[str]
    bot: bool
    system: bool

    @property
    def display_name(self) -> str:
        """:class:`str`: Returns the user's display name."""
        raise NotImplementedError

    @property
    def mention(self) -> str:
        """:class:`str`: Returns a string that allows you to mention the given user."""
        raise NotImplementedError

    @property
    def avatar(self) -> Optional[Asset]:
        """Optional[:class:`~oauth2cord.Asset`]: Returns an Asset that represents the user's avatar, if present."""
        raise NotImplementedError

    @property
    def avatar_decoration(self) -> Optional[Asset]:
        """Optional[:class:`~oauth2cord.Asset`]: Returns an Asset that represents the user's avatar decoration, if present.

        .. versionadded:: 2.4
        """
        raise NotImplementedError

    @property
    def avatar_decoration_sku_id(self) -> Optional[int]:
        """Optional[:class:`int`]: Returns an integer that represents the user's avatar decoration SKU ID, if present.

        .. versionadded:: 2.4
        """
        raise NotImplementedError

    @property
    def default_avatar(self) -> Asset:
        """:class:`~oauth2cord.Asset`: Returns the default avatar for a given user."""
        raise NotImplementedError

    @property
    def display_avatar(self) -> Asset:
        """:class:`~oauth2cord.Asset`: Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        raise NotImplementedError

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the user is mentioned in the specified message.

        Parameters
        ----------
        message: :class:`~oauth2cord.Message`
            The message to check if you're mentioned in.

        Returns
        -------
        :class:`bool`
            Indicates if the user is mentioned in the message.
        """
        raise NotImplementedError


class PrivateChannel:
    """An ABC that details the common operations on a private Discord channel.

    The following implement this ABC:

    - :class:`~oauth2cord.DMChannel`
    - :class:`~oauth2cord.GroupChannel`
    - :class:`~oauth2cord.EphemeralDMChannel`

    This ABC must also implement :class:`~oauth2cord.abc.Snowflake`.

    Attributes
    ----------
    me: :class:`~oauth2cord.ClientUser`
        The user presenting yourself.
    """

    __slots__ = ()

    id: int
    me: ClientUser

    def _add_call(self, **kwargs):
        raise NotImplementedError


class _Overwrites:
    __slots__ = ('id', 'allow', 'deny', 'type')

    ROLE = 0
    MEMBER = 1

    def __init__(self, data: PermissionOverwritePayload) -> None:
        self.id: int = int(data['id'])
        self.allow: int = int(data.get('allow', 0))
        self.deny: int = int(data.get('deny', 0))
        self.type: OverwriteType = data['type']

    def _asdict(self) -> PermissionOverwritePayload:
        return {
            'id': self.id,
            'allow': str(self.allow),
            'deny': str(self.deny),
            'type': self.type,
        }

    def is_role(self) -> bool:
        return self.type == 0

    def is_member(self) -> bool:
        return self.type == 1


class GuildChannel:
    """An ABC that details the common operations on a Discord guild channel.

    The following implement this ABC:

    - :class:`~oauth2cord.TextChannel`
    - :class:`~oauth2cord.VoiceChannel`
    - :class:`~oauth2cord.CategoryChannel`
    - :class:`~oauth2cord.StageChannel`
    - :class:`~oauth2cord.ForumChannel`

    This ABC must also implement :class:`~oauth2cord.abc.Snowflake`.

    Attributes
    ----------
    name: :class:`str`
        The channel name.
    guild: :class:`~oauth2cord.Guild`
        The guild the channel belongs to.
    position: :class:`int`
        The position in the channel list. This is a number that starts at 0.
        e.g. the top channel is position 0.
    """

    __slots__ = ()

    id: int
    name: str
    guild: Guild
    type: ChannelType
    position: int
    category_id: Optional[int]
    _state: ConnectionState
    _overwrites: List[_Overwrites]

    if TYPE_CHECKING:

        def __init__(self, *, state: ConnectionState, guild: Guild, data: GuildChannelPayload):
            ...

    def __str__(self) -> str:
        return self.name

    @property
    def _sorting_bucket(self) -> int:
        raise NotImplementedError

    def _update(self, guild: Guild, data: Dict[str, Any]) -> None:
        raise NotImplementedError

    def _fill_overwrites(self, data: GuildChannelPayload) -> None:
        self._overwrites = []
        everyone_index = 0
        everyone_id = self.guild.id

        for index, overridden in enumerate(data.get('permission_overwrites', ())):
            overwrite = _Overwrites(overridden)
            self._overwrites.append(overwrite)

            if overwrite.type == _Overwrites.MEMBER:
                continue

            if overwrite.id == everyone_id:
                # the @everyone role is not guaranteed to be the first one
                # in the list of permission overwrites, however the permission
                # resolution code kind of requires that it is the first one in
                # the list since it is special. So we need the index so we can
                # swap it to be the first one.
                everyone_index = index

        # do the swap
        tmp = self._overwrites
        if tmp:
            tmp[everyone_index], tmp[0] = tmp[0], tmp[everyone_index]

    @property
    def changed_roles(self) -> List[Role]:
        """List[:class:`~oauth2cord.Role`]: Returns a list of roles that have been overridden from
        their default values in the :attr:`~oauth2cord.Guild.roles` attribute."""
        ret = []
        g = self.guild
        for overwrite in filter(lambda o: o.is_role(), self._overwrites):
            role = g.get_role(overwrite.id)
            if role is None:
                continue

            role = copy(role)
            role.permissions.handle_overwrite(overwrite.allow, overwrite.deny)
            ret.append(role)
        return ret

    @property
    def mention(self) -> str:
        """:class:`str`: The string that allows you to mention the channel."""
        return f'<#{self.id}>'

    @property
    def jump_url(self) -> str:
        """:class:`str`: Returns a URL that allows the client to jump to the channel.

        .. versionadded:: 2.0
        """
        return f'https://discord.com/channels/{self.guild.id}/{self.id}'

    @property
    def created_at(self) -> datetime:
        """:class:`datetime.datetime`: Returns the channel's creation time in UTC."""
        return snowflake_time(self.id)

    def overwrites_for(self, obj: Union[Role, User, Object]) -> PermissionOverwrite:
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        ----------
        obj: Union[:class:`~oauth2cord.Role`, :class:`~oauth2cord.abc.User`, :class:`~oauth2cord.Object`]
            The role or user denoting whose overwrite to get.

        Returns
        -------
        :class:`~oauth2cord.PermissionOverwrite`
            The permission overwrites for this object.
        """

        if isinstance(obj, User):
            predicate = lambda p: p.is_member()
        elif isinstance(obj, Role):
            predicate = lambda p: p.is_role()
        else:
            predicate = lambda p: True

        for overwrite in filter(predicate, self._overwrites):
            if overwrite.id == obj.id:
                allow = Permissions(overwrite.allow)
                deny = Permissions(overwrite.deny)
                return PermissionOverwrite.from_pair(allow, deny)

        return PermissionOverwrite()

    @property
    def overwrites(self) -> Dict[Union[Role, Member, Object], PermissionOverwrite]:
        """Returns all of the channel's overwrites.

        This is returned as a dictionary where the key contains the target which
        can be either a :class:`~oauth2cord.Role` or a :class:`~oauth2cord.Member` and the value is the
        overwrite as a :class:`~oauth2cord.PermissionOverwrite`.

        .. versionchanged:: 2.0
            Overwrites can now be type-aware :class:`~oauth2cord.Object` in case of cache lookup failure.

        Returns
        -------
        Dict[Union[:class:`~oauth2cord.Role`, :class:`~oauth2cord.Member`, :class:`~oauth2cord.Object`], :class:`~oauth2cord.PermissionOverwrite`]
            The channel's permission overwrites.
        """
        ret = {}
        for ow in self._overwrites:
            allow = Permissions(ow.allow)
            deny = Permissions(ow.deny)
            overwrite = PermissionOverwrite.from_pair(allow, deny)
            target = None

            if ow.is_role():
                target = self.guild.get_role(ow.id)
            elif ow.is_member():
                target = self.guild.get_member(ow.id)

            if target is None:
                target_type = Role if ow.is_role() else User
                target = Object(id=ow.id, type=target_type)  # type: ignore

            ret[target] = overwrite
        return ret

    @property
    def category(self) -> Optional[CategoryChannel]:
        """Optional[:class:`~oauth2cord.CategoryChannel`]: The category this channel belongs to.

        If there is no category then this is ``None``.
        """
        return self.guild.get_channel(self.category_id)  # type: ignore # These are coerced into CategoryChannel

    @property
    def permissions_synced(self) -> bool:
        """:class:`bool`: Whether or not the permissions for this channel are synced with the
        category it belongs to.

        If there is no category then this is ``False``.

        .. versionadded:: 1.3
        """
        if self.category_id is None:
            return False

        category = self.guild.get_channel(self.category_id)
        return bool(category and category.overwrites == self.overwrites)

    def _apply_implicit_permissions(self, base: Permissions) -> None:
        # if you can't send a message in a channel then you can't have certain
        # permissions as well
        if not base.send_messages:
            base.send_tts_messages = False
            base.mention_everyone = False
            base.embed_links = False
            base.attach_files = False

        # if you can't read a channel then you have no permissions there
        if not base.read_messages:
            denied = Permissions.all_channel()
            base.value &= ~denied.value

    def permissions_for(self, obj: Union[Member, Role], /) -> Permissions:
        """Handles permission resolution for the :class:`~oauth2cord.Member`
        or :class:`~oauth2cord.Role`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides
        - Implicit permissions
        - Member timeout
        - User installed app

        If a :class:`~oauth2cord.Role` is passed, then it checks the permissions
        someone with that role would have, which is essentially:

        - The default role permissions
        - The permissions of the role used as a parameter
        - The default role permission overwrites
        - The permission overwrites of the role used as a parameter

        .. versionchanged:: 2.0
            The object passed in can now be a role object.

        .. versionchanged:: 2.0
            ``obj`` parameter is now positional-only.

        .. versionchanged:: 2.4
            User installed apps are now taken into account.
            The permissions returned for a user installed app mirrors the
            permissions Discord returns in :attr:`~oauth2cord.Interaction.app_permissions`,
            though it is recommended to use that attribute instead.

        Parameters
        ----------
        obj: Union[:class:`~oauth2cord.Member`, :class:`~oauth2cord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Returns
        -------
        :class:`~oauth2cord.Permissions`
            The resolved permissions for the member or role.
        """

        # The current cases can be explained as:
        # Guild owner get all permissions -- no questions asked. Otherwise...
        # The @everyone role gets the first application.
        # After that, the applied roles that the user has in the channel
        # (or otherwise) are then OR'd together.
        # After the role permissions are resolved, the member permissions
        # have to take into effect.
        # After all that is done.. you have to do the following:

        # If manage permissions is True, then all permissions are set to True.

        # The operation first takes into consideration the denied
        # and then the allowed.

        if self.guild.owner_id == obj.id:
            return Permissions.all()

        default = self.guild.default_role
        if default is None:

            if self._state.self_id == obj.id:
                return Permissions._user_installed_permissions(in_guild=True)
            else:
                return Permissions.none()

        base = Permissions(default.permissions.value)

        # Handle the role case first
        if isinstance(obj, Role):
            base.value |= obj._permissions

            if base.administrator:
                return Permissions.all()

            # Apply @everyone allow/deny first since it's special
            try:
                maybe_everyone = self._overwrites[0]
                if maybe_everyone.id == self.guild.id:
                    base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
            except IndexError:
                pass

            if obj.is_default():
                return base

            overwrite = get(self._overwrites, type=_Overwrites.ROLE, id=obj.id)
            if overwrite is not None:
                base.handle_overwrite(overwrite.allow, overwrite.deny)

            return base

        roles = obj._roles
        get_role = self.guild.get_role

        # Apply guild roles that the member has.
        for role_id in roles:
            role = get_role(role_id)
            if role is not None:
                base.value |= role._permissions

        # Guild-wide Administrator -> True for everything
        # Bypass all channel-specific overrides
        if base.administrator:
            return Permissions.all()

        # Apply @everyone allow/deny first since it's special
        try:
            maybe_everyone = self._overwrites[0]
            if maybe_everyone.id == self.guild.id:
                base.handle_overwrite(allow=maybe_everyone.allow, deny=maybe_everyone.deny)
                remaining_overwrites = self._overwrites[1:]
            else:
                remaining_overwrites = self._overwrites
        except IndexError:
            remaining_overwrites = self._overwrites

        denies = 0
        allows = 0

        # Apply channel specific role permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_role() and roles.has(overwrite.id):
                denies |= overwrite.deny
                allows |= overwrite.allow

        base.handle_overwrite(allow=allows, deny=denies)

        # Apply member specific permission overwrites
        for overwrite in remaining_overwrites:
            if overwrite.is_member() and overwrite.id == obj.id:
                base.handle_overwrite(allow=overwrite.allow, deny=overwrite.deny)
                break

        if obj.is_timed_out():
            # Timeout leads to every permission except VIEW_CHANNEL and READ_MESSAGE_HISTORY
            # being explicitly denied
            # N.B.: This *must* come last, because it's a conclusive mask
            base.value &= Permissions._timeout_mask()

        return base


class Messageable:
    """An ABC that details the common operations on a model that can send messages.

    The following classes implement this ABC:

    - :class:`~oauth2cord.TextChannel`
    - :class:`~oauth2cord.DMChannel`
    - :class:`~oauth2cord.EphemeralDMChannel`
    - :class:`~oauth2cord.PartialMessageable`
    - :class:`~oauth2cord.User`
    - :class:`~oauth2cord.Member`
    - :class:`~oauth2cord.Lobby`
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_messageable_destination(
        self,
    ) -> Tuple[int, MessageableDestinationType]:
        raise NotImplementedError

    # TODO: `activity=MessageActivity(type=1 | 3, party_id='party_id', session_id='gateway session id')` param, sent by SDK,
    # Also `application_id` is sent as well by it (also investigate whether it needs to be valid to send activity invite?) (update: it is!)

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        file: File = ...,
        delete_after: float = ...,
        allowed_mentions: AllowedMentions = ...,
        metadata: Optional[Dict[str, str]] = MISSING,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        files: Sequence[File] = ...,
        delete_after: float = ...,
        allowed_mentions: AllowedMentions = ...,
        metadata: Optional[Dict[str, str]] = MISSING,
    ) -> Message:
        ...

    async def send(
        self,
        content: Optional[str] = None,
        *,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        delete_after: Optional[float] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        metadata: Optional[Dict[str, str]] = MISSING,
    ) -> Message:
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~oauth2cord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~oauth2cord.File` objects.
        **Specifying both parameters will lead to an exception**.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` or
            :exc:`ValueError` instead of ``InvalidArgument``.

        Parameters
        ----------
        content: Optional[:class:`str`]
            The content of the message to send.
        file: :class:`~oauth2cord.File`
            The file to upload.
        files: List[:class:`~oauth2cord.File`]
            A list of files to upload. Must be a maximum of 10.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~oauth2cord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~oauth2cord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~oauth2cord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~oauth2cord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4
        metadata: Optional[Dict[:class:`str`, :class:`str`]]
            The message's metadata. Can be only up to 25 entries, and 1024 characters per key and value.

        Raises
        ------
        ~oauth2cord.HTTPException
            Sending the message failed.
        ~oauth2cord.Forbidden
            You do not have the proper permissions to send the message.
        ~oauth2cord.NotFound
            You sent a message with the same nonce as one that has been explicitly
            deleted shortly earlier.
        ValueError
            The ``files`` list is not of the appropriate size.
        TypeError
            You specified both ``file`` and ``files``.

        Returns
        -------
        :class:`~oauth2cord.Message`
            The message that was sent.
        """

        destination_id, destination_type = await self._get_messageable_destination()

        state = self._state
        http = state.http
        content = str(content) if content is not None else None
        previous_allowed_mentions = state.allowed_mentions

        endpoint = {
            'lobby': http.send_lobby_message,
            'user': http.send_user_message,
        }.get(destination_type, http.send_message)

        with handle_message_parameters(
            content=content,
            file=file if file is not None else MISSING,
            files=files if files is not None else MISSING,
            allowed_mentions=allowed_mentions,
            previous_allowed_mentions=previous_allowed_mentions,
            metadata=metadata,
        ) as params:
            data = await endpoint(destination_id, params=params)

        channel: Union[TextChannel, DMChannel, EphemeralDMChannel, PartialMessageable]
        if 'channel' in data:
            channel, _ = state._get_guild_channel({'channel': channel})  # type: ignore
        else:
            if destination_type == 'lobby':
                channel, _ = state._get_lobby_channel(
                    _get_as_snowflake(data, 'channel_id'),
                    int(data['lobby_id']),
                )
            elif destination_type == 'user':
                from .channel import PartialMessageable

                channel_id = int(data['channel_id'])
                channel = state._get_private_channel(channel_id)  # type: ignore
                if channel is None:
                    from .channel import PartialMessageable

                    channel = PartialMessageable(
                        state=state,
                        id=channel_id,
                        type=ChannelType.private,
                    )
            else:
                channel_id = int(data['channel_id'])
                guild_id = _get_as_snowflake(data, 'guild_id')

                tmp = None
                if guild_id is None:
                    tmp = state._get_private_channel(channel_id)
                else:
                    guild = state.get_guild(channel_id)
                    if guild is None:
                        tmp = None
                    else:
                        tmp = guild._resolve_channel(channel_id)

                if tmp is None:
                    from .channel import PartialMessageable

                    tmp = PartialMessageable(
                        state=state,
                        id=channel_id,
                    )
                channel = tmp  # type: ignore

        ret = state.create_message(channel=channel, data=data)

        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret


class Connectable(Protocol):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`~oauth2cord.DMChannel`
    - :class:`~oauth2cord.GroupChannel`
    - :class:`~oauth2cord.VoiceChannel`
    - :class:`~oauth2cord.StageChannel`
    - :class:`~oauth2cord.User`
    - :class:`~oauth2cord.Member`
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self) -> VocalChannel:
        raise NotImplementedError

    def _get_voice_client_key(self) -> Tuple[int, str]:
        raise NotImplementedError

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        raise NotImplementedError

    async def connect(
        self,
        *,
        timeout: float = 30.0,
        reconnect: bool = True,
        cls: Callable[[Client, VocalChannel], T] = VoiceClient,
        _channel: Optional[Connectable] = None,
        self_deaf: bool = False,
        self_mute: bool = False,
        self_video: bool = False,
    ) -> T:
        """|coro|

        Connects to voice and creates a :class:`~oauth2cord.VoiceClient` to establish
        your connection to the voice server.

        This requires :attr:`~oauth2cord.Intents.voice_states`.

        Parameters
        ----------
        timeout: :class:`float`
            The timeout in seconds to wait the connection to complete.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`~oauth2cord.VoiceProtocol`]
            A type that subclasses :class:`~oauth2cord.VoiceProtocol` to connect with.
            Defaults to :class:`~oauth2cord.VoiceClient`.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.
        self_video: :class:`bool`
            Indicates if the client should show camera.

        Raises
        ------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~oauth2cord.ClientException
            You are already connected to a voice channel.
        ~oauth2cord.opus.OpusNotLoaded
            The opus library has not been loaded.

        Returns
        -------
        :class:`~oauth2cord.VoiceProtocol`
            A voice client that is fully connected to the voice server.
        """

        key_id, _ = self._get_voice_client_key()
        state = self._state
        connectable = _channel or self
        channel = await connectable._get_channel()

        if state._get_voice_client(key_id):
            raise ClientException('Already connected to a voice channel')

        voice: T = cls(state._get_client(), channel)

        if not isinstance(voice, VoiceProtocol):
            raise TypeError('Type must meet VoiceProtocol abstract base class')

        state._add_voice_client(key_id, voice)

        try:
            await voice.connect(timeout=timeout, reconnect=reconnect, self_deaf=self_deaf, self_mute=self_mute)
        except asyncio.TimeoutError:
            try:
                await voice.disconnect(force=True)
            except Exception:
                pass  # We don't care if disconnect failed because connection failed
            raise  # Re-raise

        return voice
