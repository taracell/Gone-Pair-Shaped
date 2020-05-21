"""All the views for the AIOHTTP server"""
from . import index

index = index.hello_world

__all__ = (
    index
)
