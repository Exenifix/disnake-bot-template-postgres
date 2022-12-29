import disnake
from disnake.ext import commands

from utils.bot import Cog
from utils.errors import UNKNOWN, get_error_msg


class SystemListeners(Cog):
    @Cog.listener()
    async def on_slash_command_error(
        self, inter: disnake.ApplicationCommandInteraction, error: commands.CommandError
    ) -> None:
        msg = get_error_msg(error)
        if msg is UNKNOWN:
            await inter.send("Sorry unknown exception occurred, we are already working on it!", ephemeral=True)
            raise error
        await inter.send(msg)
