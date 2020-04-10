
            elif isinstance(error, disclaimer.NotAgreedError):
                return await ctx.send(
                    f"Someone who has `manage server` and `manage roles` has to agree to the terms and conditions "
                    f"before you can use this command. They can do this with `{ctx.bot.get_main_custom_prefix(ctx)}"
                    f"terms`",
                    title=f"{ctx.bot.emotes['error']} No permissions",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, disclaimer.NotGuildOwnerError):
                return await ctx.send(
                    f"You're not the owner of this guild, so you can't run this command",
                    title=f"{ctx.bot.emotes['error']} No permissions",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, commands.CommandOnCooldown):
                rem = fix_time(error.retry_after)
                return await ctx.send(
                    f"Oh no! it looks like this command is on a cooldown! try again in `{rem}`!",
                    title=f"{ctx.bot.emotes['error']} Too fast!",
                    color=ctx.bot.colors["error"]
                )

            elif isinstance(error, asyncio.TimeoutError):
                return await ctx.send(
                    f"This took a bit too long, try again and hope that both you and our servers are "
                    f"faster next time",
                    title=f"{ctx.bot.emotes['error']} Zzzzzzzzz",
                    color=ctx.bot.colors["error"]
                )

            else:  # unknown error
                print("Got an error: " + str(error) + " of type " + str(type(error)))
                exception_status = "could not be"
                try:
                    exceptions_channel = ctx.bot.get_channel(exceptions_channel_id)
                    paginator = commands.Paginator(prefix='```python\n')
                    for index in range(0, len(str(error)), 1980):
                        paginator.add_line(str(error)[index:index + 1980])
                    try:
                        raise error
                    except Exception:
                        trace = traceback.format_exc()
                    for line in trace.splitlines(keepends=False):
                        paginator.add_line(line)
                    my_permissions = iter(ctx.channel.permissions_for(ctx.me))
                    my_permissions_dict = {}
                    for (permission, value) in my_permissions:
                        my_permissions_dict[permission] = str(value)
                    author_permissions = iter(ctx.channel.permissions_for(ctx.author))
                    author_permissions_dict = {}
                    for (permission, value) in author_permissions:
                        author_permissions_dict[permission] = str(value)
                    for page in paginator.pages:
                        await exceptions_channel.send(page)
                    await exceptions_channel.send(f"> **My permissions:** `{my_permissions_dict}`\n\n"
                                                  f"> **Their permissions:** `{author_permissions_dict}`\n\n"
                                                  f"> **Guild:** {str(ctx.guild or 'No guild')} `ID: {str(ctx.guild.id) if ctx.guild else 'No guild'}`\n\n"
                                                  f"> **Channel:** `ID: {ctx.channel.id if ctx.channel else 'No channel'}`\n\n"
                                                  f"> **User:** {str(ctx.author)} `ID: {str(ctx.author.id)}`\n\n"
                                                  f"> **Command:** {ctx.command.qualified_name} `"
                                                  f"Invoked with: {ctx.invoked_with}, "
                                                  f"Command: {ctx.command.name}`\n"
                                                  f"> **Case ID:** {str(ctx.message.id)[-4:-1]}")
                    exception_status = "has been"
                except Exception as e:
                    print("Could not send an error to the exceptions channel: " + str(e))

                ctx.command.reset_cooldown(ctx)

                e = discord.Embed(title="Oops!",
                                  description=f"It looks like something went wrong. This error {exception_status} "
                                              f"sent to our developers, if you want more help with this command please"
                                              f" report the **Case ID `{str(ctx.message.id)[-4:-1]}`** to our [support "
                                              f"team](https://discord.gg/bPaNnxe)",
                                  color=ctx.bot.colors["error"])
                e.set_footer(text=f"{str(error)}",
                             icon_url='https://cdn.discordapp.com/emojis/459634743181574144.png?v=1')
                try:
                    return await ctx.send(embed=e)
                except discord.HTTPException:
                    try:
                        return await ctx.send(
                            f"There was an error. This error {exception_status} sent to our "
                            f"developers, if you want more help with this command please report the **Case "
                            f"ID `{str(ctx.message.id)[-4:-1]}`** to our support team ||"
                            f"https://discord.gg/bPaNnxe||",
                            title=f"**OOPS!**",
                            color=ctx.bot.colors["error"])
                    except discord.HTTPException:
                        try:
                            if ctx.guild:
                                return await ctx.author.send("Hey! We couldn't access you in " + str(ctx.guild),
                                                             embed=e)
                                # Send to the author's DMs
                        except discord.HTTPException:
                            pass  # There's nothing left to try...
            try:
                return await ctx.send_help(ctx.command)
            except discord.HTTPException:
                try:
                    if ctx.guild:
                        return await send_help(ctx, ctx.author, ctx.command)
                        # Send to the author's DMs
                except discord.HTTPException:
                    pass  # There's nothing left to try...
        except discord.HTTPException as e:
            try:
                await ctx.author.send(f"Hey! We couldn't access you in {str(ctx.guild)} because I don't have "
                                      f"enough permissions to give you the error... Here it is - {str(e)}")
            except discord.HTTPException:
                pass  # There's nothing left to try...


def setup(bot):
    bot.add_cog(ErrorHandler(bot))
