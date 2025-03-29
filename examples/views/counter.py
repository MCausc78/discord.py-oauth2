# This example requires the 'message_content' privileged intent to function.

from discord_slayer_sdk_slayer_sdk.ext import commands

import discord_slayer_sdk


class CounterBot(commands.Bot):
    def __init__(self):
        intents = discord_slayer_sdk.Intents.default()
        intents.message_content = True

        super().__init__(command_prefix=commands.when_mentioned_or('$'), intents=intents)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')


# Define a simple View that gives us a counter button
class Counter(discord_slayer_sdk.ui.View):

    # Define the actual button
    # When pressed, this increments the number displayed until it hits 5.
    # When it hits 5, the counter button is disabled and it turns green.
    # note: The name of the function does not matter to the library
    @discord_slayer_sdk.ui.button(label='0', style=discord_slayer_sdk.ButtonStyle.red)
    async def count(self, interaction: discord_slayer_sdk.Interaction, button: discord_slayer_sdk.ui.Button):
        number = int(button.label) if button.label else 0
        if number + 1 >= 5:
            button.style = discord_slayer_sdk.ButtonStyle.green
            button.disabled = True
        button.label = str(number + 1)

        # Make sure to update the message with our updated selves
        await interaction.response.edit_message(view=self)


bot = CounterBot()


@bot.command()
async def counter(ctx: commands.Context):
    """Starts a counter for pressing."""
    await ctx.send('Press!', view=Counter())


bot.run('token')
