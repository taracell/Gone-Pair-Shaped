from discord.ext import commands

class SkippedError(Exception):
    """The error raised when a CAH round is skipped"""
    pass

class CantPlayNow(commands.CommandError):
    """The error raised when the bot is in development mode"""
    pass

class Development(CantPlayNow):
    """The error raised when the bot is in development mode"""
    pass

class GameExists(CantPlayNow):
    """The error raised when the bot is in development mode"""
    pass
