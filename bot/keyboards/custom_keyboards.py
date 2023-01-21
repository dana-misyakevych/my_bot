from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from peewee import ModelSelect
from bot.database.models.goods import Order
from bot.misc.functions import add_price_status
from bot.middlewares.locale_middleware import get_text as _


def show_shopping_cart(orders: ModelSelect, callback_data: str, price_status: bool = True) -> InlineKeyboardMarkup:
    cart_buttons = InlineKeyboardMarkup()
    button_id = 0

    for order in orders:
        name = order.name

        if price_status:
            status = order.ordersprices.status
            if status:
                name = add_price_status(name, status)

        callback_data_ = f'{callback_data}_wr-{order.ware_id}_bt-{button_id}'
        cart_buttons.add(InlineKeyboardButton(text=name, callback_data=callback_data_))
        button_id += 1

    return cart_buttons


def edited_shopping_cart(orders, edit: int, callback_data: str, price_status: bool = True) -> InlineKeyboardMarkup:
    cart_buttons = InlineKeyboardMarkup(row_width=3)
    button_id = 0

    for order in orders:
        name = order.name

        if price_status:
            status = order.ordersprices.status
            if status:
                name = add_price_status(name, status)

        if button_id == edit:
            custom_buttons(cart_buttons, callback_data, order)
            button_id += 1
            continue

        callback_data_ = f'{callback_data}_wr-{order.ware_id}_bt-{button_id}'
        cart_buttons.add(InlineKeyboardButton(text=name, callback_data=callback_data_))
        button_id += 1

    return cart_buttons


def custom_buttons(keyboard: InlineKeyboardMarkup, params: str, order) -> InlineKeyboardMarkup:
    if params == 'order-name-new-price' or params == 'order-name':
        keyboard.add(InlineKeyboardButton(
            text='🔙', callback_data=f'back_pr-{params}_wr-{order.ware_id}')).insert(InlineKeyboardButton(
            text='📈', callback_data=f'order-price-graph_wr-{order.ware_id}_{params}')).insert(InlineKeyboardButton(
            text='🛒', url=order.url))

    elif params == 'order-name-old-order' or 'old-order':
        callback_data_1 = f'back_pr-{params}_wr-{order.ware_id}'
        callback_data_2 = f'delete_pr-true-kb_wr-{order.ware_id}_{params}'
        keyboard.add(InlineKeyboardButton(text=_('Keep'), callback_data=callback_data_1)) \
            .insert(InlineKeyboardButton(text=_('Delete🙇‍♂️'), callback_data=callback_data_2))

    return keyboard


def url_kb(ware_id: int, param: str) -> InlineKeyboardMarkup:
    url = Order.get_url(ware_id)

    url_keyboard = InlineKeyboardMarkup(row_width=2)
    url_keyboard.add(InlineKeyboardButton(text=_('Delete'), callback_data=f'may-i-delete-order_wr-{ware_id}_{param}')) \
        .insert(InlineKeyboardButton(text=_('Buy'), url=url))

    return url_keyboard


def choice_kb(ware_id: int, param: str) -> InlineKeyboardMarkup:
    choice_keyboard = InlineKeyboardMarkup()
    choice_keyboard.add(
        InlineKeyboardButton(text=_('Keep'), callback_data=f'delete_pr-false_wr-{ware_id}_{param}')) \
        .insert(InlineKeyboardButton(text=_('Delete🙇‍♂️'), callback_data=f'delete_pr-true_wr-{ware_id}_{param}'))

    return choice_keyboard


def list_of_shops() -> InlineKeyboardMarkup:
    stores_kb = InlineKeyboardMarkup(row_width=3)

    stores = {
        'Розетка': 'https://rozetka.com.ua/ua/',
        'Цитрус': 'https://www.ctrs.com.ua/',
        'Телемарт': 'https://telemart.ua/ua/',
        'Алло': 'https://allo.ua/',
        'MOYO': 'https://www.moyo.ua/ua/',
        'Наш Формат': 'https://nashformat.ua/'
    }

    for idx, values in enumerate(stores.items()):
        stores_kb.add(InlineKeyboardButton(text=values[0], url=values[1]))

    return stores_kb


def language_keyboard():
    button_uk = InlineKeyboardButton('🇺🇦', callback_data='locale_uk')
    button_en = InlineKeyboardButton('🇬🇧', callback_data='locale_en')
    button_pl = InlineKeyboardButton('🇵🇱', callback_data='locale_pl')

    return InlineKeyboardMarkup().add(button_uk).insert(button_en).insert(button_pl)
