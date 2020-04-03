import discord
from discord.ext import commands
import sys
from utils import help, checks
from utils.miniutils import minidiscord, data
import traceback
import contextlib
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io

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
    "guildmanager.cog",
    "cogs.cah",
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
    if bot.__dict__.get("allow_running_cah_games", True):
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
            title="Here are your fancy new prefixes!",
            color=bot.colors["status"]
        )
    else:
        prefixes.remove_key(
            ctx.guild.id
        )
        await ctx.send(
            f"You're back to default prefix of {bot.main_prefix}",
            title="Your custom prefixes have been removed!",
            color=bot.colors["status"]
        )


@bot.command()
@commands.guild_only()
async def getprefix(ctx):
    """Shows the bots prefix in the current guild"""
    custom_prefixes = prefixes.read_key(ctx.guild.id)
    if custom_prefixes:
        await ctx.send(
            "\n".join(f"- `{prefix}`" for prefix in prefixes.read_key(ctx.guild.id)),
            title="Here are your prefixes!",
            color=bot.colors["status"]
        )
    else:
        await ctx.send(
            "There's nothing to show you here...",
            title="You don't have any custom prefixes",
            color=bot.colors["status"]
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
    await ctx.send(
        staff + (
            "> **INVITE ME**\n[discordapp.com]"
            "(https://discordapp.com/oauth2/authorize?"
            "client_id=679361555732627476&scope=bot&permissions=130048)"
            "\n\n> **SERVER**\n[Cards Against Humanity Bot](https://discord.gg/bPaNnxe)\n"
            "This bot is not associated with Cards Against Humanity LLC. Major credits to them for creating the game "
            "though!"
        ),
        title='Cards Against Humanity - Credits',
        color=bot.colors["info"],
        paginate_by="\n"
    )


@bot.command()
@commands.check(checks.bot_mod)
async def skip(ctx):
    """Begin skipping bot checks, like permission checks and maintenance checks"""
    if ctx.author in bot.skips:
        bot.skips.remove(ctx.author)
        await ctx.send(
            "Run this command again to undo",
            title="You're now not skipping checks",
            color=bot.colors["status"]
        )
    else:
        bot.skips.append(ctx.author)
        await ctx.send(
            "Run this command again to undo",
            title="You're now skipping checks",
            color=bot.colors["status"]
        )


@bot.command(aliases=["statistics", "status"])
async def stats(ctx):
    """Shows the bot's current statistics
    """
    shard_id = ctx.guild.shard_id if ctx.guild is not None else 0
    _shard_name = "???"
    with contextlib.suppress(IndexError):
        _shard_name = bot.shard_names[shard_id]
    statistics = f"**Servers:** {len(bot.guilds)}\n" \
                 f"**Members:** {len(bot.users)}\n" \
                 f"**Emojis:** {len(bot.emojis)}\n" \
                 f"**Average Ping:** {round(bot.latency * 1000, 2)}ms\n" \
                 f"**Shard Ping:** {round(dict(bot.latencies)[shard_id] * 1000, 2)}ms\n" \
                 f"**Your Shard:** {_shard_name} ({shard_id + 1}/{len(bot.shards)})"
    with contextlib.suppress(AttributeError):
        statistics += f"\n**Games in progress:** {bot.running_cah_games}"
    if ctx.guild is None or ctx.channel.permissions_for(ctx.guild.me).attach_files:
        x_values = sorted(server.me.joined_at for server in bot.guilds if server.me.joined_at)
        plt.grid(True)
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(x_values, tuple(range(1, len(x_values) + 1)), 'k', lw=2)
        if ctx.guild is not None and ctx.guild.me.joined_at is not None:
            ax.scatter([ctx.guild.me.joined_at], x_values.index(ctx.guild.me.joined_at) + 1, lw=4)
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d-%m-%Y"))
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=((x_values[-1] - x_values[0]) / 7).days or 1))

        fig.autofmt_xdate()

        plt.title("Bot growth")
        plt.xlabel('Time')
        plt.ylabel('Servers')
        buf = io.BytesIO()
        fig.savefig(buf, format='png')
        buf.seek(0)
        await ctx.send(
            statistics,
            title="Bot statistics",
            file=discord.File(buf, filename="growth.png"),
            paginate_by="\n",
            color=bot.colors["status"]
        )
        buf.close()
        plt.close()
    else:
        await ctx.send(
            statistics,
            title="Bot statistics",
            paginate_by="\n",
            color=bot.colors["status"]
        )


@bot.command(aliases=["pong", "pingpong", "shards"])
async def ping(ctx):
    """Gets the current response time of the bot.
    """
    shard_id = ctx.guild.shard_id if ctx.guild is not None else 0
    shard_name = "???"
    with contextlib.suppress(IndexError):
        shard_name = bot.shard_names[shard_id]
    number_of_shards = len(bot.shards)
    average_latency = bot.latency * 1000
    shard_names = iter(bot.shard_names)
    content = (
        f"> You are currently on shard {shard_name} ({shard_id + 1}/{len(bot.shards)})\n"
        f"> The average latency is {round(average_latency, 2)}ms\n"
        f"**All Shards:**"
    )
    for shard, latency in bot.latencies:
        lag_difference = round(latency * 1000 - average_latency, 2)
        lag_difference_symbol = ''
        if lag_difference == 0:
            lag_difference_symbol = '±'
        elif lag_difference > 0:
            lag_difference_symbol = '+'
        # Minus signs will already be included in the float
        content += (
            f"\n{next(shard_names, '???')} - {round(latency * 1000, 2)}ms "
            f"({shard + 1}/{number_of_shards}, {lag_difference_symbol}{lag_difference}ms from average)"
        )
    await ctx.send(
        content,
        title="Shard pings",
        paginate_by="\n"
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
        print(f"Failed to load {cog} (cog {position + 1}/{len(cogs)}), Here's the error: {e}")
        print("- [x] " + "".join(traceback.format_exc()).replace("\n", "\n- [x] "))

bot.run(bot.tokens["discord"])
