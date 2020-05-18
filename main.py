"""
GPSBot by Minion3665 and the rest of ClicksMinutePer
This bot is licensed under the Apache2 4.0 sharealike blah blah blah license
Please make sure to credit us if you use our code

Thank you for using GPSBot
"""
# from utils.miniutils.minidiscord import message

import traceback

import discord
import datetime
from discord.ext import commands

from utils import help
from utils.miniutils import classes, data, minidiscord

import asyncio

with open('token.txt') as f:
    token = [line.strip() for line in f]

production = False
try:
    open("devmode").close()
except FileNotFoundError:
    production = True

main_prefix = "$" if production else "£"
cogs = [
    "utils.constants",
    "cogs.info",
    "cogs.terms",
    "jishaku",
    "guildmanager.cog",
    "cogs.gps",
    "cogs.botlist",
]

prefixes = data.Json("prefixes")


def get_command_prefix(_bot, message):
    if message.guild:
        custom_prefixes = prefixes.read_key(message.guild.id)
        if custom_prefixes:
            return commands.when_mentioned_or(*custom_prefixes)(_bot, message)
    return commands.when_mentioned_or(main_prefix, "")(_bot, message)


def get_main_custom_prefix(message):
    if message.guild:
        custom_prefixes = prefixes.read_key(message.guild.id)
        if custom_prefixes:
            return custom_prefixes[0]
    return bot.main_prefix


bot = minidiscord.AutoShardedBot(
    command_prefix=get_command_prefix,
    case_insensitive=True,
    help_command=help.MiniCustomHelp(),
    owner_ids=[317731855317336067, 438733159748599813, 261900651230003201] if production else [317731855317336067],
    exceptions_channel=686285252817059881 if production else 710184847347548181,
    activity=discord.Activity(
        name="Discord go by.",
        type=discord.ActivityType.watching
    ),  # We create a discord activity to start up with
    status=discord.Status.idle
)

bot.prefixes = prefixes
bot.get_main_custom_prefix = get_main_custom_prefix

bot.playing = 0
bot.AIDataStore = data.Json("AIStore" + str(datetime.datetime.utcnow().timestamp()))
bot.AIAnswerStore = data.Json("answers")
bot.AIQuestionStore = data.Json("questions")
bot.admins = [] + bot.owner_ids
bot.skips = []

bot.main_prefix = main_prefix


@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user} with {bot.loaded} cogs')
    if bot.__dict__.get("allow_running_gps_games", True):
        await bot.change_presence(
            status=discord.Status.online,
            activity=discord.Activity(
                name="your games of GPS",
                type=discord.ActivityType.watching,
            )
        )


with open('token.txt') as tokens:
    bot.tokens = classes.ObfuscatedDict(line.strip().split(":", 1) for line in tokens.readlines())

bot.loaded = 0
for position, cog in enumerate(cogs):
    try:
        bot.load_extension(cog)
        bot.loaded += 1
        print(f"Loaded {cog} (cog {position + 1}/{len(cogs)}, {bot.loaded} successful)")
    except Exception as e:
        print(f"Failed to load {cog} (cog {position + 1}/{len(cogs)}), Here's the error: {e}")
        print("- [x] " + "".join(traceback.format_exc()).replace("\n", "\n- [x] "))

loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(bot.start(bot.tokens["discord"]))
except KeyboardInterrupt:
    loop.run_until_complete(bot.logout())
finally:
    print("Bot shutting down: Goodbye!")
