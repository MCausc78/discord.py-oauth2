.. currentmodule:: discord.rpc

API Reference
=============

The following section outlines the API of discord.py-oauth2 RPC extension.

.. note::

    This module uses the Python logging module to log diagnostic and errors
    in an output independent way.  If the logging module is not configured,
    these logs will not be output anywhere.  See :ref:`logging_setup` for
    more information on how to set up and use the logging module with
    discord.py-oauth2.

Clients
-------

Client
~~~~~~~

.. attributetable:: Client

.. autoclass:: Client
    :members:
    :inherited-members:

.. _discord-rpc-events:

Event Reference
---------------

This section outlines the different types of events listened by :class:`Client`.

There are two ways to register an event, the first way is through the use of
:meth:`Client.event`. The second way is through subclassing :class:`Client` and
overriding the specific events. For example: ::

    import discord.rpc

    class MyClient(discord.rpc.Client):
        async def on_message(self, message):
            if message.author == self.user:
                return

            if message.content.startswith('$hello'):
                print('Someone sent hello!')


If an event handler raises an exception, :func:`on_error` will be called
to handle it, which defaults to logging the traceback and ignoring the exception.

.. warning::

    All the events must be a |coroutine_link|_. If they aren't, then you might get unexpected
    errors. In order to turn a function into a coroutine they must be ``async def``
    functions.

IPC
~~~

.. function:: on_ready()

    Called when the client is done preparing the data received from Discord.


Current User
~~~~~~~~~~~~

.. function:: on_current_user_update(before, after)

    Called when a :class:`ClientUser` updates their profile.

    This is called when one or more of the following things change:

    - avatar
    - username
    - discriminator

    :param before: The updated user's old info.
    :type before: Optional[:class:`ClientUser`]
    :param after: The updated user's updated info.
    :type after: :class:`ClientUser`

.. function:: on_current_member_update(member)

    Called when a :class:`Member` belonging to the current user updates their profile.

    :param member: The updated member's updated info.
    :type member: :class:`Member`

Guilds
~~~~~~

.. function:: on_guild_update(guild)

    Called when a :class:`PartialGuild` updates, for example:

    - Changed name
    - Changed icon

    :param guild: The guild after being updated.
    :type guild: :class:`PartialGuild`

.. function:: on_guild_join(guild)

    Called when a :class:`PartialGuild` is either created by the :class:`Client` or when the
    :class:`Client` joins a guild.

    :param guild: The guild that was joined.
    :type guild: :class:`PartialGuild`

Channels
~~~~~~~~

.. function:: on_guild_channel_create(channel)
              on_private_channel_create(channel)

    Called whenever a guild / private channel is created.

    :param channel: The channel that got created.
    :type channel: :class:`PartialChannel`

Relationships
~~~~~~~~~~~~~

.. function:: on_relationship_update(relationship)

    Called when a :class:`Relationship` is updated, e.g. when you
    block a friend or a friendship is accepted.

    :param relationship: The updated relationship.
    :type relationship: :class:`Relationship`

Voice Channels
~~~~~~~~~~~~~~

.. function:: on_voice_channel_select(channel_id, guild_id)

    Called when the current user moves between voice channels.

    :param channel_id: The ID of the channel the user joined.
    :type channel_id: Optional[:class:`int`]
    :param guild_id: The ID of the guild the channel is in.
    :type guild_id: Optional[:class:`int`]

.. function:: on_voice_state_create(voice_state)
              on_voice_state_update(voice_state)
              on_voice_state_delete(voice_state)

    Called whenever a voice state is created, updated or deleted.

    :param voice_state: The voice state that got created, updated or deleted.
    :type voice_state: :class:`VoiceState`

Settings
~~~~~~~~

.. function:: on_voice_settings_update(voice_settings)

    Called whenever the voice settings are updated.

    :param voice_settings: The updated voice settings.
    :type voice_settings: :class:`VoiceSettings`

.. function:: on_voice_connection_status_update(voice_connection_status)
    
    Called whenever a voice connection changes it's status.

    :param voice_connection_status: The current voice connection status.
    :type voice_connection_status: :class:`VoiceConnectionStatus`

Voice
~~~~~

.. function:: on_speaking_start(channel_id, user_id)
              on_speaking_stop(channel_id, user_id)

    Called whenever an user starts / stops speaking in a voice channel.

    :param channel_id: The ID of the voice channel.
    :type channel_id: :class:`int`
    :param user_id: The ID of the user that started / stopped speaking.
    :type user_id: :class:`int`

Activities
~~~~~~~~~~

.. function:: on_game_join(secret, intent)

    Called whenever an user joins a game.
    
    .. deprecated:: 3.0

        Use :func:`on_activity_join` instead.

    :param secret: The secret for joining the game.
    :type secret: :class:`str`
    :param intent: The intent for joining the game.
                   Only applicable if the application is embedded into the Discord client.
    :type intent: Optional[:class:`JoinIntent`]

.. function:: on_activity_join(secret, intent)

    Called whenever an user joins an activity.
    
    :param secret: The secret for joining the activity.
    :type secret: :class:`str`
    :param intent: The intent for joining the activity.
                   Only applicable if the application is embedded into the Discord client.
    :type intent: Optional[:class:`JoinIntent`]

.. function:: on_activity_invite(invite)

    Called whenever the current user receives a invite to join an activity.

    :param invite: The activity invite.
    :type invite: :class:`discord.ActivityInvite`

.. function:: on_pip_mode_update(is_pip_mode)

    Called whenever PiP (Picture-in-Picture) mode changes.

    :param is_pip_mode: Indicates if the current layout mode is PiP.
    :type is_pip_mode: :class:`bool`

.. function:: on_layout_mode_update(layout_mode)

    Called whenever the activity layout mode changes.

    :param layout_mode: The current layout mode.
    :type layout_mode: :class:`LayoutMode`

.. function:: on_thermal_state_update(thermal_state)

    Called whenever the thermal state changes.

    :param thermal_state: The current thermal state.
    :type thermal_state: :class:`ThermalState`

.. function:: on_orientation_update(screen_orientation)

    Called whenever the screen orientation changes.

    :param screen_orientation: The current screen orientation.
    :type screen_orientation: :class:`OrientationLockState`

.. function:: on_raw_activity_instance_participants_update(participants)

    Called whenever an user joins/leaves the activity instance.

    :param participants: The current list of activity participants.
    :type participants: List[:class:`ActivityParticipant`]

Notifications
~~~~~~~~~~~~~

.. function:: on_notification(notification)

    Called whenever the current user receives a notification.

    :param notification: The notification.
    :type notification: :class:`Notification`

Messages
~~~~~~~~

.. function:: on_message(message)

    Called when a :class:`Message` is created and sent.

    .. warning::

        Your client's own messages and private messages are sent through this
        event. This can lead cases of 'recursion' depending on how your client was
        programmed. If you want the client to not reply to itself, consider
        checking the user IDs.

    :param message: The current message.
    :type message: :class:`Message`

.. function:: on_message_edit(message)

    Called when a :class:`Message` receives an update event.

    The following non-exhaustive cases trigger this event:

    - A message has been pinned or unpinned.
    - The message content has been changed.
    - The message has received an embed.

        - For performance reasons, the embed server does not do this in a "consistent" manner.

    - The message's embeds were suppressed or unsuppressed.
    - A call message has received an update to its participants or ending time.

    :param message: The current version of the message.
    :type message: :class:`Message`

.. function:: on_message_delete(channel_id, message_id)

    Called when a message is deleted.

    :param channel_id: The ID of the channel the deleted message was sent in.
    :type channel_id: :class:`int`
    :param message_id: The ID of the deleted message.
    :type message_id: :class:`int`


Entitlements
~~~~~~~~~~~~

.. function:: on_entitlement_create(entitlement)

    Called when the current user subscribes to a SKU.

    :param entitlement: The entitlement that was created.
    :type entitlement: :class:`discord.Entitlement`

.. function:: on_entitlement_update(entitlement)

    Called when the current user updates their subscription to a SKU. This is usually called when
    the user renews or cancels their subscription.

    :param entitlement: The entitlement that was updated.
    :type entitlement: :class:`discord.Entitlement`

.. function:: on_entitlement_delete(entitlement)

    Called when an users subscription to a SKU is cancelled. This is typically only called when:

    - Discord issues a refund for the subscription.
    - Discord removes an entitlement from a user.

    .. warning::

        This event won't be called if the user cancels their subscription manually, instead
        :func:`on_entitlement_update` will be called with :attr:`~discord.Entitlement.ends_at` set to the end of the
        current billing period.

    :param entitlement: The entitlement that was deleted.
    :type entitlement: :class:`discord.Entitlement`

Video
~~~~~

.. function:: on_screenshare_state_update(active, pid, application_name)

    Called whenever screenshare state changes.

    :param active: Indicates if the screenshare video is still active.
    :type active: :class:`bool`
    :param pid: The ID of the process whose screen is being shared.
    :type pid: Optional[:class:`int`]
    :param application_name: The name of the application.
    :type application_name: Optional[:class:`str`]

.. function:: on_video_state_update(active)

    Called whenever video state changes.

    :param active: Indicates if the video is still active.
    :type active: :class:`bool`

.. _discord-api-enums:

Enumerations
------------

The RPC API provides some enumerations for certain types of strings to avoid the API
from being stringly typed in case the strings change in the future.

All enumerations are subclasses of an internal class which mimics the behaviour
of :class:`enum.Enum`.

.. class:: CertifiedDeviceType

    Specifies the type of certified device.

    .. attribute:: audio_input

        The device accepts audio as input.

    .. attribute:: audio_output

        The device generates audio as output.

    .. attribute:: video_input

        The device accepts video as input.

.. class:: DeepLinkLocation

    Specifies the type of deep link.

    .. attribute:: user_settings

        The deep link navigates to the user settings.

    .. attribute:: changelog

        The deep link navigates to the changelogs.

    .. attribute:: library

        The deep link navigates to the game library.

    .. attribute:: store_home

        The deep link navigates to store.

    .. attribute:: store_listing

        The deep link navigates to a store listing.

    .. attribute:: pick_guild_settings

        The deep link navigates to picking settings for a guild.

    .. attribute:: channel

        The deep link navigates to channel or message.

    .. attribute:: quest_home

        The deep link navigates to Quests.

    .. attribute:: discovery_game_results

        ...

    .. attribute:: oauth2

        The deep link navigates to Authorized Apps.

    .. attribute:: shop

        The deep link navigates to shop.

    .. attribute:: features

        The deep link navigates to features.

    .. attribute:: activities

        The deep link navigates to activities.

.. class:: JoinIntent

    Specifies the type of join intent.

    .. attribute:: play

        The user wants to play.
    
    .. attribute:: spectate

        The user wants to spectate.

.. class:: LayoutMode

    Specifies the layout mode.

    .. attribute:: focused

        The activity is focused.
    
    .. attribute:: pip

        The activity is in picture in an another picture.
    
    .. attribute:: grid

        The activity is placed in a grid.

.. class:: LogLevel

    Specifies the logging level.

    .. attribute:: log

        Use `console.log <https://developer.mozilla.org/en-US/docs/Web/API/console/log_static>`_ for logging.

    .. attribute:: warn

        Use `console.warn <https://developer.mozilla.org/en-US/docs/Web/API/console/warn_static>`_ for logging.

    .. attribute:: debug

        Use `console.debug <https://developer.mozilla.org/en-US/docs/Web/API/console/debug_static>`_ for logging.

    .. attribute:: info

        Use `console.info <https://developer.mozilla.org/en-US/docs/Web/API/console/info_static>`_ for logging.

    .. attribute:: error

        Use `console.error <https://developer.mozilla.org/en-US/docs/Web/API/console/error_static>`_ for logging.

.. class:: Opcode

    Specifies the RPC socket opcode.

    .. attribute:: handshake

        Start RPC socket handshake.

    .. attribute:: frame

        Send a command.

    .. attribute:: close

        The RPC socket is closing.

    .. attribute:: ping

        The RPC socket requests you to send :attr:`pong`.

    .. attribute:: pong

        The RPC socket is responding to ``ping``.

.. class:: OrientationLockState

    Specifies the state of orientation.

    .. attribute:: unlocked

        The orientation is unlocked.

    .. attribute:: portrait

        The orientation is in portrait.

    .. attribute:: landscape

        The orientation is in landscape.

.. class:: PromptBehavior
	
    Specifies the behavior of prompt.
    
    .. attribute:: none
	
        Skips the authorization screen and immediately redirects the user.
        Requires previous authorization with the requested scopes.
	
    .. attribute:: consent
	
        Prompts the user to re-approve their authorization.

.. class:: ShortcutKeyComboType

    Specifies the type of shortcut key combo.
    
    .. attribute:: keyboard_key

        The combo is binded to a keyboard key.
    
    .. attribute:: mouse_button
        
        The combo is binded to a mouse button.
    
    .. attribute:: keyboard_modifier_key
        
        The combo is binded to a keyboard modifier key.
    
    .. attribute:: gamepad_button

        The combo is binded to a gamepad button.

.. class:: ThermalState

    Specifies the thermal state.

    .. attribute:: nominal

        The thermal state is currently nominal.

    .. attribute:: fair

        The thermal state is currently fair.
    
    .. attribute:: serious

        The thermal state is serious.
    
    .. attribute:: critical

        The thermal state is critical.

.. class:: VoiceConnectionState

    Specifies the state of voice connection.
    
    .. attribute:: disconnected

        The voice server is disconnected.

    .. attribute:: awaiting_endpoint

        The client is waiting for a voice endpoint.

    .. attribute:: authenticating

        Discord has connected to your real-time communication server and is currently securing the connection.

    .. attribute:: connecting

        A RTC server has been allocated and Discord is attempting to connect to it.

    .. attribute:: rtc_disconnected

        A connection has been interrupted. Discord will attempt to re-establish the connection in a moment.

    .. attribute:: rtc_connecting

        A secure connection to real-time communication server is established
        and attempting to send data.

    .. attribute:: rtc_connected

        ...

    .. attribute:: no_route

        The connection cannot be established. Discord will try again in a moment.

    .. attribute:: ice_checking

        A secure connection to real-time communication server is established
        and attempting to send data.

    .. attribute:: dtls_conneccting

        A secure connection to real-time communication server is established
        and attempting to send data.

.. class:: VoiceSettingsModeType

    Specifies the type of voice settings mode.

    .. attribute:: ptt

        Push-To-Talk.
    
    .. attribute:: voice_activity
        
        Voice activity.

.. _discord_rpc_models:

Discord Models
--------------

Models are classes that are received from Discord and are not meant to be created by
the user of the library.

.. danger::

    The classes listed below are **not intended to be created by users** and are also
    **read-only**.

    For example, this means that you should not make your own :class:`ActivityParticipant` instances
    nor should you modify the :class:`ActivityParticipant` instance yourself.

    If you want to get one of these model classes instances they'd have to be through
    the cache, and a common way of doing so is through the :func:`utils.find` function
    or attributes of model classes that you receive from the events specified in the
    :ref:`discord-rpc-events`.

.. note::

    Nearly all classes here have :ref:`py:slots` defined which means that it is
    impossible to have dynamic attributes to the data classes.


ActivityParticipant
~~~~~~~~~~~~~~~~~~~

.. attributetable:: ActivityParticipant

.. autoclass:: ActivityParticipant()
    :members:
    :inherited-members:


PartialChannel
~~~~~~~~~~~~~~

.. attributetable:: PartialChannel

.. autoclass:: PartialChannel()
    :members:
    :inherited-members:


GuildChannel
~~~~~~~~~~~~

.. attributetable:: GuildChannel

.. autoclass:: GuildChannel()
    :members:
    :inherited-members:

SharedLink
~~~~~~~~~~

.. attributetable:: SharedLink

.. autoclass:: SharedLink()
    :members:
    :inherited-members:

PlatformBehaviors
~~~~~~~~~~~~~~~~~

.. attributetable:: PlatformBehaviors

.. autoclass:: PlatformBehaviors()
    :members:
    :inherited-members:

EmbeddedActivityConfig
~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: EmbeddedActivityConfig

.. autoclass:: EmbeddedActivityConfig()
    :members:
    :inherited-members:

PartialGuild
~~~~~~~~~~~~

.. attributetable:: PartialGuild

.. autoclass:: PartialGuild()
    :members:
    :inherited-members:

Guild
~~~~~

.. attributetable:: Guild

.. autoclass:: Guild()
    :members:
    :inherited-members:

Member
~~~~~~

.. attributetable:: Member

.. autoclass:: Member()
    :members:
    :inherited-members:

Message
~~~~~~~

.. attributetable:: Message

.. autoclass:: Message()
    :members:
    :inherited-members:

Notification
~~~~~~~~~~~~

.. attributetable:: Notification

.. autoclass:: Notification()
    :members:
    :inherited-members:

UserVoiceSettings
~~~~~~~~~~~~~~~~~

.. attributetable:: UserVoiceSettings

.. autoclass:: UserVoiceSettings()
    :members:
    :inherited-members:

VoiceSettingsMode
~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceSettingsMode

.. autoclass:: VoiceSettingsMode()
    :members:
    :inherited-members:

VoiceSettings
~~~~~~~~~~~~~

.. attributetable:: VoiceSettings

.. autoclass:: VoiceSettings()
    :members:
    :inherited-members:

VoiceConnectionPing
~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceConnectionPing

.. autoclass:: VoiceConnectionPing()
    :members:
    :inherited-members:

VoiceConnectionStatus
~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: VoiceConnectionStatus

.. autoclass:: VoiceConnectionStatus()
    :members:
    :inherited-members:

VoiceState
~~~~~~~~~~

.. attributetable:: VoiceState

.. autoclass:: VoiceState()
    :members:
    :inherited-members:

Data Classes
------------

Some classes are just there to be data containers, this lists them.

Unlike :ref:`models <discord_rpc_models>` you are allowed to create
most of these yourself, even if they can also be used to hold attributes.

Nearly all classes here have :ref:`py:slots` defined which means that it is
impossible to have dynamic attributes to the data classes.

CertifiedDevice
~~~~~~~~~~~~~~~

.. attributetable:: CertifiedDevice

.. autoclass:: CertifiedDevice()
    :members:
    :inherited-members:

PreviewImage
~~~~~~~~~~~~

.. attributetable:: PreviewImage

.. autoclass:: PreviewImage()
    :members:
    :inherited-members:

AvailableDevice
~~~~~~~~~~~~~~~

.. attributetable:: AvailableDevice

.. autoclass:: AvailableDevice()
    :members:
    :inherited-members:

VoiceIOSettings
~~~~~~~~~~~~~~~

.. attributetable:: VoiceIOSettings

.. autoclass:: VoiceIOSettings()
    :members:
    :inherited-members:

ShortcutKeyCombo
~~~~~~~~~~~~~~~~

.. attributetable:: ShortcutKeyCombo

.. autoclass:: ShortcutKeyCombo()
    :members:
    :inherited-members:

PartialVoiceSettingsMode
~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: PartialVoiceSettingsMode

.. autoclass:: PartialVoiceSettingsMode()
    :members:
    :inherited-members:

VoiceInputMode
~~~~~~~~~~~~~~

.. attributetable:: VoiceInputMode

.. autoclass:: VoiceInputMode()
    :members:
    :inherited-members:

EventSubscription
~~~~~~~~~~~~~~~~~

.. attributetable:: EventSubscription

.. autoclass:: EventSubscription()
    :members:
    :inherited-members:

GenericSubscription
~~~~~~~~~~~~~~~~~~~

.. attributetable:: GenericSubscription

.. autoclass:: GenericSubscription()
    :members:
    :inherited-members:

ChannelSubscription
~~~~~~~~~~~~~~~~~~~

.. attributetable:: ChannelSubscription

.. autoclass:: ChannelSubscription()
    :members:
    :inherited-members:

GuildSubscription
~~~~~~~~~~~~~~~~~

.. attributetable:: GuildSubscription

.. autoclass:: GuildSubscription()
    :members:
    :inherited-members:

SpeakingEventSubscription
~~~~~~~~~~~~~~~~~~~~~~~~~

.. attributetable:: SpeakingEventSubscription

.. autoclass:: SpeakingEventSubscription()
    :members:
    :inherited-members:

Button
~~~~~~

.. attributetable:: Button

.. autoclass:: Button()
    :members:
    :inherited-members:

Pan
~~~

.. attributetable:: Pan

.. autoclass:: Pan()
    :members:
    :inherited-members:
