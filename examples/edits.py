# This example requires the 'message_content' privileged intent to function.

import oauth2cord
import asyncio


class MyClient(oauth2cord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        if message.content.startswith('!editme'):
            msg = await message.channel.send('10')
            await asyncio.sleep(3.0)
            await msg.edit(content='40')

    async def on_message_edit(self, before: oauth2cord.Message, after: oauth2cord.Message):
        if before.content == after.content:
            return

        msg = f'**{before.author}** edited their message:\n{before.content} -> {after.content}'
        await before.channel.send(msg)


intents = oauth2cord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('token')
