from typing import Type, Union, List

import os
import sys

sys.path.append(os.getcwd()+"/..")

from spotify_api_git.src.searcher.searcher import Searcher
from spotify_api_git.src.searcher.search_item import SpotifySearchItem
from spotify_api_git.src.searcher.search_track import SpotifySearchTrack
from spotify_api_git.src.searcher.search_album import SpotifySearchAlbum

def search_spotify_track(search_item: str,
                         searcher: Searcher):
    """
    Searchs on Spotify API for the asked item and filters
    it to the best response of the searched class.

    Parameters:
        - search_item: Term to search
        - searcher: Spotify Searcher item
    """
    all_results = searcher.search(search_item)

    class_results = []
    for search_result in all_results:
        if isinstance(search_result, SpotifySearchTrack):
            class_results.append(search_result)
        if isinstance(search_result, SpotifySearchAlbum):
            album_type = search_result.album_type
            if album_type == "SINGLE":
                class_results.append(search_result)

    if len(class_results) == 0:
        return None, None
    
    same_name = [item for item in class_results if item.name == search_item]
    if len(same_name) == 0:
        result_item = class_results[0]
    else:
        same_name_class_results = []
        for search_result in same_name:
            if isinstance(search_result, SpotifySearchTrack):
                same_name_class_results.append(search_result)

        if len(same_name_class_results) > 0:
            result_item = same_name_class_results[0]
        else:
            result_item = same_name[0]

    return result_item.item_id, result_item.item_type


def search_spotify(search_item: str,
                   searcher: Searcher,
                   searched_class: Type[SpotifySearchItem]):
    """
    Searchs on Spotify API for the asked item and filters
    it to the best response of the searched class.

    Parameters:
        - search_item: Term to search
        - searcher: Spotify Searcher item
        - searched_class: What class to search for.
    """
    all_results = searcher.search(search_item)

    class_results = []
    for search_result in all_results:
        if isinstance(search_result, searched_class):
            class_results.append(search_result)

    if len(class_results) == 0:
        return None

    return class_results[0].item_id


ID_STANDARD_LENGTH = 22


def is_spotify_id(possible_id: str):
    """
    Check if a string matches the basic needs for being a Spotify ID

    Parameters:
        - possible_id: String that could be an id
    """
    if len(possible_id) < ID_STANDARD_LENGTH:
        return False

    if not any(char.isdigit() for char in possible_id):
        return False

    if all(char.isdigit() for char in possible_id):
        return False

    if possible_id.isdecimal():
        return False

    if possible_id.upper() == possible_id:
        return False

    if possible_id.lower() == possible_id:
        return False

    return True