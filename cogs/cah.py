from discord.ext import commands
import discord
import typing
from utils import game


class CardsAgainstHumanity(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.games = {}  # type: typing.Dict[discord.TextChannel, game.Game]
    self.maxPlayers = 15
    self.minPlayers = 3
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
      "discord": "A pack we made specially for you, containing cards that we wanted but couldn't quite make an excuse "
                 "to put in the other packs.",
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

  @commands.command(aliases=["start"])
  @commands.guild_only()
  @commands.is_nsfw()
  async def play(self, ctx):
    """Play a game
Options can be selected after running this command"""
    embed = discord.Embed(
      description=f'Waiting for players... If you want to join type `$join` in this channel',
      color=discord.Color(0xf44336)
    )
    await ctx.channel.send(embed=embed)
    while True:


  @commands.command(aliases=["lstart", "legacyplay", "legacystart"])
  @commands.guild_only()
  @commands.is_nsfw()
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
    players = [user for user in players if not user.bot]
    players.append(ctx.author)
    players = set(players)
    if len(players) < self.minPlayers:
      embed = discord.Embed(
        description=f'There too few players in this game. '
                    f'Please ping a minimum of {self.minPlayers - 1} '
                    f'people for a {self.minPlayers} player game',
        color=discord.Color(0xf44336)
      )
      return await ctx.channel.send(embed=embed)
    if len(players) > self.maxPlayers:
      embed = discord.Embed(
        description=f'There too many players in this game. '
                    f'Please ping a maximum of {self.maxPlayers - 1} '
                    f'people for a {self.maxPlayers} player game',
        color=discord.Color(0xf44336)
      )
      return await ctx.channel.send(embed=embed)

    if self.games.get(ctx.channel, None):
      return await ctx.channel.send("A game is already in progress.")

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
  @commands.guild_only()
  async def end(self, ctx, force=False):
    """End the game
Optionally run '%%end True' to end the game instantly (WIP, doesn't work yet)
Note- You must have manage channels or be playing to end the game"""
    channel_game = self.games.get(ctx.channel, None)
    if not channel_game:
      return await ctx.send("There doesn't appear to be a game running in this channel...")
    if (
            channel_game.players and ctx.author not in [user.member for user in channel_game.players]
    ) and not ctx.author.permissions_in(ctx.channel).manage_channels:
      return await ctx.send("You aren't playing and you don't have manage channels, so you can't end this game...")
    await channel_game.end(force)

  @commands.command()
  async def packs(self, ctx):
    """Shows a list of packs to enable and disable in the game
    They are added when using the %%play command"""
    embed = discord.Embed(
      title=f'Packs ( {len(self.packs)} )',
      description='Do $play {@ people} {packs} to activate specific packs. '
                  'If no packs are chosen, base only will be selected. '
                  'Alternatively, setting the pack to "all" will enable all packs.\n\n'
                  + "\n".join(f"{pack[0]}: {pack[3]}" for pack in self.packs),
      color=discord.Color(0xf44336)
    )
    await ctx.channel.send(embed=embed)

  @commands.command()
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


def setup(bot: commands.Bot):
  bot.add_cog(CardsAgainstHumanity(bot))
