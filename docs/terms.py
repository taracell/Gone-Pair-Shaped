from functools import partial
import asyncio
from discord.ext import commands
import functools
from utils.miniutils.data import json
from utils.miniutils.minidiscord import input
from utils import checks
import contextlib
import datetime
import discord


class Disclaimers(commands.Cog):
    class NotAgreedError(commands.CheckFailure):
        """This error specifies that the guild has not agreed to the disclaimer"""
        pass

    class NotGuildOwnerError(commands.CheckFailure):
        """This error specifies that the executor of the command is not an owner in the guild"""
        pass

    async def NotAgreedCompleteErrorHandler(self, ctx, _error, _next):
        if isinstance(_error, self.NotAgreedError):
            return await ctx.send_exception(
                " ".join(_error.args),
                title=f"You haven't agreed to the terms",
            )
        if isinstance(_error, commands.CommandNotFound):
            return
        if json.Json("disclaimer").read_key(ctx.guild.id) is None:
            await ctx.send_exception(
                f"An error occurred... but I can't help. You have to agree to the terms with the `terms` command "
                f"before I can handle errors properly. If you want help you can go and tell my developers `{_error}` "
                f"in the support server. They'll understand what you mean.",
                title=f"You haven't agreed to the terms",
            )
        else:
            _next(_error)

    @staticmethod
    async def NotGuildOwnerErrorHandler(ctx, _error, _next):
        await ctx.send_exception(
            " ".join(_error.args),
            title=f"No permissions",
        )

    def is_guild_owner(self):
        def predicate(ctx):
            if ctx.guild is not None and ctx.guild.owner_id == ctx.author.id:
                return True
            else:
                raise self.NotGuildOwnerError("You must be the server owner to get the server's info")

        return commands.check(predicate)

    def initial_agree_check(self):
        def predicate(ctx):
            if not ctx.guild:
                return False
            agrees = json.Json("disclaimer").read_key(ctx.guild.id)
            if not agrees:
                raise self.NotAgreedError(
                    "Your guild needs to agree to the terms before this command works in your guild"
                )
            if agrees["member"]["id"] != ctx.author.id:
                return False
            return True

        return commands.check(predicate)

    def __init__(self, bot):
        self.bot = bot
        self.agrees = json.Json("disclaimer")
        self.json_saves = {
            self.agrees,
            json.Json("prefixes"),
            json.Json("languages")
        }
        self.timeout = 300
        bot.check(checks.bypass_check(self.agreed_check()))

    def agreed_check(self):
        def predicate(ctx):
            if not ctx.guild:
                return True
            allowed_commands = [
                "help",
                "terms",
                "info",
                "skip",
                "server"
            ]
            if ctx.command.qualified_name in allowed_commands:
                return True
            if self.agrees.read_key(ctx.guild.id) is not None:
                return True
            if ctx.channel.permissions_for(ctx.author):
                raise self.NotAgreedError(
                    "You must agree to the terms with the `$terms` command before the bot works in this server"
                )
            else:
                raise self.NotAgreedError(
                    "We need someone with `manage server` and `manage roles` to agree to the terms of service before the "
                    "bot works in this server"
                )

        return commands.check(predicate)

    async def agree(self, ctx):
        self.agrees.save_key(
            ctx.guild.id,
            {
                "member": {
                    "id": ctx.author.id,
                    "user": str(ctx.author),
                    "nick": ctx.author.nick,
                },
                "timestamp": datetime.datetime.now().timestamp()
            }
        )
        await ctx.send(
            f"We've enabled all commands for your server. If you change your mind just run the "
            f"`{ctx.bot.get_main_custom_prefix(ctx)}disagree` command and "
            "we'll remove all our data.",
            title="❤️ Thank You"
        )

    async def _disagree(self, ctx):
        for save in self.json_saves:
            save.remove_key(ctx.guild.id)
        await ctx.send(
            "We're sad you didn't want to agree to the terms. If you change your mind later feel free to run the "
            "`terms` command again later. We won't even remember you didn't agree...",
            title="💔 Bye bye"
        )

    @commands.command()
    @commands.guild_only()
    @commands.check_any(commands.check(checks.bypass_check(
        commands.has_permissions(
            manage_guild=True,
            manage_permissions=True
        ))), commands.check(initial_agree_check))
    async def disagree(self, ctx):
        """Decide you don't agree to the terms after all and delete all your data from the bot"""
        await self._disagree(ctx)

    @commands.command(aliases=["guild"])
    @commands.check(checks.bypass_check(is_guild_owner()))
    async def server(self, ctx):
        """Look at some information about this guild"""
        added_by = "I can't tell who added me\n"
        with contextlib.suppress(discord.Forbidden):
            for action in await (ctx.guild.audit_logs(action=discord.AuditLogAction.bot_add)).flatten():
                if action.target == ctx.guild.me:
                    added_by = f"I was last invited by {action.user.mention}\n"
                    break
        terms = "You haven't agreed to the terms yet"
        agrees = self.agrees.read_key(ctx.guild.id)
        if agrees is not None:
            agreeing_member = ctx.guild.get_member(agrees['member']['id'])
            global_agreeing_member = None
            if agreeing_member is None:
                global_agreeing_member = self.bot.get_user(agrees['member']['id'])
            agreeing_member = (
                agreeing_member.mention if agreeing_member else (
                    str(global_agreeing_member)
                    if global_agreeing_member else
                    self.bot.get_user(agrees['member']['user'])
                )
            )
            terms = f"{agreeing_member} agreed to the terms " \
                    f"for this guild " \
                    f"{datetime.datetime.utcfromtimestamp(agrees['timestamp']).strftime('on %d/%m/%y at %H:%M UTC')}"
        await ctx.send(
            f"You have {len(ctx.guild.members)} members, "
            f"{len([member for member in ctx.guild.members if not member.bot])} of whom are not bots\n"
            f"Your server has been around since {ctx.guild.created_at.strftime('%d/%m/%y at %H:%M UTC')}\n" +
            (f"Your server has using me since {ctx.guild.me.joined_at.strftime('%d/%m/%y at %H:%M UTC')}\n" if
             ctx.guild.me.joined_at else "I can't tell when I joined your server\n") +
            added_by +
            terms,
            title=f"{self.bot.emotes['settings']} Server Information",
            paginate_by="\n"
        )


def setup(bot):
    disclaimers = Disclaimers(bot)

    bot.error_handler.handles(Exception)(disclaimers.NotAgreedCompleteErrorHandler)
    bot.error_handler.handles(disclaimers.NotGuildOwnerError)(disclaimers.NotGuildOwnerErrorHandler)

    bot.add_cog(disclaimers)


def pages(help_command):
    permissions = help_command.context.has_permissions(help_command.context.author)
    can_agree = all((permissions.manage_guild, permissions.manage_permissions))

    can_agree_message = 'Once you have read through the terms you can agree by running `{prefix}agree`'
    cannot_agree_message = 'You should get someone who has these permissions in the server to read these terms'

    has_agreed = f"""This server last agreed to the terms on **date** at **time**. The terms **have/have not** been \
updated since then and if they have show how to confirm"""
    has_not_agreed = f"""This server has not agreed to the terms and so playing games is disabled. 
**You are {'' if can_agree else 'not '}able to agree to the terms and conditions at this time
as you {'' if can_agree else 'do not'}have both manage server and manage permissions.**
"""
    f"**You are {'' if can_agree else 'not '}able to agree to the terms and conditions at this "
    f"time as you {'' if can_agree else 'do not'}have both manage server and manage "
    f"permissions.** "
    f"Please carefully read through the terms and conditions, ensuring that you are happy with "
    f"everything inside before agreeing"

    in_dms = f"""Run this in a server to view if the server has agreed to the terms"""
    return [
        {
            "description": f"> **Terms and conditions**\n",
            "buttons": {
                "◀️": {
                    "action": "to go to the end of the terms",
                    "callback": partial(help_command.move, 5),
                },
                "▶️": {
                    "action": "to go onwards and see the terms",
                    "callback": help_command.move,
                },
                "⏪": {
                    "action": "to return to the main help menu",
                    "callback": partial(help_command.set_pos, 0)
                },
            }
        },
        {
            "description": f"> We are not associated in any way with `Cards Against Humanity LLC`\n"
                           f"First, the legal stuff. We are not associated with `Cards Against Humanity LLC` "
                           f"(The company that made the original Cards Against Humanity card game). "
                           f"That's also why we called our bot something else. They said we had to credit them and we "
                           f"figured that here was the 100% best place to put it.",
            "buttons": {
                "◀️": {
                    "action": "to go back to the info on how to agree",
                    "callback": partial(help_command.move, -1),
                },
                "▶️": {
                    "action": "to see the next section",
                    "callback": help_command.move,
                },
                "⏪": {
                    "action": "to return to the main help menu",
                    "callback": partial(help_command.set_pos, 0)
                },
            }
        },
        {
            "description": f"> You agree for us to invite ourselves\n"
                           f"If you granted the bot the `Create Invite` permission, you agree that we can use this "
                           f"permission to invite the bot developers if you're facing an issue such as an error "
                           f"(or if we *really really* want a game). If you run a private server and don't want us to "
                           f"join, just deny us the permission.",
            "buttons": {
                "◀️": {
                    "action": "to go back to the previous section",
                    "callback": partial(help_command.move, -1),
                },
                "▶️": {
                    "action": "to see the next section",
                    "callback": help_command.move,
                },
                "⏪": {
                    "action": "to return to the main help menu",
                    "callback": partial(help_command.set_pos, 0)
                },
            }
        },
        {
            "description": f"> You agree that we process some of your data\n"
                           f"You agree that we can store information necessary to run the bot, such as your guild's "
                           f"ID, prefixes, pack language, and the time you agreed to these terms. We'll also save "
                           f"your ID, and username with this server's data as the person who agreed to the terms. We "
                           f"won't give any IDs or personally identifiable information (including IDs, and usernames) "
                           f"to anyone apart from the server owner if they request information about who agreed with "
                           f"the `%%server` command",
            "buttons": {
                "◀️": {
                    "action": "to go back to the previous section",
                    "callback": partial(help_command.move, -1),
                },
                "▶️": {
                    "action": "to see the next section",
                    "callback": help_command.move,
                },
                "⏪": {
                    "action": "to return to the main help menu",
                    "callback": partial(help_command.set_pos, 0)
                },
            }
        },
        {
            "description": f"> You agree that we don't have control of 3rd party packs\n"
                           f"We have a connection to cardcast :tada: (https://www.cardcastgame.com/#). You agree "
                           f"that we don't control and won't censor any of the packs that are used on there. They may "
                           f"be insane, offensive or otherwise inappropriate. Then again, if you're trying to play "
                           f"cards against humanity you probably don't mind much...",
            "buttons": {
                "◀️": {
                    "action": "to go back to the previous section",
                    "callback": partial(help_command.move, -1),
                },
                "▶️": {
                    "action": "to see the next section",
                    "callback": help_command.move,
                },
                "⏪": {
                    "action": "to return to the main help menu",
                    "callback": partial(help_command.set_pos, 0)
                },
            }
        },
        {
            "description": f"> You agree that we can change these terms\n"
                           f"Reading terms is always available from this command, but we may change them at any time. "
                           f"**We __strongly recommend__ that you read the terms regularly as we __will not__ tell you "
                           f"when we change them.** This is to avoid us having to cancel all your games, reset your "
                           f"prefixes and restrict your users from playing before you've got online to confirm your "
                           f"agreement",
            "buttons": {
                "◀️": {
                    "action": "to go back to the previous section",
                    "callback": partial(help_command.move, -1),
                },
                "▶️": {
                    "action": "to go and see how to agree",
                    "callback": partial(help_command.move, -5),
                },
                "⏪": {
                    "action": "to return to the main help menu",
                    "callback": partial(help_command.set_pos, 0)
                },
            }
        },
    ]