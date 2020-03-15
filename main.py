import discord
from discord.ext import commands
from utils import help

maxPlayers = 10
minPlayers = 3

with open('token.txt', 'r') as f:
  token = [line.strip() for line in f]

production = False
try:
    open("devmode", "r").close()
except FileNotFoundError:
    production = True

main_prefix = "$" if production else "£"
cogs = [
<<<<<<< HEAD
    "jishaku",
    "cogs.cah",
    "cogs.management",
    "cogs.errors"
=======
  "jishaku",
  "cogs.cah",
  "cogs.management",
  "cogs.errors",
  "cogs.botlist"
>>>>>>> 2ab7ff3eb34b00155b9b80c34ffe7f7d96103a85
]

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(main_prefix),
    case_insensitive=True,
    help_command=help.HelpCommand(),
    owner_ids=[317731855317336067, 438733159748599813, 261900651230003201]
)
# bot.owner_ids.remove(438733159748599813)  # Uncomment on dragdev

bot.admins = [438733159748599813] + bot.owner_ids
bot.skips = []

bot.main_prefix = main_prefix

<<<<<<< HEAD
=======
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, discord.ext.commands.errors.CommandNotFound):
        return
    elif isinstance(error, discord.ext.commands.errors.NoPrivateMessage):
        return
    elif isinstance(error, discord.ext.commands.NSFWChannelRequired):
      embed = discord.Embed(
        title=f'This is not an NSFW channel.',
        color=discord.Color(0xf44336)
      )
      await ctx.send(embed=embed)
      return
    else:
      raise error
>>>>>>> 2ab7ff3eb34b00155b9b80c34ffe7f7d96103a85

@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user}')
    success = 0
    for position, cog in enumerate(cogs):
        try:
            bot.load_extension(cog)
            success += 1
            print(f"Loaded {cog} (cog {position + 1}/{len(cogs)}, {success} successful)")
        except Exception as e:
            print(f"Failed to load {cog} (cog {position + 1}/{len(cogs)}), Here's the error: {e}")


file = open('token.txt', 'r')
bot.tokens = [line.strip() for line in file]
file.close()

bot.run(bot.tokens[0])
