import asyncio
import json
import os

import discord
from discord.ext import commands

from utils.userInfo import User
from utils.serverInfo import Server


class Moderation(commands.Cog):
    def __init__(self, bot):
        """
        :param bot: The bot instance that will be used
        """
        self.config = json.load(open(os.getcwd() + '/config/config.json'))  # The config file is loaded so we can use it later
        self.bot = bot

    def cog_check(self, ctx):
        """
        :param ctx: Context on where the command was called

        This is called before every single command, it lets us do some cool things. We will only use it to
        re-load the config file on each command tho
        """
        self.config = json.load(open(os.getcwd() + '/config/config.json'))  # The config file is re-loaded
        return True

    @commands.command(name="Close", aliases=['CS', 'C', 'closeSession'], help="Closes a support ticket", usage="Close")
    async def CMD_closeSession(self, ctx):
        """
        :param ctx: Context on where the command was called
        Closes a support ticket
        """
        user = discord.utils.get(ctx.guild.members, id=int(ctx.channel.name))   # We get all info on the user that we stored using a custom database class
        if not user:  # If this was not called inside of a support channel rwe return and do nothing
            return
        activeUser = User(bot=self.bot, ctx=ctx, user=user)  # we get the status of the users support ticket
        await ctx.send("Verifying with the user...")  # we send a message to the channel telling them we need to verify with the user
        try:  # try/except block to prevent errors
            while True:  # we create a loop
                activeUser.update_value("activeSession", 2)  # we update the session value to 2 so that other parts of out code function
                await user.send("Has your issue been solved? `Yes` or `No`\n*This will close automatically in 30 seconds if you do not respond*")  # we send a verify message to the user
                msg = await self.bot.wait_for('message', check=lambda m: m.author.id == user.id and not m.guild, timeout=30.0)  # Waits for the user to send a message
                if msg.content.lower() in ['y', 'ye', 'yes']:  # if they said yes we continue with the command and exit the loop
                    break
                elif msg.content.lower() in ['n', 'no']:  # if they said no we tell the channel that the user still needs help and we keep the ticket open
                    activeUser.update_value("activeSession", 1)
                    await ctx.send("The user still needs help! This channel will stay open")
                    return await user.send("Okay, I have kept the channel open")
                else:
                    await user.send("Please answer `Yes` or `No`")  # otherwise we loop again waiting for a message
        except asyncio.TimeoutError:  # if the user takes to long to reply we close the ticket
            pass
        # This is how we close the ticket, we set all values to 0 then close the ticket and delete the channel
        await ctx.send("Closing this ModMail Session...")
        await user.send("This ModMail session has been closed!")
        await asyncio.sleep(1)
        await ctx.channel.delete()

        activeUser.update_value("serverSelect", 0)
        return activeUser.update_value("activeSession", 0)

    @commands.command(name="Reply", aliases=['R', 'Respond'], help="Relies to a user in an active support session", usage="Reply <message>")
    async def CMD_reply(self, ctx, *, message=None):
        if message is None and not ctx.message.attachments:  # Checks if the message is blank
            return await ctx.send("You cant reply with a blank message")

        user = discord.utils.get(ctx.guild.members, id=int(ctx.channel.name))  # Gets the user
        server = Server(self.bot, ctx)  # Gets the server
        if user:  # If the user is valid we do this
            message = message.split(' ')  # We split the message

            for word in message:  # we check to see if we have any custom commands in the message
                if word[len(self.bot.prefix):] in server.commands:  # if we do then we send the reply of the custom command
                    await ctx.message.add_reaction("\N{THUMBS UP SIGN}")
                    return await user.send(server.commands[word[len(self.bot.prefix):]])

            message = " ".join(message)  # we join the message back to 1 string

            embed = discord.Embed(title=ctx.author.name, color=discord.Color.green())  # we create a rich embed
            if len(ctx.message.content) > 1024:  # we check to see if the message it soo long for one embed field, if so we split it into 2 fields
                embed.add_field(name=f"Message (1/2)", value=f"{message[:1024]}" if message else "Attachment(s) Below")
                embed.add_field(name=f"Message (2/2)", value=f"{message[1024:]}" if message else "Attachment(s) Below")
            else:  # otherwise we keep it as one field
                embed.add_field(name=f"Message (1/1)", value=f"{message}" if message else "Attachment(s) Below")
            await user.send(embed=embed)  # we now send the embed field
            for attachment in ctx.message.attachments if ctx.message.attachments else []:  # we send all message attachments
                await user.send(attachment.url)
            await ctx.message.add_reaction("\N{THUMBS UP SIGN}")  # we react to the !reply message to let the support manager know we sent the message

    @commands.command(name="Prefix", aliases=[], help="Set a new server prefix", usage="Prefix <prefix>")
    @commands.has_permissions(manage_guild=True)
    async def CMD_prefix(self, ctx, prefix=None):
        if prefix is None:
            return await ctx.send(f"The servers current prefix is `{self.bot.prefix}`")
        server = Server(self.bot, ctx)  # we get the server
        server.update_value("prefix", prefix)  # we update the server prefix
        await ctx.send(f"Okay! The prefix has been updated to {prefix}")  # we let the server know it worked

    @commands.command(name="Save", aliases=['CustomCommand', 'CC', 'S'], help="Saves a new custom command", usage="Save <name> <reply>")
    @commands.has_permissions(manage_guild=True)
    async def CMD_Save(self, ctx, name, *, response):
        server = Server(self.bot, ctx)  # we get the server
        server.save_customCommand(name, response)  # we save the command
        await ctx.send("Command Added!")  # we let the server know

    @commands.command(name="Delete", aliases=['D', 'Remove'], help="Delete a custom command", usage="Delete <name>")
    @commands.has_permissions(manage_guild=True)
    async def CMD_delCustomCommand(self, ctx, name):
        server = Server(self.bot, ctx)  # we get the server
        server.del_customCommand(name)  # we delete the command
        await ctx.send("Command Removed!")  # we let the server know

    @commands.command(name="Invite", aliases=['I', 'Inv'], help="Invite the bot to your server or join the support server!", usage="Invite")
    async def CMD_invite(self, ctx):
        embed = discord.Embed(title="Invite Links", color=discord.Color.green())
        embed.add_field(name="Bot Invite", value=f"[Invite me to your server!]({self.config['Bot']['InviteLink']})")
        embed.add_field(name="Bot Invite", value=f"[Join my support server!]({self.config['Bot']['ServerInviteLink']})")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Moderation(bot))
