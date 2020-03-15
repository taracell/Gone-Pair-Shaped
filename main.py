import discord
from discord.ext import commands
from utils import help

maxPlayers = 10
minPlayers = 3

production = False
try:
    open("devmode", "r").close()
except FileNotFoundError:
    production = True

main_prefix = "$" if production else "£"
cogs = [
    "jishaku",
    "cogs.cah",
    "cogs.management",
    "cogs.errors"
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
