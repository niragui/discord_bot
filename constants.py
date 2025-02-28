import os
import sys

sys.path.append(os.getcwd()+"/..")

from Utils.utils import AUTOMATATIONS_FOLDER, DIRECTORY_SEPARATION
from Utils.diccionarios import read_json

THIS_FOLDER = AUTOMATATIONS_FOLDER + DIRECTORY_SEPARATION + "Discord" + DIRECTORY_SEPARATION

CHANNELS_JSON_FILE = THIS_FOLDER + "channels.json"
ROLES_JSON_FILE = THIS_FOLDER + "roles.json"

CHANNELS_PARSER = read_json(THIS_FOLDER + "directions.json")

if __name__ == "__main__":
    print(CHANNELS_PARSER)
    print(CHANNELS_PARSER.get("Certification TOTC"))

    exit = input("Exit")