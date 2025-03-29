import discord_slayer_sdk
from discord_slayer_sdk_slayer_sdk import app_commands

import traceback

# The guild in which this slash command will be registered.
# It is recommended to have a test guild to separate from your "production" bot
TEST_GUILD = discord_slayer_sdk.Object(0)


class MyClient(discord_slayer_sdk.Client):
    def __init__(self) -> None:
        # Just default intents and a `discord_slayer_sdk.Client` instance
        # We don't need a `commands.Bot` instance because we are not
        # creating text-based commands.
        intents = discord_slayer_sdk.Intents.default()
        super().__init__(intents=intents)

        # We need an `discord_slayer_sdk.app_commands.CommandTree` instance
        # to register application commands (slash commands in this case)
        self.tree = app_commands.CommandTree(self)

    async def on_ready(self):
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

    async def setup_hook(self) -> None:
        # Sync the application command with Discord.
        await self.tree.sync(guild=TEST_GUILD)


class Feedback(discord_slayer_sdk.ui.Modal, title='Feedback'):
    # Our modal classes MUST subclass `discord_slayer_sdk.ui.Modal`,
    # but the title can be whatever you want.

    # This will be a short input, where the user can enter their name
    # It will also have a placeholder, as denoted by the `placeholder` kwarg.
    # By default, it is required and is a short-style input which is exactly
    # what we want.
    name = discord_slayer_sdk.ui.TextInput(
        label='Name',
        placeholder='Your name here...',
    )

    # This is a longer, paragraph style input, where user can submit feedback
    # Unlike the name, it is not required. If filled out, however, it will
    # only accept a maximum of 300 characters, as denoted by the
    # `max_length=300` kwarg.
    feedback = discord_slayer_sdk.ui.TextInput(
        label='What do you think of this new feature?',
        style=discord_slayer_sdk.TextStyle.long,
        placeholder='Type your feedback here...',
        required=False,
        max_length=300,
    )

    async def on_submit(self, interaction: discord_slayer_sdk.Interaction):
        await interaction.response.send_message(f'Thanks for your feedback, {self.name.value}!', ephemeral=True)

    async def on_error(self, interaction: discord_slayer_sdk.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)

        # Make sure we know what the error actually is
        traceback.print_exception(type(error), error, error.__traceback__)


client = MyClient()


@client.tree.command(guild=TEST_GUILD, description="Submit feedback")
async def feedback(interaction: discord_slayer_sdk.Interaction):
    # Send the modal with an instance of our `Feedback` class
    # Since modals require an interaction, they cannot be done as a response to a text command.
    # They can only be done as a response to either an application command or a button press.
    await interaction.response.send_modal(Feedback())


client.run('token')
