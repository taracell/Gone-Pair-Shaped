"""
The terms commands for the bot, allowing data collection (and unauthorized self-inviting) since 2020
"""

import datetime

from discord.ext import commands

from utils import checks
from utils.miniutils.data import json

agrees = json.Json("disclaimer")


class NotAgreedError(commands.CheckFailure):
    """The error that is raised when a server that has not agreed to the terms attempts to use a command"""
    pass


def agreed_check(allow_pms=True, use_whitelist=True):
    """
    A decorator requiring the server in question to agree to the terms
    """

    def predicate(ctx):
        """
        Determine if a server has agreed to the terms by passing a context
        """
        whitelisted = (
            "help",
            "agree",
            "disagree",
            "stats",
            "info",
            "ping",
            "bug",
            "suggest",
            "server",
            "invite",
        )
        if use_whitelist and ctx.valid and ctx.command.qualified_name in whitelisted:
            return True
        if ctx.guild is None:
            if allow_pms:
                return True
            raise commands.NoPrivateMessage(
                "This cannot be run in private messages as it requires a guild which has agreed to the terms")
        if agrees.read_key(ctx.guild.id) is not None:
            return True
        raise NotAgreedError("Your guild has not agreed to the terms. Please run %%agree first")

    return commands.check(predicate)


def original_agree_check():
    """
    A decorator requiring the author to have been the original user to agree to the terms
    """

    def predicate(ctx):
        """
        Determine if the author was the original user to agree by passing a context
        """
        if ctx.guild is None:
            raise commands.NoPrivateMessage(
                "This cannot be run in private messages as it requires a guild which has agreed to the terms")
        guild_agreement = agrees.read_key(ctx.guild.id)
        if guild_agreement is None:
            raise NotAgreedError("Your guild has not agreed to the terms. Please run %%agree first")
        elif guild_agreement["user_id"] != str(ctx.author.id):
            raise NotAgreedError("You were not the person who last agreed to the terms, so no data about you is stored in the bot")
        return True

    return commands.check(predicate)


class Disclaimers(commands.Cog):
    """
    A discord bot cog to add a disclaimer that all users must agree to
    """

    def __init__(self, bot):
        self.bot = bot
        self.json_saves = {
            agrees,
            json.Json("prefixes"),
            json.Json("languages"),
            json.Json("settings"),
        }
        self.bot.check(agreed_check().predicate)

    @commands.command()
    @checks.bypass_check(
        commands.check_any(
            commands.has_guild_permissions(manage_guild=True, manage_permissions=True),
            original_agree_check()
        )
    )
    async def disagree(self, ctx):
        """
        Disagree to the disclaimer and remove all the data we have on your server
        """
        agrees.remove_key(ctx.guild.id)
        for save in self.json_saves:
            save.remove_key(ctx.guild.id)

        await ctx.send(
            "We've gone ahead and removed all the data we have on you. Thank you for using Cardboard Against Humankind "
            "by Clicks Minute Per; we hope to see you again soon",
            title="💔 Bye for now",
        )

    @commands.command(aliases=["accept"])
    @checks.bypass_check(commands.has_guild_permissions(manage_guild=True, manage_permissions=True))
    async def agree(self, ctx):
        """
        Agree to the disclaimer and start playing some CAH
        """
        agrees.save_key(
            ctx.guild.id,
            {
                "user_id": ctx.author.id,
                "time": datetime.datetime.utcnow().timestamp()
            }
        )

        await ctx.send(
            f"To get started, run %%help and select 🎮 to see how to play. If you ever want us to delete all your settings, you can do that with %%disagree",
            title="❤ Welcome!",
        )


def setup(bot):
    """
    Setup the terms and conditions cog on your bot
    """
    # bot.error_handler.handles(Exception)(disclaimers.NotAgreedCompleteErrorHandler)
    # bot.error_handler.handles(disclaimers.NotGuildOwnerError)(disclaimers.NotGuildOwnerErrorHandler)

    bot.add_cog(Disclaimers(bot))
