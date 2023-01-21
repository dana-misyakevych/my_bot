import random
import re

from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.types import Message

from bot.config import dp
from bot.database.models.goods import User
from bot.data.texts import answers
from bot.keyboards.reply_keyboards import help_kb
from bot.misc.pars import validate_shop
from bot.middlewares.locale_middleware import get_text as _


class UsersMiddleware(BaseMiddleware):

    @staticmethod
    def is_url(expression: str):
        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(" \
                r"\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        url = re.findall(regex, expression)

        return [x[0] for x in url]

    @staticmethod
    async def on_process_message(message: Message, data: dict[str]):

        lang = str(User.get_user_locale(message.from_user.id))
        store = validate_shop(message.text)

        if message.text[0] == '/':

            commands = [x.command for x in await dp.bot.get_my_commands()]
            if message.text[1:] not in commands and message.text != '/start':
                await message.answer(_('Unavailable command', locale=lang), reply_markup=help_kb)
                raise CancelHandler()

        elif not UsersMiddleware.is_url(message.text):

            answer = random.choice(answers)
            await message.answer(_(answer, locale=lang), reply_markup=help_kb)
            raise CancelHandler()

        elif not store:
            await message.answer(_("Something went wrong 😮‍💨, try again later", locale=lang), reply_markup=help_kb)
            raise CancelHandler()
