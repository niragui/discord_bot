from discord.message import Message
from discord.client import Client

import traceback

import json

import datetime

from .constants import PERMITS_FILES, MEMES_FILES
from .constants import UPDATE_TIME, COMMAND_START, MAX_LENGTH, BASE_SPOTIFY_LINK
from .utils import search_spotify, is_spotify_id, search_spotify_track

import os
import sys

sys.path.append(os.getcwd()+"/../..")

from spotify_api_git.src.session.spotifysession import SpotifySession
from spotify_api_git.src.session.counterreader import CounterReader
from spotify_api_git.src.items.spotifyalbum import SpotifyAlbum
from spotify_api_git.src.items.spotifyartist import SpotifyArtist
from spotify_api_git.src.items.spotifyplaylist import SpotifyPlaylist
from spotify_api_git.src.items.spotifytrack import SpotifyTrack

from spotify_api_git.src.searcher.searcher import Searcher
from spotify_api_git.src.searcher.search_album import SpotifySearchAlbum
from spotify_api_git.src.searcher.search_artist import SpotifySearchArtist
from spotify_api_git.src.searcher.search_playlist import SpotifySearchPlaylist

from script_handler.src.manual_handler import list_scripts, activate_script, deactivate_script, restart_script

TRACK_COMMAND = "track"
ALBUM_COMMAND = "album"
PLAYLIST_COMMAND = "playlist"
ARTIST_COMMAND = "artist"

LIST_SCRIPTS_COMMAND = "scripts"
RESTART_SCRIPTS_COMMAND = "restart"
ACTIVATE_SCRIPTS_COMMAND = "activate"
DEACTIVATE_SCRIPTS_COMMAND = "deactivate"

PARAMLESS_COMMANDS = [LIST_SCRIPTS_COMMAND]

HELP_COMMAND = "help"


class MessageHandler():
    def __init__(self,
                 bot: Client) -> None:
        self.bot = bot
        self.permits = {}
        self.memes = {}
        self.session = SpotifySession()
        self.reader = CounterReader(self.session)
        self.searcher = Searcher(self.session)
        self.last_update = datetime.datetime.now()
        self.load_dict_datas()

    def load_dict_datas(self):
        """
        Load the permits for each channel.
        """
        with open(PERMITS_FILES, "r", encoding="utf-8") as f:
            self.permits = json.load(f)

        with open(MEMES_FILES, "r", encoding="utf-8") as f:
            self.memes = json.load(f)

        self.last_update = datetime.datetime.now()

    def is_by_bot(self,
                  message: Message):
        """
        Check if the given message was sent
        by this bot instance

        Parameters:
            - message: Message to check
        """
        return message.author == self.bot.user

    def check_update(self):
        """
        Check if it should update the local permits copy
        and if needed updates them
        """
        check_time = datetime.datetime.now()

        time_since_last = check_time - self.last_update

        if time_since_last.total_seconds() // 60 > UPDATE_TIME:
            self.load_dict_datas()

    def get_channel_permits(self,
                            channel: str):
        """
        Given a channel name, it checks to see what comamnds
        it has permitted
        """
        self.check_update()

        return self.permits.get(channel, None)

    def split_message(self,
                      message: Message):
        """
        Given a message it spltis it into
        command and parameters:

        Parameters:
            - message: Message to split
        """
        msg_content = message.content.strip()
        command_parts = msg_content.split(" ")
        command = command_parts[0].lower()[1:]

        return command, command_parts[1:]

    def meme_name(self,
                  search_term: str,
                  command: str):
        """
        Give the new search_term to use in case there is a
        meme one related to it.

        Parameter:
            - search_term: Current Search Term
            - command: Command being used
        """
        memes_for_command = self.memes.get(command, None)
        print(self.memes)
        print(command)
        if memes_for_command is None:
            return search_term

        new_term = memes_for_command.get(search_term, search_term)

        return new_term

    def split_long_line(self,
                        line: str):
        """
        Split a long text into a list of long enough
        messages to send.

        Parameters:
            - line: Line to split into parts
        """
        parts = []

        words = line.split(" ")

        aux = ""

        for i, word in enumerate(words):
            add_word = word
            if len(add_word) > 0:
                add_word = f" {word}"

            aux += add_word

            if i + 1 == len(words):
                break

            next_length = len(aux) + len(words[i + 1]) + 1

            if next_length > MAX_LENGTH:
                parts.append(aux)
                aux = ""

        parts.append(aux)
        if len(parts[-1]) == 0:
            parts = parts[:-1]

        return parts

    async def send_message(self,
                           message: Message,
                           text: str):
        """
        Send a message by truncating it to secure
        that it doesn't cross the 4k limit

        Parameters:
            - message: Message to use to send
            - text
        """
        parts = []
        lines = text.split("\n")

        aux = ""

        for i, line in enumerate(lines):
            if len(line) > MAX_LENGTH:
                if len(aux) > 0:
                    parts.append(aux)
                    aux = ""
                parts_aux = self.split_line(line)
                parts.extend(parts_aux)
                continue
            
            add_line = line
            if len(aux) > 0:
                add_line = "\n" + line
            aux += add_line

            if i + 1 == len(lines):
                break

            next_length = len(aux) + len(lines[i + 1]) + 1

            if next_length > MAX_LENGTH:
                parts.append(aux)
                aux = ""

        parts.append(aux)
        if len(parts[-1]) == 0:
            parts = parts[:-1]

        for part in parts:
            await message.channel.send(part)

    async def track_function(self,
                             message: Message):
        """
        Handles a track command request

        Parameters:
            - message: Message that requested the track
        """
        command, params = self.split_message(message)

        if len(params) == 0:
            return

        search_term = None
        search_id = params[0]
        search_type = command
        if len(params) == 1 and not is_spotify_id(search_id):
            search_term = search_id

        if len(params) > 1:
            search_term = " ".join(params)

        if search_term is not None:
            search_term = self.meme_name(search_term, command)
            search_id, search_type = search_spotify_track(search_term, self.searcher)

        if search_id is None:
            return

        if search_type == "album":
            track = SpotifyAlbum(search_id, self.reader)
            streams = track.get_total_streams()
        else:
            track = SpotifyTrack(search_id, self.reader)
            streams = track.get_streams()
        
        item_link = f"{BASE_SPOTIFY_LINK}{search_type}/{search_id}"
        track_message = f"# [{track.name} - {track.get_credits()}](<{item_link}>)\n"
        track_message += f"**Streams** - {streams:,}"

        await self.send_message(message, track_message)

    async def playlist_function(self,
                                message: Message):
        """
        Handles a playlist command request

        Parameters:
            - message: Message that requested the playlist
        """
        command, params = self.split_message(message)

        if len(params) == 0:
            return

        search_term = None
        search_id = params[0]
        if len(params) == 1 and not is_spotify_id(search_id):
            search_term = search_id

        if len(params) > 1:
            search_term = " ".join(params)

        if search_term is not None:
            search_term = self.meme_name(search_term, command)
            search_id = search_spotify(search_term, self.searcher, SpotifySearchPlaylist)

        if search_id is None:
            return

        playlist = SpotifyPlaylist(search_id, self.reader)

        item_link = f"{BASE_SPOTIFY_LINK}{command}/{search_id}"
        playlist_message = f"# [{playlist.name}](<{item_link}>)\n"
        tracks = playlist.get_tracks()
        total_streams = 0
        for i, track in enumerate(tracks, 1):
            streams = track.get_streams()
            total_streams += streams
            playlist_message += f"\t#{i} - {track.name} - {track.get_credits()} - {streams:,}\n"
        playlist_message += f"**Total Streams** - {total_streams:,}"

        await self.send_message(message, playlist_message)

    async def album_function(self,
                             message: Message):
        """
        Handles a album command request

        Parameters:
            - message: Message that requested the album
        """
        command, params = self.split_message(message)

        if len(params) == 0:
            return

        search_term = None
        search_id = params[0]
        if len(params) == 1 and not is_spotify_id(search_id):
            search_term = search_id

        if len(params) > 1:
            search_term = " ".join(params)

        if search_term is not None:
            search_term = self.meme_name(search_term, command)
            search_id = search_spotify(search_term, self.searcher, SpotifySearchAlbum)

        if search_id is None:
            return

        album = SpotifyAlbum(search_id, self.reader)

        item_link = f"{BASE_SPOTIFY_LINK}{command}/{search_id}"
        album_message = f"# [{album.name} - {album.get_credits()}](<{item_link}>)\n"
        tracks = album.get_tracks()
        for i, track in enumerate(tracks, 1):
            streams = track.get_streams()
            album_message += f"\t#{i} - {track.name} - {track.get_credits()} - {streams:,}\n"
        streams = album.get_total_streams()
        album_message += f"**Total Streams** - {streams:,}"

        await self.send_message(message, album_message)

    async def list_saved_scripts(self,
                                 message: Message):
        """
        Handles a list scripts request

        Parameters:
            - message: Message that requested the album
        """
        command, params = self.split_message(message)

        if len(params) > 0:
            raise ValueError(f"List Scripts Take No Parameters")

        scripts = list_scripts()

        scripts_text = "# Active:"

        for script in scripts:
            if script[1]:
                scripts_text += f"{script[0]}\n"

        for script in scripts:
            if not script[1]:
                scripts_text += f"{script[0]}\n"

        await self.send_message(message, scripts_text)

    async def restart_saved_scripts(self,
                                    message: Message):
        """
        Handles a restart scripts request

        Parameters:
            - message: Message that requested the album
        """
        command, params = self.split_message(message)

        if len(params) == 0:
            raise ValueError(f"Restart Scripts Must Have Parameters")

        script_name = " ".join(params)

        restart_script(script_name)

        await self.send_message(message, f"{script_name} Restarted")

    async def activate_saved_scripts(self,
                                     message: Message):
        """
        Handles a restart scripts request

        Parameters:
            - message: Message that requested the album
        """
        command, params = self.split_message(message)

        if len(params) == 0:
            raise ValueError(f"Activate Scripts Must Have Parameters")

        script_name = " ".join(params)

        activate_script(script_name)

        await self.send_message(message, f"{script_name} Activated")

    async def deactivate_saved_scripts(self,
                                       message: Message):
        """
        Handles a restart scripts request

        Parameters:
            - message: Message that requested the album
        """
        command, params = self.split_message(message)

        if len(params) == 0:
            raise ValueError(f"Deactivate Scripts Must Have Parameters")

        script_name = " ".join(params)

        deactivate_script(script_name)

        await self.send_message(message, f"{script_name} Deactivated")

    async def artist_function(self,
                              message: Message):
        """
        Handles a track command request

        Parameters:
            - message: Message that requested the track
        """
        command, params = self.split_message(message)

        if len(params) == 0:
            return

        search_term = None
        search_id = params[0]
        if len(params) == 1 and not is_spotify_id(search_id):
            search_term = search_id

        if len(params) > 1:
            search_term = " ".join(params)

        if search_term is not None:
            search_term = self.meme_name(search_term, command)
            search_id = search_spotify(search_term, self.searcher, SpotifySearchArtist)

        if search_id is None:
            return

        artist = SpotifyArtist(search_id, self.reader)

        item_link = f"{BASE_SPOTIFY_LINK}{command}/{search_id}"
        artist_message = f"# [{artist.name}](<{item_link}>)\n"

        followers = artist.get_followers()
        artist_message += f"**Followers** - {followers:,}\n"

        pos_listeners = artist.get_listeners_rank()
        listeners = artist.get_monthly_listeners()
        if pos_listeners > 0:
            artist_message += f"**Listeners** - #{pos_listeners} {listeners:,}\n"
        else:
            artist_message += f"**Listeners** - {listeners:,}\n"
        cities = artist.get_top_cities()
        artist_message += "**Top Cities:**\n"
        for i, city in enumerate(cities, 1):
            city_listeners = city['numberOfListeners']
            artist_message += f"\t #{i} - {city['city']}, {city['country']} - {city_listeners:,}\n"

        top_tracks = artist.get_top_tracks()
        artist_message += f"**Top Tracks:**\n"
        for i, track in enumerate(top_tracks, 1):
            streams = track.get_streams()
            artist_message += f"\t #{i} - {track.name} - {streams:,}\n"

        await self.send_message(message, artist_message)

    def get_command_function(self,
                             command: str):
        """
        Given a command, it returns the function that handles the
        message of it
        """
        if command == TRACK_COMMAND:
            return self.track_function
        elif command == ALBUM_COMMAND:
            return self.album_function
        elif command == PLAYLIST_COMMAND:
            return self.playlist_function
        elif command == ARTIST_COMMAND:
            return self.artist_function
        elif command == LIST_SCRIPTS_COMMAND:
            return self.list_saved_scripts
        elif command == RESTART_SCRIPTS_COMMAND:
            return self.restart_saved_scripts
        elif command == ACTIVATE_SCRIPTS_COMMAND:
            return self.activate_saved_scripts
        elif command == DEACTIVATE_SCRIPTS_COMMAND:
            return self.deactivate_saved_scripts

        return None

    async def process_message(self,
                              message: Message):
        """
        Handle Message and returns what to
        reply in case there is something to
        """
        if self.is_by_bot(message):
            print("Ignored Cause Self Message")
            return

        msg_content = message.content.strip()
        if not msg_content.startswith(COMMAND_START):
            return

        if msg_content.startswith(COMMAND_START + COMMAND_START):
            return

        command_parts = msg_content.split(" ")
        command = command_parts[0].lower().replace(COMMAND_START, "")

        if len(command) == 0:
            return

        has_params = len(command_parts) > 1
        should_have_params = command in LIST_SCRIPTS_COMMAND

        if should_have_params and not has_params:
            print(f"Ignored Cause No Paramas [{msg_content}]")
            return

        guild = message.guild
        if guild is None:
            print("Ignored Cause Commands Only In Guild")
            return

        channel = message.channel
        channel_name = f"{guild.name}, {channel.name}"

        pos_commands = self.get_channel_permits(channel_name)

        if pos_commands is None:
            print(f"Ignored Cause No Commands Were Found For This Channel [{channel_name}]")
            return

        # Split the message into command and argument

        if command not in pos_commands:
            print(f"Ignored Cause Command Not Permitted For This Channel [{channel_name} -> {pos_commands}]")
            return

        command_handler = self.get_command_function(command)

        if command_handler is None:
            return

        try:
            await command_handler(message)
        except:
            print(traceback.format_exc())
            await self.send_message(message, "Error Handling Request, Sorry :)")