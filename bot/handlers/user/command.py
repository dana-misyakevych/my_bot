from aiogram import Dispatcher, types

from bot import config
from bot.database.models.goods import Order
from bot.misc.functions import work_with_product
from bot.keyboards.custom_keyboards import Keyboard
from bot.middlewares.throttling import rate_limit
from bot.misc.pars import Shop, Product
from bot.middlewares.locale_middleware import get_text as _
from bot.data.texts import HELP_COMMAND


@rate_limit(limit=3)
async def start_command(message: types.Message):

    await message.answer(text=_(HELP_COMMAND), reply_markup=Keyboard.language_keyboard())


@rate_limit(limit=3)
async def help_command(message: types.Message):

    await message.answer(text=_(HELP_COMMAND), reply_markup=Keyboard.language_keyboard())


@rate_limit(limit=3)
async def list_of_stores(message: types.Message):

    text = _('Shops are available: ')
    await message.answer(text=text, reply_markup=Keyboard.list_of_shops())


@rate_limit(limit=3)
async def shopping_cart(message: types.Message):

    orders = Order.get_user_orders(message.from_user.id)

    if not orders:
        return await message.answer(text=_('Your cart is empty 🧐'))

    inline_keyboard = Keyboard.show_shopping_cart(orders, price_status=True, callback_data='order-name')
    await message.answer(text=_('Here\'s your shopping cart:'), reply_markup=inline_keyboard)


@rate_limit(limit=3)
async def set_language(message: types.Message):

    await message.answer(text='🇺🇦 Оберіть мову спілкування\n'
                              '🇬🇧 Chose your language\n'
                              '🇵🇱 Wybierz swój język',
                         reply_markup=Keyboard.language_keyboard())


@rate_limit(limit=6)
@config.dp.async_task
async def main_handler(message: types.Message):
    url = message.text

    message_obj = await message.answer(_('Сheck the goods'))
    product = Product(url)
    shop = Shop(url)
    await message.answer(message.chat.id)
    price, title = await product.get_price_and_title(shop)
    if not (isinstance(price, int) and title):
        await config.bot.edit_message_text(
            _('Something went wrong 😮‍💨, try again later'), message_id=message_obj.message_id, chat_id=message.chat.id)

    await work_with_product(product, price, message, config.bot, message_obj)


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(set_language, commands=['language'])
    dp.register_message_handler(list_of_stores, commands=['stores'])
    dp.register_message_handler(start_command, commands=['start'])
    dp.register_message_handler(shopping_cart, commands=['cart'])
    dp.register_message_handler(help_command, commands=['help'])
    dp.register_message_handler(main_handler)
