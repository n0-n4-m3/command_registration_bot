import json

from aiogram import Bot, Dispatcher, html
from aiogram import Bot, Dispatcher, F, Router, html
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.scene import Scene, SceneRegistry, ScenesManager, on
from aiogram.fsm.storage.memory import SimpleEventIsolation
from aiogram.types import KeyboardButton, Message, ReplyKeyboardRemove, PollAnswer
from aiogram.utils.keyboard import ReplyKeyboardBuilder

start_text = json.load(open("./questions/light_of_gospel.json"))["start_text"]

from os import getenv
TOKEN = getenv("BOT_TOKEN")

bot = Bot(token=TOKEN) # type: ignore