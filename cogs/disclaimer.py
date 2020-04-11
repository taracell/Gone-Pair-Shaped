import asyncio
from discord.ext import commands
import functools
from utils.miniutils.data import json
from utils.miniutils.minidiscord import input
from utils import checks
import contextlib
import datetime
import discord


class NotAgreedError(commands.CheckFailure):
    """This error specifies that the guild has not agreed to the disclaimer"""
    pass


class NotGuildOwnerError(commands.CheckFailure):
    """This error specifies that the executor of the command is not an owner in the guild"""
    pass


async def NotAgreedErrorHandler(ctx, _error, _next):
    await ctx.send_exception(
        " ".join(_error.args),
        title=f"You haven't agreed to the terms",
    )


async def NotGuildOwnerErrorHandler(ctx, _error, _next):
    await ctx.send_exception(
        " ".join(_error.args),
        title=f"No permissions",
    )


def is_guild_owner(ctx):
    if ctx.guild is not None and ctx.guild.owner_id == ctx.author.id:
        return True
    else:
        raise NotGuildOwnerError("You must be the server owner to get the server's info")


def initial_agree_check(ctx):
    if not ctx.guild:
        return False
    agrees = json.Json("disclaimer").read_key(ctx.guild.id)
    if not agrees:
        raise NotAgreedError("Your guild needs to agree to the terms before this command works in your guild")
    if agrees["member"]["id"] != ctx.author.id:
        return False
    return True


class Disclaimers(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.agrees = json.Json("disclaimer")
        self.json_saves = {
            self.agrees,
            json.Json("prefixes"),
            json.Json("languages")
        }
        self.timeout = 300
        self.terms = {
            "We are not associated in any way with `Cards Against Humanity LLC`": "First, the legal stuff. We are not "
                                                                                  "associated with `Cards Against "
                                                                                  "Humanity LLC` (The company that "
                                                                                  "made the original Cards Against "
                                                                                  "Humanity card game). That's also "
                                                                                  "why we called our bot something "
                                                                                  "else. They said we had to credit "
                                                                                  "them and we figured that here was "
                                                                                  "the 100% best place to put it.",
            "You agree for us to invite ourselves": "If you granted the bot the `Create Invite` permission, you agree "
                                                    "that we can use this permission to invite the bot developers if "
                                                    "you're facing an issue such as an error (or if we *really really* "
                                                    "want a game). If you run a private server and don't want us to "
                                                    "join, just deny us the permission.",
            "You agree that we process some of your data": "You agree that we can store information necessary to run "
                                                           "the bot, such as your guild's ID, prefixes, pack language, "
                                                           "and the time you agreed to these terms. We'll also save "
                                                           "your ID, and username with this server's data as the "
                                                           "person who agreed to the terms. We won't give any IDs or "
                                                           "personally identifiable information (including IDs, and "
                                                           "usernames) to anyone apart from the server owner if they "
                                                           "request information about who agreed with the `%%server` "
                                                           "command",
            "You agree that we don't have control of 3rd party packs": "We have a connection to cardcast :tada: "
                                                                       "(https://www.cardcastgame.com/#). You agree "
                                                                       "that we don't control and won't censor any of "
                                                                       "the packs that are used on there. They may be "
                                                                       "insane, offensive or otherwise inappropriate. "
                                                                       "Then again, if you're trying to play cards "
                                                                       "against humanity you probably don't mind "
                                                                       "much...",
            "You agree that we can change these terms": "Reading terms is always available from this command, but we "
                                                        "may change them at any time. If we change what data we store "
                                                        " (so that we store data that it is not clear why we need to "
                                                        "store it (so not including server configuration and similar "
                                                        "needs)) we will force you to agree again, however if we "
                                                        "change what we do with the permissions you give us, we won't. "
                                                        "We promise it won't be bad, but as a rule of thumb don't give "
                                                        "any bot permissions you don't want it to use (even ours)"
        }
        bot.check(checks.bypass_check(self.agreed_check))

    def agreed_check(self, ctx):
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
            raise NotAgreedError(
                "You must agree to the terms with the `$terms` command before the bot works in this server"
            )
        else:
            raise NotAgreedError(
                "We need someone with `manage server` and `manage roles` to agree to the terms of service before the "
                "bot works in this server"
            )

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
        checks.has_permissions_predicate,
        manage_guild=True,
        manage_permissions=True
    )), commands.check(initial_agree_check))
    async def disagree(self, ctx):
        """Decide you don't agree to the terms after all and delete all your data from the bot"""
        await self._disagree(ctx)

    @commands.command()
    async def terms(self, ctx):
        """List all the terms and conditions for the bot"""
        agrees = self.agrees.read_key(ctx.guild.id) if ctx.guild else None
        title = "The CAHBot terms"
        if ctx.guild:
            if agrees:
                agreed_time = datetime.datetime.utcfromtimestamp(agrees['timestamp']) \
                    .strftime("on %d/%m/%y at %H:%M UTC")
                title = f"✅ Your guild agreed to these terms {agreed_time}, if you want " \
                        f"to cancel your agreement and delete your data run " \
                        f"`{ctx.bot.get_main_custom_prefix(ctx)}disagree`"
            else:
                title = "❌ Your guild has not agreed to these terms"
        await ctx.send(
            "\n".join(
                f"{position + 1}) **{term}** - {desc.replace('%%', ctx.bot.get_main_custom_prefix(ctx))}"
                for position, (term, desc) in enumerate(self.terms.items())
            ),
            title=title,
            paginate_by="\n"
        )
        if (
                ctx.guild and
                not agrees and
                (
                        (
                                ctx.channel.permissions_for(ctx.author).manage_guild and
                                ctx.channel.permissions_for(ctx.author).manage_permissions
                        ) or (
                                ctx.author in self.bot.skips and
                                checks.bot_mod(ctx)
                        )
                )
        ):
            if ctx.channel.permissions_for(ctx.guild.me).add_reactions:
                menu = input.Menu(
                    self.bot,
                    callbacks=True,
                    timeout=self.timeout,
                    timeout_callback=functools.partial(self._disagree, ctx)
                )  # Create our reaction menu
                menu.add("✅", functools.partial(self.agree, ctx))
                menu.add("❌", functools.partial(self._disagree, ctx))

                agree_message = await ctx.send(
                    "You have the permissions needed to agree to these terms and unlock all commands for your server. "
                    "React with (or say in chat) ✅ to agree or ❌ to disagree for now. If you don't type within "
                    f"{self.timeout} seconds we'll assume you're not ready to agree yet. Keep in mind that disagreeing "
                    f"will not allow your server to use the bot until you run this command again and agree. *If your "
                    f"press doesn't register then maybe discord's being slow, just try again. If the error persists "
                    f"please report this as a bug to the developers*",
                    title="Ready to agree? Just press ✅ (once I've added it)"
                )

                await menu(
                    message=agree_message,
                    responding=ctx.author
                )
            else:
                try:
                    agreed = await ctx.input(
                        title="Ready to agree? Just say yes",
                        prompt="You have the permissions needed to agree to these terms and unlock all commands for "
                               "your server. Just type `yes` in chat to agree or `no` to disagree. If you don't type "
                               f"within {self.timeout} seconds we'll assume you're not ready to agree yet. Keep in "
                               "mind that disagreeing will not allow your server to use the bot until you run this "
                               "command again and agree",
                        required_type=bool,
                        timeout=self.timeout,
                        error=f"{self.bot.emotes['valueerror']} Pick either `yes` or `no`",
                        color=self.bot.colors['status']
                    )
                    if agreed:
                        await self.agree(ctx)
                    else:
                        await self._disagree(ctx)
                except asyncio.TimeoutError:
                    await self._disagree(ctx)

    @commands.command(aliases=["guild"])
    @commands.check(checks.bypass_check(is_guild_owner))
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
    bot.error_handler.handles(NotAgreedError)(NotAgreedErrorHandler)
    bot.error_handler.handles(NotGuildOwnerError)(NotGuildOwnerErrorHandler)
    bot.add_cog(Disclaimers(bot))
