import discord
from discord.ext import commands


class HelpCommand(commands.HelpCommand):
  def __init__(self):
    commands.HelpCommand.__init__(self)
    self.owners = [
      "PineappleFan#9955",
      "Minion3665#6456",
    ]
    self.helpers = {
      "Waldigo#6969": "Programming help",
      "nwunder#4018": "Programming help",
      "Mine#4200": "Tester & legend"
    }

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
              command.help.replace("%%", self.context.bot.main_prefix) or "No help available"
      ) for command in filtered
    }
    for cmd, desc in custom_help_descriptions.items():
      descriptions[self.context.bot.main_prefix + cmd] = desc
    embed = discord.Embed(
      title='Cards Against Humanity - Commands',
      description="\n".join(
        [f"```diff\n- {command}: {description}```" for command, description in
         descriptions.items() if description]
      ),
      color=discord.Color(0x8bc34a)
    )
    embed.add_field(
      name="Made by",
      value="**Co-owners:**\n" + "\n".join("> " + user for user in self.owners) +
            "\n**Helpers (Good people):**\n" + "\n".join(
        "> " + user + ": " + reason for user, reason in self.helpers.items()),
      inline=False
    )
    embed.add_field(
      name="Server",
      value="https://discord.gg/bPaNnxe",
      inline=False
    )
    embed.add_field(
      name="Invite me!",
      value="[Press here]"
            "(https://discordapp.com/oauth2/authorize?client_id=679361555732627476&scope=bot&permissions=130048)"
            "\n*(Please note we need certain permissions, such as embed links, to function)*",
      inline=False
    )
    await self.context.send(embed=embed)
