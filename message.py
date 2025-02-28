import json
import discord

from PIL import Image
from time import time

import os
import sys


sys.path.append(os.getcwd()+"/..")

from Utils.utils import DIRECTORY_SEPARATION, AUTOMATATIONS_FOLDER
from Utils.diccionarios import read_json
from Utils.imageshrinker import resize_image

from Discord.constants import CHANNELS_JSON_FILE, ROLES_JSON_FILE

QUEUE_DIRECTORY = AUTOMATATIONS_FOLDER + DIRECTORY_SEPARATION
QUEUE_DIRECTORY += "Discord" + DIRECTORY_SEPARATION
QUEUE_DIRECTORY += "queue"

MAX_LENGTH = 1700
IMAGE_LIMIT = 9000


def read_message_from_file(file, ids):
    f = open(file, "r", encoding="utf-8")

    channels = []
    message = ""
    files = []
    tagged = True

    channels_read = False
    message_read = False

    lines_existing = 0
    lines_counted = 0

    for i, line in enumerate(f):
        short = line.strip()
        if i == 0:
            tagged = short == "True"
        if i == 1:
            lines_existing = int(short)
        if i > 1:
            if not channels_read:
                if short.isnumeric():
                    channels.append(int(short))
                elif short in ids:
                    channels.append(ids.get(short))
                else:
                    print(f"{short} Channel Couldn't Be Founded")
                lines_counted += 1
                if lines_counted == lines_existing:
                    channels_read = True
                    lines_counted = -1
            elif channels_read and lines_counted < 0 and not message_read:
                lines_existing = int(short)
                lines_counted = 0
            elif channels_read and not message_read:
                message += line
                lines_counted += 1
                if lines_counted == lines_existing:
                    message_read = True
            else:
                if os.path.isfile(short):
                    files.append(short)

    if len(channels) == 0:
        return None

    return Message(message, channels, files, tagged)


def get_size(file_path):
    """
    Check if a file is an image and return the total number of pixels if it is.

    :param file_path: Path to the file to check.
    :return: Tuple total_pixels where is the total number of pixels if it's an
        image, or None if it's not an image.
    """
    try:
        img = Image.open(file_path)
        width, height = img.size
        return (width, height)
    except:
        # If an exception is raised, it's not an image
        return None


def compress_image(file_path):
    img_size = get_size(file_path)

    print(f"{file_path} -> {img_size}")

    if img_size is None:
        return

    if img_size[0] > IMAGE_LIMIT or img_size[1] > IMAGE_LIMIT:
        factor = IMAGE_LIMIT / max([img_size[0], img_size[1]])
        print(f"Refactor With {factor}")
        resize_image(file_path, file_path, factor)

class Message():
    def __init__(self, message, channels, files=[], roles=True):
        self.channels = []

        if channels:
            for sub_channels in channels:
                if isinstance(sub_channels, list):
                    for channel in sub_channels:
                        self.channels.append(channel)
                else:
                    self.channels.append(sub_channels)

        self.rol_tag = roles
        self.roles = read_json(ROLES_JSON_FILE)

        self.message = message

        self.files = []
        if isinstance(files, list):
            for file in files:
                if file is not None and os.path.isfile(file):
                    self.files.append(file)

    def save_file(self):
        for channel in self.channels:
            stamp = str(int(time()))
            file = QUEUE_DIRECTORY + DIRECTORY_SEPARATION + str(stamp) + ".txt"
            i = 1
            while os.path.exists(file):
                stamp = int(stamp) + i
                stamp = str(stamp)
                file = QUEUE_DIRECTORY + DIRECTORY_SEPARATION + str(stamp) + ".txt"
                i += 1
            f = open(file, "w", encoding="utf-8")

            messages_len = len(self.message.split("\n"))

            f.write(f"{self.rol_tag}\n")
            f.write("1\n")
            f.write(str(channel)+"\n")
            f.write(str(messages_len)+"\n")
            f.write(self.message+"\n")
            for send_file in self.files:
                f.write(send_file+"\n")

    def split_line(self, line):
        parts = []

        words = line.split(" ")

        count = 0
        aux = ""

        for i, word in enumerate(words):
            if count == 0:
                aux += word
                count += len(word)
            else:
                aux += " " + word
                count += len(word) + 1

            if i + 1 < len(words) and count + len(words[i+1]) + 1 > MAX_LENGTH:
                parts.append(aux)
                aux = ""
                count = 0

        parts.append(aux)

        return parts

    def split_lines(self, message):
        parts = []
        lines = message.split("\n")

        count = 0
        aux = ""

        for i, line in enumerate(lines):
            if len(line) > MAX_LENGTH:
                parts_aux = self.split_line(line)
                for part in parts_aux:
                    parts.append(part)
                continue
            if count == 0:
                aux += line
                count += len(line)
            else:
                aux += "\n" + line
                count += len(line) + 1

            if i + 1 < len(lines) and count + len(lines[i+1]) + 1 > MAX_LENGTH:
                parts.append(aux)
                aux = ""
                count = 0

        parts.append(aux)
        if len(parts[-1]) == 0:
            parts.pop(len(parts)-1)

        return parts

    def split_message(self, message):
        if message.count("\n") == 1:
            return self.split_line(message)
        else:
            return self.split_lines(message)

    async def send_message(self, bot):
        for channel_id in self.channels:
            channel = bot.get_channel(channel_id)
            if channel:

                message = self.message
                for rol, id in self.roles.items():
                    if self.rol_tag:
                        message = message.replace(f"@{rol}", f"<@&{id}>")
                    else:
                        message = message.replace(f"@{rol}", f"@\u200B{rol}")

                parts = self.split_message(message)
                for part in parts:
                    await channel.send(part)

                discord_files = []
                for file in self.files:
                    if os.path.isfile(file):
                        compress_image(file)
                        discord_files.append(discord.File(file))

                if len(discord_files) > 0:
                    for i in range(0, len(discord_files), 10):
                        end = i + 10
                        if end > len(discord_files):
                            end = len(discord_files)
                        await channel.send(files=discord_files[i: end])
            else:
                print(f"Can't Find Channel {channel_id}")


if __name__ == "__main__":
    #channels = read_json(CHANNELS_JSON_FILE)
    #message = read_message_from_file("test.txt", channels)

    #message = Message("Hola 3 @Tag Test, @Muted", [1081626700535836782])
    #message.save_file()

    compress_image("test_big.jpg")

    #exit = input("Exit")
