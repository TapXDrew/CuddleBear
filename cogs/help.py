import discord
from discord.ext import commands


class Help(commands.Cog):
    """
    Command file to be loaded into a discord bot
    """
    def __init__(self, bot):
        """
        Initializes the bot
        :param bot: discord.Bot
        """
        self.bot = bot  # Lets us use the bot in various other parts of the bot to access information like the voice state of the bot

    @commands.command(name='Help', aliases=['H'], help="The command you are looking at", usage="Help [command]")
    async def help(self, ctx, search_command=None):
        """
        Help command shows all other commands
        :param ctx: Information on the context of where the command was called
        :param search_command: Shows a more detailed explanation of the command and how to use it
        """
        if not search_command:  # We check if they are wanting help with a specific command, if not we do this
            embed = discord.Embed(title=f'{self.bot.user.name} Help Page', color=discord.Color.green())  # Create a rich embed object
            for command in self.bot.commands:  # loop over all commands
                if command.name in ['jishaku'] or command.hidden:  # if the command is hidden, or the name is jishaku we skip it
                    continue
                embed.add_field(name=command.qualified_name, value=command.help, inline=False)  # Otherwise we will add an embed field with the name of the command
            embed.set_footer(text=f"Look at more info on a command with {self.bot.prefix}Help <command>")  # here we let the user know how to get more info on a command
            embed.set_thumbnail(url=self.bot.user.avatar_url)
            await ctx.send(embed=embed)  # we send the embed object to the channel
        else:  # the user needs help with a specific command
            for command in self.bot.commands:  # we loop over all commands
                if command.name.lower() == search_command.lower() or search_command.lower() in [aliases.lower() for aliases in command.aliases]:  # we check if the command they need help with is a real command name or aliases
                    embed = discord.Embed(title=command.name, color=discord.Color.green())  # if it is we create a rich embed for it
                    embed.add_field(name="Command Help", value=command.help, inline=False)  # we all a lot of embed fields for the command to show info
                    embed.add_field(name="Command Usage", value=self.bot.prefix+command.usage, inline=False)
                    embed.add_field(name="Command Aliases", value=', '.join(command.aliases) if command.aliases else "No Aliases", inline=False)
                    embed.set_footer(text="<> are required command parameters and [] is optional parameters")
                    embed.set_thumbnail(url=self.bot.user.avatar_url)
                    return await ctx.send(embed=embed)  # we send the embed
            await ctx.send("Sorry but I could not find that command!")  # if the name did not match a command name or aliases we send them a message saying we could not find the command


def setup(bot):
    bot.add_cog(Help(bot))
