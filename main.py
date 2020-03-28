import discord
from discord.ext import commands
import sys
from utils import help, checks
from utils.miniutils import minidiscord, data
import traceback
import contextlib

with open('token.txt') as f:
    token = [line.strip() for line in f]

production = False
try:
    open("devmode").close()
except FileNotFoundError:
    production = True

main_prefix = "$" if production else "£"
cogs = [
    "jishaku",
    "cogs.cah",
    "guildmanager.cog",
    "cogs.errors",
    "cogs.botlist",
    "utils.constants",
]

prefixes = data.Json("prefixes")


def get_command_prefix(_bot, message):
    if message.guild:
        custom_prefixes = prefixes.read_key(message.guild.id)
        if custom_prefixes:
            return commands.when_mentioned_or(*custom_prefixes)(_bot, message)
    return commands.when_mentioned_or(main_prefix)(_bot, message)


def get_main_custom_prefix(message):
    if message.guild:
        custom_prefixes = prefixes.read_key(message.guild.id)
        if custom_prefixes:
            return custom_prefixes[0]
    return bot.main_prefix


bot = minidiscord.AutoShardedBot(
    command_prefix=get_command_prefix,
    case_insensitive=True,
    help_command=help.HelpCommand(),
    owner_ids=[317731855317336067, 438733159748599813, 261900651230003201, 421698654189912064],
    activity=discord.Activity(
        name="discord go by.",
        type=discord.ActivityType.watching
    ),  # We create a discord activity to start up with
    status=discord.Status.idle
)

bot.prefixes = prefixes
bot.get_main_custom_prefix = get_main_custom_prefix

bot.playing = 0
bot.admins = [] + bot.owner_ids
bot.skips = []

bot.main_prefix = main_prefix


@bot.event
async def on_ready():
    print(f'Logged in successfully as {bot.user} with {bot.loaded} cogs')
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            name="your games of CAH",
            type=discord.ActivityType.watching,
        )
    )


@bot.command()
@commands.guild_only()
@checks.bypass_check(checks.has_permissions_predicate, manage_guild=True)
async def setprefix(ctx, *new_prefixes):
    """Changes the prefixes of the bot in this guild. Pass as many prefixes as you like separated by spaces. \
If you want a multi-word prefix enclose it in speech marks or quotation marks"""
    if new_prefixes:
        prefixes.save_key(
            ctx.guild.id,
            new_prefixes
        )
        await ctx.send(
            "\n".join(f"- `{prefix}`" for prefix in prefixes.read_key(ctx.guild.id)),
            title="Here are your fancy new prefixes!"
        )
    else:
        prefixes.remove_key(
            ctx.guild.id
        )
        await ctx.send(
            f"You're back to default prefix of {bot.main_prefix}",
            title="Your custom prefixes have been removed!"
        )


@bot.command()
@commands.guild_only()
async def getprefix(ctx):
    """Shows the bots prefix in the current guild"""
    custom_prefixes = prefixes.read_key(ctx.guild.id)
    if custom_prefixes:
        await ctx.send(
            "\n".join(f"- `{prefix}`" for prefix in prefixes.read_key(ctx.guild.id)),
            title="Here are your prefixes!"
        )
    else:
        await ctx.send(
            "There's nothing to show you here...",
            title="You don't have any custom prefixes"
        )


@bot.command()
async def info(ctx):
    """View some information about the bot's owners"""
    staff = ""
    with contextlib.suppress(AttributeError):
        if bot.constants_initialized:
            members = set()
            for title, role in bot.staff_roles.items():
                unique_members = set(role.members).difference(members)
                staff += (f"\n**{title}**\n" + "\n".join(
                    "> " + str(user) for user in unique_members
                ) if unique_members else "")
                members = members.union(unique_members)
            if staff:
                staff = "> **STAFF**" + staff + "\n\n"
    embed = discord.Embed(
        title='Cards Against Humanity - Commands',
        description=staff + (
            "> **INVITE ME**\n[discordapp.com]"
            "(https://discordapp.com/oauth2/authorize?"
            "client_id=679361555732627476&scope=bot&permissions=130048)"
            "\n\n> **SERVER**\n[Cards Against Humanity Bot](https://discord.gg/bPaNnxe)"
        ),
        color=bot.colors["success"]
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.check(checks.bot_mod)
async def skip(ctx):
    """Begin skipping bot checks, like permission checks and maintenance checks"""
    if ctx.author in bot.skips:
        bot.skips.remove(ctx.author)
        await ctx.send(
            "Run this command again to undo",
            title="You're now not skipping checks"
        )
    else:
        bot.skips.append(ctx.author)
        await ctx.send(
            "Run this command again to undo",
            title="You're now skipping checks"
        )


with open('token.txt') as tokens:
    bot.tokens = dict(line.strip().split(":", 1) for line in tokens.readlines())

bot.loaded = 0
for position, cog in enumerate(cogs):
    try:
        bot.load_extension(cog)
        bot.loaded += 1
        print(f"Loaded {cog} (cog {position + 1}/{len(cogs)}, {bot.loaded} successful)")
    except Exception as e:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        print(f"Failed to load {cog} (cog {position + 1}/{len(cogs)}), Here's the error: {e}")
        print("- [x] " + "".join(traceback.format_tb(exc_traceback)).replace("\n", "\n- [x] "))

bot.run(bot.tokens["discord"])
