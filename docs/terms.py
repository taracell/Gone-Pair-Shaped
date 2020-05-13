from functools import partial
import asyncio
from discord.ext import commands
import functools
from utils.miniutils.data import json
from utils import checks
import contextlib
import datetime
import discord


class Disclaimers(commands.Cog):
    """
    A discord bot cog to add a disclaimer that all users must agree to
    """

    def __init__(self, bot):
        self.bot = bot
        self.agrees = json.Json("disclaimer")
        self.json_saves = {
            self.agrees,
            json.Json("prefixes"),
            json.Json("languages"),
            json.Json("settings"),
        }

    @commands.command()
    async def disagree(self, ctx):
        """
        Disagree to the disclaimer and remove all the data we have on your server
        """
        self.agrees.remove_key(ctx.guild.id)
        for save in self.json_saves:
            save.remove_key(ctx.guild.id)

        await ctx.send(
            "We've gone ahead and removed all the data we have on you. Thank you for using Cardboard Against Humankind "
            "by Clicks Minute Per; we hope to see you again soon",
            title="💔 Bye for now",
        )

    @commands.command(aliases=["accept"])
    @checks.bypass_check(commands.has_permissions(manage_guild=True, manage_permissions=True))
    async def agree(self, ctx):
        """
        Agree to the disclaimer and start playing some CAH
        """
        self.agrees.save_key(
            ctx.guild.id,
            {
                "user_id": ctx.author.id,
                "time": datetime.datetime.utcnow().timestamp()
            }
        )

        await ctx.send(
            f"To get started, run %%help and select 🎮 to see how to play",
            title="❤ Welcome!",
        )


def setup(bot):
    """
    Setup the terms and conditions cog on your bot
    """
    # bot.error_handler.handles(Exception)(disclaimers.NotAgreedCompleteErrorHandler)
    # bot.error_handler.handles(disclaimers.NotGuildOwnerError)(disclaimers.NotGuildOwnerErrorHandler)

    bot.add_cog(Disclaimers(bot))


def pages(help_command):
    """
    Get the pages for the help command
    """
    permissions = help_command.context.permissions_for(help_command.context.author)
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
