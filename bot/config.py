import os

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from dotenv import load_dotenv

from bot.database.models.goods import init_db
from bot.handlers import register_all_handlers
from bot.middlewares import setup_middleware
from bot.misc.scheduler import scheduler
from bot.utils.set_commands import set_bot_commands
from aiogram.utils.executor import start_webhook


DEPLOY = os.environ.get('DEPLOY', False)
if not DEPLOY:
    from bot.data import data_path
    load_dotenv(dotenv_path=f'{data_path}/.env')

BOT_TOKEN = str(os.environ.get('BOT_TOKEN'))
ADMIN_ID = os.getenv('ADMIN_ID')

bot = Bot(BOT_TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, storage=MemoryStorage())

WEBHOOK_PORT = 8080

WEBHOOK_HOST = 'https://tsinovyk.herokuapp.com/'
WEBHOOK_PATH = ''
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

WEBAPP_HOST = 'localhost'  # or ip
WEBAPP_PORT = int(os.getenv('PORT', 5000))


async def on_startup(_):

    if DEPLOY:
        await bot.set_webhook(url=WEBHOOK_URL, drop_pending_updates=True)

    init_db()
    scheduler()
    setup_middleware(dp)
    register_all_handlers(dp)

    await set_bot_commands(dp)


async def on_shutdown(_):

    await bot.delete_webhook()
    await dp.storage.close()
    await dp.storage.wait_closed()


def main():

    if DEPLOY:
        start_webhook(
            dispatcher=dp,
            webhook_path=WEBHOOK_PATH,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            skip_updates=True,
            host=WEBHOOK_HOST,
            port=WEBAPP_PORT
        )

    else:
        executor.start_polling(dp, skip_updates=True, on_startup=on_startup)

