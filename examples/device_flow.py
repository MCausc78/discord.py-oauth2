# This examples assumes that the application has Public Client option enabled

from __future__ import annotations

import asyncio
import oauth2cord

client_id = 1169421761859833997


async def main():
    oauth2cord.utils.setup_logging()

    client = oauth2cord.Client()

    await client.login()
    flow = await client.start_device_flow(client_id, scopes=['sdk.social_layer', 'guilds'])
    print('Go to', flow.complete_verification_uri, 'to complete the device flow.')

    result = await flow.poll()
    await client.login(result.access_token)

    print("Authorized successfully! Let's see what you have.")

    @client.event
    async def on_ready():
        first_line = f'Logged in as {client.user}'
        print(first_line)
        print('-' * len(first_line))

        blocked_count = len(client.blocked)
        friend_count = len(client.friends)
        game_friend_count = len(client.game_friends)
        guild_count = len(client.guilds)

        print(f'Count of users you have blocked: {blocked_count}')
        print(f'Friends: {friend_count}')
        print(f'Game friends (in {client.application_name}): {game_friend_count}')
        print(f'Guilds: {guild_count}')

        await client.close()

    await client.connect()


asyncio.run(main())
