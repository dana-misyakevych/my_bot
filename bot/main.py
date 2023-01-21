from aiogram import executor

from bot.config import dp
from database.models.goods import init_db
from handlers.main import register_all_handlers
from middlewares import setup_middleware
from misc.scheduler import scheduler
from utils.set_commands import set_bot_commands


async def on_startup(_):

    init_db()
    scheduler()
    setup_middleware(dp)
    register_all_handlers(dp)

    await set_bot_commands(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)
