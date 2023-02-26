from aiogram import Dispatcher
from bot.handlers.user import callback
from bot.handlers.user import command


def register_all_handlers(dp: Dispatcher):

    handlers = [
        command.register_user_handlers,
        callback.register_callback_handlers,
    ]

    for handler in handlers:
        handler(dp)
