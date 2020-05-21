"""The index page for the AIOHTTP server"""
from aiohttp import web
from ..utils import responses

form = f"""

"""


async def hello_world(request):
    """Send a basic 'hello world' response"""
    return responses.html_response(html='Hello World!')
