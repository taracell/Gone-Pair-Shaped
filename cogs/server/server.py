from discord.ext import commands
import discord
import asyncio
import aiohttp
import logging
from aiohttp import web
from . import routes


def setup():
    """
    Setup the aiohttp webserver for ConnectMyPairs
    """
    app = web.Application()

    routes.setup_routes(app)

    return app


async def run(app):
    """Run the server"""
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 9000, reuse_address=True, reuse_port=True)
    await site.start()
    return runner, site
