from discord.ext import commands
from utils import help
import discord

with open('token.txt', 'r') as f:
  token = [line.strip() for line in f]

production = False
try:
    open("devmode", "r").close()
except FileNotFoundError:
    production = True

main_prefix = "$" if production else "£"
cogs = [
    "jishaku",
    "cogs.cah",
    "guildmanager.cog",
    "cogs.errors",
    "cogs.botlist"
]

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(main_prefix),
    case_insensitive=True,
    help_command=help.HelpCommand(),
    owner_ids=[317731855317336067, 438733159748599813, 261900651230003201],
    activity=discord.Activity(
        name="the whirr of my fans as I boot up and check the status of the website at https://cahdiscord.glitch.me "
             "shameless plug.",
        type=discord.ActivityType.listening
    ),  # We create a discord activity to start up with
    status=discord.Status.idle
)

bot.playing = 0
bot.admins = [] + bot.owner_ids
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
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name="your games of CAH",
            type=discord.ActivityType.watching,
        )
    )


file = open('token.txt', 'r')
bot.tokens = [line.strip() for line in file]
file.close()

bot.run(bot.tokens[0])
