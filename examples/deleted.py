# This example requires the 'message_content' privileged intent to function.

import slaycord


class MyClient(slaycord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def on_message(self, message):
        if message.content.startswith('!deleteme'):
            msg = await message.channel.send('I will delete myself now...')
            await msg.delete()

            # this also works
            await message.channel.send('Goodbye in 3 seconds...', delete_after=3.0)

    async def on_message_delete(self, message: slaycord.Message):
        msg = f'{message.author} has deleted the message: {message.content}'
        await message.channel.send(msg)


intents = slaycord.Intents.default()
intents.message_content = True

client = MyClient(intents=intents)
client.run('token')
