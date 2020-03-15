import dbl
from discord.ext import commands


async def on_guild_post():
    print("Server count posted successfully")


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        token_file = open("dbltoken.txt", "r")
        self.token = token_file.read().strip()
        token_file.close()
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True)


def setup(bot):
    bot.add_cog(TopGG(bot))
