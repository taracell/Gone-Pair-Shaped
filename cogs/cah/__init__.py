from discord.ext import commands
import discord
from .objects import game
import contextlib
from utils import checks
import asyncio
import os
from . import errors
import typing


def allow_runs(ctx):
    if not ctx.bot.allow_running_cah_games:
        raise errors.Development("Unfortunately I'm in development mode right now, come back later")
    return True


def no_cah_in_channel(ctx):
    if ctx.bot.running_cah_game_objects.get(ctx.channel, None) is not None:
        raise errors.GameExists("There's already a game in this channel. Try ending it first?")
    return True


class CAH(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            bot.running_cah_games
        except AttributeError:
            bot.set(
                "running_cah_games",
                0
            )
        try:
            bot.allow_running_cah_games
        except AttributeError:
            bot.set(
                "allow_running_cah_games",
                True
            )
        try:
            bot.running_cah_game_objects
        except AttributeError:
            bot.set(
                "running_cah_game_objects",
                {}
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

    @commands.command(aliases=["start"])
    @commands.check(no_cah_in_channel)
    @checks.bypass_check(allow_runs)
    @commands.guild_only()
    async def play(self, ctx, advanced: typing.Optional[bool] = False, whitelist: commands.Greedy[discord.Member] = ()):
        self.bot.running_cah_games += 1
        _game = game.Game(
            context=ctx,
            advanced_setup=advanced,
            whitelist=whitelist,
        )
        self.bot.running_cah_game_objects[ctx.channel] = _game
        with contextlib.suppress(asyncio.CancelledError):
            _game.coro = asyncio.create_task(_game.setup())
            if await _game.coro:
                await _game.begin()
        with contextlib.suppress(KeyError):
            del self.bot.running_cah_game_objects[ctx.channel]
        self.bot.running_cah_games -= 1

    @commands.command()
    @commands.guild_only()
    async def end(self, ctx, instantly: typing.Optional[bool] = False):
        old_game = self.bot.running_cah_game_objects.get(ctx.channel, None)
        if not (ctx.author.permissions_in(ctx.channel).manage_channels or ctx.author == old_game.context.author):
            return await ctx.send(
                "You didn't start this game, and you can't manage this channel",
                title="You don't have permission to do that"
            )
        if old_game is not None:
            with contextlib.suppress(Exception):
                del self.bot.running_cah_game_objects[ctx.channel]
                old_game.active = False
                await old_game.end(instantly=instantly)
        else:
            await ctx.send(
                "Has it already been ended?",
                title="We couldn't find a game in this channel..."
            )

    @commands.command(aliases=["bc", "sall"])
    @commands.check(checks.is_owner)
    async def broadcast(self, ctx, nostart: typing.Optional[bool] = True, *, message):
        self.bot.allow_running_cah_games = False if nostart else self.bot.allow_running_cah_games
        for _game in self.bot.running_cah_game_objects.values():
            with contextlib.suppress(Exception):
                await _game.context.send(
                    message,
                    title="Developer broadcast - Because you're playing CAH here..."
                )
        await ctx.send(
            message,
            title="Sent to every server currently ingame..."
        )

    @commands.command(aliases=["denystart", "stopstart"])
    @commands.check(checks.is_owner)
    async def nostart(self, ctx, end: typing.Optional[bool] = False, instantly: typing.Optional[bool] = True):
        self.bot.allow_running_cah_games = False
        if end:
            for _game in self.bot.running_cah_game_objects.values():
                with contextlib.suppress(Exception):
                    await _game.end(
                        instantly=instantly,
                        reason="the bot is going into development mode..."
                    )
        await ctx.send(
            (
                f"Old games {'have ended' if instantly else 'will end after the current round'}"
                if end else "Old games will continue to run their course"
            ),
            title="Stopped new games from being started"
        )

    @commands.command(aliases=["allowstart", "startstart", 'yestart'])
    @commands.check(checks.is_owner)
    async def yesstart(self, ctx):
        self.bot.allow_running_cah_games = True
        await ctx.send(
            "Games can be started again",
            title="Action complete!"
        )


def setup(bot):
    bot.add_cog(CAH(bot))
