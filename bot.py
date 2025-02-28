import discord
from discord.ext import tasks
from dotenv import load_dotenv
from shutil import copyfile
import json
import traceback
import os
import sys

from message import read_message_from_file
from constants import CHANNELS_JSON_FILE, ROLES_JSON_FILE

from src.handle_message import MessageHandler

# Load environment variables from a .env file
load_dotenv()

# Get the Discord bot token from environment variables
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")


def main():
    """
    Main function to run the Discord bot
    """

    # Set up Discord intents (permissions) - can customize as needed
    intents = discord.Intents.default()
    intents.message_content = True

    # Initialize the bot client with specified intents
    bot = discord.Client(intents=intents)
    commands_handler = MessageHandler(bot)

    # Event triggered when the bot is ready and connected to Discord
    @bot.event
    async def on_ready():
        """
        Actions to perform when the bot is ready.
        This will read channel and role IDs from the guilds and start the message loop.
        """
        try:
            read_ids(bot)
            read_roles(bot)
            print(f"Bot is connected to {len(bot.guilds)} server(s)")

            # Start the task loop (runs every 10 seconds)
            myLoop.start()

        except Exception as e:
            print(f"Error during startup: {e}")
            sys.exit(1)

    def read_ids(bot):
        """
        Reads and stores channel IDs of each guild the bot is connected to in a JSON file.
        """
        try:
            channels = {}
            for guild in bot.guilds:
                for channel in guild.channels:
                    private_id = f"{guild.name}, {channel.name}"
                    channels[private_id] = channel.id

            # Save the channels to a JSON file
            with open(CHANNELS_JSON_FILE, "w") as f:
                json.dump(channels, f, indent=4)

            print(f"Channel IDs saved to {CHANNELS_JSON_FILE}")

        except Exception as e:
            print(f"Error while reading channel IDs: {e}")

    def read_roles(bot):
        """
        Reads and stores role IDs of each guild the bot is connected to in a JSON file.
        """
        try:
            roles = {}
            for guild in bot.guilds:
                for role in guild.roles:
                    private_id = f"{role}"
                    roles[private_id] = role.id

            # Save the roles to a JSON file
            with open(ROLES_JSON_FILE, "w") as f:
                json.dump(roles, f, indent=4)

            print(f"Role IDs saved to {ROLES_JSON_FILE}")

        except Exception as e:
            print(f"Error while reading role IDs: {e}")

    @bot.event
    async def on_message(message):
        """
        Event listener for when a new message is received in any channel the bot has access to.
        Currently, it ignores any message from the bot itself.
        """
        await commands_handler.process_message(message)

    @tasks.loop(seconds=10)
    async def myLoop():
        """
        A background task that runs every 10 seconds to check the 'queue' folder
        for files to process as messages.
        """
        try:
            # Load channel data from JSON
            with open(CHANNELS_JSON_FILE, "r") as f:
                channels = json.load(f)

            # Get the list of files in the 'queue' directory
            file_list = sorted(os.listdir("queue"))

            # Process each file in the queue
            for file in file_list:
                msg_file = os.path.join("queue", file)
                err_direct = os.path.join("error", file)

                if os.path.isfile(msg_file):
                    try:
                        # Read the message from the file and find the associated channel
                        message = read_message_from_file(msg_file, channels)

                        if message:
                            error_count = 0
                            while True:
                                try:
                                    # Send the message
                                    await message.send_message(bot)
                                    print(f"Message from {file} sent successfully.")
                                    break
                                except Exception as e:
                                    error_count += 1
                                    if error_count > 3:
                                        # Move the file to 'error' directory after 3 failed attempts
                                        copyfile(msg_file, err_direct)
                                        print(f"Failed to send message from {file}. Moved to 'error'.")
                                        break
                                    else:
                                        print(f"Error sending message from {file}: {e}")
                                        continue

                    except Exception as e:
                        # If processing the message fails, move it to 'error' directory
                        copyfile(msg_file, err_direct)
                        print(f"Error processing {file}: {e}")

                    finally:
                        # Clean up by removing the original file from the queue
                        print(f"File {file} processed and removed.")
                        os.remove(msg_file)

        except Exception as e:
            print(f"Error in myLoop task: {e}")

    # Run the bot using the token
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    main()
