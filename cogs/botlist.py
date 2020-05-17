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
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=False)

    @commands.command()
    @commands.is_owner()
    async def post(self, ctx, amount: int):
        await self.dblpy.http.post_guild_count(self.dblpy.bot_id, amount, None, None)
        await ctx.send("Check the server count")


def setup(bot):
    with contextlib.suppress(KeyError):
        bot.add_cog(TopGG(bot))
