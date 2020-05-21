from utils.miniutils.minidiscord import input
# Import my reaction menu utility to create our reaction menus
from cogs import terms
import cogs.terms.docs
# Import our help documentation
from discord.ext import commands
# Import discord's commands extension to create our help command
from functools import partial
# Import partials so that we can create functions that have arguments, this is useful to, for example, scroll pages in
# the help command
import discord
# Import discord so we can use stuff like the abstract base classes and Embeds
import random
# Import random for giving a random 'no' message if the bot doesn't have enough permissions
import inspect

from discord.ext.commands import converter


# Import inspect for fiddling around with parameters


class MiniCustomHelp(commands.HelpCommand):
    def __init__(self, **options):  # When our help command is being created...
        super().__init__(**options)  # Firstly, run the initialization method of discord's commands.HelpCommand
        self.position = 0  # Set our position to 0 so that we start there
        self.sections = {}  # Set up our sections so that we can have sections loaded if the cogs are loaded and not if
        # not
        self.pages = []  # Initialize our pages list
        self.msg = None  # Set our message ID (for deletion and editing, for example) to None as we haven't sent the
        # help message yet
        self.timeout = 300  # Set our help command timeout, after which the bot will timeout and delete the help message
        # to 300 seconds, or 5 minutes

    async def prepare_help_command(self, ctx, command=None):  # When our help command is being prepared to be sent...
        # We set pages here not in __init__ because at this point we have our context in the form of the ctx variable
        try:
            await terms.agreed_check(use_whitelist=False).predicate(ctx)
        except terms.NotAgreedError:
            self.position = 1
        sections = {
            "terms": {
                "pages": cogs.terms.docs.pages(self),
                "cog": True,
                "action": "to look at the terms and conditions for using the bot",
                "emote": "📜",
            },
        }
        offset = 1
        buttons = {}
        self.sections = {}
        for name, section in sections.items():
            if section["cog"] is True or self.context.bot.cogs.get(section["cog"], None):
                self.sections[name] = section
        for section in self.sections.values():
            buttons[section["emote"]] = partial(self.set_pos, offset)
            offset += len(section["pages"])
        self.pages = [
            {
                "description": f"Welcome to Cardboard Against Humankind by ClicksMinutePer, "
                               f"throughout this help menu you can either say or react with emojis to view the help topics\n\n"
                               f"To view the terms and conditions of using the bot press 📜\n"
                               f"To view how to play press 🎮\n"
                               f"To close this embed, press ⏹",
                "buttons": {
                    **buttons,
                    "⏹️": self.delete
                }
            },
        ]
        for section in self.sections.values():
            self.pages = self.pages + section["pages"]

    async def render(self):  # To display our help command...
        x = None
        if self.get_destination().guild:
            perms = self.get_destination().permissions_for(self.get_destination().guild.me)
            # Get our permissions in the current channel
            x = [perms.manage_messages, perms.add_reactions, perms.external_emojis, perms.embed_links]  # These are the
            # required permissions for our help command to function
        if not (isinstance(self.context.channel, discord.abc.PrivateChannel) or all(x)):  # If we don't have them
            no = ["n-n-n-n-n-n-n-n-n-n-n-no (n-n-n-n-no n-n-n-n-no)...",
                  "nope!",
                  "sorry, no can do!",
                  "uhhhh... you realise you can't do that, right?",
                  "about that..."
                  ]  # Here are our possible responses
            return await self.get_destination().send(f"{self.context.author.mention}, {random.choice(no)} The bot "
                                                     f"doesn't seem to have the correct permissions to perform this "
                                                     f"action. Try running `{self.context.bot.main_prefix}help` in "
                                                     f"direct messages\n"
                                                     f"Alternatively all the information can be found online at "
                                                     f"https://docs.dragdev.xyz/global")
            # Send one of them along with an error message to the user

        menu = input.Menu(self.context.bot,
                          self.timeout,
                          True,
                          self.delete)  # Create our reaction menu
        old_message = self.msg  # Get the old message saved to a variable, as we will overwrite the self.msg before
        # deleting it
        embed = discord.Embed(
            title="Cardboard Against Humankind Help",
            description=f"{self.pages[self.position]['description']}",
            color=0x1c66b8)  # Create an embed, using the page description as it's description and inserting a
        # 'helpful buttons' section if there are any reactions in the reactions menu
        number_of_buttons = len(self.pages[self.position].get("buttons", {}))
        # find out how many buttons there will be in total
        for position, data in enumerate(self.pages[self.position].get("buttons", {}).items()):
            menu.add(data[0], data[1])
        embed.set_author(name=str(self.context.author), icon_url=self.context.author.avatar_url)
        if self.get_destination().guild and old_message:
            await old_message.clear_reactions()
            await old_message.edit(embed=embed)
        else:
            self.msg = await self.get_destination().send(embed=embed)
            if old_message:
                await old_message.delete()
        await menu(self.msg, self.context.author)

    async def delete(self):
        if self.msg:
            await self.msg.delete()

    async def set_pos(self, new_pos):
        self.position = (new_pos if new_pos < len(self.pages) else len(self.pages) - 1) if new_pos > 0 else 0
        await self.render()

    async def move(self, distance=1):
        await self.set_pos(self.position + distance)

    async def send_bot_help(self, mapping):
        custom_help_descriptions = {
            "help": "Shows this message",
        }
        for page in self.pages:
            split_desc = page["description"].split("%list(", 1)
            if len(split_desc) != 2:
                page["description"] = page["description"].replace("%%", self.context.bot.main_prefix)
                continue
            first_part = split_desc[0]
            split_desc = split_desc[1].split(")list%", 1)
            if len(split_desc) != 2:
                page["description"] = page["description"].replace("%%", self.context.bot.main_prefix)
                continue
            last_part = split_desc[1]
            split_desc = split_desc[0].split(",")
            new_desc_parts = []
            for cog, cmds in reversed(await self.filter_commands(mapping.items())):
                if cog is None and 'None' not in split_desc:
                    continue
                elif cog is None or cog.qualified_name in split_desc:
                    if cog is None:
                        split_desc.remove('None')
                    else:
                        split_desc.remove(cog.qualified_name)
                    for cmd in cmds:
                        first_doc_line = cmd.callback.__doc__.split("\n")[0] \
                            if cmd.callback.__doc__ else \
                            'No help available'
                        try:
                            first_doc_line = custom_help_descriptions[cmd.qualified_name]
                        except KeyError:
                            pass
                        new_desc_parts.append(f"```ldif\n{self.clean_prefix}{cmd.qualified_name} : "
                                              f"{first_doc_line}```")
            for cog in split_desc:
                new_desc_parts.append(f"```diff\n- Couldn't get commands as the {cog.lower()} cog was not found, "
                                      f"perhaps it isn't loaded?```")
            page["description"] = (first_part + "".join(new_desc_parts) + last_part) \
                .replace("%%", self.clean_prefix)
        if not self.context.bot.loaded:
            return await self.get_destination().send("The bot hasn't finished loading yet... please wait a few "
                                                     "moments...")
        await self.render()

    async def send_group_help(self, group):
        split_doc = group.callback.__doc__.split("\n") if group.invoke_without_command else [
            f"Can't be run without providing a sub-command"
        ]
        first_doc_line = split_doc[0] if split_doc else 'No help available'
        extra_doc_lines = "```diff\n" + "\n".join(split_doc[1:]) + "```" \
            if split_doc and len(split_doc) > 1 else ''
        subcommands = ["+ Valid subcommands"]
        for command in await self.filter_commands(group.commands):
            command_split_doc = command.callback.__doc__.split("\n")
            command_first_doc_line = command_split_doc[0] if command_split_doc else 'No help available'
            subcommands.append(
                f"- {self.clean_prefix}{command.qualified_name}\n{command_first_doc_line}"
            )
        subcommands = "\n".join(subcommands)
        self.pages = [
            {
                "description": f"Command help for {group.qualified_name}"
                               f"```ldif\n{self.clean_prefix}{group.qualified_name} {{sub_command}}: {first_doc_line}"
                               f"```"
                               f"{extra_doc_lines}"
                               f"```diff\n{subcommands}```".replace("%%", self.clean_prefix),
                "buttons": {
                    "▶️️": {
                        "action": f"to see how to use {self.clean_prefix}"
                                  f"{list(group.commands)[0].qualified_name}",
                        "callback": self.move,
                    },
                    "⏹️": {
                        "action": "to close this message",
                        "callback": self.delete
                    },
                } if group.commands else {
                    "⏹️": {
                        "action": "to close this message",
                        "callback": self.delete
                    },
                }
            },
        ]
        for position, command in enumerate(group.commands):
            doc = f"```ldif\n{command.callback.__doc__}```" \
                if command.callback.__doc__ else '```ldif\nNo help available```'
            parameters = [
                {
                    "default": param.default if param.default != inspect.Parameter.empty else None,
                    "name": name,
                    "repeatable": param.kind == inspect.Parameter.KEYWORD_ONLY
                                  or isinstance(param.annotation, converter._Greedy)
                }
                for name, param in command.clean_params.items()
            ]
            params = ' '.join(
                (f"{{"
                 f"{param['name']}"
                 f"{' (Default: ' + str(param['default']) + ')' if param['default'] is not None else ''}"
                 f"}}"
                 f"{'...' if param['repeatable'] else ''}"
                 for param in parameters)
            )
            self.pages.append(
                {
                    "description": f"Command help for {command.qualified_name}"
                                   f"```ldif\n{self.clean_prefix}{command.qualified_name}: "
                                   f"{params}```"
                                   f"{doc}".replace("%%", self.clean_prefix),
                    "buttons": {
                        "◀️": {
                            "action": f"to see how to use {self.clean_prefix}"
                                      f"{list(group.commands)[position - 1].qualified_name}"
                            if position == 0
                            else f"to go back to the main group",
                            "callback": partial(self.move, -1),
                        },
                        "▶️️": {
                            "action": f"to see how to use {self.clean_prefix}"
                                      f"{list(group.commands)[position + 1].qualified_name}",
                            "callback": self.move,
                        },
                        "⏪": {
                            "action": "to go back to the main group",
                            "callback": partial(self.set_pos, 0)
                        },
                        "⏹️": {
                            "action": "to close this message",
                            "callback": self.delete
                        },
                    } if position + 1 < len(group.commands) else {
                        "◀️": {
                            "action": f"to see how to use {self.clean_prefix}"
                                      f"{list(group.commands)[position - 1].qualified_name}"
                            if position == 0
                            else f"to go back to the main group",
                            "callback": partial(self.move, -1),
                        },
                        "⏹️": {
                            "action": "to close this message",
                            "callback": self.delete
                        },
                    }
                },
            )
        await self.render()

    async def send_command_help(self, command):
        doc = f"```ldif\n{command.callback.__doc__}```" \
            if command.callback.__doc__ else '```ldif\nNo help available```'
        parameters = [
            {
                "default": param.default if param.default != inspect.Parameter.empty else None,
                "name": name,
                "repeatable": param.kind == inspect.Parameter.KEYWORD_ONLY
                              or isinstance(param.annotation, converter._Greedy)
            }
            for name, param in command.clean_params.items()
        ]
        params = ' '.join(
            (f"{{"
             f"{param['name']}"
             f"{' (Default: ' + str(param['default']) + ')' if param['default'] is not None else ''}"
             f"}}"
             f"{'...' if param['repeatable'] else ''}"
             for param in parameters)
        )
        self.pages = [
            {
                "description": f"Command help for {command.qualified_name}"
                               f"```dust\n{self.clean_prefix}{command.qualified_name} {params}```"
                               f"{doc}".replace("%%", self.clean_prefix),
                "buttons": {
                    "⏹️": {
                        "action": "to close this message",
                        "callback": self.delete
                    },
                },
            },
        ]
        await self.render()

    async def send_cog_help(self, cog):
        cog_commands = []
        for command in cog.get_commands():
            first_doc_line = command.callback.__doc__.split("\n")[0] if command.callback.__doc__ else \
                'No help available'
            cog_commands.append(f"```ldif\n{self.clean_prefix}{command.qualified_name} : {first_doc_line}```")
        if not cog_commands:
            cog_commands.append(f"```diff\n- No commands here```")
        self.pages = [
            {
                "description": f"Commands list for {cog.qualified_name}"
                               f"\n{''.join(cog_commands)}".replace("%%", self.clean_prefix),
                "buttons": {
                    "⏹️": {
                        "action": "to close this message",
                        "callback": self.delete
                    },
                },
            },
        ]
        await self.render()
