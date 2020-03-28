from discord.ext import commands
import discord
from .objects import game
import contextlib
from utils import checks


class CAH(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.set(
            "running_cah_games",
            0
        )
        bot.set(
            "allow_running_cah_games",
            True
        )

    @staticmethod
    def allow_runs(ctx):
        return ctx.bot.allow_running_cah_games

    @commands.Command()
    @commands.max_concurrency(0, commands.BucketType.channel)
    @checks.bypass_check(allow_runs)
    async def play(self, ctx, advanced=False, whitelist: commands.Greedy[discord.Member] = ()):
        self.bot.running_cah_games += 1
        with contextlib.suppress(Exception):
            _game = game.Game(
                context=ctx,
                advanced_setup=advanced,
                whitelist=whitelist,
            )
            await _game.begin()
        self.bot.running_cah_games -= 1


def setup(bot):
    bot.add_cog(CAH(bot))
