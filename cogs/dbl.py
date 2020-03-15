import dbl
import discord
from discord.ext import commands

with open("dbltoken.txt", "r") as f:
    token = f.readlines()[0]


async def on_guild_post():
    print("Server count posted successfully")


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = token
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True)


def setup(bot):
    bot.add_cog(TopGG(bot))
