import discord
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
    def __init__(self):
        commands.HelpCommand.__init__(self)

    def get_command_signature(self, command):
        """Retrieves the signature portion of the help page.
    Parameters
    ------------
    command: :class:`Command`
        The command to get the signature of.
    Returns
    --------
    :class:`str`
        The signature for the command.
    Modified from discord.py's get_command_signature function
    """

        parent = command.full_parent_name
        if len(command.aliases) > 0:
            aliases = '|'.join(command.aliases)
            fmt = '[%s|%s]' % (command.name, aliases)
            if parent:
                fmt = parent + ' ' + fmt
            alias = fmt
        else:
            alias = command.name if not parent else parent + ' ' + command.name

        return '%s%s %s' % (self.context.bot.main_prefix, alias, command.signature)

    async def send_bot_help(self, mapping):
        unfiltered = []
        for cmd_map in mapping.values():
            unfiltered += cmd_map
        filtered = await self.filter_commands(unfiltered)
        custom_help_descriptions = {
            "help": "The help command... shows this message, and that's about it!",
            "help [command]": "",
        }
        descriptions = {
            self.get_command_signature(command): (
                (command.help or "No help available").replace("%%", self.context.bot.main_prefix)
            ) for command in filtered
        }
        for cmd, desc in custom_help_descriptions.items():
            descriptions[self.context.bot.main_prefix + cmd] = desc
        embed = discord.Embed(
            title='Cards Against Humanity - Commands',
            description="> **STAFF**\n**Co-owners:**\n" + "\n".join("> " + user for user in self.context.bot.owners) +
                        "\n**Helpers (Good people):**\n" + "\n".join(
                "> " + user + ": " + reason for user, reason in self.context.bot.helpers.items()
            ) +
            "\n\n> **INVITE ME**\n[discordapp.com]"
            "(https://discordapp.com/oauth2/authorize?client_id=679361555732627476&scope=bot&permissions=130048)"
            + "\n\n> **SERVER**\n[Cards Against Humanity Bot](https://discord.gg/bPaNnxe)",
            color=self.context.bot.colors["success"]
        )
        for command, description in descriptions.items():
            if not description:
                continue
            embed.add_field(name=command, value=description, inline=False)
        await self.context.send(embed=embed)
