import json

start_text = json.load(open("./questions/light_of_gospel.json"))["start_text"]

from os import getenv
TOKEN = getenv("BOT_TOKEN")