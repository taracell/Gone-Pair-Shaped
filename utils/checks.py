import asyncio

import discord
from discord.ext import commands


# Define commonly used functions. We use a single underscore ('_') to let people know that we shouldn't access this
# outside of this module but still allow it
def bot_mod(ctx):
    mod_users = []
    mod_roles = [686310450618695703, 684493117017161963]
    if ctx.author is None:
        return False
    if ctx.author.id in mod_users:
        return True
    if ctx.author.id in ctx.bot.admins:
        return True
    mods = []
    for role in mod_roles:
        mods = mods + discord.utils.get(
            ctx.bot.get_guild(684492926528651336).roles, id=role).members
    mod_ids = []
    for mod in mods:
        mod_ids.append(mod.id)
    if ctx.author.id in mod_ids:
        return True
    return False


def is_owner(ctx):
    if ctx.author.id in ctx.bot.admins:
        return True
    return False


def tester(ctx):
    testers = []
    test_roles = [686310450748719243]
    if ctx.author is None:
        return False
    if ctx.author in testers:
        return True
    testers = []
    for role in test_roles:
        testers = testers + discord.utils.get(
            ctx.bot.get_guild(684492926528651336).roles, id=role).members
    test_ids = []
    for test in testers:
        test_ids.append(test.id)
    if ctx.author.id in test_ids:
        return True
    return False


# Define the checks
def bypass_check(
        check
):  # If the user is a bot mod this check will allow them to skip the check if it fails
    """If the user is a bot mod this check will allow them to skip the check if it fails. Auto-passes the ctx
    parameter """
    predicate = check.predicate

    async def pred(ctx):
        try:
            if asyncio.iscoroutinefunction(predicate):
                result = await predicate(ctx)
            else:
                result = predicate(ctx)
            if result:
                return True
            else:
                raise commands.CheckFailure("Check failed: " + predicate.__name__)
        except Exception as e:
            if bot_mod(ctx) and ctx.author in ctx.bot.skips:
                try:
                    await ctx.send(
                        "Sadly the check " + ctx.command.qualified_name + "." + predicate.__name__ +
                        " failed (Error: " + str(e) +
                        "), but as you're a bot moderator you can skip this check! Do you want to skip? (y/n)",
                        delete_after=30
                    )

                    def message_check(message):
                        if not message.channel == ctx.channel or not message.author == ctx.author:
                            return False
                        if message.content.lower(
                        ) in ["y", "n"]:
                            return True
                        else:
                            ctx.bot.loop.create_task(ctx.send("Your response must be y or n (yes, no). Try Again"))
                            return False

                    bypass_response = "n"
                    try:
                        bypass_response = await ctx.bot.wait_for(
                            "message", check=message_check, timeout=30)
                    except asyncio.TimeoutError:
                        await ctx.send("Your message timed out. An option of n (no) has been selected")
                    if bypass_response.content.lower() == "y":
                        return True
                    raise e
                except Exception:
                    raise e
            raise e

    return pred


def development(ctx):  # If the command is in development don't let the user run the command
    return False
