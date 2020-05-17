from discord.ext import commands
import contextlib
import re
import datetime
import discord
from utils import help, checks
from utils.miniutils import minidiscord, data, classes
import traceback
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import io


class Info(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.prefixes = data.Json("prefixes")
        self.tos_agrees = data.Json("disclaimer")

    @commands.command()
    @commands.guild_only()
    @commands.check(checks.bypass_check(commands.has_permissions(manage_guild=True)))
    async def setprefix(self, ctx, *new_prefixes):
        """Changes the prefixes of the bot in this guild. Pass as many prefixes as you like separated by spaces. \
    If you want a multi-word prefix enclose it in speech marks"""
        new_prefixes = [prefix[:20] for prefix in new_prefixes]
        if new_prefixes:
            self.prefixes.save_key(
                ctx.guild.id,
                new_prefixes
            )
            await ctx.send(
                "\n".join(f"- `{prefix}`" for prefix in self.prefixes.read_key(ctx.guild.id)),
                title="Here are your fancy new prefixes!",
                color=self.bot.colors["status"]
            )
        else:
            self.prefixes.remove_key(
                ctx.guild.id
            )
            await ctx.send(
                f"You're back to default prefix of {self.bot.main_prefix}",
                title="Your custom prefixes have been removed!",
                color=self.bot.colors["status"]
            )


    @commands.command()
    @commands.guild_only()
    async def getprefix(self, ctx):
        """Shows the bots prefix in the current guild"""
        custom_prefixes = self.prefixes.read_key(ctx.guild.id)
        if custom_prefixes:
            await ctx.send(
                "\n".join(f"- `{prefix}`" for prefix in self.prefixes.read_key(ctx.guild.id)),
                title="Here are your prefixes!",
                color=self.bot.colors["status"]
            )
        else:
            await ctx.send(
                "There's nothing to show you here...",
                title="You don't have any custom prefixes",
                color=self.bot.colors["status"]
            )


    @commands.command()
    async def info(self, ctx):
        """View some information about the bot's owners"""
        staff = ""
        with contextlib.suppress(AttributeError):
            if self.bot.constants_initialized:
                members = set()
                for title, role in self.bot.staff_roles.items():
                    unique_members = set(role.members).difference(members)
                    staff += (f"\n**{title}**\n" + "\n".join(sorted(
                        ("> " + (
                            re.sub(r"^(\[\S*\] )?(.*)$", r"\2", user.nick) if user.nick is not None else user.name
                        )) for user in unique_members
                    ) if unique_members else ""))
                    members = members.union(unique_members)
                if staff:
                    staff = "> **STAFF**" + staff + "\n\n"
        await ctx.send(
            staff + (
                "> **INVITE ME**\n[discordapp.com]"
                "(https://discordapp.com/oauth2/authorize?"
                "client_id=679361555732627476&scope=bot&permissions=130048)"
                "\n\n> **SERVER**\n[Cardboard Against Humankind Bot](https://discord.gg/bPaNnxe)\n"
                "This bot is not associated with Cards Against Humanity LLC. Major credits to them for creating the "
                "game though!"
            ),
            title='Cardboard Against Humankind - Credits',
            color=self.bot.colors["info"],
            paginate_by="\n"
        )


    @commands.command()
    @commands.check(checks.bot_mod)
    async def skip(self, ctx):
        """Begin skipping bot checks, like permission checks and maintenance checks"""
        if ctx.author in self.bot.skips:
            self.bot.skips.remove(ctx.author)
            await ctx.send(
                "Run this command again to undo",
                title="You're now not skipping checks",
                color=self.bot.colors["status"]
            )
        else:
            self.bot.skips.append(ctx.author)
            await ctx.send(
                "Run this command again to undo",
                title="You're now skipping checks",
                color=self.bot.colors["status"]
            )


    @commands.command(aliases=["statistics", "status"])
    async def stats(self, ctx):
        """Shows the bot's current statistics
        """
        shard_id = ctx.guild.shard_id if ctx.guild is not None else 0
        _shard_name = "???"
        agrees = self.tos_agrees.load_data() or []
        with contextlib.suppress(IndexError):
            _shard_name = self.bot.shard_names[shard_id]
        statistics = f"**Servers:** {len(self.bot.guilds)}\n" \
                     f"**Disclaimer agreements:** {len(agrees)} ({round(len(agrees)/len(self.bot.guilds)*100,2)}%)\n" \
                     f"**Members:** {len(self.bot.users)}\n" \
                     f"**Emojis:** {len(self.bot.emojis)}\n" \
                     f"**Average Ping:** {round(self.bot.latency * 1000, 2)}ms\n" \
                     f"**Shard Ping:** {round(dict(self.bot.latencies)[shard_id] * 1000, 2)}ms\n" \
                     f"**Your Shard:** {_shard_name} ({shard_id + 1}/{len(self.bot.shards)})"
        with contextlib.suppress(AttributeError):
            statistics += f"\n**Games in progress:** {self.bot.running_cah_games}"
            with contextlib.suppress(Exception):
                if self.bot.running_cah_games != len(self.bot.running_cah_game_objects) and checks.bot_mod(ctx):
                    await ctx.send(f"Games according to tally: {self.bot.running_cah_games}\nGames according to objects: {len(self.bot.running_cah_game_objects)}\n\nProceed with caution", title="Warn: The game count may be inaccurate")
        if ctx.guild is None or ctx.channel.permissions_for(ctx.guild.me).attach_files:
            joins_x_values = sorted(server.me.joined_at for server in self.bot.guilds if server.me.joined_at)
            agrees_x_values = sorted(
                datetime.datetime.utcfromtimestamp(server['timestamp']) for server in agrees.values()
            )
            plt.grid(True)
            fig, ax = plt.subplots(figsize=(10, 6))

            merged_x_values = sorted(joins_x_values + agrees_x_values)

            ax.plot(joins_x_values, tuple(range(1, len(joins_x_values) + 1)), 'k', lw=2, label="Servers Joined")
            ax.plot(agrees_x_values, tuple(range(1, len(agrees_x_values) + 1)), 'r', lw=2, label="Disclaimer Agrees")
            if ctx.guild is not None and ctx.guild.me.joined_at is not None:
                ax.scatter([ctx.guild.me.joined_at], joins_x_values.index(ctx.guild.me.joined_at) + 1, lw=4)
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%a %d-%m-%Y"))
            ax.xaxis.set_major_locator(
                mdates.DayLocator(interval=((merged_x_values[-1] - merged_x_values[0]) / 7).days or 1)
            )

            fig.autofmt_xdate()

            plt.title("Bot growth")
            plt.xlabel('Time (UTC)')
            plt.ylabel('Servers')
            plt.legend()
            buf = io.BytesIO()
            fig.savefig(buf, format='png')
            buf.seek(0)
            await ctx.send(
                statistics,
                title="Bot statistics",
                file=discord.File(buf, filename="growth.png"),
                paginate_by="\n",
                color=self.bot.colors["status"]
            )
            buf.close()
            plt.close()
        else:
            await ctx.send(
                statistics,
                title="Bot statistics",
                paginate_by="\n",
                color=self.bot.colors["status"]
            )


    @commands.command(aliases=["pong", "pingpong", "shards"])
    async def ping(self, ctx):
        """Gets the current response time of the bot.
        """
        shard_id = ctx.guild.shard_id if ctx.guild is not None else 0
        shard_name = "???"
        with contextlib.suppress(IndexError):
            shard_name = self.bot.shard_names[shard_id]
        number_of_shards = len(self.bot.shards)
        average_latency = self.bot.latency * 1000
        shard_names = iter(self.bot.shard_names)
        content = (
            f"> You are currently on shard {shard_name} ({shard_id + 1}/{len(self.bot.shards)})\n"
            f"> The average latency is {round(average_latency, 2)}ms\n"
            f"**All Shards:**"
        )
        for shard, latency in self.bot.latencies:
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
            paginate_by="\n",
            color=self.bot.colors["success"]
        )


def setup(bot):
    bot.add_cog(Info(bot))
