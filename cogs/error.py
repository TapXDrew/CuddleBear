import asyncio
import sys
import traceback

import discord
from discord.ext import commands


class CommandErrorHandler(commands.Cog):
    def __init__(self, bot):
        """
        :param bot: The bot instance that will be used
        """
        self.bot = bot  # This is how we will be interacting with the bot in the class
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """
        Handles errors raised while executing a command
        :param ctx: Information on the context of where the command was called
        :param error: The Exception that was called
        """
        if hasattr(ctx.command, 'on_error'):  # Ignores all basic command errors
            return
        
        ignored = (commands.CommandNotFound, discord.ext.commands.errors.CheckFailure, asyncio.TimeoutError)  # These are all the command errors that we will be ignoring
        error = getattr(error, 'original', error)  # The original error we will be checking
        
        if isinstance(error, ignored):  # If the error is in our tuple of ignored errors then we will do nothing
            return

        elif isinstance(error, commands.DisabledCommand):
            return await ctx.send(f'{ctx.command} has been disabled.')  # disabled=True was set in the command kwargs, so we can not use the command

        elif isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.author.send(f'{ctx.command} can not be used in Private Messages.')  # The command was decorated with @commands.guild_only but was used in a PM
            except Exception:
                pass  # We try to send a message, if we fail we do nothing

        elif isinstance(error, commands.BadArgument) or isinstance(error, commands.MissingRequiredArgument) or isinstance(error, commands.UserInputError):  # If the user uses the command incorrectly we show the proper way to use the command
            return await ctx.send(f"You did not use this command correctly! Use `{self.bot.command_prefix}Help {ctx.command.qualified_name}` for information on how to use the command!")
            # This happens whenever a user does not input the correct args, doesnt enter enough args, or enter no args. It sends basic information on using the command

        else:  # The command did not fall into any of the other categories so we will raise the error to the console so we can debug
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


def setup(bot):
    bot.add_cog(CommandErrorHandler(bot))
