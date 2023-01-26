import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from dotenv import load_dotenv

load_dotenv(dotenv_path='/home/oleh/PycharmProjects/tsinovyk/bot/data/.env')

DEPLOY = False

BOT_TOKEN = str(os.getenv('BOT_TOKEN'))
ADMIN_ID = os.getenv('ADMIN_ID')

bot = Bot(BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

WEBHOOK_PORT = 8080
WEBHOOK_HOST = ''
WEBHOOK_PATH = BOT_TOKEN
