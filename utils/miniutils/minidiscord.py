import discord
from discord.ext import commands
import functools

class MiniContext(commands.Context):
    def __init__(self, context):
        commands.Context.__init__(self, **context.__dict__)
        self.mention = self.channel.mention if isinstance(self.channel, discord.TextChannel) else "No channel"

    async def send(self,
                   description=None, *,
                   title=None,
                   color=None,
                   tts=False,
                   file=None,
                   files=None,
                   delete_after=None,
                   nonce=None):
        my_perms = self.channel.permissions_for(self.channel.guild.me) if isinstance(self.channel, discord.TextChannel) else None
        if not isinstance(self.channel, discord.TextChannel) or my_perms.embed_links:
            embed = discord.Embed(
                title=title,
                description=description,
                color=color,
            )
            return await self.channel.send(
                embed=embed,
                tts=tts,
                file=file,
                files=files,
                delete_after=delete_after,
                nonce=nonce,
            )
        else:
            return await self.channel.send(
                (f"> **{title}**" if title is not None else "") +
                (f"\n{description}" if description is not None else ""),
                tts=tts,
                file=file,
                files=files,
                delete_after=delete_after,
                nonce=nonce,
            )

def minictx(*args, **kwargs):
    def deco(function):
        @functools.wraps(function)
        async def predicate(cog, ctx, *function_args, **function_kwargs):
            ctx = MiniContext(ctx)
            return await function(cog, ctx, *function_args, **function_kwargs)
        return predicate
    return deco
