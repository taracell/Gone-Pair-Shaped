from discord.ext import commands
import discord
from .objects import game
import contextlib
from utils import checks
import asyncio
import os


def allow_runs(ctx):
    return ctx.bot.allow_running_cah_games

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
        self._load_packs()

    @commands.command(aliases=["reloadpacks", "rpacks"])
    @commands.check(checks.bot_mod)
    async def loadpacks(self, ctx):
        self._load_packs()
        await ctx.send(
            "I've reloaded all the packs",
            title="Complete!"
        )

    def _load_packs(self):
        packs = {}
        for path, _, files in os.walk("packs"):
            lang = path.replace("\\", "/").split("/")[-1]
            if files:
                lang_packs = {}
                for pack in files:
                    pack_name = ".".join(pack.split(".")[:-1])
                    with open(os.path.join(path, pack)) as file:
                        lang_packs[pack_name] = [card.strip() for card in file.readlines()]
                packs[lang] = lang_packs
        self.bot.set(
            "cah_packs",
            packs
        )

    @commands.command()
    @commands.max_concurrency(1, commands.BucketType.channel)
    @checks.bypass_check(allow_runs)
    async def play(self, ctx, advanced=False, whitelist: commands.Greedy[discord.Member] = ()):
        self.bot.running_cah_games += 1
        _game = game.Game(
            context=ctx,
            advanced_setup=advanced,
            whitelist=whitelist,
        )
        with contextlib.suppress(asyncio.CancelledError):
            _game.coro = asyncio.create_task(_game.setup())
            if await _game.coro:
                await _game.begin()
        self.bot.running_cah_games -= 1


def setup(bot):
    bot.add_cog(CAH(bot))
