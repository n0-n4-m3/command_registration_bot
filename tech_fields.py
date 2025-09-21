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

import gspread
from google.oauth2.service_account import Credentials
from base64 import urlsafe_b64encode

# Укажите путь к вашему JSON-файлу с ключом
CREDENTIALS_FILE = './credentials.json'

# Укажите URL вашей таблицы
SPREADSHEET_URL = 'https://docs.google.com/spreadsheets/d/1xwj_NPtjRO9Jb_D3Eu-Au2vCmCpngAwRmYy-gWTHuY4/edit'

# Настройка доступа
scopes = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/drive']

credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scopes)
gc = gspread.authorize(credentials)

sheet = gc.open_by_url(SPREADSHEET_URL).sheet1 