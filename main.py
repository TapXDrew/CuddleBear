import asyncio
import json
import os
import traceback

import discord
from discord.ext import commands
from discord.utils import get

from utils.serverInfo import Server
from utils.userInfo import User

initial_extensions = [  # The command files that we will load into the bot, located in the 'cogs' folder
                "cogs.modMail",
                "cogs.error",
                "cogs.help"
                    ]


class CuddleBear(commands.AutoShardedBot):
    """
    This is our bot, we need to create an instance of the bot and run it for it to be online
    """
    def __init__(self):
        """
        The __init__ method is called whenever an instance of the class is made, it initializes the class
        """
        self.prefix = None
        self.config = json.load(open(os.getcwd() + '/config/config.json'))  # Lets us use the config.json file in out bot

        super().__init__(command_prefix=commands.when_mentioned_or(self.get_prefix), case_insensitive=True)  # We are inheriting from the class commands.AutoShardedBot so we also inherit from its __init__ using super()

        self.remove_command('help')  # Remove the help command so we can add our own

        er = 0
        for extension in initial_extensions:
            try:
                self.load_extension(extension)  # Loads in the extension
                print(f"Loaded {extension}")
            except Exception:
                er += 1
                print(f"Failed to load extension {extension}.")  # If it fails, we print the traceback error
                traceback.print_exc()
        print(f"All cog files loaded - {er} error(s)")
        try:
            self.load_extension('jishaku')
        except Exception:
            print("Use 'pip install jishaku' to get access to more owner-only commands")
        print("\nBot Starting...")

    async def get_prefix(self, message):
        """
        Returns the server prefix stored in a database; this lets us have per-server prefixes
        :param message: The message object that was sent
        """
        self.prefix = Server(self, message).prefix  # Gets the server prefix
        return commands.when_mentioned_or(self.prefix)(self, message)  # Sets the stored prefix as the prefix to be used in the server

    async def on_message(self, message):
        """
        Triggered whenever a message is sent that the bot has access to
        :param message: The message object that was sent
        """
        activeUser = User(bot=self, ctx=message, user=message.author)  # Gets information on the user from out database

        self.config = json.load(open(os.getcwd() + '/config/config.json'))  # Reloads the config file to make sure we have the most up-to-date information in it
        if message.author == self.user or message.author.bot:  # If it is the bot sending a message, ignore it
            return
        if message.content == 'close':
            c = []
            for guild in self.guilds:
                for channel in guild.channels:
                    c.append(channel)
            channel = discord.utils.get(c, name=str(message.author.id))
            await channel.send("The user has terminated this ModMail Session, the channel will stay open but they can no longer contact you with the same ModMail session, to close the channel use the `close`  command")
            await message.author.send("This ModMail session has been closed!")
            activeUser.update_value("serverSelect", 0)
            return activeUser.update_value("activeSession", 0)
        if not message.guild:  # If we are not in a server, then we received a DM
            relations = [guild for guild in self.guilds if message.author in guild.members]  # This is a list of all servers that the user and the bot have in common
            if not activeUser.activeSession and activeUser.serverSelect != 1:
                activeUser.update_value("activeSession", 1)  # Sets the user to be in an active session
                activeUser.update_value("serverSelect", 1)  # Lets the bot know for future reference that the user is still selecting what server he needs help in
                embed = discord.Embed(name="What server do you need help in?", color=discord.Color.green())  # Creates an embed object
                embed.add_field(name="Possible Servers", value='\n'.join([f'{number+1}) {guild.name}' for number, guild in enumerate(relations)]))  # Shows all of the servers that the user and the bot have in common
                embed.set_footer(text="Please select a guild to get support in (EX 1)")  # Sets the embed footer text
                await message.author.send(embed=embed)  # Sends the embed to the user

                while True:  # Creates a loop
                    try:
                        msg = await self.wait_for('message', check=lambda m: m.author.id == message.author.id, timeout=30.0)  # Waits for the user to send a message
                        if msg.content in [str(number+1) for number, _ in enumerate(relations)]:  # Checks if the message in a number (ex 1, 2, 3)
                            server = relations[int(msg.content)-1]  # If it is a number then we gets the server object
                            activeUser.update_value("serverSelect", server.id)  # Lets the bot know that the user has chosen a server for help in
                            await message.author.send(f"Okay! You now have an active ModMail session open with {server.name}! You can now send your question\n*To manually close the session say `close`*")  # Sends to the user that the bot is ready to send messages to the help server
                            print(f"Session Created with {server.name}")
                            channel = get(server.channels, name=str(message.author.id))
                            if not channel:
                                channel = await server.create_text_channel(str(message.author.id))
                                everyone = get(server.roles, name="@everyone")
                                await channel.set_permissions(everyone, read_messages=False, send_messages=False)
                                await channel.send(everyone)

                            break
                        elif message.content in ["quit", "stop"]:  # If the user wrote quit or stop we return
                            activeUser.update_value("activeSession", 0)
                            activeUser.update_value("serverSelect", 0)
                            return
                        else:  # If they did not enter a valid number and did not say quit or stop, we continue
                            await message.author.send(f"Please pick a number between 1 and {len(relations)}")
                            continue
                    except asyncio.TimeoutError:
                        activeUser.update_value("activeSession", 0)
            else:
                if activeUser.serverSelect not in [0, 1]:  # Checks what type of active session is open. 0 means Closed, 1 means selecting a server, anything else means it is a server ID
                    if activeUser.activeSession == 2:  # if the active session is set to 2 then we do nothing
                        return
                    server = discord.utils.get(self.guilds, id=activeUser.serverSelect)  # We get the server we need based on the user
                    channel = get(server.channels, name=str(message.author.id))  # we get the channel
                    await channel.send(f"{message.author} --> {message.content}")  # we send the message to the chanel
                    return await message.author.send(f"The support team in {server.name} has received your question!\n`{message.content}`")  # we send that the message was sent and recieved

        else:  # We are in a server so we will check to see if we are using a custom command
            await self.get_prefix(message)  # We get the server prefix
            if message.content.startswith(self.prefix):  # We check if their message started with the prefix
                server = Server(self, message)  # if it did then we check if its a custom command so we get the server info stored in out database
                command_name = message.content.split(" ")[0][len(self.prefix):].lower()  # we get the command name the author used
                if command_name in server.commands:  # if the server has saved that as a custom command
                    return await message.channel.send(server.commands[command_name])  # we will return the output of the command
            await self.process_commands(message)  # We now process the message to see if there are any non-custom commands in it (This is only called if there was no custom command before it)

    async def status_updater(self):
        while True:
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=f"{len(self.guilds)} servers for ModMail!"))
            await asyncio.sleep(60)

    async def on_ready(self):
        """
        Triggered whenever the bot becomes ready for use
        """
        # This prints out basic information of the bot such as the name and ID along with what version of Discord.py is being used to run the bot
        self.loop.create_task(self.status_updater())
        print("------------------------------------")
        print("Bot Name: " + self.user.name)
        print("Bot ID: " + str(self.user.id))
        print("Discord Version: " + discord.__version__)
        print("------------------------------------")

    def run(self):
        """
        This is how we run the bot
        """
        super().run(self.config["Bot"]["Token"], reconnect=True)


if __name__ == "__main__":
    CuddleBot = CuddleBear()
    CuddleBot.run()
