import dbl
import contextlib
from discord.ext import commands


async def on_guild_post():
    print("Server count posted successfully")


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = bot.tokens["topgg"]
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True)


def setup(bot):
    with contextlib.suppress(KeyError):
        bot.add_cog(TopGG(bot))
