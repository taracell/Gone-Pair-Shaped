from discord.ext import commands
import discord
import typing
from utils import game, checks
from utils.miniutils.minidiscord import minictx
import asyncio
import time


class CardsAgainstHumanity(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}  # type: typing.Dict[discord.TextChannel, game.Game]
        bot.games = self.games
        self.maxPlayers = 25
        self.minPlayers = 3
        bot.allowStart = False
        packs = {
            "base": "Just the basic, base pack",
            "spongebob": "SpongeBob themed cards!",
            "ex1": "The first extension pack.",
            "ex2": "The sequel to the first extension pack.",
            "ex3": "The sequel to the first extension pack, the sequel!",
            "ex4": "Yet another extension pack, but the green box.",
            "ex5": "more",
            "ex6": "Same again.",
            "ex7": "The last expansion pack.",
            "pax": "The PAX convention pack.",
            "base2": "An additional base pack / alternative extension",
            "anime": "Nani?",
            "discord": "A pack we made specially for you, containing cards that we wanted but couldn't quite make an "
                       "excuse to put in the other packs.",
        }
        self.packs = []
        for position, pack_data in enumerate(packs.items()):
            pack_to_read, pack_description = pack_data
            question_cards_in_pack = open(f"packs/{pack_to_read}b.txt", "r")
            answer_cards_in_pack = open(f"packs/{pack_to_read}w.txt", "r")
            self.packs.append(
                (
                    pack_to_read,
                    [card.strip() for card in question_cards_in_pack.readlines()],
                    [card.strip() for card in answer_cards_in_pack.readlines()],
                    pack_description
                )
            )
            question_cards_in_pack.close()
            answer_cards_in_pack.close()

    # @commands.command(aliases=["start"])
    @minictx()
    @commands.guild_only()
    async def play(self, ctx):
        """Play a game
Options can be selected after running this command"""
        await ctx.send(
            f'Waiting for players... If you want to join type `{ctx.bot.main_prefix}join` in this channel',
            color=discord.Color(0xf44336)
        )
        players = [ctx.author]

        def check(message):
            return message.channel == ctx.channel and message.content == ctx.bot.main_prefix + "join"

        expiry = time.time() + 60
        while True:
            try:
                await ctx.bot.wait_for("message", check=check, timeout=expiry)
            except asyncio.TimeoutError:
                break

        await ctx.send(
            f'The game has been created. Before we start, we need to get a few game settings...',
            color=discord.Color(0xf44336)
        )

    @commands.command(name="play", aliases=["start", "lstart", "legacyplay", "legacystart"])
    @minictx()
    @commands.guild_only()
    async def lplay(self,
                    ctx,
                    players: commands.Greedy[discord.Member],
                    score_to_win: typing.Optional[int] = 7,
                    *enabled_packs
                    ):
        """The legacy play command...
Play a game
Run %%play [@ping as many players as you like] [number of rounds, or enter 0 for unlimited (default unlimited)] [packs]
Optionally specify how many points a player needs to win (default is 7)
Note: press 0 to have an endless game
Optionally specify which packs to include (run %%packs to view all the options or enter all to go crazy)"""
        if not self.bot.allowStart:
            return await ctx.send(
                "Unfortunately, we're about to go down and are in maintenance mode waiting for the last few games to "
                "end, you can't start anything right now...",
                title="Try again later...",
                color=discord.Color(0xf44336)
            )
        players = [user for user in players if not user.bot]
        players.append(ctx.author)
        players = set(players)
        if len(players) < self.minPlayers:
            return await ctx.send(
                f'There too few players in this game. '
                f'Please ping a minimum of {self.minPlayers - 1} '
                f'people for a {self.minPlayers} player game',
                color=discord.Color(0xf44336)
            )
        if len(players) > self.maxPlayers:
            return await ctx.send(
                f'There too many players in this game. '
                f'Please ping a maximum of {self.maxPlayers - 1} '
                f'people for a {self.maxPlayers} player game',
                color=discord.Color(0xf44336)
            )

        if self.games.get(ctx.channel, None):
            await ctx.send(
                f'A game is already in progress',
                color=discord.Color(0xf44336)
            )

        self.games[ctx.channel] = game.Game(
            ctx,
            players,
            self.packs,
            enabled_packs,
            score_to_win if score_to_win > 0 else None,
            self.minPlayers,
            self.maxPlayers
        )
        await self.games[ctx.channel].start()
        del self.games[ctx.channel]

    @commands.command()
    @minictx()
    @commands.guild_only()
    async def end(self, ctx, force=False):
        """End the game
Optionally run '%%end True' to end the game instantly (WIP, doesn't work yet)
Note- You must have manage channels or be playing to end the game"""
        channel_game = self.games.get(ctx.channel, None)
        if not channel_game:
            await ctx.send(
                f"There isn't an active game in this channel",
                color=discord.Color(0xf44336)
            )
        if (
                channel_game.players and ctx.author not in [user.member for user in channel_game.players]
        ) and not ctx.author.permissions_in(ctx.channel).manage_channels:
            return await ctx.send(
                "You aren't playing and you don't have manage channels, so you can't end this game...",
                color=discord.Color(0xf44336)
            )
        await channel_game.end(force)

    @commands.command()
    @minictx()
    async def packs(self, ctx):
        """Shows a list of packs to enable and disable in the game
    They are added when using the %%play command"""
        ctx.send(
            'Do $play {@ people} {packs} to activate specific packs. '
            'If no packs are chosen, base only will be selected. '
            'Alternatively, setting the pack to "all" will enable all packs.\n\n'
            + "\n".join(f"{pack[0]}: {pack[3]}" for pack in self.packs),
            title=f'Packs ( {len(self.packs)} )',
            color=discord.Color(0xf44336)
        )

    @commands.command()
    @minictx()
    async def legal(self, ctx):
        """Shows all the legal notices about Cards Against Humanity Creative Commons. We know you won't do this."""
        embed = discord.Embed(
            title=f'Legal notices',
            description='[✔ NonCommercial] Firstly, this bot is not designed to make money.\n'
                        '[✔ Attribution] This bot is based off the concept by Cards Against Humanity LLC. \n'
                        '[✔ ShareAlike] This bot uses the same licence as the original game, '
                        '[Creative Commons by-nc-sa 2.0](https://creativecommons.org/licenses/by-nc-sa/2.0/)',
            color=discord.Color(0xf44336)
        )
        await ctx.channel.send(embed=embed)

    @commands.command()
    @minictx()
    async def stats(self, ctx):
        """Shows the stats of the bot."""
        await ctx.send(
            f'Servers: {len(self.bot.guilds)}\n'
            f'Members: {len(self.bot.users)}\n'
            f'Games being played: {len(self.games)}',
            title=f'Stats',
            color=discord.Color(0xf44336)
        )

    @commands.command()
    @minictx()
    @commands.check(checks.is_owner)
    async def endall(self, ctx):
        """Shows the stats of the bot."""
        self.bot.allowStart = False
        for playingGame in self.games.values():
            await playingGame.end(True)
        await ctx.send(
            f'Force-ended all games & disabled starting new ones',
            title=f'Games will end soon',
            color=discord.Color(0xf44336)
        )

    @commands.command()
    @minictx()
    @commands.check(checks.is_owner)
    async def allowstart(self, ctx):
        """Shows the stats of the bot."""
        self.bot.allowStart = True
        await ctx.send(
            f'Games can be started again',
            title=f'You can play again :tada:',
            color=discord.Color(0xf44336)
        )


def setup(bot: commands.Bot):
    bot.add_cog(CardsAgainstHumanity(bot))
