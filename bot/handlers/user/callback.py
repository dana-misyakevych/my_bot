from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Text

from bot.config import bot
from bot.database.models.goods import UsersOrders, Order, User
from bot.keyboards.custom_keyboards import url_kb, show_shopping_cart, \
    choice_kb, language_keyboard, order_from_diff_stores, list_of_shops
from bot.middlewares.throttling import rate_limit
from bot.misc.functions import query_to_db, plot_graph, CallBackInfo
from bot.middlewares.locale_middleware import get_text as _
from bot.data.texts import HELP_COMMAND


@rate_limit(limit=3)
async def delete_or_safe(callback: types.CallbackQuery):

    c = CallBackInfo(callback)

    if 'false' in c.answer:
        return await callback.message.edit_reply_markup(url_kb(c.ware_id, c.param))

    UsersOrders.del_user_order(c.user_id, c.ware_id)

    if 'kb' not in c.answer:
        await callback.answer(_('Done!'), show_alert=True)
        return await callback.message.delete()

    orders = query_to_db(c.param, c.user_id)
    if not any(orders):
        return await callback.message.edit_text(text=_('Your cart is empty'))

    keyboard = show_shopping_cart(orders, c.param, price_status=False)
    await callback.message.edit_reply_markup(reply_markup=keyboard)
    await callback.answer(_('Done!'))


@rate_limit(limit=3)
async def show_plot_price(callback: types.CallbackQuery):
    print('acsa')
    c = CallBackInfo(callback)

    if not UsersOrders.check_availability_on_user(c.user_id, c.ware_id):
        return await callback.answer(text=_('You don\'t have this product🧐'))

    photo = plot_graph(c.ware_id)
    keyboard = url_kb(c.ware_id, c.param)
    await bot.send_photo(c.user_id, photo, reply_markup=keyboard)
    await callback.answer()


@rate_limit(limit=3)
async def may_i_delete_order(callback: types.CallbackQuery):

    c = CallBackInfo(callback)
    await callback.message.edit_reply_markup(reply_markup=choice_kb(c.ware_id, c.param))


@rate_limit(limit=3)
async def change_buttons_on_orders_cart(callback: types.CallbackQuery):

    c = CallBackInfo(callback)

    if c.param == 'order-name-new-price':

        orders = Order.get_orders_with_new_prices(c.user_id)
        keyboard = show_shopping_cart(orders, c.param, edit=c.button_id, startend=c.offset)

    elif c.param == 'order-name-old-order':

        orders = Order.get_second_last_month_orders(c.user_id)
        keyboard = show_shopping_cart(orders, c.param, edit=c.button_id, price_status=False, startend=c.offset)

    else:
        orders = Order.get_user_orders(c.user_id)
        keyboard = show_shopping_cart(orders, c.param, edit=c.button_id, startend=c.offset)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@rate_limit(limit=3)
async def back_to_original_orders_cart(callback: types.CallbackQuery):

    c = CallBackInfo(callback)

    if not UsersOrders.check_user_cart(c.user_id):
        return await callback.message.edit_text(text=_('Your cart is empty'))

    if c.param == 'order-name-new-price':
        orders = Order.get_orders_with_new_prices(c.user_id)
        keyboard = show_shopping_cart(orders, c.param, startend=c.offset)

    elif c.param == 'order-name-old-order':
        orders = Order.get_second_last_month_orders(c.user_id)
        keyboard = show_shopping_cart(orders, c.param, price_status=False, startend=c.offset)

    elif c.param == 'buying':

        keyboard = url_kb(c.ware_id, c.param)

    else:
        keyboard = show_shopping_cart(Order.get_user_orders(c.user_id), callback_data=c.param, startend=c.offset)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


@rate_limit(limit=3)
async def save_locale(callback: types.CallbackQuery):

    loc = callback.data[-2:]
    prev_loc = str(User.get_user_locale(callback.from_user.id))

    if loc != prev_loc:
        User.set_user_locale(callback.from_user.id, loc)
        await callback.message.edit_text(text=_(HELP_COMMAND, locale=loc), reply_markup=language_keyboard())


async def buy_it_now(callback: types.CallbackQuery):

    c = CallBackInfo(callback)

    keyboard = order_from_diff_stores(c.ware_id, c.param)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


async def show_available_shops(callback: types.CallbackQuery):

    c = CallBackInfo(callback)
    keyboard = list_of_shops(c.offset)

    await callback.message.edit_reply_markup(reply_markup=keyboard)


def register_callback_handlers(dp: Dispatcher):
    dp.register_callback_query_handler(change_buttons_on_orders_cart, Text(startswith='pr-order-name'))
    dp.register_callback_query_handler(may_i_delete_order, Text(startswith='may-i-delete-order'))
    dp.register_callback_query_handler(show_plot_price, Text(contains='order-price-graph'))
    dp.register_callback_query_handler(back_to_original_orders_cart, Text(startswith='back'))
    dp.register_callback_query_handler(show_available_shops, Text(startswith='stores'))
    dp.register_callback_query_handler(delete_or_safe, Text(startswith='delete'))
    dp.register_callback_query_handler(save_locale, Text(startswith='locale'))
    dp.register_callback_query_handler(buy_it_now, Text(startswith='buy-it'))
