import datetime
from discord.ext import commands
import discord
import typing


def channel_converter(*allowed_types: discord.ChannelType, allow_outside_of_guild: typing.Optional[bool] = False) -> \
        typing.Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel, discord.DMChannel,
                     discord.GroupChannel, commands.Converter]:
    class Channel(commands.Converter):
        async def convert(self, ctx, argument):
            result = None
            if ctx.guild:
                channels = [channel for channel in ctx.guild.channels if isinstance(channel, allowed_types)]
                result = discord.utils.get(channels, name=argument)
            try:
                if allow_outside_of_guild:
                    result = ctx.bot.get_channel(int(argument))
                else:
                    result = ctx.guild.get_channel(int(argument))
            except ValueError:
                pass
            if argument.startswith("<#") and argument.endswith(">"):
                try:
                    if allow_outside_of_guild:
                        result = ctx.bot.get_channel(int(argument[2:-1]))
                    else:
                        result = ctx.guild.get_channel(int(argument[2:-1]))
                except ValueError:
                    pass

            if not isinstance(result, allowed_types):
                raise discord.ext.commands.BadArgument('Channel "{}" not found.'.format(argument))

            return result
    return Channel


# BEGIN EEK'S CONVERTORS


def ago_time(time):
    """Convert a time (datetime) to a human readable format.
    """
    date_join = datetime.datetime.strptime(str(time), "%Y-%m-%d %H:%M:%S.%f")
    date_now = datetime.datetime.now(datetime.timezone.utc)
    date_now = date_now.replace(tzinfo=None)
    since_join = date_now - date_join

    m, s = divmod(int(since_join.total_seconds()), 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    y = 0
    while d >= 365:
        d -= 365
        y += 1

    if y > 0:
        msg = "{4}y, {0}d {1}h {2}m {3}s ago"
    elif d > 0 and y == 0:
        msg = "{0}d {1}h {2}m {3}s ago"
    elif d == 0 and h > 0:
        msg = "{1}h {2}m {3}s ago"
    elif d == 0 and h == 0 and m > 0:
        msg = "{2}m {3}s ago"
    elif d == 0 and h == 0 and m == 0 and s > 0:
        msg = "{3}s ago"
    else:
        msg = ""
    return msg.format(d, h, m, s, y)


def fix_time(time: int = None, *, return_ints: bool = False, brief: bool = False):
    """Convert a time (in seconds) into a readable format, e.g:
    86400 -> 1d
    3666 -> 1h, 1m, 1s

    set ::return_ints:: to True to get a tuple of (days, minutes, hours, seconds).
    --------------------------------
    :param time: int -> the time (in seconds) to convert to format.
    :keyword return_ints: bool -> whether to return the tuple or (default) formatted time.
    :raises ValueError: -> ValueError: time is larger then 7 days.
    :returns Union[str, tuple]:
    to satisfy pycharm:
    """
    seconds = round(time, 2)
    minutes = 0
    hours = 0
    overflow = 0

    d = 'day(s)' if not brief else 'd'
    h = 'hour(s)' if not brief else 'h'
    m = 'minute(s)' if not brief else 'm'
    s = 'seconds(s)' if not brief else 's'
    a = 'and' if not brief else '&'

    while seconds >= 60:
        minutes += 1
        seconds -= 60
    while minutes >= 60:
        hours += 1
        minutes -= 60
    while hours > 23:
        overflow += 1
        hours -= 23

    if return_ints:
        return overflow, hours, minutes, seconds
    if overflow > 0:
        return f'{overflow} day(s), {hours} hour(s), {minutes} minute(s) and {round(seconds, 2)} second(s)'
    elif overflow == 0 and hours > 0:
        return f'{hours} hour(s), {minutes} minute(s) and {round(seconds, 2)} second(s)'
    elif overflow == 0 and hours == 0 and minutes > 0:
        return f'{minutes} minute(s) and {round(seconds, 2)} second(s)'
    else:
        return f'{round(seconds, 2)} second(s)'
