"""The server cog for the Connect My Pairs API"""
from discord.ext import commands
from . import server


class ConnectMyPairs(commands.Cog):
    """Connect my pairs"""

    def __init__(self, bot):
        self.bot = bot
        self.app = server.setup()
        self.running = False
        self.unloaded = False
        self.runner = None
        self.site = None
        if bot.is_ready():
            bot.loop.create_task(self.on_ready())

    @commands.Cog.listener()
    async def on_ready(self):
        """
        An event that runs when the bot connects to discord
        """
        if self.running or self.unloaded:
            return
        self.running = True
        print("== SERVER GOING UP ==")
        self.runner, self.site = await server.run(self.app)
        print("== SERVER IS UP ==")

    def cog_unload(self):
        """
        An event that runs when the cog is unloaded
        """
        self.unloaded = True
        print("== SERVER GOING DOWN ==")
        self.bot.loop.run_until_complete(self.runner.cleanup())
        print("== SERVER IS DOWN ==")


def setup(bot):
    """
    Setup the Connect My Pairs cog
    """
    bot.add_cog(ConnectMyPairs(bot))
