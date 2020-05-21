"""
Create documentation for the terms, arguably the most important documentation in the entire bot as it contains information which is required to use the bot
"""
from functools import partial
from .. import terms
import datetime

last_terms_update = 1589370441.928744


def pages(help_command):
    """
    Get the pages for the help command
    """
    permissions = help_command.context.permissions_for(help_command.context.author)
    can_agree = all((permissions.manage_guild, permissions.manage_permissions))
    guild_agreement_data = terms.agrees.read_key(help_command.context.guild.id)

    can_agree_message = 'Once you have read through the terms you can agree by running `%%agree`'
    cannot_agree_message = 'You should get someone who has these permissions in the server to read these terms'

    if guild_agreement_data:
        update_time = datetime.datetime.fromtimestamp(last_terms_update)
        agreement_time = datetime.datetime.fromtimestamp(guild_agreement_data["time"])
        agreement_time_repr = agreement_time.strftime("%A %d %B at %-H:%M:%S UTC")
        updated = agreement_time < update_time
        guild_message = f"""This server last agreed to the terms on {agreement_time_repr}. The terms **have{'' if updated else ' not'}** been updated since then
{', you can confirm your agreement to the terms with %%agree' if updated else ''}

If you ever want to disagree to the terms, you can run `%%disagree`. Please note that this will also delete all your settings"""
    else:
        guild_message = f"""This server has not agreed to the terms and so playing games is disabled. 
**You are {'' if can_agree else 'not '}able to agree to the terms and conditions at this time
as you {'' if can_agree else 'do not'}have both manage server and manage permissions.{' You can do this with %%agree' if can_agree else ''}**
Please carefully read through the terms and conditions, ensuring that you are happy with everything inside before agreeing
"""

    dms_message = f"""You will need to agree to these terms before your server can play GPS

Run this in a server to view if the server has agreed to the terms"""
    return [
        {
            "description": f"> **Terms and conditions**\n{guild_message if help_command.context.guild is not None else dms_message}\n\n"
                           f"You can use ◀ and ▶️ to navigate through these terms and ⏪ to go back to the main menu. You can either react with these *or* say them in this channel",
            "buttons": {
                "⏪": partial(help_command.set_pos, 0),
                "◀️": partial(help_command.move, 3),
                "▶️️": help_command.move,
            }
        },
        {
            "description": f"> You agree for us to invite ourselves\n"
                           f"If you granted the bot the `Create Invite` permission, you agree that we can use this "
                           f"permission to invite ClicksMinutePer staff members to help if you're facing an issue such as an error "
                           f"(or if we *really really* want a game). If you run a private server and don't want us to "
                           f"join, just deny us the permission.",
            "buttons": {
                "⏪": partial(help_command.set_pos, 0),
                "◀️": partial(help_command.move, -1),
                "▶️️": help_command.move,
            }
        },
        {
            "description": f"> You agree that we process some of your data\n"
                           f"You agree that we can store information necessary to run the bot, such as your guild's "
                           f"ID, prefixes, server-specific settings, and the time you agreed to these terms. We'll also save "
                           f"your ID, with this server's data as the person who last agreed to the terms. We "
                           f"won't give your ID to anyone. Ever, and if someone else confirms agreement to the terms we'll delete your ID again",
            "buttons": {
                "⏪": partial(help_command.set_pos, 0),
                "◀️": partial(help_command.move, -1),
                "▶️️": help_command.move,
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
                "⏪": partial(help_command.set_pos, 0),
                "◀️": partial(help_command.move, -1),
                "▶️️": partial(help_command.move, -3),
            }
        },
    ]
