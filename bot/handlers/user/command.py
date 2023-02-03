from aiogram import Dispatcher, types

from bot.database.models.goods import Order
from bot.misc.functions import save_to_db, find_product_in_another_store
from bot.keyboards.custom_keyboards import show_shopping_cart, list_of_shops, language_keyboard
from bot.middlewares.throttling import rate_limit
from bot.misc.pars import big_parser, validate_shop
from bot.middlewares.locale_middleware import get_text as _
from bot.data.texts import HELP_COMMAND


@rate_limit(limit=3)
async def start_command(message: types.Message):

    await message.answer(text=_(HELP_COMMAND), reply_markup=language_keyboard())


@rate_limit(limit=3)
async def help_command(message: types.Message):

    await message.answer(text=_(HELP_COMMAND), reply_markup=language_keyboard())


@rate_limit(limit=3)
async def list_of_stores(message: types.Message):

    text = _('Shops are available: ')
    await message.answer(text=text, reply_markup=list_of_shops())


@rate_limit(limit=3)
async def shopping_cart(message: types.Message):

    orders = Order.get_user_orders(message.from_user.id)

    if not orders:
        return await message.answer(text=_('Your cart is empty 🧐'))

    inline_keyboard = show_shopping_cart(orders, price_status=True, callback_data='order-name')
    await message.answer(text=_('Here\'s your shopping cart:'), reply_markup=inline_keyboard)


@rate_limit(limit=3)
async def set_language(message: types.Message):

    await message.answer(text='🇺🇦 Оберіть мову спілкування\n'
                              '🇬🇧 Chose your language\n'
                              '🇵🇱 Wybierz swój język',
                         reply_markup=language_keyboard())


@rate_limit(limit=6)
async def main_handler(message: types.Message):
    url = message.text
    user_id = message.from_user.id

    store_name, store = validate_shop(url)
    price, title = big_parser(url, store)

    if not (isinstance(price, int) and title):
        return await message.answer(_('Something went wrong 😮‍💨, try again later'))

    await message.answer(text=save_to_db(user_id, title, url, price))

    await find_product_in_another_store(title, store_name)


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(set_language, commands=['language'])
    dp.register_message_handler(list_of_stores, commands=['stores'])
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(shopping_cart, commands=['cart'])
    dp.register_message_handler(help_command, commands=['help'])
    dp.register_message_handler(main_handler)
