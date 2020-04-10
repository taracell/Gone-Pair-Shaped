from discord.ext import commands


class CantPlayNow(commands.CommandError):
    """The error raised when you can't play"""
    pass


class Development(CantPlayNow):
    """The error raised when the bot is in development mode"""
    pass


class GameExists(CantPlayNow):
    """The error raised when there's already a game in the channel"""
    pass


async def CantPlayHandler(ctx, _error, _next):
    await ctx.send(
        " ".join(_error.args),
        title=f"{ctx.bot.emotes['error']} You can't play now...",
        color=ctx.bot.colors["error"]
    )


def setup_handlers(handler):
    handler.handles(CantPlayNow)(CantPlayHandler)
