"""A web HTML response for aiohttp"""
from aiohttp import web


def html_response(text="", html=None, file=None, **kwargs):
    """

    :param file: A file that you would like to read from. Will be formatted
    :type file: str
    :param html: Your HTML that you would like to return
    :type html: str
    :param text: Synonymous to HTML
    :type text: str
    :return: The response for your website
    :rtype: web.Response
    """
    if file is not None:
        with open(file) as html:
            return web.Response(text=html.read(), content_type="text/html")
    else:
        return web.Response(text=html if html is not None else text, content_type="text/html")
