from aiogram import types
from bot.middlewares.locale_middleware import get_text as _


async def set_bot_commands(dp):

    await dp.bot.set_my_commands([
        types.BotCommand('cart', _('Список товарів')),
        types.BotCommand('help', _('Підказки')),
        types.BotCommand('language', _('Мова')),
        types.BotCommand('stores', _('Список доступних крамниць'))
    ])
