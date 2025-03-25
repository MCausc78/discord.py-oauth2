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

import copy
import secrets
import asyncio
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    TYPE_CHECKING,
    Protocol,
    Sequence,
    Tuple,
    TypeVar,
    Union,
    overload,
    runtime_checkable,
)

from .object import Object
from .enums import ChannelType
from .errors import ClientException
from .mentions import AllowedMentions
from .permissions import PermissionOverwrite, Permissions
from .role import Role
from .file import File
from .http import handle_message_parameters
from .voice_client import VoiceClient, VoiceProtocol
from .sticker import GuildSticker, StickerItem
from . import utils

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
    from .client import Client
    from .user import ClientUser
    from .asset import Asset
    from .state import ConnectionState
    from .guild import Guild
    from .member import Member
    from .channel import CategoryChannel
    from .embeds import Embed
    from .message import Message, MessageReference, PartialMessage
    from .channel import (
        TextChannel,
        DMChannel,
        GroupChannel,
        PartialMessageable,
        VoiceChannel,
        StageChannel,
    )
    from .poll import Poll
    from .threads import Thread
    from .types.channel import (
        PermissionOverwrite as PermissionOverwritePayload,
        GuildChannel as GuildChannelPayload,
        OverwriteType,
    )
    from .types.snowflake import (
        SnowflakeList,
    )

    PartialMessageableChannel = Union[TextChannel, VoiceChannel, StageChannel, Thread, DMChannel, PartialMessageable]
    MessageableChannel = Union[PartialMessageableChannel, GroupChannel]
    SnowflakeTime = Union["Snowflake", datetime]

MISSING = utils.MISSING


class _Undefined:
    def __repr__(self) -> str:
        return 'see-below'


_undefined: Any = _Undefined()


@runtime_checkable
class Snowflake(Protocol):
    """An ABC that details the common operations on a Discord model.

    Almost all :ref:`Discord models <discord_api_models>` meet this
    abstract base class.

    If you want to create a snowflake on your own, consider using
    :class:`.Object`.

    Attributes
    -----------
    id: :class:`int`
        The model's unique ID.
    """

    id: int


@runtime_checkable
class User(Snowflake, Protocol):
    """An ABC that details the common operations on a Discord user.

    The following implement this ABC:

    - :class:`~discord.User`
    - :class:`~discord.ClientUser`
    - :class:`~discord.Member`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
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
        """Optional[:class:`~discord.Asset`]: Returns an Asset that represents the user's avatar, if present."""
        raise NotImplementedError

    @property
    def avatar_decoration(self) -> Optional[Asset]:
        """Optional[:class:`~discord.Asset`]: Returns an Asset that represents the user's avatar decoration, if present.

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
        """:class:`~discord.Asset`: Returns the default avatar for a given user."""
        raise NotImplementedError

    @property
    def display_avatar(self) -> Asset:
        """:class:`~discord.Asset`: Returns the user's display avatar.

        For regular users this is just their default avatar or uploaded avatar.

        .. versionadded:: 2.0
        """
        raise NotImplementedError

    def mentioned_in(self, message: Message) -> bool:
        """Checks if the user is mentioned in the specified message.

        Parameters
        -----------
        message: :class:`~discord.Message`
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

    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    me: :class:`~discord.ClientUser`
        The user presenting yourself.
    """

    __slots__ = ()

    id: int
    me: ClientUser


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

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.CategoryChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.ForumChannel`

    This ABC must also implement :class:`~discord.abc.Snowflake`.

    Attributes
    -----------
    name: :class:`str`
        The channel name.
    guild: :class:`~discord.Guild`
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
        """List[:class:`~discord.Role`]: Returns a list of roles that have been overridden from
        their default values in the :attr:`~discord.Guild.roles` attribute."""
        ret = []
        g = self.guild
        for overwrite in filter(lambda o: o.is_role(), self._overwrites):
            role = g.get_role(overwrite.id)
            if role is None:
                continue

            role = copy.copy(role)
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
        return utils.snowflake_time(self.id)

    def overwrites_for(self, obj: Union[Role, User, Object]) -> PermissionOverwrite:
        """Returns the channel-specific overwrites for a member or a role.

        Parameters
        -----------
        obj: Union[:class:`~discord.Role`, :class:`~discord.abc.User`, :class:`~discord.Object`]
            The role or user denoting whose overwrite to get.

        Returns
        ---------
        :class:`~discord.PermissionOverwrite`
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
        can be either a :class:`~discord.Role` or a :class:`~discord.Member` and the value is the
        overwrite as a :class:`~discord.PermissionOverwrite`.

        .. versionchanged:: 2.0
            Overwrites can now be type-aware :class:`~discord.Object` in case of cache lookup failure

        Returns
        --------
        Dict[Union[:class:`~discord.Role`, :class:`~discord.Member`, :class:`~discord.Object`], :class:`~discord.PermissionOverwrite`]
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
        """Optional[:class:`~discord.CategoryChannel`]: The category this channel belongs to.

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
        """Handles permission resolution for the :class:`~discord.Member`
        or :class:`~discord.Role`.

        This function takes into consideration the following cases:

        - Guild owner
        - Guild roles
        - Channel overrides
        - Member overrides
        - Implicit permissions
        - Member timeout
        - User installed app

        If a :class:`~discord.Role` is passed, then it checks the permissions
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
            permissions Discord returns in :attr:`~discord.Interaction.app_permissions`,
            though it is recommended to use that attribute instead.

        Parameters
        ----------
        obj: Union[:class:`~discord.Member`, :class:`~discord.Role`]
            The object to resolve permissions for. This could be either
            a member or a role. If it's a role then member overwrites
            are not computed.

        Returns
        -------
        :class:`~discord.Permissions`
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

            overwrite = utils.get(self._overwrites, type=_Overwrites.ROLE, id=obj.id)
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

    - :class:`~discord.TextChannel`
    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`
    - :class:`~discord.DMChannel`
    - :class:`~discord.GroupChannel`
    - :class:`~discord.PartialMessageable`
    - :class:`~discord.User`
    - :class:`~discord.Member`
    - :class:`~discord.ext.commands.Context`
    - :class:`~discord.Thread`
    """

    __slots__ = ()
    _state: ConnectionState

    async def _get_channel(self) -> MessageableChannel:
        raise NotImplementedError

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        # view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embed: Embed = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        # view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[Embed] = ...,
        file: File = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        # view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    @overload
    async def send(
        self,
        content: Optional[str] = ...,
        *,
        tts: bool = ...,
        embeds: Sequence[Embed] = ...,
        files: Sequence[File] = ...,
        stickers: Sequence[Union[GuildSticker, StickerItem]] = ...,
        delete_after: float = ...,
        nonce: Union[str, int] = ...,
        allowed_mentions: AllowedMentions = ...,
        reference: Union[Message, MessageReference, PartialMessage] = ...,
        mention_author: bool = ...,
        # view: View = ...,
        suppress_embeds: bool = ...,
        silent: bool = ...,
        poll: Poll = ...,
    ) -> Message:
        ...

    async def send(
        self,
        content: Optional[str] = None,
        *,
        tts: bool = False,
        embed: Optional[Embed] = None,
        embeds: Optional[Sequence[Embed]] = None,
        file: Optional[File] = None,
        files: Optional[Sequence[File]] = None,
        stickers: Optional[Sequence[Union[GuildSticker, StickerItem]]] = None,
        delete_after: Optional[float] = None,
        nonce: Optional[Union[str, int]] = None,
        allowed_mentions: Optional[AllowedMentions] = None,
        reference: Optional[Union[Message, MessageReference, PartialMessage]] = None,
        mention_author: Optional[bool] = None,
        # view: Optional[View] = None,
        suppress_embeds: bool = False,
        silent: bool = False,
        poll: Optional[Poll] = None,
    ) -> Message:
        """|coro|

        Sends a message to the destination with the content given.

        The content must be a type that can convert to a string through ``str(content)``.
        If the content is set to ``None`` (the default), then the ``embed`` parameter must
        be provided.

        To upload a single file, the ``file`` parameter should be used with a
        single :class:`~discord.File` object. To upload multiple files, the ``files``
        parameter should be used with a :class:`list` of :class:`~discord.File` objects.
        **Specifying both parameters will lead to an exception**.

        To upload a single embed, the ``embed`` parameter should be used with a
        single :class:`~discord.Embed` object. To upload multiple embeds, the ``embeds``
        parameter should be used with a :class:`list` of :class:`~discord.Embed` objects.
        **Specifying both parameters will lead to an exception**.

        .. versionchanged:: 2.0
            This function will now raise :exc:`TypeError` or
            :exc:`ValueError` instead of ``InvalidArgument``.

        Parameters
        ------------
        content: Optional[:class:`str`]
            The content of the message to send.
        tts: :class:`bool`
            Indicates if the message should be sent using text-to-speech.
        embed: :class:`~discord.Embed`
            The rich embed for the content.
        embeds: List[:class:`~discord.Embed`]
            A list of embeds to upload. Must be a maximum of 10.

            .. versionadded:: 2.0
        file: :class:`~discord.File`
            The file to upload.
        files: List[:class:`~discord.File`]
            A list of files to upload. Must be a maximum of 10.
        nonce: :class:`int`
            The nonce to use for sending this message. If the message was successfully sent,
            then the message will have a nonce with this value.
        delete_after: :class:`float`
            If provided, the number of seconds to wait in the background
            before deleting the message we just sent. If the deletion fails,
            then it is silently ignored.
        allowed_mentions: :class:`~discord.AllowedMentions`
            Controls the mentions being processed in this message. If this is
            passed, then the object is merged with :attr:`~discord.Client.allowed_mentions`.
            The merging behaviour only overrides attributes that have been explicitly passed
            to the object, otherwise it uses the attributes set in :attr:`~discord.Client.allowed_mentions`.
            If no object is passed at all then the defaults given by :attr:`~discord.Client.allowed_mentions`
            are used instead.

            .. versionadded:: 1.4

        reference: Union[:class:`~discord.Message`, :class:`~discord.MessageReference`, :class:`~discord.PartialMessage`]
            A reference to the :class:`~discord.Message` to which you are referencing, this can be created using
            :meth:`~discord.Message.to_reference` or passed directly as a :class:`~discord.Message`.
            In the event of a replying reference, you can control whether this mentions the author of the referenced
            message using the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions`` or by
            setting ``mention_author``.

            .. versionadded:: 1.6

        mention_author: Optional[:class:`bool`]
            If set, overrides the :attr:`~discord.AllowedMentions.replied_user` attribute of ``allowed_mentions``.

            .. versionadded:: 1.6
        view: :class:`discord.ui.View`
            A Discord UI View to add to the message.

            .. versionadded:: 2.0
        stickers: Sequence[Union[:class:`~discord.GuildSticker`, :class:`~discord.StickerItem`]]
            A list of stickers to upload. Must be a maximum of 3.

            .. versionadded:: 2.0
        suppress_embeds: :class:`bool`
            Whether to suppress embeds for the message. This sends the message without any embeds if set to ``True``.

            .. versionadded:: 2.0
        silent: :class:`bool`
            Whether to suppress push and desktop notifications for the message. This will increment the mention counter
            in the UI, but will not actually send a notification.

            .. versionadded:: 2.2
        poll: :class:`~discord.Poll`
            The poll to send with this message.

            .. versionadded:: 2.4

        Raises
        --------
        ~discord.HTTPException
            Sending the message failed.
        ~discord.Forbidden
            You do not have the proper permissions to send the message.
        ~discord.NotFound
            You sent a message with the same nonce as one that has been explicitly
            deleted shortly earlier.
        ValueError
            The ``files`` or ``embeds`` list is not of the appropriate size.
        TypeError
            You specified both ``file`` and ``files``,
            or you specified both ``embed`` and ``embeds``,
            or the ``reference`` object is not a :class:`~discord.Message`,
            :class:`~discord.MessageReference` or :class:`~discord.PartialMessage`.

        Returns
        ---------
        :class:`~discord.Message`
            The message that was sent.
        """

        channel = await self._get_channel()
        state = self._state
        content = str(content) if content is not None else None
        previous_allowed_mention = state.allowed_mentions

        if stickers is not None:
            sticker_ids: SnowflakeList = [sticker.id for sticker in stickers]
        else:
            sticker_ids = MISSING

        if reference is not None:
            try:
                reference_dict = reference.to_message_reference_dict()
            except AttributeError:
                raise TypeError('reference parameter must be Message, MessageReference, or PartialMessage') from None
        else:
            reference_dict = MISSING

        # if view and not hasattr(view, '__discord_ui_view__'):
        #     raise TypeError(f'view parameter must be View not {view.__class__.__name__}')

        if suppress_embeds or silent:
            from .message import MessageFlags  # circular import

            flags = MessageFlags._from_value(0)
            flags.suppress_embeds = suppress_embeds
            flags.suppress_notifications = silent
        else:
            flags = MISSING

        if nonce is None:
            nonce = secrets.randbits(64)

        with handle_message_parameters(
            content=content,
            tts=tts,
            file=file if file is not None else MISSING,
            files=files if files is not None else MISSING,
            embed=embed if embed is not None else MISSING,
            embeds=embeds if embeds is not None else MISSING,
            nonce=nonce,
            allowed_mentions=allowed_mentions,
            message_reference=reference_dict,
            previous_allowed_mentions=previous_allowed_mention,
            mention_author=mention_author,
            stickers=sticker_ids,
            # view=view,
            flags=flags,
            poll=poll,
        ) as params:
            data = await state.http.send_message(channel.id, params=params)

        ret = state.create_message(channel=channel, data=data)
        # if view and not view.is_finished():
        #     state.store_view(view, ret.id)

        if poll:
            poll._update(ret)

        if delete_after is not None:
            await ret.delete(delay=delete_after)
        return ret


class Connectable(Protocol):
    """An ABC that details the common operations on a channel that can
    connect to a voice server.

    The following implement this ABC:

    - :class:`~discord.VoiceChannel`
    - :class:`~discord.StageChannel`
    """

    __slots__ = ()
    _state: ConnectionState

    def _get_voice_client_key(self) -> Tuple[int, str]:
        raise NotImplementedError

    def _get_voice_state_pair(self) -> Tuple[int, int]:
        raise NotImplementedError

    async def connect(
        self,
        *,
        timeout: float = 30.0,
        reconnect: bool = True,
        cls: Callable[[Client, Connectable], T] = VoiceClient,
        self_deaf: bool = False,
        self_mute: bool = False,
    ) -> T:
        """|coro|

        Connects to voice and creates a :class:`~discord.VoiceClient` to establish
        your connection to the voice server.

        This requires :attr:`~discord.Intents.voice_states`.

        Parameters
        -----------
        timeout: :class:`float`
            The timeout in seconds to wait the connection to complete.
        reconnect: :class:`bool`
            Whether the bot should automatically attempt
            a reconnect if a part of the handshake fails
            or the gateway goes down.
        cls: Type[:class:`~discord.VoiceProtocol`]
            A type that subclasses :class:`~discord.VoiceProtocol` to connect with.
            Defaults to :class:`~discord.VoiceClient`.
        self_mute: :class:`bool`
            Indicates if the client should be self-muted.

            .. versionadded:: 2.0
        self_deaf: :class:`bool`
            Indicates if the client should be self-deafened.

            .. versionadded:: 2.0

        Raises
        -------
        asyncio.TimeoutError
            Could not connect to the voice channel in time.
        ~discord.ClientException
            You are already connected to a voice channel.
        ~discord.opus.OpusNotLoaded
            The opus library has not been loaded.

        Returns
        --------
        :class:`~discord.VoiceProtocol`
            A voice client that is fully connected to the voice server.
        """

        key_id, _ = self._get_voice_client_key()
        state = self._state

        if state._get_voice_client(key_id):
            raise ClientException('Already connected to a voice channel.')

        client = state._get_client()
        voice: T = cls(client, self)

        if not isinstance(voice, VoiceProtocol):
            raise TypeError('Type must meet VoiceProtocol abstract base class.')

        state._add_voice_client(key_id, voice)

        try:
            await voice.connect(timeout=timeout, reconnect=reconnect, self_deaf=self_deaf, self_mute=self_mute)
        except asyncio.TimeoutError:
            try:
                await voice.disconnect(force=True)
            except Exception:
                # we don't care if disconnect failed because connection failed
                pass
            raise  # re-raise

        return voice
