import asyncio
import sys

import oauth2cord
import oauth2cord.rpc
from oauth2cord.utils import setup_logging

client_id = 1169421761859833997


async def using_rpc():
    client = oauth2cord.rpc.Client()
    flow_task = await client.start(client_id, background=True)

    await client.change_presence(activity=oauth2cord.Game("Rich presence with oauth2cord.py-oauth2 (PRC)"))

    try:
        await flow_task
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass

    await client.close()


async def using_gateway(token):
    client = oauth2cord.Client()

    @client.event
    async def on_ready():
        await client.change_presence(activity=oauth2cord.Game("Rich presence with oauth2cord.py-oauth2 (Gateway)"))

    await client.start(token)


async def using_http(token: str):
    client = oauth2cord.Client()

    me = await client.login(token)
    application_id = me.application.id

    activity = oauth2cord.Game(
        name="Hackplug",
        details="Rich presence with oauth2cord.py-oauth2 (Headless session)",
        application_id=application_id,
        platform=oauth2cord.ActivityPlatform.desktop,
    )
    await client.create_headless_session(activities=[activity])


async def main():
    setup_logging()

    if len(sys.argv) == 1:
        await using_rpc()
    else:
        token = sys.argv[1]
        await using_gateway(token)


asyncio.run(main())
