import json

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.data import data_path
from bot.database.models.goods import Url, OrdersPrices
from bot.middlewares.locale_middleware import get_text as _
from bot.misc.functions import add_price_status


def show_shopping_cart(orders, callback_data: str, startend=None, edit=None, price_status: bool = True) -> InlineKeyboardMarkup:
    cart_buttons = InlineKeyboardMarkup(row_width=4)
    button_id = 0
    start_end = [0, 10]
    offset = None

    if startend:
        start_end = startend

    range_of_buttons = [x for x in range(start_end[0], start_end[1])]
    for order in orders:

        if button_id in range_of_buttons:
            name = order.name

            if price_status:
                status = order.ordersprices.status
                if status:
                    name = add_price_status(name, status)

            if button_id == edit:
                custom_buttons(cart_buttons, callback_data, order, f'{start_end[0]}-{start_end[1]}')
                button_id += 1
                continue

            callback_data_ = f'{callback_data}_wr-{order.ware_id}_bt-{button_id}_of-{start_end[0]}-{start_end[1]}'
            cart_buttons.add(InlineKeyboardButton(text=name, callback_data=callback_data_))
            button_id += 1
            offset = ((button_id - 1) // 10) + 1

            continue

        button_id += 1

    pages = (len(orders) // 10) + 1
    if pages > 2:
        set_pages(cart_buttons, pages, offset, callback_data, start_end)
    if pages == 2:
        set_prev_next_pages(cart_buttons, pages, offset, callback_data, start_end)

    return cart_buttons


def custom_buttons(keyboard: InlineKeyboardMarkup, params: str, order, offset) -> InlineKeyboardMarkup:
    if params == 'order-name-new-price' or params == 'order-name':
        keyboard.add(InlineKeyboardButton(
            text='🔙', callback_data=f'back_pr-{params}_wr-{order.ware_id}_of-{offset}')).insert(InlineKeyboardButton(
            text='📈', callback_data=f'order-price-graph_wr-{order.ware_id}_{params}')).insert(InlineKeyboardButton(
            text='🛒', url=order.url))

    elif params == 'order-name-old-order' or 'old-order':
        callback_data_1 = f'back_pr-{params}_wr-{order.ware_id}'
        callback_data_2 = f'delete_pr-true-kb_wr-{order.ware_id}_{params}'
        keyboard.add(InlineKeyboardButton(text=_('Keep'), callback_data=callback_data_1)) \
            .insert(InlineKeyboardButton(text=_('Delete🙇‍♂️'), callback_data=callback_data_2))

    return keyboard


def url_kb(ware_id: int, param: str) -> InlineKeyboardMarkup:

    url_keyboard = InlineKeyboardMarkup(row_width=2)
    url_keyboard.add(InlineKeyboardButton(text=_('Delete'), callback_data=f'may-i-delete-order_wr-{ware_id}_pr-{param}')) \
        .insert(InlineKeyboardButton(text=_('Buy'), callback_data=f'buy-it_wr-{ware_id}_pr-{param}'))

    return url_keyboard


def choice_kb(ware_id: int, param: str) -> InlineKeyboardMarkup:
    choice_keyboard = InlineKeyboardMarkup()
    choice_keyboard.add(
        InlineKeyboardButton(text=_('Keep'), callback_data=f'delete_pr-false_wr-{ware_id}_{param}')) \
        .insert(InlineKeyboardButton(text=_('Delete🙇‍♂️'), callback_data=f'delete_pr-true_wr-{ware_id}_{param}'))

    return choice_keyboard


def list_of_shops(startend=None) -> InlineKeyboardMarkup:

    stores_kb = InlineKeyboardMarkup(row_width=3)
    with open(f'{data_path}/stores.json') as file_obj:
        stores = json.load(file_obj)

    start_end = [0, 10]
    offset = None
    if startend:
        start_end = startend

    range_of_buttons = [x for x in range(start_end[0], start_end[1])]
    for idx, values in enumerate(stores.items()):
        if idx in range_of_buttons:
            stores_kb.add(InlineKeyboardButton(text=values[0], url=values[1]))
            offset = ((idx - 1) // 10) + 1

    pages = (len(stores) // 10) + 1
    if pages > 1:
        set_prev_next_pages(stores_kb, pages, offset, 'stores', start_end)

    return stores_kb


def language_keyboard():
    button_uk = InlineKeyboardButton('🇺🇦', callback_data='locale_uk')
    button_en = InlineKeyboardButton('🇬🇧', callback_data='locale_en')
    button_pl = InlineKeyboardButton('🇵🇱', callback_data='locale_pl')

    return InlineKeyboardMarkup().add(button_uk).insert(button_en).insert(button_pl)


def order_from_diff_stores(ware_id, param):

    keyboard = InlineKeyboardMarkup(row_width=2)
    urls = Url.select(Url.url, OrdersPrices.store)\
        .join(OrdersPrices, on=(OrdersPrices.ware_id == Url.ware_id))\
        .where(Url.ware_id == ware_id)\
        .group_by(OrdersPrices.store)

    keyboard.add(InlineKeyboardButton(text='🔙', callback_data=f'back_pr-buying_wr-{ware_id}'))
    for idx, url in enumerate(urls):
        if idx % 2 == 0:
            keyboard.add(InlineKeyboardButton(url.ordersprices.store, url=url.url))
        else:
            keyboard.insert(InlineKeyboardButton(url.ordersprices.store, url=url.url))

    return keyboard


def set_pages(keyboard, pages: int, page, param, current_page):
    buttons = {
        1: '1️⃣', 2: '2️⃣', 3: '3️⃣', 4: '4️⃣', 5: '5️⃣', 6: '6️⃣', 7: '7️⃣', 8: '8️⃣', 9: '9️⃣', 0: '0️⃣', 10: '🔟'
    }

    btn = InlineKeyboardButton
    prev_offset = [(x - 10)for x in current_page]
    next_offset = [(x + 10)for x in current_page]
    next_next_offset = [(x + 20)for x in current_page]
    left_to_end = buttons.get(page + 1)
    end = buttons.get(page + 2)

    if page != pages:
        first_button = btn('◀️', callback_data=f'{param}_of-{prev_offset[0]}-{prev_offset[1]}')

        if page == 1:
            first_button = btn('⏺', callback_data='0')

        left_to_end_button = btn(left_to_end, callback_data=f'{param}_of-{next_offset[0]}-{next_offset[1]}')
        end_button = btn(end, callback_data=f'{param}_of-{next_next_offset[0]}-{next_next_offset[1]}')

        if pages - page == 1:
            left_to_end_button = btn('⏮', callback_data=f'{param}_of-0-10')
            end_button = btn(left_to_end, callback_data=f'{param}_of-{next_offset[0]}-{next_offset[1]}')

        keyboard.add(first_button).insert(left_to_end_button).insert(end_button) \
            .insert(btn('▶️', callback_data=f'{param}_of-{next_offset[0]}-{next_offset[1]}'))

    if page == pages:
        keyboard.add(btn('◀️', callback_data=f'{param}_of-{prev_offset[0]}-{prev_offset[1]}')) \
            .insert(btn('⏮', callback_data=f'{param}_of-0-10')) \
            .insert(btn('⏺', callback_data='0'))

    return keyboard


def set_prev_next_pages(keyboard, pages: int, page, param, current_page):

    btn = InlineKeyboardButton
    prev_offset = [(x - 10) for x in current_page]
    next_offset = [(x + 10) for x in current_page]

    first_button = btn('◀️', callback_data=f'{param}_of-{prev_offset[0]}-{prev_offset[1]}')
    if page == 1:
        first_button = btn('⏺', callback_data='0')

    second_button = btn('▶️', callback_data=f'{param}_of-{next_offset[0]}-{next_offset[1]}')
    if page == pages:
        second_button = btn('⏺', callback_data='0')

    keyboard.add(first_button).insert(second_button)

    return keyboard
