:orphan:

.. _discord-intro:

Managing Relationships
======================

discord.py-oauth2 lets you manage user's relationships between players in your app. This guide page will tell you how to do following:

- Sending and accepting friend requests
- Handling different relationship types
- Blocking and unblocking users
- Working with both Discord and in-game friendships

Understanding Relationship Types
--------------------------------

Discord models the relationship between two users using the :class:`discord.Relationship` class.
Relationships aren't made just for friendships. Relationships are also used to send and receive friend requests, block other users and ignoring them.

.. warning::

    While discord.py-oauth2 allows you to manage user's relationships, **you never should not act without their explicit consent**. You generally should not send or accept friend requests automatically. You should manage relationships only when requested by the user.

The following table demonstrates differences between platform-wide and in-game relationships:

+----------+------------------------------------------------+--------------+-----------------------------------------------------+-----------------------------------------------------------------------+
| Type     | Do they persist across all games and platform? | Limit        | Presence accessibility                              | Private Messaging functionality                                       |
+----------+------------------------------------------------+--------------+-----------------------------------------------------+-----------------------------------------------------------------------+
| Discord  | Yes                                            | 1000 friends | Friends can see your status everywhere              | Friends can message you at any time                                   |
+----------+------------------------------------------------+--------------+-----------------------------------------------------+-----------------------------------------------------------------------+
| In-Game  | Only in your game                              | None         | Friends can see your status only when you play game | Friends can message you only when you play the game they added you in |
+----------+------------------------------------------------+--------------+-----------------------------------------------------+-----------------------------------------------------------------------+


Relationship Actions
--------------------

Sending In-Game Friend Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Send (or accept, if a relationship of type :attr:`~discord.RelationshipType.incoming_request` exists) an in-game friend request to the target user.

You can send in-game friend requests to users through either their unique username or user ID.

After a friend request is sent, the target user will have a game relationship of type :attr:`~discord.RelationshipType.incoming_request` added,
and the current user will have a game relationship of type :attr:`~discord.RelationshipType.outgoing_request`.

.. note::

    If the current user has relationship with type :attr:`~discord.RelationshipType.outgoing_request`, both target user and current user will become in-game friends.

.. code-block:: python3
   :emphasize-lines: 2,6

    # Using an username
    await client.send_game_friend_request('gatewaydisc.rdgg')
    print('\N{VIDEO GAME} Successfully sent in-game friend request.')

    # Using an user ID
    await client.send_game_friend_request(1073325901825187841)
    print('\N{VIDEO GAME} Successfully sent in-game friend request.')

Sending Discord Friend Requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Sending Discord-wide friend requests to users is mostly similar to how you would send in-game friend requests above, except :meth:`discord.Client.send_friend_request` and :class:`discord.Relationship` should be used instead.

Accepting incoming friend requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can allow players to accept friend requests through utilizing :meth:`discord.Relationship.accept` (or :meth:`discord.GameRelationship.accept` for in-game relationships) method.

.. code-block:: python3
   :emphasize-lines: 2,6,10,14

    # Accepting a Discord friend request
    relationship = client.get_relationship(1073325901825187841)
    if relationship is None:
        print("He didn't sent friend request to you yet!")
    else:
        await relationship.accept()
        print('\N{VIDEO GAME} Successfully accepted friend request.')

    # Accepting an in-game friend request
    game_relationship = client.get_game_relationship(1073325901825187841)
    if game_relationship is None:
        print("He didn't sent friend request to you yet in your game!")
    else:
        await game_relationship.accept()
        print('\N{VIDEO GAME} Successfully accepted in-game friend request.')

Rejecting/Cancelling incoming friend requests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Players may choose to not become friends if they don't like other user sending a friend request to them.
Or... you did not like sending a friend request to them? Cancel these friend requests then.

.. code-block:: python3
   :emphasize-lines: 2,6,13,17

    # Rejecting a Discord friend request
    relationship = client.get_relationship(1073325901825187841)
    if relationship is None:
        print("He didn't sent friend request to you yet!")
    else:
        await relationship.delete()
        if relationship.type == discord.RelationshipType.incoming_request:
            print('Successfully rejected friend request :(')
        else:
            print('Successfully canceled friend request.')

    # Rejecting an in-game friend request
    game_relationship = client.get_game_relationship(1073325901825187841)
    if game_relationship is None:
        print("He didn't sent friend request to you yet in your game!")
    else:
        await game_relationship.delete()
        if relationship.type == discord.RelationshipType.incoming_request:
            print('Successfully rejected in-game friend request :(')
        else:
            print('Successfully canceled in-game friend request.')


Blocking Users
~~~~~~~~~~~~~~

Sometimes players do not like others at all. They want to prevent others from messaging them, sending friend requests, or activity invites.

Blocking an user will remove all existing Discord and in-game relationships with them. Blocking user is done globally, meaning the target user is blocked in all games and Discord as well.

.. code-block:: python3
   :emphasize-lines: 6

    # Currently, an instance of :class:`discord.User` is required to block them. In future, discord.py-oauth2 will have a way to do by having an user ID.
    user = client.get_user(1073325901825187841)
    if user is None:
        print('Huh? Where are they?')
    else:
        await user.block()
        print('Successfully blocked them :(')


Unblocking Users
~~~~~~~~~~~~~~~~

Likewise, players may have misunderstood what other player did, and as such unblock them. Note that unblocking user will not restore previously-created relationships.

.. code-block:: python3
   :emphasize-lines: 6

    # Currently, an instance of :class:`discord.User` is required to block them. In future, discord.py-oauth2 will have a way to do by having an user ID.
    relationship = client.get_relationship(1073325901825187841)
    if relationship is None or relationship.type != discord.RelationshipType.blocked:
        print('They are not blocked.')
    else:
        await relationship.delete()
        print('Successfully unblocked them.')
