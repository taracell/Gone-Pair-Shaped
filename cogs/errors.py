import discord
from discord.ext import commands
from utils.converters import fix_time
from discord.ext.commands.core import Group, Command
import traceback
import asyncio
import cogs.cah.errors as cah_errors
from cogs import disclaimer

exceptions_channel_id = 686285252817059881


async def send_help(ctx, send_to, *args):
    ctx.channel = send_to
    bot = ctx.bot
    cmd = bot.help_command
    if cmd is None:
        return None
    cmd = cmd.copy()
    cmd.context = ctx
    if len(args) == 0:
        await cmd.prepare_help_command(ctx, None)
        mapping = cmd.get_bot_mapping()
        return await cmd.send_bot_help(mapping)
    entity = args[0]
    if entity is None:
        return None
    if isinstance(entity, str):
        entity = bot.get_cog(entity) or bot.get_command(entity)
    try:
        qualified_name = entity.qualified_name
    except AttributeError:
        # if we're here then it's not a cog, group, or command.
        return None
    await cmd.prepare_help_command(ctx, entity.qualified_name)
    if hasattr(entity, '__cog_commands__'):
        return await cmd.send_cog_help(entity)
    elif isinstance(entity, Group):
        return await cmd.send_group_help(entity)
    elif isinstance(entity, Command):
        return await cmd.send_command_help(entity)
    else:
        return None


class Blacklisted(commands.CheckFailure):
    def __init__(self, user: discord.User, server: discord.guild, reason: str = None):
        self.reason = reason

    def __str__(self):
        return f"Sorry... Something around here is blacklisted. reason: {self.reason}\n" \
               f"Want to appeal? Go to the support guild at https://discord.gg/bPaNnxe"

    def __int__(self):
        return 403


class BlacklistedGuild(commands.CheckFailure):
    def __init__(self, user: discord.User, server: discord.guild, reason: str = None):
        self.reason = reason
        self.server = server

    def __str__(self):
        return f"Sorry, but the server {self.server.name} is blacklisted. reason: {self.reason}\n" \
               f"Want to appeal? Get {self.server.owner.display_name} to go to the support guild at " \
               f"https://discord.gg/bPaNnxe "


class BlacklistedUser(Blacklisted):
    def __init__(self, user: discord.User, reason: str = None):
        self.user = user
        self.reason = reason

    def __str__(self):
        return f"Sorry {self.user.display_name}, but you are blacklisted. reason: {self.reason}\nWant to appeal? " \
               f"go to the support guild at https://discord.gg/bPaNnxe"


class PremiumOnly(Blacklisted):
    def __str__(self):
        return "Only premium members can run this command!"


class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.error_channel = bot.get_channel(613073501372416000)
        self.default_responses = {
            BlacklistedUser: "Sorry {author.name}, but you are banned from using this bot for: `{reason}`. If"
                             " You believe this was unfair, please ping my developer.",
            BlacklistedGuild: "Sorry {author.name}, but this guild has been banned from using this bot for: `{reason}`."
                              " Please ask the owner to appeal this with the developer.",
            commands.NoPrivateMessage: "This command can't be run in DMs. try running it in a server?"
        }

    @commands.Cog.listener(name="on_command_error")
    async def error_handler(self, ctx, error):
        try:
            ctx = await self.bot.get_context(ctx.message)
            if not ctx.valid:
                return  # If ctx is not valid this means that a command that is not defined was run. Pass
            elif isinstance(error, (commands.BadUnionArgument, commands.BadArgument, commands.MissingRequiredArgument)):
                return await ctx.send(
                    f"Missing or incorrect argument\n(`{str(error)}`)",
                    title=f"{ctx.bot.emotes['error']} Invalid argument",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.TooManyArguments):
                num = len(ctx.command.clean_params)
                return await ctx.send(
                    f"This command takes {num} arguments, but you passed {len(ctx.args) + len(ctx.kwargs)}! if you "
                    f"wanted a sub-command, check the name and try again",
                    title=f"{ctx.bot.emotes['error']} Invalid argument",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, [commands.errors.UnexpectedQuoteError, commands.errors.ExpectedClosingQuoteError]):
                num = len(ctx.command.clean_params)
                return await ctx.send(
                    f"Try surrounding each argument in speech marks (`\"`) and placing backslashes (`\\`) before any "
                    f"speech marks other than surrounding speech marks in your arguments",
                    title=f"{ctx.bot.emotes['error']} Invalid argument",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.NotOwner):
                if ctx.author.id in self.bot.admins:
                    return
                owner_names = str(self.bot.get_user(self.bot.owner_ids[0]))
                for owner in self.bot.owner_ids[1:]:
                    owner_names = owner_names + " or " + str(self.bot.get_user(owner))
                return await ctx.send(
                    f"You must be {owner_names} to run this command!",
                    title=f"{ctx.bot.emotes['error']} No permissions",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, disclaimer.NotAgreedError):
                return await ctx.send(
                    f"Someone who has `manage server` and `manage roles` has to agree to the terms and conditions "
                    f"before you can use this command. They can do this with `{ctx.bot.get_main_custom_prefix(ctx)}"
                    f"terms`",
                    title=f"{ctx.bot.emotes['error']} No permissions",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, disclaimer.NotGuildOwnerError):
                return await ctx.send(
                    f"You're not the owner of this guild, so you can't run this command",
                    title=f"{ctx.bot.emotes['error']} No permissions",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, cah_errors.CantPlayNow):
                return await ctx.send(
                    f"{' '.join(error.args)}",
                    title=f"{ctx.bot.emotes['error']} You can't play now...",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.CommandOnCooldown):
                rem = fix_time(error.retry_after)
                return await ctx.send(
                    f"Oh no! it looks like this command is on a cooldown! try again in `{rem}`!",
                    title=f"{ctx.bot.emotes['error']} Too fast!",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.BotMissingPermissions):
                x = [m.replace('_', ' ') for m in error.missing_perms]
                n = '\n• '
                return await ctx.send(
                    f"I'm' missing the following permissions:\n```\n• {n.join(x)}\n```",
                    title=f"{ctx.bot.emotes['error']} I don't got perms",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.MissingPermissions):
                x = [m.replace('_', ' ') for m in error.missing_perms]
                n = '\n• '
                return await ctx.send(
                    f"You're missing the following permissions:\n```\n• {n.join(x)}\n```",
                    title=f"{ctx.bot.emotes['error']} No permissions",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, asyncio.TimeoutError):
                return await ctx.send(
                    f"This took a bit too long, try again and hope that both you and our servers are "
                    f"faster next time",
                    title=f"{ctx.bot.emotes['error']} Zzzzzzzzz",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.errors.CommandInvokeError) and \
                    isinstance(error.original, (discord.HTTPException, discord.Forbidden)):
                return await ctx.send(
                    f"It looks like I don't have enough permissions to do this. The full error was: "
                    f"{str(error)}",
                    title=f"{ctx.bot.emotes['error']} I don't got perms",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.CheckFailure):
                if 'premium only' in str(error).lower():
                    return await ctx.send(str(error))
                else:
                    return await ctx.send(
                        f"Insufficient permissions to run this command (you don't meet a check)"
                        f"\n(`{str(error)}`)",
                        title=f"{ctx.bot.emotes['error']} No permissions",
                        color=ctx.bot.colors["error"]
                    )

            else:  # unknown error
                print("Got an error: " + str(error) + " of type " + str(type(error)))
                exception_status = "could not be"
                try:
                    exceptions_channel = ctx.bot.get_channel(exceptions_channel_id)
                    paginator = commands.Paginator(prefix='```python\n')
                    for index in range(0, len(str(error)), 1980):
                        paginator.add_line(str(error)[index:index + 1980])
                    try:
                        raise error
                    except Exception:
                        trace = traceback.format_exc()
                    for line in trace.splitlines(keepends=False):
                        paginator.add_line(line)
                    my_permissions = iter(ctx.channel.permissions_for(ctx.me))
                    my_permissions_dict = {}
                    for (permission, value) in my_permissions:
                        my_permissions_dict[permission] = str(value)
                    author_permissions = iter(ctx.channel.permissions_for(ctx.author))
                    author_permissions_dict = {}
                    for (permission, value) in author_permissions:
                        author_permissions_dict[permission] = str(value)
                    for page in paginator.pages:
                        await exceptions_channel.send(page)
                    await exceptions_channel.send(f"> **My permissions:** `{my_permissions_dict}`\n\n"
                                                  f"> **Their permissions:** `{author_permissions_dict}`\n\n"
                                                  f"> **Guild:** {str(ctx.guild or 'No guild')} `ID: {str(ctx.guild.id) if ctx.guild else 'No guild'}`\n\n"
                                                  f"> **Channel:** `ID: {ctx.channel.id if ctx.channel else 'No channel'}`\n\n"
                                                  f"> **User:** {str(ctx.author)} `ID: {str(ctx.author.id)}`\n\n"
                                                  f"> **Command:** {ctx.command.qualified_name} `"
                                                  f"Invoked with: {ctx.invoked_with}, "
                                                  f"Command: {ctx.command.name}`\n"
                                                  f"> **Case ID:** {str(ctx.message.id)[-4:-1]}")
                    exception_status = "has been"
                except Exception as e:
                    print("Could not send an error to the exceptions channel: " + str(e))

                ctx.command.reset_cooldown(ctx)

                e = discord.Embed(title="Oops!",
                                  description=f"It looks like something went wrong. This error {exception_status} "
                                              f"sent to our developers, if you want more help with this command please"
                                              f" report the **Case ID `{str(ctx.message.id)[-4:-1]}`** to our [support "
                                              f"team](https://discord.gg/bPaNnxe)",
                                  color=ctx.bot.colors["error"])
                e.set_footer(text=f"{str(error)}",
                             icon_url='https://cdn.discordapp.com/emojis/459634743181574144.png?v=1')
                try:
                    return await ctx.send(embed=e)
                except discord.HTTPException:
                    try:
                        return await ctx.send(
                            f"There was an error. This error {exception_status} sent to our "
                            f"developers, if you want more help with this command please report the **Case "
                            f"ID `{str(ctx.message.id)[-4:-1]}`** to our support team ||"
                            f"https://discord.gg/bPaNnxe||",
                            title=f"**OOPS!**",
                            color=ctx.bot.colors["error"])
                    except discord.HTTPException:
                        try:
                            if ctx.guild:
                                return await ctx.author.send("Hey! We couldn't access you in " + str(ctx.guild),
                                                             embed=e)
                                # Send to the author's DMs
                        except discord.HTTPException:
                            pass  # There's nothing left to try...
            try:
                return await ctx.send_help(ctx.command)
            except discord.HTTPException:
                try:
                    if ctx.guild:
                        return await send_help(ctx, ctx.author, ctx.command)
                        # Send to the author's DMs
                except discord.HTTPException:
                    pass  # There's nothing left to try...
        except discord.HTTPException as e:
            try:
                await ctx.author.send(f"Hey! We couldn't access you in {str(ctx.guild)} because I don't have "
                                      f"enough permissions to give you the error... Here it is - {str(e)}")
            except discord.HTTPException:
                pass  # There's nothing left to try...


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
