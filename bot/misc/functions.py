import datetime
import io
import random
import re
import aiogram.types

from typing import Optional
from matplotlib import pyplot as plt
from peewee import ModelSelect
from bot.middlewares.locale_middleware import get_text as _
from bot.database.models.goods import Order, UsersOrders, OrdersPrices, User
from bot.data.texts import reply_to_start_tracking


def save_to_db(user_id: int, name: str, url: str, price: int) -> str:
    ware_id = my_hash(name)
    today = datetime.date.today()

    if not User.get_or_none(User.user_id == user_id):
        User.create(user_id=user_id).save()

    if not Order.get_or_none(Order.name == name):

        Order.create(ware_id=ware_id, name=name, date=today, url=url).save()
        UsersOrders.create(user_id=user_id, ware_id=ware_id, date=today).save()
        OrdersPrices.create(ware_id=ware_id, date=today, price=price).save()

        message = _(random.choice(reply_to_start_tracking))

    else:

        if UsersOrders.check_availability_on_user(user_id, ware_id):
            message = _('Already following 😎')

        else:

            UsersOrders.create(user_id=user_id, ware_id=ware_id, date=today).save()
            message = _('Started following 🫡')

    return message


def query_to_db(action: str, user_id=None) -> ModelSelect:

    if action == 'order-name':
        return Order.get_user_orders(user_id)

    elif action == 'new-price' or action == 'order-name-new-price':
        return Order.get_orders_with_new_prices(user_id)

    elif action == 'old-order' or action == 'order-name-old-order':
        return Order.get_second_last_month_orders(user_id)


def get_callback_data(callback: aiogram.types.CallbackQuery) -> list[int, Optional[str]]:

    callback_data = [callback.from_user.id]
    callback = callback.data.split('_')
    for data in callback:

        if data in ('order-name', 'order-name-new-price', 'order-name-old-order'):
            callback_data.insert(6, data)

        prefix = data[:2]
        data = data[3:]

        if prefix == 'wr':
            callback_data.insert(1, int(data))

        elif prefix == 'bt':
            callback_data.insert(2, int(data))

        elif prefix == 'pr':
            callback_data.insert(5, data)

    return callback_data


def my_hash(text: str) -> int:

    hash_ = 245225525

    for ch in text:
        hash_ = (hash_ * 281 ^ ord(ch) * 997) & 0xFFFFFFFF

    return hash_


def clear_price(price: str) -> int:
    result = ''

    for char in price:
        try:
            int(char)
            result += char
        except ValueError:
            continue

    if result:
        return int(result)


def plot_graph(ware_id: int):
    ware_info = OrdersPrices.get_last_moth_prices(ware_id)
    ware_name = Order.get_name(ware_id)

    if len(ware_name) > 90:
        ware_name = ware_name[:90] + '...'

    date = [data.date.strftime('%d-%m-%y') for data in ware_info]
    price = [data.price for data in ware_info]

    plt.style.use('seaborn')
    plt.plot(date, price, 'o', linestyle='solid')
    plt.title(ware_name)

    with io.BytesIO() as file_object:
        plt.savefig(file_object, format='png')
        file_object.seek(0)
        plt.close()
        return file_object.read()


def is_url(expression: str) -> Optional[list]:
    regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]" \
            r"+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
    url = re.findall(regex, expression)

    return [x[0] for x in url]


def add_price_status(name: str, status: int) -> str:

    if status > 0:
        name = f'+{status}🏷️ ' + name

    elif status < 0:
        name = f'{status}🏷️ ' + name

    return name
