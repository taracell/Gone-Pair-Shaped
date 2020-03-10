import discord
import json
import asyncio

from discord.ext import commands, tasks
from utils import checks, converters
import typing

try:
    from utils.converters import fix_time
except ImportError:
    pass


class DynamicGuild(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            argument = int(argument)
        except TypeError:
            pass
        bot = ctx.bot
        if isinstance(argument, int):
            # check if its an ID first, else check enumerator
            guild = bot.get_guild(argument)
            if guild is not None:  # YAY
                return guild
            else:  # AWW
                for number, guild in enumerate(bot.guilds, start=1):
                    if number == argument:
                        return guild
                else:
                    if guild is None:
                        raise commands.BadArgument(f"Could not convert '{argument}' to 'Guild' with reason 'type None'")
                    else:
                        raise commands.BadArgument(f"Could not convert '{argument}' to 'Guild' as loop left.")
        elif isinstance(argument, str):  # assume its a name
            for guild in bot.guilds:
                if guild.name.lower() == argument.lower():
                    return guild
            else:
                raise commands.BadArgument(f"Could not convert '{argument}' to 'Guild' with reason 'type None' at 1")
        else:
            raise commands.BadArgument(f"Could not convert argument of type '{type(argument)}' to 'Guild'")


class Owner(commands.Cog, name="core"):
    """Bot management cog that just does the boring HR stuff."""

    def __init__(self, bot):
        self.bot = bot
        self.trigger_me.start()

    @commands.group(invoke_without_command=True)
    @commands.check(checks.bot_mod)
    async def servers(self, ctx):
        """Lists servers."""
        paginator = commands.Paginator(prefix="```md")
        for number, guild in enumerate(ctx.bot.guilds, start=1):
            dot = '\u200B.'
            backtick = '\u200B`'
            paginator.add_line(
                discord.utils.escape_markdown(f'{number}) {guild.name.replace(".", dot).replace("`", backtick)}\n'))
        for page in paginator.pages:
            await ctx.send(page)

    @tasks.loop(minutes=5)
    async def trigger_me(self):
        print("Adding official tester roles")
        g = self.bot.get_guild(684492926528651336)
        if not g:
            return print("I don't appear to be in the CAH guild")
        test_role = g.get_role(686310450748719243)
        for guild in self.bot.guilds:
            member = guild.owner
            if member in g.members and test_role not in [x.id for x in g.get_member(member.id).roles]:
                try:
                    user = await g.get_member(member.id)
                    await user.add_roles(test_role,
                                         reason=f"User of {self.bot.user.name} - Official tester.")
                    print(f"added role to {user}")
                except discord.NotFound:
                    pass

    @servers.command(aliases=['join'])
    @commands.check(checks.bot_mod)
    async def invite(self, ctx, *, guild: DynamicGuild()):
        """get an invite to a guild

        you can pass a name, id or enumerator number. ID is better."""
        if guild.me.guild_permissions.manage_guild:
            m = await ctx.send("Attempting to find an invite.")
            invites = await guild.invites()
            for invite in invites:
                if invite.max_age == 0:
                    return await m.edit(content=f"Infinite Invite: {invite}")
            else:
                await m.edit(content="No Infinite Invites found - creating.")
                for channel in guild.text_channels:
                    try:
                        invite = await channel.create_invite(max_age=60, max_uses=1, unique=True,
                                                             reason=f"Invite requested"
                                                                    f" by {ctx.author} via official management "
                                                                    f"command. do not be alarmed, this is usually "
                                                                    f"just "
                                                                    f" to check something.")
                        break
                    except:
                        continue
                else:
                    return await m.edit(content=f"Unable to create an invite - missing permissions.")
                await m.edit(content=f"Temp invite: {invite.url} -> max age: 60s, max uses: 1")
        else:
            m = await ctx.send("Attempting to create an invite.")
            for channel in guild.text_channels:
                try:
                    invite = await channel.create_invite(max_age=60, max_uses=1, unique=True, reason=f"Invite requested"
                                                                                                     f" by {ctx.author} via official management command. do not be alarmed, this is usually just"
                                                                                                     f" to check something.")
                    break
                except:
                    continue
            else:
                return await m.edit(content=f"Unable to create an invite - missing permissions.")
            await m.edit(content=f"Temp invite: {invite.url} -> max age: 60s, max uses: 1")

    @servers.command(name='leave')
    @commands.check(checks.bot_mod)
    async def _leave(self, ctx, guild: DynamicGuild(), *, reason: str = None):
        """Leave a guild. if ::reason:: is provided, then an embed is sent to the guild owner/system channel
        stating who made the bot leave (you), the reason and when.

        supply no reason to do a 'silent' leave"""
        if reason:
            e = discord.Embed(color=discord.Color.orange(), description=reason, timestamp=ctx.message.created_at)
            e.set_author(name=str(ctx.author), icon_url=ctx.author.avatar_url_as(static_format='png'))
            if guild.system_channel is not None:
                if guild.system_channel.permissions_for(guild.me).send_messages:
                    if guild.system_channel.permissions_for(guild.me).embed_links:
                        await guild.system_channel.send(embed=e)
            else:
                try:
                    await guild.owner.send(embed=e)
                except discord.Forbidden:
                    pass

        await guild.leave()

    @servers.command()
    @commands.dm_only()
    @commands.check(checks.bot_mod)
    async def info(self, ctx, *, guild: DynamicGuild()):
        """Force get information on a guild. this includes debug information."""
        owner, mention = guild.owner, guild.owner.mention
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.text_channels)
        roles, totalroles = [(role.name, role.permissions) for role in reversed(guild.roles)], len(guild.roles)
        bot_to_human_ratio = '{}:{}'.format(len([u for u in guild.members if u.bot]),
                                            len([u for u in guild.members if not u.bot]))
        default_perms = guild.default_role.permissions.value
        invites = len(await guild.invites()) if guild.me.guild_permissions.manage_guild else 'Not Available'
        fmt = f"Owner: {owner} ({owner.mention})\nText channels: {text_channels}\nVoice Channels: {voice_channels}\n" \
              f"Roles: {totalroles}\nBTHR: {bot_to_human_ratio}\n`@everyone` role permissions: {default_perms}\nInvites: " \
              f"{invites}"
        await ctx.send(fmt)

        paginator = commands.Paginator()
        for name, value in roles:
            paginator.add_line(f"@{name}: {value}")
        for page in paginator.pages:
            await ctx.send(page)
        return await ctx.message.add_reaction('\U00002705')

    @staticmethod
    async def getconfig():
        with open('./data/owner.json', 'r') as raw:
            data = json.load(raw)
        return data

    @staticmethod
    async def setconfig(*, data: dict):
        with open('./data/owner.json', 'w+') as fi:
            json.dump(data, fi, indent=2)
        return True

    @commands.command(name='getlog', aliases=['getlogs', 'botlog', 'debuglog', 'debug'])
    @commands.check(checks.is_owner)
    async def _getlog(self, ctx):
        """Uploads the current log file. assuming that its small enough.

        It may take a moment to remove sensitive information from the file."""
        try:
            with open('./data/debug.log', 'r') as abc:
                lines = abc.readlines()
                new = []
                for line in lines:
                    line = line.replace(self.bot.http.token, '[token hidden]')
                    new.append(line)
                pag = commands.Paginator(prefix='```bash', max_size=2000)
                for line in new:
                    if len(line) >= 1975:
                        pag.add_line(line[:1975] + '...')
                    else:
                        pag.add_line(line)
                for page in pag.pages:
                    try:
                        await ctx.author.send(page)
                    except discord.Forbidden:
                        return await ctx.send("Enable your DMs.")
        except UnicodeDecodeError:
            try:
                await ctx.author.send(file=discord.File('./data/debug.log'))
            except discord.Forbidden:
                return await ctx.send("Enable your DMs.")
            except UnicodeDecodeError:
                await ctx.send("Fatal error while reading from the file.")

    @commands.command()
    @commands.check(checks.bot_mod)
    async def skip(self, ctx):
        """Enable or disable skipping checks

+ Bot moderator only
+ Allows you to run a command even if a check failed
Run:
- %%skip"""
        if ctx.author in self.bot.skips:
            self.bot.skips.remove(ctx.author)
            return await ctx.send(f"Ok {ctx.author.mention}, I've disabled skipping for you")
        else:
            self.bot.skips.append(ctx.author)
            return await ctx.send(f"Ok {ctx.author.mention}, I've enabled skipping for you")

    @commands.command()
    async def inviteme(self, ctx):
        """Find out how to invite the bot

Run:
- %%inviteme"""
        return await ctx.send(f"You can use the URL https://discordapp.com/oauth2/authorize?client_id={ctx.me.id}"
                              f"&scope=bot"
                              f"&permissions=8 to invite me to your server")


    @commands.command()
    @commands.check(checks.is_owner)
    async def logout(self, ctx):
        """Logout the bot, *YOU WILL NEED VPS ACCESS TO START IT UP AGAIN, DON'T DO THIS UNLESS YOU KNOW WHAT YOU'RE DOING*"""
        await ctx.bot.logout()


def setup(bot):
    # bot.add_check(Owner(bot).bot_check)
    bot.add_cog(Owner(bot))
