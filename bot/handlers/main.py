from aiogram import Dispatcher
from bot.handlers.user.callback import register_callback_handlers
from bot.handlers.user.command import register_user_handlers


def register_all_handlers(dp: Dispatcher):

    handlers = [
        register_user_handlers,
        register_callback_handlers,
    ]

    for handler in handlers:
        handler(dp)

