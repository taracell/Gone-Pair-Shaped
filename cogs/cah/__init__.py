from discord.ext import commands
import discord
from .objects import game
import contextlib
from utils import checks
from utils.miniutils.data import json
from utils.miniutils.minidiscord import input
import asyncio
import os
from . import errors
import typing
import re
import flag

default_lang = "gb"


def allow_runs(ctx):
    if not ctx.bot.allow_running_cah_games:
        raise errors.Development("Unfortunately I'm in development mode right now, come back later")
    return True


def no_cah_in_channel(ctx):
    if ctx.bot.running_cah_game_objects.get(ctx.channel, None) is not None:
        raise errors.GameExists("There's already a game in this channel. Try ending it first?")
    return True


# noinspection DuplicatedCode
class CAH(commands.Cog):
    def __init__(self, bot):
        self.languages = json.Json("languages")
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
        """Reloads all packs.
        """
        self._load_packs()
        await ctx.send(
            "I've reloaded all the packs",
            title=f"{ctx.bot.emotes['success']} Complete!",
            color=ctx.bot.colors["info"]
        )

    @commands.command(aliases=["language", "lang", "setlang"])
    async def setlanguage(self, ctx):
        """Set what language you want to use for your packs.
        """
        languages = {
            "gb": "English",
            "es": "Español",
            "fr": "Français",
            "de": "Deutsch",
            "ru": "русский",
            "ua": "Українська",
            "nl": "Nederlands",
            "pt": "Português"
        }
        supported = "**Already supported:**"
        for language in self.bot.cah_packs:
            supported += f"\n:flag_{language}: {languages.get(language, 'Unknown')}"
        soon = "||**Coming Soon:**"
        for language, name in languages.items():
            if language not in self.bot.cah_packs:
                soon += f"\n:flag_{language}: {name}"
        language = self.languages.read_key(ctx.guild.id) if ctx.guild else None
        title = f"{self.bot.emotes['choice']} All available languages:"
        if language is not None:
            title += f" (You currently have your language set to :flag_{language}:)"
        if ctx.channel.permissions_for(ctx.author).manage_guild:
            menu = input.Menu(
                self.bot,
                callbacks=False,
                emojify=True
            )  # Create our reaction menu
            for language in self.bot.cah_packs:
                menu.add(flag.flag(language))
            msg = await ctx.send(
                supported + "\n\n" + soon + "||\n\n*Select a flag below (or say it in chat) to set it as the default "
                "language for this server*",
                title=title
            )
            try:
                emote = flag.dflagize(
                    await menu(
                        msg,
                        ctx.author
                    )
                )[1:-1].lower()
                self.languages.save_key(ctx.guild.id, emote)
                await ctx.send(
                    "We've successfully changed your language",
                    title=f":flag_{emote}: Language changed"
                )
            except TimeoutError:
                pass
            finally:
                with contextlib.suppress(discord.NotFound):
                    await msg.delete()
        else:
            await ctx.send(
                supported + "\n\n" + soon + "||",
                title=title
            )


    @commands.command(aliases=["listpacks", "list"])
    async def packs(self, ctx):
        """Shows a list of packs avaliable in your language.
        """
        lang = (self.languages.read_key(ctx.guild.id) if ctx.guild else None) or default_lang

        packs = "*Language switching is currently in beta while we wait on our translators and give the commands a " \
                "good test*"

        lang_packs = self.bot.cah_packs.get(lang, None)
        if not lang_packs:
            lang = default_lang
            lang_packs = self.bot.cah_packs.get(lang, None)

        for pack in lang_packs["packs"]:
            if pack.endswith("w"):
                packs += f"\n~ **{pack[:-1]}** - {lang_packs['descriptions'].get(pack[:-1], 'No description found')}"

        await ctx.send(
            packs,
            title=f":flag_{lang}: All the packs available for your language",
            paginate_by="\n",
            color=ctx.bot.colors["info"]
        )

    def _load_packs(self):
        packs = {}
        for path, _, files in os.walk("packs"):
            lang = path.replace("\\", "/").split("/")[-1]
            if files:
                lang_packs = {
                    "packs": {},
                    "descriptions": {}
                }
                for pack in sorted(files):
                    with open(os.path.join(path, pack)) as file:
                        if pack == "-descriptions.txt":
                            descriptions = [
                                desc.strip().split(
                                    ":", 1
                                ) for desc in file.readlines() if len(desc.strip().split(
                                    ":", 1
                                ))
                            ]
                            lang_packs["descriptions"] = dict(descriptions)
                        pack_name = ".".join(pack.split(".")[:-1])
                        lang_packs["packs"][pack_name] = [card.strip() for card in file.readlines()]
                packs[lang] = lang_packs
        self.bot.set(
            "cah_packs",
            packs
        )

    @commands.command(aliases=["start"])
    @commands.check(no_cah_in_channel)
    @commands.check(checks.bypass_check(allow_runs))
    @commands.guild_only()
    async def play(self, ctx, advanced: typing.Optional[bool] = False, whitelist: commands.Greedy[discord.Member] = ()):
        """Starts the game.
        `%%play` will start a game, and allow players to join using the %%join command, or do %%play True for even more
        game options.
        """
        self.bot.running_cah_games += 1
        try:
            _game = game.Game(
                context=ctx,
                advanced_setup=advanced,
                whitelist=whitelist,
                lang=(self.languages.read_key(ctx.guild.id) if ctx.guild else None) or default_lang
            )
            self.bot.running_cah_game_objects[ctx.channel] = _game
            with contextlib.suppress(asyncio.CancelledError):
                _game.coro = asyncio.create_task(_game.setup())
                if await _game.coro:
                    await _game.begin()
            with contextlib.suppress(KeyError):
                del self.bot.running_cah_game_objects[ctx.channel]
            self.bot.running_cah_games -= 1
        except Exception as e:
            raise e

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.channel, wait=True)
    async def join(self, ctx):
        """Joins an active game in the channel. This can be during the 1m period when starting a game, or midway through.
        """
        _game = self.bot.running_cah_game_objects.get(ctx.channel, None)
        if _game is None:
            return await ctx.send(
                "There doesn't seem to be a game in this channel",
                title=f"{ctx.bot.emotes['valueerror']} No game",
                color=ctx.bot.colors["error"]
            )
        if _game.whitelisted_players and ctx.author not in _game.whitelisted_players:
            return await ctx.send(
                "You aren't whitelisted so you can't join this game",
                title=f"{ctx.bot.emotes['valueerror']} Couldn't join...",
                color=ctx.bot.colors["error"]
            )
        if len(_game.players) >= _game.maximumPlayers:
            return await ctx.send(
                f"For safe social distancing we can't have more than {_game.maximumPlayers} in this game",
                # TODO: ^ Change this when corona becomes irrelevant
                title=f"{ctx.bot.emotes['valueerror']} It's a bit busy round here...",
                color=ctx.bot.colors["error"]
            )
        if any(_player == ctx.author for _player in _game.players):
            return await ctx.send(
                f"You're already in this game, I haven't added you but you're still in there anyway...",
                title=f"{ctx.bot.emotes['valueerror']} *Confused applause*",
                color=ctx.bot.colors["error"]
            )
        if _game.joined:
            await _game.add_player(ctx.author)

    @commands.command(aliases=["leave"])
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def exit(self, ctx):
        """Removes the player who ran it from the current game in that channel.
        """
        _game = self.bot.running_cah_game_objects.get(ctx.channel, None)
        if _game is None:
            return await ctx.send(
                "There doesn't seem to be a game in this channel",
                title=f"{ctx.bot.emotes['valueerror']} No game",
                color=ctx.bot.colors["error"]
            )
        if not _game.chosen_options:
            return await ctx.send(
                "This game isn't setup yet",
                title=f"{ctx.bot.emotes['valueerror']} I'm not ready yet...",
                color=ctx.bot.colors["error"]
            )
        for player in _game.players:
            if player == ctx.author:
                await player.quit()
                break
        else:
            return await ctx.send(
                f"You're not in this game... I couldn't remove you but I guess that doesn't matter much",
                title=f"{ctx.bot.emotes['valueerror']} *Confused applause*",
                color=ctx.bot.colors["error"]
            )

    @commands.command(aliases=["mulligan"])
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def shuffle(self, ctx):
        """Reshuffles your cards
        """
        _game = self.bot.running_cah_game_objects.get(ctx.channel, None)
        if _game is None:
            return await ctx.send(
                "There doesn't seem to be a game in this channel",
                title=f"{ctx.bot.emotes['valueerror']} No game",
                color=ctx.bot.colors["error"]
            )
        if not _game.chosen_options:
            return await ctx.send(
                "This game isn't setup yet",
                title=f"{ctx.bot.emotes['valueerror']} I'm not ready yet...",
                color=ctx.bot.colors["error"]
            )
        for player in _game.players:
            if player == ctx.author:
                await player.shuffle(ctx)
                break
        else:
            return await ctx.send(
                f"You're not in this game. Not only can I not shuffle your cards: you don't even have any cards to "
                f"shuffle",
                title=f"{ctx.bot.emotes['valueerror']} *Not sure what's going on here...*",
                color=ctx.bot.colors["error"]
            )

    @commands.command()
    @commands.guild_only()
    async def end(self, ctx, instantly: typing.Optional[bool] = False):
        """Ends the current game in that channel.
        """
        old_game = self.bot.running_cah_game_objects.get(ctx.channel, None)
        if old_game is not None:
            if not (ctx.author.permissions_in(ctx.channel).manage_channels or ctx.author == old_game.context.author):
                return await ctx.send(
                    "You didn't start this game, and you can't manage this channel",
                    title=f"{ctx.bot.emotes['valueerror']} You don't have permission to do that",
                    color=ctx.bot.colors["error"]
                )
            with contextlib.suppress(Exception):
                del self.bot.running_cah_game_objects[ctx.channel]
                await old_game.end(instantly=instantly)
        else:
            await ctx.send(
                "Has it already been ended?",
                title=f"{ctx.bot.emotes['valueerror']} We couldn't find a game in this channel...",
                color=ctx.bot.colors["error"]
            )

    @commands.command()
    @commands.guild_only()
    @commands.check(checks.bot_mod)
    async def setmaxplayers(self, ctx, new_max=25):
        """Set the maximum player count of the game. Can only be used in setup and when players are joining
        """
        _game = self.bot.running_cah_game_objects.get(ctx.channel, None)
        if _game is None:
            return await ctx.send(
                "Did you mean another channel?",
                title=f"{ctx.bot.emotes['valueerror']} We couldn't find a game in this channel...",
                color=ctx.bot.colors["error"]
            )
        _game.maximumPlayers = new_max
        _game.players = _game.players[:new_max]
        if new_max < _game.minimumPlayers:
            return await ctx.send(
                f"The minimum minimum player count is {_game.minimumPlayers}",
                title=f"{ctx.bot.emotes['valueerror']} Bit to small...",
                color=ctx.bot.colors['error']
            )
        if _game.chosen_options:
            return await ctx.send(
                f"This command can only be used before players are given the option to join",
                title=f"{ctx.bot.emotes['valueerror']} You're too late",
                color=ctx.bot.colors['error']
            )
        await ctx.send(
            f"We've set the player limit on this game to {new_max} and kicked out any players who bring the game over "
            f"that limit",
            title=f"{ctx.bot.emotes['success']}  Great!",
            color=ctx.bot.colors['status']
        )

    @commands.command(aliases=["bc", "sall"])
    @commands.check(checks.is_owner)
    async def broadcast(self, ctx, nostart: typing.Optional[bool] = True, *, message):
        """Broadcasts a message to every currently active game channel.
        """
        if nostart:
            self.bot.allow_running_cah_games = False
            await self.bot.change_presence(
                status=discord.Status.dnd,
                activity=discord.Activity(
                    name="my developers in maintenance mode",
                    type=discord.ActivityType.listening,
                )
            )
        for _game in self.bot.running_cah_game_objects.values():
            with contextlib.suppress(Exception):
                await _game.context.send(
                    message,
                    title="Developer broadcast - Because you're playing CAH here...",
                    color=ctx.bot.colors["dev"]
                )
        await ctx.send(
            message,
            title="Sent to every server currently ingame..."
        )

    @commands.command(aliases=["denystart", "stopstart"])
    @commands.check(checks.is_owner)
    async def nostart(self, ctx, end: typing.Optional[bool] = False, instantly: typing.Optional[bool] = False):
        """Stops games from being played
        """
        self.bot.allow_running_cah_games = False
        await self.bot.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                name="my developers in maintenance mode",
                type=discord.ActivityType.listening,
            )
        )
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
        """Allows games to be started.
        """
        self.bot.allow_running_cah_games = True
        await self.bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                name="your games of CAH",
                type=discord.ActivityType.watching,
            )
        )
        await ctx.send(
            "Games can be started again",
            title="Action complete!"
        )


def setup(bot):
    errors.setup_handlers(bot.error_handler)
    bot.add_cog(CAH(bot))
