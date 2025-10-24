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

from functools import reduce
from operator import or_
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Iterator,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    overload,
)

from .enums import UserFlags

if TYPE_CHECKING:
    from typing_extensions import Self

    from .types.presences import ActivityPlatformType as ActivityPlatformTypePayload


__all__ = (
    'AppCommandContext',
    'ActivityFlags',
    'ActivityPlatforms',
    'AppInstallationType',
    'ApplicationFlags',
    'AttachmentFlags',
    'AutoModPresets',
    'ChannelFlags',
    'EmbedFlags',
    'GiftFlags',
    'Intents',
    'LobbyMemberFlags',
    'MediaScanFlags',
    'MemberCacheFlags',
    'MemberFlags',
    'MessageFlags',
    'OverlayMethodFlags',
    'PublicUserFlags',
    'RecipientFlags',
    'RoleFlags',
    'SKUFlags',
    'SystemChannelFlags',
)

BF = TypeVar('BF', bound='BaseFlags')


class flag_value:
    def __init__(self, func: Callable[[Any], int]):
        self.flag: int = func(None)
        self.__doc__: Optional[str] = func.__doc__

    @overload
    def __get__(self, instance: None, owner: Type[BF]) -> Self:
        ...

    @overload
    def __get__(self, instance: BF, owner: Type[BF]) -> bool:
        ...

    def __get__(self, instance: Optional[BF], owner: Type[BF]) -> Any:
        if instance is None:
            return self
        return instance._has_flag(self.flag)

    def __set__(self, instance: BaseFlags, value: bool) -> None:
        instance._set_flag(self.flag, value)

    def __repr__(self) -> str:
        return f'<flag_value flag={self.flag!r}>'


class alias_flag_value(flag_value):
    pass


def fill_with_flags(*, inverted: bool = False) -> Callable[[Type[BF]], Type[BF]]:
    def decorator(cls: Type[BF]) -> Type[BF]:
        # fmt: off
        cls.VALID_FLAGS = {
            name: value.flag
            for name, value in cls.__dict__.items()
            if isinstance(value, flag_value)
        }
        # fmt: on

        if inverted:
            max_bits = max(cls.VALID_FLAGS.values()).bit_length()
            cls.DEFAULT_VALUE = -1 + (2**max_bits)
        else:
            cls.DEFAULT_VALUE = 0

        return cls

    return decorator


# n.b. flags must inherit from this and use the decorator above
class BaseFlags:
    VALID_FLAGS: ClassVar[Dict[str, int]]
    DEFAULT_VALUE: ClassVar[int]

    value: int

    __slots__ = ('value',)

    def __init__(self, **kwargs: bool):
        self.value = self.DEFAULT_VALUE
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
            setattr(self, key, value)

    @classmethod
    def _from_value(cls, value: int) -> Self:
        self = cls.__new__(cls)
        self.value = value
        return self

    def __or__(self, other: Self) -> Self:
        return self._from_value(self.value | other.value)

    def __and__(self, other: Self) -> Self:
        return self._from_value(self.value & other.value)

    def __xor__(self, other: Self) -> Self:
        return self._from_value(self.value ^ other.value)

    def __ior__(self, other: Self) -> Self:
        self.value |= other.value
        return self

    def __iand__(self, other: Self) -> Self:
        self.value &= other.value
        return self

    def __ixor__(self, other: Self) -> Self:
        self.value ^= other.value
        return self

    def __invert__(self) -> Self:
        max_bits = max(self.VALID_FLAGS.values()).bit_length()
        max_value = -1 + (2**max_bits)
        return self._from_value(self.value ^ max_value)

    def __bool__(self) -> bool:
        return self.value != self.DEFAULT_VALUE

    def __eq__(self, other: object) -> bool:
        return isinstance(other, self.__class__) and self.value == other.value

    def __ne__(self, other: object) -> bool:
        return not self.__eq__(other)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f'<{self.__class__.__name__} value={self.value}>'

    def __iter__(self) -> Iterator[Tuple[str, bool]]:
        for name, value in self.__class__.__dict__.items():
            if isinstance(value, alias_flag_value):
                continue

            if isinstance(value, flag_value):
                yield (name, self._has_flag(value.flag))

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) == o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value |= o
        elif toggle is False:
            self.value &= ~o
        else:
            raise TypeError(f'Value to set for {self.__class__.__name__} must be a bool.')


class ArrayFlags(BaseFlags):
    @classmethod
    def _from_value(cls: Type[Self], value: Sequence[int]) -> Self:
        self = cls.__new__(cls)
        # This is a micro-optimization given the frequency this object can be created.
        # (1).__lshift__ is used in place of lambda x: 1 << x
        # prebinding to a method of a constant rather than define a lambda.
        # Pairing this with map, is essentially equivalent to (1 << x for x in value)
        # reduction using operator.or_ instead of defining a lambda each call
        # Discord sends these starting with a value of 1
        # Rather than subtract 1 from each element prior to left shift,
        # we shift right by 1 once at the end.
        self.value = reduce(or_, map((1).__lshift__, value), 0) >> 1
        return self

    def to_array(self, *, offset: int = 0) -> List[int]:
        return [i + offset for i in range(self.value.bit_length()) if self.value & (1 << i)]

    @classmethod
    def all(cls: Type[Self]) -> Self:
        """A factory method that creates an instance of ArrayFlags with everything enabled."""
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = (1 << bits) - 1
        self = cls.__new__(cls)
        self.value = value
        return self

    @classmethod
    def none(cls: Type[Self]) -> Self:
        """A factory method that creates an instance of ArrayFlags with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self


@fill_with_flags()
class ActivityFlags(BaseFlags):
    r"""Wraps up the Discord activity flags.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two ActivityFlags flags are equal.

        .. describe:: x != y

            Checks if two ActivityFlags flags are not equal.

        .. describe:: x | y, x |= y

            Returns an ActivityFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns an ActivityFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns an ActivityFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns an ActivityFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def instance(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity is an instanced game session (a match that will end)."""
        return 1 << 0

    @flag_value
    def join(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity can be joined by other users."""
        return 1 << 1

    @flag_value
    def spectate(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity can be spectated by other users (deprecated)."""
        return 1 << 2

    @flag_value
    def sync(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity can be synced."""
        return 1 << 4

    @flag_value
    def play(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity can be played."""
        return 1 << 5

    @flag_value
    def party_privacy_friends(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity's party can be joined by friends."""
        return 1 << 6

    @flag_value
    def party_privacy_voice_channel(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity's party can be joined by users in the same voice channel."""
        return 1 << 7

    @flag_value
    def embedded(self) -> int:
        """:class:`bool`: Returns ``True`` if the activity is embedded within the Discord client."""
        return 1 << 8


@fill_with_flags()
class ActivityPlatforms(BaseFlags):
    r"""Represents a list of platforms supported by Discord activity.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two ActivityPlatforms flags are equal.

        .. describe:: x != y

            Checks if two ActivityPlatforms flags are not equal.

        .. describe:: x | y, x |= y

            Returns an ActivityPlatforms instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns an ActivityPlatforms instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns an ActivityPlatforms instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns an ActivityPlatforms instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def desktop(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on desktop platforms."""
        return 1 << 0

    @flag_value
    def xbox(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on Xbox."""
        return 1 << 1

    @flag_value
    def samsung(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on Samsung devices."""
        return 1 << 2

    @flag_value
    def ios(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on iOS."""
        return 1 << 3

    @flag_value
    def android(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on Android."""
        return 1 << 4

    @flag_value
    def embedded(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on embedded platforms."""
        return 1 << 5

    @flag_value
    def ps4(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on PS4."""
        return 1 << 6

    @flag_value
    def ps5(self) -> int:
        """:class:`bool`: Returns ``True`` if activity is supported on PS5."""
        return 1 << 7

    @classmethod
    def from_string_array(cls, payload: List[ActivityPlatformTypePayload]) -> Self:
        return cls(
            desktop='desktop' in payload,
            xbox='xbox' in payload,
            samsung='samsung' in payload,
            ios='ios' in payload,
            android='android' in payload,
            embedded='embedded' in payload,
            ps4='ps4' in payload,
            ps5='ps5' in payload,
        )

    def to_string_array(self) -> List[ActivityPlatformTypePayload]:
        payload: List[ActivityPlatformTypePayload] = []

        if self.desktop:
            payload.append('desktop')

        if self.xbox:
            payload.append('xbox')

        if self.samsung:
            payload.append('samsung')

        if self.ios:
            payload.append('ios')

        if self.android:
            payload.append('android')

        if self.embedded:
            payload.append('embedded')

        if self.ps4:
            payload.append('ps4')

        if self.ps5:
            payload.append('ps5')

        return payload


@fill_with_flags()
class AppCommandContext(ArrayFlags):
    r"""Wraps up the Discord :class:`~discord.BaseCommand` execution context.

    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two AppCommandContext flags are equal.

        .. describe:: x != y

            Checks if two AppCommandContext flags are not equal.

        .. describe:: x | y, x |= y

            Returns an AppCommandContext instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns an AppCommandContext instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns an AppCommandContext instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns an AppCommandContext instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    DEFAULT_VALUE = 3

    @flag_value
    def guild(self) -> int:
        """:class:`bool`: Whether the context allows usage in a guild."""
        return 1 << 0

    @flag_value
    def dm_channel(self) -> int:
        """:class:`bool`: Whether the context allows usage in a DM channel."""
        return 1 << 1

    @flag_value
    def private_channel(self) -> int:
        """:class:`bool`: Whether the context allows usage in a DM or a GDM channel."""
        return 1 << 2


@fill_with_flags()
class AppInstallationType(ArrayFlags):
    r"""Represents the installation location of an application command.

    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two AppInstallationType flags are equal.

        .. describe:: x != y

            Checks if two AppInstallationType flags are not equal.

        .. describe:: x | y, x |= y

            Returns an AppInstallationType instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns an AppInstallationType instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns an AppInstallationType instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns an AppInstallationType instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def guild(self) -> int:
        """:class:`bool`: Whether the integration is a guild install."""
        return 1 << 0

    @flag_value
    def user(self) -> int:
        """:class:`bool`: Whether the integration is a user install."""
        return 1 << 1


@fill_with_flags()
class ApplicationFlags(BaseFlags):
    r"""Wraps up the Discord Application flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two ApplicationFlags are equal.
        .. describe:: x != y

            Checks if two ApplicationFlags are not equal.

        .. describe:: x | y, x |= y

            Returns an ApplicationFlags instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns an ApplicationFlags instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns an ApplicationFlags instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns an ApplicationFlags instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    .. versionadded:: 2.0

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def embedded_released(self) -> int:
        """:class:`bool`: Returns ``True`` if the embedded application is released to the public."""
        return 1 << 1

    @flag_value
    def managed_emoji(self) -> int:
        """:class:`bool`: Returns ``True`` if the application can create managed emojis."""
        return 1 << 2

    @flag_value
    def embedded_iap(self) -> int:
        """:class:`bool`: Returns ``True`` if the embedded application can use in-app purchases."""
        return 1 << 3

    @flag_value
    def group_dm_create(self) -> int:
        """:class:`bool`: Returns ``True`` if the application can create group DMs without limit."""
        return 1 << 4

    @flag_value
    def auto_mod_badge(self) -> int:
        """:class:`bool`: Returns ``True`` if the application uses at least 100 automod rules across all guilds.
        This shows up as a badge in the official client.

        .. versionadded:: 2.3
        """
        return 1 << 6

    @flag_value
    def game_profile_disabled(self) -> int:
        """:class:`bool`: Returns ``True`` if the application has it's game profile page disabled."""
        return 1 << 7

    @flag_value
    def public_oauth2_client(self) -> int:
        """:class:`bool`: Returns ``True`` if the application's OAuth2 credentials are public."""
        return 1 << 8

    @flag_value
    def contextless_activity(self) -> int:
        """:class:`bool`: Returns ``True`` if the embedded application's activity can be launched without a context."""
        return 1 << 9

    @flag_value
    def social_layer_integration_limited(self) -> int:
        """:class:`bool`: Returns ``True`` if the application has limited access to the social layer API."""
        return 1 << 10

    @flag_value
    def gateway_presence(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        receive presence information over the gateway.
        """
        return 1 << 12

    @flag_value
    def gateway_presence_limited(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is allowed to receive limited
        presence information over the gateway.
        """
        return 1 << 13

    @flag_value
    def gateway_guild_members(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        receive guild members information over the gateway.
        """
        return 1 << 14

    @flag_value
    def gateway_guild_members_limited(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is allowed to receive limited
        guild members information over the gateway.
        """
        return 1 << 15

    @flag_value
    def verification_pending_guild_limit(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is currently pending verification
        and has hit the guild limit.
        """
        return 1 << 16

    @flag_value
    def embedded(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is embedded within the Discord client."""
        return 1 << 17

    @flag_value
    def gateway_message_content(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is verified and is allowed to
        read message content in guilds."""
        return 1 << 18

    @flag_value
    def gateway_message_content_limited(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is unverified and is allowed to
        read message content in guilds."""
        return 1 << 19

    @flag_value
    def embedded_first_party(self) -> int:
        """:class:`bool`: Returns ``True`` if the embedded application is created by Discord."""
        return 1 << 20

    @flag_value
    def application_command_migrated(self) -> int:
        """:class:`bool`: Unknown."""
        return 1 << 21

    @flag_value
    def app_commands_badge(self) -> int:
        """:class:`bool`: Returns ``True`` if the application has registered a global application
        command. This shows up as a badge in the official client."""
        return 1 << 23

    @flag_value
    def active(self) -> int:
        """:class:`bool`: Returns ``True`` if the application has had at least one global application
        command used in the last 30 days.

        .. versionadded:: 2.1
        """
        return 1 << 24

    @flag_value
    def active_grace_period(self) -> int:
        """:class:`bool`: Returns ``True`` if the application has not had any global application commands
        used in the last 30 days and has lost the :attr:`~.active` flag."""
        return 1 << 25

    @flag_value
    def iframe_modal(self) -> int:
        """:class:`bool`: Returns ``True`` if the application can use IFrames within modals."""
        return 1 << 26

    @flag_value
    def social_layer_integration(self) -> int:
        """:class:`bool`: Returns ``True`` if the application can use the social layer API."""
        return 1 << 27

    @flag_value
    def promoted(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is promoted by Discord in the application directory."""
        return 1 << 29

    @flag_value
    def partner(self) -> int:
        """:class:`bool`: Returns ``True`` if the application is partnered with Discord."""
        return 1 << 30


@fill_with_flags()
class AttachmentFlags(BaseFlags):
    r"""Wraps up the Discord Attachment flags.

    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two AttachmentFlags are equal.

        .. describe:: x != y

            Checks if two AttachmentFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a AttachmentFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a AttachmentFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a AttachmentFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a AttachmentFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def clip(self) -> int:
        """:class:`bool`: Returns ``True`` if the attachment is a clip."""
        return 1 << 0

    @flag_value
    def thumbnail(self) -> int:
        """:class:`bool`: Returns ``True`` if the attachment is a thumbnail."""
        return 1 << 1

    @flag_value
    def remix(self) -> int:
        """:class:`bool`: Returns ``True`` if the attachment has been edited using the remix feature."""
        return 1 << 2

    @flag_value
    def spoiler(self) -> int:
        """:class:`bool`: Returns ``True`` if the attachment was marked as a spoiler.

        .. versionadded:: 2.5
        """
        return 1 << 3

    @flag_value
    def contains_explicit_media(self) -> int:
        """:class:`bool`: Returns ``True`` if the attachment was flagged as sensitive content.

        .. versionadded:: 2.5
        """
        return 1 << 4

    @flag_value
    def animated(self) -> int:
        """:class:`bool`: Returns ``True`` if the attachment is an animated image.

        .. versionadded:: 2.5
        """
        return 1 << 5


@fill_with_flags()
class AutoModPresets(ArrayFlags):
    r"""Wraps up the Discord :class:`AutoModRule` presets.

    .. versionadded:: 2.0


    .. container:: operations

        .. describe:: x == y

            Checks if two AutoMod preset flags are equal.

        .. describe:: x != y

            Checks if two AutoMod preset flags are not equal.

        .. describe:: x | y, x |= y

            Returns an AutoModPresets instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns an AutoModPresets instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns an AutoModPresets instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns an AutoModPresets instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    def to_array(self) -> List[int]:
        return super().to_array(offset=1)

    @flag_value
    def profanity(self) -> int:
        """:class:`bool`: Whether to use the preset profanity filter."""
        return 1 << 0

    @flag_value
    def sexual_content(self) -> int:
        """:class:`bool`: Whether to use the preset sexual content filter."""
        return 1 << 1

    @flag_value
    def slurs(self) -> int:
        """:class:`bool`: Whether to use the preset slurs filter."""
        return 1 << 2


@fill_with_flags()
class ChannelFlags(BaseFlags):
    r"""Wraps up the Discord :class:`~discord.abc.GuildChannel` or :class:`Thread` flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two channel flags are equal.
        .. describe:: x != y

            Checks if two channel flags are not equal.

        .. describe:: x | y, x |= y

            Returns a ChannelFlags instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns a ChannelFlags instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns a ChannelFlags instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns a ChannelFlags instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    .. versionadded:: 2.0

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def guild_feed_removed(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel is hidden from the guild's feed."""
        return 1 << 0

    @flag_value
    def pinned(self) -> int:
        """:class:`bool`: Returns ``True`` if the thread is pinned to the forum channel."""
        return 1 << 1

    @flag_value
    def active_channels_removed(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel has been removed from the guild's active channels."""
        return 1 << 2

    @flag_value
    def require_tag(self) -> int:
        """:class:`bool`: Returns ``True`` if a tag is required to be specified when creating a thread
        in a :class:`ForumChannel`.

        .. versionadded:: 2.1
        """
        return 1 << 4

    @flag_value
    def spam(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel is marked as spammy."""
        return 1 << 5

    # Nice skip, 1 << 6

    @flag_value
    def guild_resource_channel(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel is used as a read-only resource for onboarding and is not shown in the channel list."""
        return 1 << 7

    @flag_value
    def clyde_ai(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel is created by Clyde AI, which has full access to all message content."""
        return 1 << 8

    @flag_value
    def scheduled_for_deletion(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel is scheduled for deletion and is not shown in the UI."""
        return 1 << 9

    @flag_value
    def summaries_disabled(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel has summaries disabled."""
        return 1 << 11

    @flag_value
    def role_subscription_template_preview_channel(self) -> int:
        """:class:`bool`: Returns ``True`` if role subscription tier for this guild channel has not been published yet."""
        return 1 << 13

    @flag_value
    def broadcasting(self) -> int:
        """:class:`bool`: Returns ``True`` if the group is used for broadcasting a live stream."""
        return 1 << 14

    @flag_value
    def hide_media_download_options(self) -> int:
        """:class:`bool`: Returns ``True`` if the client hides embedded media download options in a :class:`ForumChannel`.
        Only available in media channels.

        .. versionadded:: 2.4
        """
        return 1 << 15

    @flag_value
    def join_request_interview_channel(self) -> int:
        """:class:`bool`: Returns ``True`` if the group is used for guild join request interviews."""
        return 1 << 16

    @flag_value
    def obfuscated(self) -> int:
        """:class:`bool`: Returns ``True`` if the user does not have permissions to view the channel."""
        return 1 << 17

    @flag_value
    def is_moderator_report_channel(self) -> int:
        """:class:`bool`: Returns ``True`` if the channel is a Mod Queue channel."""
        return 1 << 19


@fill_with_flags()
class EmbedFlags(BaseFlags):
    r"""Wraps up the Discord Embed flags.

    .. versionadded:: 2.5

    .. container:: operations

        .. describe:: x == y

            Checks if two EmbedFlags are equal.

        .. describe:: x != y

            Checks if two EmbedFlags are not equal.

        .. describe:: x | y, x |= y

            Returns an EmbedFlags instance with all enabled flags from
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns an EmbedFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns an EmbedFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Returns the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def contains_explicit_media(self) -> int:
        """:class:`bool`: Returns ``True`` if the embed was flagged as sensitive content."""
        return 1 << 4

    @flag_value
    def content_inventory_entry(self) -> int:
        """:class:`bool`: Returns ``True`` if the embed is a reply to an activity card, and is no
        longer displayed.
        """
        return 1 << 5


@fill_with_flags()
class GiftFlags(BaseFlags):
    r"""Wraps up the Discord Gift flags.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two GiftFlags are equal.

        .. describe:: x != y

            Checks if two GiftFlags are not equal.

        .. describe:: x | y, x |= y

            Returns an GiftFlags instance with all enabled flags from
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns an GiftFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns an GiftFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Returns the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def payment_source_required(self) -> int:
        """:class:`bool`: Returns ``True`` if the gift requires a payment source to be redeemed."""
        return 1 << 0

    @flag_value
    def existing_subscription_disallowed(self) -> int:
        """:class:`bool`: Returns ``True`` if the gift cannot be redeemed by users with existing premium subscription."""
        return 1 << 1

    @flag_value
    def not_self_redeemable(self) -> int:
        """:class:`bool`: Returns ``True`` if the gift cannot be redeemed by the gifter."""
        return 1 << 2

    @flag_value
    def promotion(self) -> int:
        """:class:`bool`: Returns ``True`` if the gift is from a promotion."""
        return 1 << 3


@fill_with_flags()
class Intents(BaseFlags):
    r"""Wraps up a Discord Gateway intent flags.

    Similar to :class:`Permissions`\, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    This is used to disable certain Gateway features that are unnecessary to
    run your client. To make use of this, it is passed to the ``intents`` keyword
    argument of :class:`Client`.

    .. versionadded:: 1.5

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.

        .. describe:: x | y, x |= y

            Returns an Intents instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns an Intents instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns an Intents instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns an Intents instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

        .. describe:: bool(b)

            Returns whether any intent is enabled.

            .. versionadded:: 2.0

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    # Only following intents can be used in OAuth2 context:

    # GUILDS
    # GUILD_MEMBERS
    # GUILD_VOICE_STATES
    # GUILD_PRESENCES
    # DIRECT_MESSAGES
    # PRIVATE_CHANNELS
    # 1 << 19
    # USER_RELATIONSHIPS
    # USER_PRESENCE
    # LOBBIES
    # LOBBY_DELETE

    __slots__ = ()

    def __init__(self, value: int = 0, **kwargs: bool) -> None:
        self.value: int = value
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
            setattr(self, key, value)

    @classmethod
    def all(cls: Type[Intents]) -> Intents:
        """A factory method that creates a :class:`Intents` with everything available enabled."""
        self = cls.__new__(cls)
        self.value = 0
        self.guilds = True
        self.members = True
        self.voice_states = True
        self.guild_presences = True
        self.dm_messages = True
        self.private_channels = True
        self.calls = True
        self.relationships = True
        self.user_presences = True
        self.lobbies = True
        self.lobby_delete = True
        return self

    @classmethod
    def none(cls: Type[Intents]) -> Intents:
        """A factory method that creates a :class:`Intents` instance with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self

    @classmethod
    def default(cls: Type[Intents]) -> Intents:
        """A factory method that creates a :class:`Intents` instance with everything enabled
        except :attr:`members`, :attr:`presences`, and :attr:`message_content`.
        """
        self = cls.all()
        self.message_content = False
        return self

    @classmethod
    def sdk(cls: Type[Intents]) -> Intents:
        """A factory method that creates a :class:`Intents` instance with intents the official SDK
        enables.

        The following intents are enabled by the SDK:

        - :attr:`~.dm_messages`
        - :attr:`~.private_channels`
        - :attr:`~.calls`
        - :attr:`~.relationships`
        - :attr:`~.user_presences`
        - :attr:`~.lobbies`
        - :attr:`~.lobby_delete`
        """

        self = cls.none()
        self.dm_messages = True
        self.private_channels = True
        self.calls = True
        self.relationships = True
        self.user_presences = True
        self.lobbies = True
        self.lobby_delete = True
        # This is enabled by default in SDK since v1.5.
        # However with this intent we get only Guild.name and Guild.id in following places so far:
        # - READY->guilds[i]
        # - GUILD_UPDATE
        # But I am betting it's going to be removed and replaced with a capability instead.
        # self.guild_names_only = True
        return self

    @flag_value
    def guilds(self) -> int:
        """:class:`bool`: Whether guild related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_join`
        - :func:`on_guild_remove`
        - :func:`on_guild_available`
        - :func:`on_guild_unavailable`
        - :func:`on_guild_channel_update`
        - :func:`on_guild_channel_create`
        - :func:`on_guild_channel_delete`
        - :func:`on_guild_channel_pins_update`
        - :func:`on_thread_create`
        - :func:`on_thread_join`
        - :func:`on_thread_update`
        - :func:`on_thread_delete`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Client.guilds`
        - :class:`Guild` and all its attributes.
        - :meth:`Client.get_channel`
        - :meth:`Client.get_all_channels`

        It is highly advisable to leave this intent enabled for your client to function.
        """
        return 1 << 0

    @flag_value
    def members(self) -> int:
        """:class:`bool`: Whether guild member related events are enabled.

        This corresponds to the following events:

        - :func:`on_member_join`
        - :func:`on_member_remove`
        - :func:`on_member_update`
        - :func:`on_user_update`
        - :func:`on_thread_member_join`
        - :func:`on_thread_member_remove`

        This also corresponds to the following attributes and classes in terms of cache:

        - :meth:`Client.get_all_members`
        - :meth:`Client.get_user`
        - :meth:`Guild.chunk`
        - :meth:`Guild.fetch_members`
        - :meth:`Guild.get_member`
        - :attr:`Guild.members`
        - :attr:`Member.roles`
        - :attr:`Member.nick`
        - :attr:`Member.premium_since`
        - :attr:`User.name`
        - :attr:`User.avatar`
        - :attr:`User.discriminator`
        - :attr:`User.global_name`

        For more information go to the :ref:`member intent documentation <need_members_intent>`.

        .. note::

            Currently, this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return 1 << 1

    @flag_value
    def moderation(self) -> int:
        """:class:`bool`: Whether guild moderation related events are enabled.

        This corresponds to the following events:

        - :func:`on_member_ban`
        - :func:`on_member_unban`
        - :func:`on_audit_log_entry_create`

        This does not correspond to any attributes or classes in the library in terms of cache.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 2

    @alias_flag_value
    def bans(self) -> int:
        """:class:`bool`: An alias of :attr:`moderation`.

        .. versionchanged:: 2.2
            Changed to an alias.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 2

    @alias_flag_value
    def emojis(self) -> int:
        """:class:`bool`: Alias of :attr:`.expressions`.

        .. versionchanged:: 2.0
            Changed to an alias.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 3

    @alias_flag_value
    def emojis_and_stickers(self) -> int:
        """:class:`bool`: Alias of :attr:`.expressions`.

        .. versionadded:: 2.0

        .. versionchanged:: 2.5
            Changed to an alias.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 3

    @flag_value
    def expressions(self) -> int:
        """:class:`bool`: Whether guild emoji, sticker, and soundboard sound related events are enabled.

        .. versionadded:: 2.5

        This corresponds to the following events:

        - :func:`on_guild_emojis_update`
        - :func:`on_guild_stickers_update`
        - :func:`on_soundboard_sound_create`
        - :func:`on_soundboard_sound_update`
        - :func:`on_soundboard_sound_delete`

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Emoji`
        - :class:`GuildSticker`
        - :class:`SoundboardSound`
        - :meth:`Client.get_emoji`
        - :meth:`Client.get_sticker`
        - :meth:`Client.get_soundboard_sound`
        - :meth:`Client.emojis`
        - :meth:`Client.stickers`
        - :meth:`Client.soundboard_sounds`
        - :attr:`Guild.emojis`
        - :attr:`Guild.stickers`
        - :attr:`Guild.soundboard_sounds`

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 3

    @flag_value
    def integrations(self) -> int:
        """:class:`bool`: Whether guild integration related events are enabled.

        This corresponds to the following events:

        - :func:`on_guild_integrations_update`
        - :func:`on_integration_create`
        - :func:`on_integration_update`
        - :func:`on_raw_integration_delete`

        This does not correspond to any attributes or classes in the library in terms of cache.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 4

    @flag_value
    def webhooks(self) -> int:
        """:class:`bool`: Whether guild webhook related events are enabled.

        This corresponds to the following events:

        - :func:`on_webhooks_update`

        This does not correspond to any attributes or classes in the library in terms of cache.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 5

    @flag_value
    def invites(self) -> int:
        """:class:`bool`: Whether guild invite related events are enabled.

        This corresponds to the following events:

        - :func:`on_invite_create`
        - :func:`on_invite_delete`

        This does not correspond to any attributes or classes in the library in terms of cache.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 6

    @flag_value
    def voice_states(self) -> int:
        """:class:`bool`: Whether guild voice state related events are enabled.

        This corresponds to the following events:

        - :func:`on_voice_state_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`VoiceChannel.members`
        - :attr:`VoiceChannel.voice_states`
        - :attr:`Member.voice`

        .. note::

            This intent is required to connect to voice.
        """
        return 1 << 7

    @flag_value
    def presences(self) -> int:
        """:class:`bool`: Whether guild/user presence related events are enabled.

        This corresponds to the following events:

        - :func:`on_presence_update`
        - :func:`on_user_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Member.activities`
        - :attr:`Member.status`
        - :attr:`Member.raw_status`
        - :attr:`Relationship.activities`
        - :attr:`Relationship.status`
        - :attr:`Relationship.raw_status`

        For more information go to the :ref:`presence intent documentation <need_presence_intent>`.
        """
        return (1 << 8) | (1 << 23)

    @flag_value
    def guild_presences(self) -> int:
        """:class:`bool`: Whether guild presence related events are enabled.

        This corresponds to the following events:

        - :func:`on_presence_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Member.activities`
        - :attr:`Member.status`
        - :attr:`Member.raw_status`

        For more information go to the :ref:`presence intent documentation <need_presence_intent>`.

        .. note::

            Currently, for bots this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.
        """
        return 1 << 8

    @flag_value
    def user_presences(self) -> int:
        """:class:`bool`: Whether user presence related events are enabled.

        This corresponds to the following events:

        - :func:`on_presence_update`
        - :func:`on_user_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Relationship.activities`
        - :attr:`Relationship.status`
        - :attr:`Relationship.raw_status`

        For more information go to the :ref:`presence intent documentation <need_presence_intent>`.
        """
        return 1 << 23

    @alias_flag_value
    def messages(self) -> int:
        """:class:`bool`: Whether guild and direct message related events are enabled.

        This is a shortcut to set or get both :attr:`guild_messages` and :attr:`dm_messages`.

        This corresponds to the following events:

        - :func:`on_message` (both guilds and DMs)
        - :func:`on_message_edit` (both guilds and DMs)
        - :func:`on_message_delete` (both guilds and DMs)
        - :func:`on_raw_message_delete` (both guilds and DMs)
        - :func:`on_raw_message_edit` (both guilds and DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages`

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (both guilds and DMs)
        - :func:`on_reaction_remove` (both guilds and DMs)
        - :func:`on_reaction_clear` (both guilds and DMs)

        .. warning::
            :attr:`guild_messages` intent is not usable by user accounts.
        """
        return (1 << 9) | (1 << 12)

    @flag_value
    def guild_messages(self) -> int:
        """:class:`bool`: Whether guild message related events are enabled.

        See also :attr:`dm_messages` for DMs or :attr:`messages` for both.

        This corresponds to the following events:

        - :func:`on_message` (only for guilds)
        - :func:`on_message_edit` (only for guilds)
        - :func:`on_message_delete` (only for guilds)
        - :func:`on_raw_message_delete` (only for guilds)
        - :func:`on_raw_message_edit` (only for guilds)

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages` (only for guilds)

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (only for guilds)
        - :func:`on_reaction_remove` (only for guilds)
        - :func:`on_reaction_clear` (only for guilds)

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 9

    @flag_value
    def dm_messages(self) -> int:
        """:class:`bool`: Whether direct message related events are enabled.

        See also :attr:`guild_messages` for guilds or :attr:`messages` for both.

        This corresponds to the following events:

        - :func:`on_message` (only for DMs)
        - :func:`on_message_edit` (only for DMs)
        - :func:`on_message_delete` (only for DMs)
        - :func:`on_raw_message_delete` (only for DMs)
        - :func:`on_raw_message_edit` (only for DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :class:`Message`
        - :attr:`Client.cached_messages` (only for DMs)

        Note that due to an implicit relationship this also corresponds to the following events:

        - :func:`on_reaction_add` (only for DMs)
        - :func:`on_reaction_remove` (only for DMs)
        - :func:`on_reaction_clear` (only for DMs)
        """
        return 1 << 12

    @alias_flag_value
    def reactions(self) -> int:
        """:class:`bool`: Whether guild and direct message reaction related events are enabled.

        This is a shortcut to set or get both :attr:`guild_reactions` and :attr:`dm_reactions`.

        This corresponds to the following events:

        - :func:`on_reaction_add` (both guilds and DMs)
        - :func:`on_reaction_remove` (both guilds and DMs)
        - :func:`on_reaction_clear` (both guilds and DMs)
        - :func:`on_raw_reaction_add` (both guilds and DMs)
        - :func:`on_raw_reaction_remove` (both guilds and DMs)
        - :func:`on_raw_reaction_clear` (both guilds and DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (both guild and DM messages)

        .. warning::
            This intent is not usable by user accounts.
        """
        return (1 << 10) | (1 << 13)

    @flag_value
    def guild_reactions(self) -> int:
        """:class:`bool`: Whether guild message reaction related events are enabled.

        See also :attr:`dm_reactions` for DMs or :attr:`reactions` for both.

        This corresponds to the following events:

        - :func:`on_reaction_add` (only for guilds)
        - :func:`on_reaction_remove` (only for guilds)
        - :func:`on_reaction_clear` (only for guilds)
        - :func:`on_raw_reaction_add` (only for guilds)
        - :func:`on_raw_reaction_remove` (only for guilds)
        - :func:`on_raw_reaction_clear` (only for guilds)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (only for guild messages)

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 10

    @flag_value
    def dm_reactions(self) -> int:
        """:class:`bool`: Whether direct message reaction related events are enabled.

        See also :attr:`guild_reactions` for guilds or :attr:`reactions` for both.

        This corresponds to the following events:

        - :func:`on_reaction_add` (only for DMs)
        - :func:`on_reaction_remove` (only for DMs)
        - :func:`on_reaction_clear` (only for DMs)
        - :func:`on_raw_reaction_add` (only for DMs)
        - :func:`on_raw_reaction_remove` (only for DMs)
        - :func:`on_raw_reaction_clear` (only for DMs)

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Message.reactions` (only for DM messages)

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 13

    @alias_flag_value
    def typing(self) -> int:
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        This is a shortcut to set or get both :attr:`guild_typing` and :attr:`dm_typing`.

        This corresponds to the following events:

        - :func:`on_typing` (both guilds and DMs)

        This does not correspond to any attributes or classes in the library in terms of cache.

        .. warning::
            This intent is not usable by user accounts.
        """
        return (1 << 11) | (1 << 14)

    @flag_value
    def guild_typing(self) -> int:
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        See also :attr:`dm_typing` for DMs or :attr:`typing` for both.

        This corresponds to the following events:

        - :func:`on_typing` (only for guilds)

        This does not correspond to any attributes or classes in the library in terms of cache.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 11

    @flag_value
    def dm_typing(self) -> int:
        """:class:`bool`: Whether guild and direct message typing related events are enabled.

        See also :attr:`guild_typing` for guilds or :attr:`typing` for both.

        This corresponds to the following events:

        - :func:`on_typing` (only for DMs)

        This does not correspond to any attributes or classes in the library in terms of cache.

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 14

    @flag_value
    def message_content(self) -> int:
        """:class:`bool`: Whether message content, attachments, embeds and components will be available in messages
        which do not meet the following criteria:

        - The message was sent by the client
        - The message was sent in direct messages
        - The message mentions the client

        This applies to the following events:

        - :func:`on_message`
        - :func:`on_message_edit`
        - :func:`on_message_delete`
        - :func:`on_raw_message_edit`

        For more information go to the :ref:`message content intent documentation <need_message_content_intent>`.

        .. note::

            Currently, for bots this requires opting in explicitly via the developer portal as well.
            Bots in over 100 guilds will need to apply to Discord for verification.

        .. versionadded:: 2.0

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 15

    @flag_value
    def guild_scheduled_events(self) -> int:
        """:class:`bool`: Whether guild scheduled event related events are enabled.

        This corresponds to the following events:

        - :func:`on_scheduled_event_create`
        - :func:`on_scheduled_event_update`
        - :func:`on_scheduled_event_delete`
        - :func:`on_scheduled_event_user_add`
        - :func:`on_scheduled_event_user_remove`

        .. versionadded:: 2.0

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 16

    @flag_value
    def private_channels(self) -> int:
        """:class:`bool`: Whether private channel related events are enabled.

        This corresponds to the following events:

        - :func:`on_private_channel_create`
        - :func:`on_private_channel_update`
        - :func:`on_private_channel_delete`
        - :func:`on_group_join`
        - :func:`on_group_remove`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Client.private_channels`
        - :attr:`Member.dm_channel`
        - :attr:`User.dm_channel`

        It is highly advisable to leave this intent enabled for your client to function.
        """

        return 1 << 18

    @flag_value
    def calls(self) -> int:
        """:class:`bool`: Whether call related events are enabled.

        This corresponds to the following events:

        - :func:`on_call_create`
        - :func:`on_call_update`
        - :func:`on_call_delete`
        - :func:`on_voice_state_update`
        """
        return 1 << 19

    @alias_flag_value
    def auto_moderation(self) -> int:
        """:class:`bool`: Whether auto moderation related events are enabled.

        This is a shortcut to set or get both :attr:`auto_moderation_configuration`
        and :attr:`auto_moderation_execution`.

        This corresponds to the following events:

        - :func:`on_automod_rule_create`
        - :func:`on_automod_rule_update`
        - :func:`on_automod_rule_delete`
        - :func:`on_automod_action`

        .. versionadded:: 2.0

        .. warning::
            This intent is not usable by user accounts.
        """
        return (1 << 20) | (1 << 21)

    @flag_value
    def auto_moderation_configuration(self) -> int:
        """:class:`bool`: Whether auto moderation configuration related events are enabled.

        This corresponds to the following events:

        - :func:`on_automod_rule_create`
        - :func:`on_automod_rule_update`
        - :func:`on_automod_rule_delete`

        .. versionadded:: 2.0

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 20

    @flag_value
    def auto_moderation_execution(self) -> int:
        """:class:`bool`: Whether auto moderation execution related events are enabled.

        This corresponds to the following events:
        - :func:`on_automod_action`

        .. versionadded:: 2.0

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 21

    @flag_value
    def relationships(self) -> int:
        """:class:`bool`: Whether relationship related events are enabled.

        This corresponds to the following events:

        - :func:`on_relationship_add`
        - :func:`on_relationship_update`
        - :func:`on_relationship_remove`
        - :func:`on_game_relationship_add`
        - :func:`on_game_relationship_update`
        - :func:`on_game_relationship_remove`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Client.blocked`
        - :attr:`Client.friends`
        - :attr:`Client.game_friends`
        - :attr:`Client.game_relationships`
        - :attr:`Client.incoming_friend_requests`
        - :attr:`Client.incoming_game_friend_requests`
        - :attr:`Client.outgoing_friend_requests`
        - :attr:`Client.outgoing_game_friend_requests`
        - :attr:`Client.relationships`
        - :attr:`Member.relationship`
        - :attr:`User.relationship`
        """
        return 1 << 22

    @alias_flag_value
    def polls(self) -> int:
        """:class:`bool`: Whether guild and direct messages poll related events are enabled.

        This is a shortcut to set or get both :attr:`guild_polls` and :attr:`dm_polls`.

        This corresponds to the following events:

        - :func:`on_poll_vote_add` (both guilds and DMs)
        - :func:`on_poll_vote_remove` (both guilds and DMs)
        - :func:`on_raw_poll_vote_add` (both guilds and DMs)
        - :func:`on_raw_poll_vote_remove` (both guilds and DMs)

        .. versionadded:: 2.4

        .. warning::
            :attr:`guild_polls` and :attr:`dm_polls` intents are not usable by user accounts.
        """
        return (1 << 24) | (1 << 25)

    @flag_value
    def guild_polls(self) -> int:
        """:class:`bool`: Whether guild poll related events are enabled.

        See also :attr:`dm_polls` and :attr:`polls`.

        This corresponds to the following events:

        - :func:`on_poll_vote_add` (only for guilds)
        - :func:`on_poll_vote_remove` (only for guilds)
        - :func:`on_raw_poll_vote_add` (only for guilds)
        - :func:`on_raw_poll_vote_remove` (only for guilds)

        .. versionadded:: 2.4

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 24

    @flag_value
    def dm_polls(self) -> int:
        """:class:`bool`: Whether direct messages poll related events are enabled.

        See also :attr:`guild_polls` and :attr:`polls`.

        This corresponds to the following events:

        - :func:`on_poll_vote_add` (only for DMs)
        - :func:`on_poll_vote_remove` (only for DMs)
        - :func:`on_raw_poll_vote_add` (only for DMs)
        - :func:`on_raw_poll_vote_remove` (only for DMs)

        .. versionadded:: 2.4

        .. warning::
            This intent is not usable by user accounts.
        """
        return 1 << 25

    @flag_value
    def lobbies(self) -> int:
        """:class:`bool`: Whether lobby related events are enabled.

        This corresponds to the following events:

        - :func:`on_lobby_create`
        - :func:`on_lobby_update`
        - :func:`on_lobby_member_join`
        - :func:`on_lobby_member_update`
        - :func:`on_lobby_member_remove`
        - :func:`on_lobby_message`
        - :func:`on_lobby_message_update`
        - :func:`on_lobby_message_delete`
        - :func:`on_lobby_voice_state_update`

        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Client.lobbies`
        - :meth:`Client.get_lobby`
        """
        return 1 << 27

    @flag_value
    def lobby_delete(self) -> int:
        """:class:`bool`: Whether lobby delete event is enabled.

        This corresponds to the following events:

        - :func:`on_lobby_remove`
        """
        return 1 << 28

    @flag_value
    def guild_names_only(self) -> int:
        """:class:`bool`: Whether to include only :attr:`Guild.name` and :attr:`Guild.id`.
        
        This affects the following events:
        
        - :func:`on_guild_join`
        - :func:`on_guild_update`
        - :func:`on_guild_remove`
        
        This also corresponds to the following attributes and classes in terms of cache:

        - :attr:`Client.guilds`
        - :meth:`Client.get_guild`

        It is highly advisable to leave this intent enabled for your client to properly function.
        """
        return 1 << 29


@fill_with_flags()
class LobbyMemberFlags(BaseFlags):
    r"""Wraps up the Discord Lobby Member flags.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two LobbyMemberFlags are equal.

        .. describe:: x != y

            Checks if two LobbyMemberFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a LobbyMemberFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a LobbyMemberFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a LobbyMemberFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a LobbyMemberFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Returns the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def can_link_lobby(self) -> int:
        """:class:`bool`: Returns ``True`` if the member can link lobby to a channel.."""
        return 1 << 0


@fill_with_flags()
class MediaScanFlags(BaseFlags):
    r"""Wraps up the media scan flags.

    .. versionadded:: 3.0

    .. container:: operations

        .. describe:: x == y

            Checks if two MediaScanFlags are equal.

        .. describe:: x != y

            Checks if two MediaScanFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a MediaScanFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a MediaScanFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a MediaScanFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a MediaScanFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Returns the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def explicit(self) -> int:
        """:class:`bool`: Returns ``True`` if the media contains explicit content."""
        return 1 << 0

    @flag_value
    def gore(self) -> int:
        """:class:`bool`: Returns ``True`` if the media has gore.."""
        return 1 << 1


@fill_with_flags()
class MemberCacheFlags(BaseFlags):
    """Controls the library's cache policy when it comes to members.

    This allows for finer grained control over what members are cached.
    Note that the bot's own member is always cached. This class is passed
    to the ``member_cache_flags`` parameter in :class:`Client`.

    Due to a quirk in how Discord works, in order to ensure proper cleanup
    of cache resources it is recommended to have :attr:`Intents.members`
    enabled. Otherwise the library cannot know when a member leaves a guild and
    is thus unable to cleanup after itself.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    The default value is all flags enabled.

    .. versionadded:: 1.5

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.

        .. describe:: x | y, x |= y

            Returns a MemberCacheFlags instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns a MemberCacheFlags instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns a MemberCacheFlags instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns a MemberCacheFlags instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

            .. versionadded:: 2.0

    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    __slots__ = ()

    def __init__(self, **kwargs: bool):
        bits = max(self.VALID_FLAGS.values()).bit_length()
        self.value: int = (1 << bits) - 1
        for key, value in kwargs.items():
            if key not in self.VALID_FLAGS:
                raise TypeError(f'{key!r} is not a valid flag name.')
            setattr(self, key, value)

    @classmethod
    def all(cls: Type[MemberCacheFlags]) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with everything enabled."""
        bits = max(cls.VALID_FLAGS.values()).bit_length()
        value = (1 << bits) - 1
        self = cls.__new__(cls)
        self.value = value
        return self

    @classmethod
    def none(cls: Type[MemberCacheFlags]) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` with everything disabled."""
        self = cls.__new__(cls)
        self.value = self.DEFAULT_VALUE
        return self

    @property
    def _empty(self) -> int:
        return self.value == self.DEFAULT_VALUE

    @flag_value
    def voice(self) -> int:
        """:class:`bool`: Whether to cache members that are in voice.

        This requires :attr:`Intents.voice_states`.

        Members that leave voice are no longer cached.
        """
        return 1

    @flag_value
    def joined(self) -> int:
        """:class:`bool`: Whether to cache members that joined the guild
        or are chunked as part of the initial log in flow.

        This requires :attr:`Intents.members`.

        Members that leave the guild are no longer cached.
        """
        return 2

    @classmethod
    def from_intents(cls: Type[MemberCacheFlags], intents: Intents) -> MemberCacheFlags:
        """A factory method that creates a :class:`MemberCacheFlags` based on
        the currently selected :class:`Intents`.

        Parameters
        ----------
        intents: :class:`Intents`
            The intents to select from.

        Returns
        -------
        :class:`MemberCacheFlags`
            The resulting member cache flags.
        """

        self = cls.none()
        if intents.members:
            self.joined = True
        if intents.voice_states:
            self.voice = True

        return self

    def _verify_intents(self, intents: Intents):
        if self.voice and not intents.voice_states:
            raise ValueError('MemberCacheFlags.voice requires Intents.voice_states')

        if self.joined and not intents.members:
            raise ValueError('MemberCacheFlags.joined requires Intents.members')

    @property
    def _voice_only(self) -> int:
        return self.value == 1


@fill_with_flags()
class MemberFlags(BaseFlags):
    r"""Wraps up the Discord Guild Member flags.

    .. versionadded:: 2.2

    .. container:: operations

        .. describe:: x == y

            Checks if two MemberFlags are equal.

        .. describe:: x != y

            Checks if two MemberFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a MemberFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a MemberFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a MemberFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a MemberFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def did_rejoin(self) -> int:
        """:class:`bool`: Returns ``True`` if the member left and rejoined the :attr:`~discord.Member.guild`."""
        return 1 << 0

    @flag_value
    def completed_onboarding(self) -> int:
        """:class:`bool`: Returns ``True`` if the member has completed onboarding."""
        return 1 << 1

    @flag_value
    def bypasses_verification(self) -> int:
        """:class:`bool`: Returns ``True`` if the member can bypass the guild verification requirements."""
        return 1 << 2

    @flag_value
    def started_onboarding(self) -> int:
        """:class:`bool`: Returns ``True`` if the member has started onboarding."""
        return 1 << 3

    @flag_value
    def guest(self) -> int:
        """:class:`bool`: Returns ``True`` if the member is a guest and can only access
        the voice channel they were invited to.

        .. versionadded:: 2.5
        """
        return 1 << 4

    @flag_value
    def started_home_actions(self) -> int:
        """:class:`bool`: Returns ``True`` if the member has started Server Guide new member actions.

        .. versionadded:: 2.5
        """
        return 1 << 5

    @flag_value
    def completed_home_actions(self) -> int:
        """:class:`bool`: Returns ``True`` if the member has completed Server Guide new member actions.

        .. versionadded:: 2.5
        """
        return 1 << 6

    @flag_value
    def automod_quarantined_username(self) -> int:
        """:class:`bool`: Returns ``True`` if the member's username, nickname, or global name has been
        blocked by AutoMod.

        .. versionadded:: 2.5
        """
        return 1 << 7

    @flag_value
    def dm_settings_upsell_acknowledged(self) -> int:
        """:class:`bool`: Returns ``True`` if the member has dismissed the DM settings upsell.

        .. versionadded:: 2.5
        """
        return 1 << 9

    @flag_value
    def automod_quarantined_clan_tag(self) -> int:
        """:class:`bool`: Returns ``True`` if the member's clan tag has been blocked by AutoMod."""
        return 1 << 10


@fill_with_flags()
class MessageFlags(BaseFlags):
    r"""Wraps up a Discord Message flag value.

    See :class:`SystemChannelFlags`.

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.
        .. describe:: x != y

            Checks if two flags are not equal.

        .. describe:: x | y, x |= y

            Returns a MessageFlags instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns a MessageFlags instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns a MessageFlags instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns a MessageFlags instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

               Return the flag's hash.
        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

            .. versionadded:: 2.0

    .. versionadded:: 1.3

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def crossposted(self) -> int:
        """:class:`bool`: Returns ``True`` if the message is the original crossposted message."""
        return 1 << 0

    @flag_value
    def is_crossposted(self) -> int:
        """:class:`bool`: Returns ``True`` if the message was crossposted from another channel."""
        return 1 << 1

    @flag_value
    def suppress_embeds(self) -> int:
        """:class:`bool`: Returns ``True`` if the message's embeds have been suppressed."""
        return 1 << 2

    @flag_value
    def source_message_deleted(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message for this crosspost has been deleted."""
        return 1 << 3

    @flag_value
    def urgent(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message is an urgent message.

        An urgent message is one sent by Discord Trust and Safety.
        """
        return 1 << 4

    @flag_value
    def has_thread(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message is associated with a thread.

        .. versionadded:: 2.0
        """
        return 1 << 5

    @flag_value
    def ephemeral(self) -> int:
        """:class:`bool`: Returns ``True`` if the source message is ephemeral.

        .. versionadded:: 2.0
        """
        return 1 << 6

    @flag_value
    def loading(self) -> int:
        """:class:`bool`: Returns ``True`` if the message is an interaction response and the bot
        is "thinking".

        .. versionadded:: 2.0
        """
        return 1 << 7

    @flag_value
    def failed_to_mention_some_roles_in_thread(self) -> int:
        """:class:`bool`: Returns ``True`` if the message failed to mention some roles in a thread
        and add their members to the thread.

        .. versionadded:: 2.0
        """
        return 1 << 8

    @flag_value
    def guild_feed_hidden(self) -> int:
        """:class:`bool`: Returns ``True`` if the message is hidden from the guild's feed."""
        return 1 << 9

    @flag_value
    def should_show_link_not_discord_warning(self) -> int:
        """:class:`bool`: Returns ``True`` if the message contains a link that impersonates Discord."""
        return 1 << 10

    @flag_value
    def suppress_notifications(self) -> int:
        """:class:`bool`: Returns ``True`` if the message will not trigger push and desktop notifications.

        .. versionadded:: 2.2
        """
        return 1 << 12

    @alias_flag_value
    def silent(self) -> int:
        """:class:`bool`: Alias for :attr:`suppress_notifications`.

        .. versionadded:: 2.2
        """
        return 1 << 12

    @flag_value
    def voice(self) -> int:
        """:class:`bool`: Returns ``True`` if the message is a voice message.

        .. versionadded:: 2.3
        """
        return 1 << 13

    @flag_value
    def forwarded(self) -> int:
        """:class:`bool`: Returns ``True`` if the message is a forwarded message.

        .. versionadded:: 2.5
        """
        return 1 << 14

    @flag_value
    def has_components_v2(self) -> int:
        """:class:`bool`: Whether the message contains v2 components."""
        return 1 << 15

    @flag_value
    def sent_by_social_layer_integration(self) -> int:
        """:class:`bool`: Whether the message is trigged by the social layer integration."""
        return 1 << 16


@fill_with_flags()
class OverlayMethodFlags(BaseFlags):
    """Wraps up the Discord Overlay method flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two OverlayMethodFlags are equal.
        .. describe:: x != y

            Checks if two OverlayMethodFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a OverlayMethodFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a OverlayMethodFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a OverlayMethodFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a OverlayMethodFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

    .. versionadded:: 3.0

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    @flag_value
    def out_of_process(self) -> int:
        """:class:`bool`: Returns ``True`` if the overlay can be rendered out of process."""
        return 1 << 0


@fill_with_flags()
class PublicUserFlags(BaseFlags):
    r"""Wraps up the Discord User Public flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two PublicUserFlags are equal.
        .. describe:: x != y

            Checks if two PublicUserFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a PublicUserFlags instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns a PublicUserFlags instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns a PublicUserFlags instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns a PublicUserFlags instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

            Return the flag's hash.
        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

            .. versionadded:: 2.0

    .. versionadded:: 1.4

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    @flag_value
    def staff(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a Discord Employee."""
        return UserFlags.staff.value

    @flag_value
    def partner(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a Discord Partner."""
        return UserFlags.partner.value

    @flag_value
    def hypesquad(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Events member."""
        return UserFlags.hypesquad.value

    @flag_value
    def bug_hunter(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a Discord Bug Hunter."""
        return UserFlags.bug_hunter.value

    @flag_value
    def mfa_sms(self) -> int:
        """:class:`bool`: Returns ``True`` if the user has SMS recovery for Multi Factor Authentication enabled.."""
        return UserFlags.mfa_sms.value

    @flag_value
    def premium_promo_dismissed(self) -> int:
        """:class:`bool`: Returns ``True`` if the user has dismissed the Discord Nitro promotion."""
        return UserFlags.premium_promo_dismissed.value

    @flag_value
    def hypesquad_bravery(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Bravery member."""
        return UserFlags.hypesquad_bravery.value

    @flag_value
    def hypesquad_brilliance(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Brilliance member."""
        return UserFlags.hypesquad_brilliance.value

    @flag_value
    def hypesquad_balance(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a HypeSquad Balance member."""
        return UserFlags.hypesquad_balance.value

    @flag_value
    def early_supporter(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is an Early Supporter."""
        return UserFlags.early_supporter.value

    @flag_value
    def team_user(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a Team User."""
        return UserFlags.team_user.value

    @flag_value
    def system(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a system user (i.e. represents Discord officially)."""
        return UserFlags.system.value

    @flag_value
    def has_unread_urgent_messages(self) -> int:
        """:class:`bool`: Returns ``True`` if the user has an unread system message."""
        return UserFlags.has_unread_urgent_messages.value

    @flag_value
    def bug_hunter_level_2(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a Bug Hunter Level 2"""
        return UserFlags.bug_hunter_level_2.value

    @flag_value
    def verified_bot(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a Verified Bot."""
        return UserFlags.verified_bot.value

    @flag_value
    def verified_bot_developer(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is an Early Verified Bot Developer."""
        return UserFlags.verified_bot_developer.value

    @alias_flag_value
    def early_verified_bot_developer(self) -> int:
        """:class:`bool`: An alias for :attr:`verified_bot_developer`.

        .. versionadded:: 1.5
        """
        return UserFlags.verified_bot_developer.value

    @flag_value
    def discord_certified_moderator(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a Discord Certified Moderator.

        .. versionadded:: 2.0
        """
        return UserFlags.discord_certified_moderator.value

    @flag_value
    def bot_http_interactions(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a bot that only uses HTTP interactions
        and is shown in the online member list.

        .. versionadded:: 2.0
        """
        return UserFlags.bot_http_interactions.value

    @flag_value
    def spammer(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is flagged as a spammer by Discord.

        .. versionadded:: 2.0
        """
        return UserFlags.spammer.value

    @flag_value
    def active_developer(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is an active developer.

        .. versionadded:: 2.1
        """
        return UserFlags.active_developer.value

    @flag_value
    def provisional_account(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a provisional account.

        .. versionadded:: 3.0
        """
        return UserFlags.provisional_account.value

    @flag_value
    def quarantined(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is quarautined.

        .. versionadded:: 3.0
        """
        return UserFlags.quarantined.value

    @flag_value
    def collaborator(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a collaborator and considered staff.

        .. versionadded:: 3.0
        """
        return UserFlags.collaborator.value

    @flag_value
    def restricted_collaborator(self) -> int:
        """:class:`bool`: Returns ``True`` if the user is a restricted collaborator and considered staff.

        .. versionadded:: 3.0
        """
        return UserFlags.restricted_collaborator.value

    def all(self) -> List[UserFlags]:
        """List[:class:`UserFlags`]: Returns all public flags the user has."""
        return [public_flag for public_flag in UserFlags if self._has_flag(public_flag.value)]


@fill_with_flags()
class RecipientFlags(BaseFlags):
    r"""Wraps up the Discord DM channel recipient flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two RecipientFlags are equal.

        .. describe:: x != y

            Checks if two RecipientFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a RecipientFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a RecipientFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a RecipientFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a RecipientFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def dismissed_in_game_message_nux(self) -> int:
        """:class:`bool`: Returns ``True`` if the user dismissed :attr:`~MessageType.in_game_message_nux` message."""
        return 1 << 0

    @flag_value
    def dismissed_current_chat_wallpaper(self) -> int:
        """:class:`bool`: Returns ``True`` if the user dismissed current chat wallpaper."""
        return 1 << 1


@fill_with_flags()
class RoleFlags(BaseFlags):
    r"""Wraps up the Discord Role flags.

    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two RoleFlags are equal.

        .. describe:: x != y

            Checks if two RoleFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a RoleFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a RoleFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a RoleFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a RoleFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def in_prompt(self) -> int:
        """:class:`bool`: Returns ``True`` if the role can be selected by members in an onboarding prompt."""
        return 1 << 0


@fill_with_flags()
class SKUFlags(BaseFlags):
    r"""Wraps up the Discord SKU flags.

    .. versionadded:: 2.4

    .. container:: operations

        .. describe:: x == y

            Checks if two SKUFlags are equal.

        .. describe:: x != y

            Checks if two SKUFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a SKUFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a SKUFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a SKUFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a SKUFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def premium_purchase(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a premium purchase."""
        return 1 << 0

    @flag_value
    def has_free_premium_content(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU has free premium content."""
        return 1 << 1

    @flag_value
    def available(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is available for purchase."""
        return 1 << 2

    @flag_value
    def premium_and_distribution(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a premium and distribution product."""
        return 1 << 3

    @flag_value
    def sticker_pack(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a premium sticker pack."""
        return 1 << 4

    @flag_value
    def guild_role_subscription(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a guild role subscription. These are subscriptions made to guilds for premium perks."""
        return 1 << 5

    @flag_value
    def premium_subscription(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a Discord premium subscription or related first-party product.
        These are subscriptions like Nitro and Server Boosts. These are the only giftable subscriptions.
        """
        return 1 << 6

    @flag_value
    def application_guild_subscription(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a application subscription.

        These are subscriptions made to applications for premium perks bound to a guild.
        """
        return 1 << 7

    @flag_value
    def application_user_subscription(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a application subscription.

        These are subscriptions made to applications for premium perks bound to an user.
        """
        return 1 << 8

    @flag_value
    def creator_monetization(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a creator monetization product (e.g. guild role subscription, guild product)."""
        # For some reason this is only actually present on products...
        return 1 << 9

    @flag_value
    def guild_product(self) -> int:
        """:class:`bool`: Returns ``True`` if the SKU is a guild product.

        These are one-time purchases made by guilds for premium perks.
        """
        return 1 << 10


@fill_with_flags(inverted=True)
class SystemChannelFlags(BaseFlags):
    r"""Wraps up a Discord system channel flag value.

    Similar to :class:`Permissions`\, the properties provided are two way.
    You can set and retrieve individual bits using the properties as if they
    were regular bools. This allows you to edit the system flags easily.

    To construct an object you can pass keyword arguments denoting the flags
    to enable or disable.

    .. container:: operations

        .. describe:: x == y

            Checks if two flags are equal.

        .. describe:: x != y

            Checks if two flags are not equal.

        .. describe:: x | y, x |= y

            Returns a SystemChannelFlags instance with all enabled flags from
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x & y, x &= y

            Returns a SystemChannelFlags instance with only flags enabled on
            both x and y.

            .. versionadded:: 2.0

        .. describe:: x ^ y, x ^= y

            Returns a SystemChannelFlags instance with only flags enabled on
            only one of x or y, not on both.

            .. versionadded:: 2.0

        .. describe:: ~x

            Returns a SystemChannelFlags instance with all flags inverted from x.

            .. versionadded:: 2.0

        .. describe:: hash(x)

               Return the flag's hash.

        .. describe:: iter(x)

               Returns an iterator of ``(name, value)`` pairs. This allows it
               to be, for example, constructed as a dict or a list of pairs.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.

            .. versionadded:: 2.0

    Attributes
    ----------
    value: :class:`int`
        The raw value. This value is a bit array field of a 53-bit integer
        representing the currently available flags. You should query
        flags via the properties rather than using this raw value.
    """

    __slots__ = ()

    # For some reason the flags for system channels are "inverted"
    # ergo, if they're set then it means "suppress" (off in the GUI toggle)
    # Since this is counter-intuitive from an API perspective and annoying
    # these will be inverted automatically

    def _has_flag(self, o: int) -> bool:
        return (self.value & o) != o

    def _set_flag(self, o: int, toggle: bool) -> None:
        if toggle is True:
            self.value &= ~o
        elif toggle is False:
            self.value |= o
        else:
            raise TypeError('Value to set for SystemChannelFlags must be a bool.')

    @flag_value
    def join_notifications(self) -> int:
        """:class:`bool`: Returns ``True`` if the system channel is used for member join notifications."""
        return 1

    @flag_value
    def premium_subscriptions(self) -> int:
        """:class:`bool`: Returns ``True`` if the system channel is used for "Nitro boosting" notifications."""
        return 2

    @flag_value
    def guild_reminder_notifications(self) -> int:
        """:class:`bool`: Returns ``True`` if the system channel is used for server setup helpful tips notifications.

        .. versionadded:: 2.0
        """
        return 4

    @flag_value
    def join_notification_replies(self) -> int:
        """:class:`bool`: Returns ``True`` if sticker reply button ("Wave to say hi!") is
        shown for member join notifications.

        .. versionadded:: 2.0
        """
        return 8

    @flag_value
    def role_subscription_purchase_notifications(self) -> int:
        """:class:`bool`: Returns ``True`` if role subscription purchase and renewal
        notifications are enabled.

        .. versionadded:: 2.2
        """
        return 16

    @flag_value
    def role_subscription_purchase_notification_replies(self) -> int:
        """:class:`bool`: Returns ``True`` if the role subscription notifications
        have a sticker reply button.

        .. versionadded:: 2.2
        """
        return 32


@fill_with_flags()
class ThreadMemberFlags(BaseFlags):
    r"""Wraps up the Discord Thread member flags.

    .. container:: operations

        .. describe:: x == y

            Checks if two ThreadMemberFlags are equal.

        .. describe:: x != y

            Checks if two ThreadMemberFlags are not equal.

        .. describe:: x | y, x |= y

            Returns a ThreadMemberFlags instance with all enabled flags from
            both x and y.

        .. describe:: x & y, x &= y

            Returns a ThreadMemberFlags instance with only flags enabled on
            both x and y.

        .. describe:: x ^ y, x ^= y

            Returns a ThreadMemberFlags instance with only flags enabled on
            only one of x or y, not on both.

        .. describe:: ~x

            Returns a ThreadMemberFlags instance with all flags inverted from x.

        .. describe:: hash(x)

            Return the flag's hash.

        .. describe:: iter(x)

            Returns an iterator of ``(name, value)`` pairs. This allows it
            to be, for example, constructed as a dict or a list of pairs.
            Note that aliases are not shown.

        .. describe:: bool(b)

            Returns whether any flag is set to ``True``.


    Attributes
    ----------
    value: :class:`int`
        The raw value. You should query flags via the properties
        rather than using this raw value.
    """

    @flag_value
    def interacted(self) -> int:
        """:class:`bool`: Returns ``True`` if the user has interacted with the thread."""
        return 1 << 0

    @flag_value
    def all_messages(self) -> int:
        """:class:`bool`: Returns ``True`` if the user receives notifications for all messages."""
        return 1 << 1

    @flag_value
    def only_mentions(self) -> int:
        """:class:`bool`: Returns ``True`` if the user receives only for messages that mention them."""
        return 1 << 2

    @flag_value
    def no_messages(self) -> int:
        """:class:`bool`: Returns ``True`` if the user does not receives any notifictaions."""
        return 1 << 3
