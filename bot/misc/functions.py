# -*- coding: utf-8 -*-
import io
import re

import aiogram.types
from typing import Optional, Union
from matplotlib import pyplot as plt

from peewee import ModelSelect
from bot.middlewares.locale_middleware import get_text as _
from bot.database.models.goods import Order, OrdersPrices
from bot.data import stores_info
import tldextract as tldextract


def query_to_db(action: str, user_id=None) -> ModelSelect:

    if action == 'order-name':
        return Order.get_user_orders(user_id)

    elif action == 'new-price' or action == 'order-name-new-price':
        return Order.get_orders_with_new_prices(user_id)

    elif action == 'old-order' or action == 'order-name-old-order':
        return Order.get_second_last_month_orders(user_id)


class CallBackInfo:

    def __init__(self, callback: aiogram.types.CallbackQuery):
        params = self.get_callback_data(callback)
        self.user_id = params.get('user_id')
        self.button_id = params.get('bt')
        self.ware_id = params.get('wr')
        self.answer = params.get('an')
        self.offset = params.get('of')
        self.param = params.get('pr')

    @staticmethod
    def get_callback_data(callback: aiogram.types.CallbackQuery) -> dict[str, Union[str, list[int]]]:

        callback_data = {'user_id': callback.from_user.id}
        callback_d = callback.data.split('_')

        for data in callback_d:

            prefix = data[:2]
            data = data[3:]

            if 'of' == prefix:
                data = [int(x) for x in data.split('-')]

            callback_data[prefix] = data

        return callback_data


def my_hash(text: str) -> int:

    hash_ = 245225525

    for ch in text:
        hash_ = (hash_ * 281 ^ ord(ch) * 997) & 0xFFFFFFFF

    return hash_


def clear_price(price_str: str) -> Optional[int]:
    digits = ''
    for char in price_str:
        if char.isdigit():
            digits += char
    return int(digits) if digits else None


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


def plot_graph(ware_id: int):

    plot = build_plot(ware_id)
    return save_image_into_png(plot)


async def work_with_product(product, price, message, bot, message_obj):

    user_id = message.from_user.id

    code = await find_and_save_good(product, user_id, price, message, bot, message_obj)

    if code == 200:
        await find_and_save_good_from_other_stores(message, bot, product)


async def find_and_save_good(product, user_id, price, message, bot, message_obj):

    code, answer_text = product.save_to_db(user_id, price)
    await bot.edit_message_text(text=answer_text, message_id=message_obj.message_id, chat_id=message.chat.id)

    return code


async def find_and_save_good_from_other_stores(message, bot, product):

    message_obj = await message.answer(_('Looking for goods in other stores'))
    text = _('Here\'s what I found')

    await product.find_in_another_store()
    await bot.edit_message_text(text=text, message_id=message_obj.message_id, chat_id=message.chat.id)


class Shop:

    def __init__(self, url=None, domain=None):
        domain, info = self.validate_shop(url, domain)
        product_price_class, product_title_class, name, main_page, color = None, None, None, None, None

        if domain:
            product_price_class, product_title_class, name, main_page, color = info

        self.product_price_class = product_price_class
        self.product_title_class = product_title_class
        self.main_page = main_page
        self.domain = domain
        self.color = color
        self.name = name

    @staticmethod
    def validate_shop(url=None, domain=None):

        if not domain:
            domain = tldextract.extract(url).domain
        print(domain)
        params = stores_info.get(domain)

        if not params:
            return None, None

        second_params = params[1]
        if '0re-' == second_params[:4]:
            params = [params[0], re.compile(r"^{}".format(second_params[4:])), *params[2:]]

        return domain, params

    def __bool__(self):
        return bool(self.name)

    def __repr__(self):
        return self.name


def get_info_for_build_plot(ware_id):
    date = []
    stores = {}

    ware_name = Order.get_name(ware_id)
    ware_info = OrdersPrices.get_last_moth_prices(ware_id)

    for item in ware_info:

        if item.date.strftime('%d-%m-%y') not in date:
            date.append(item.date.strftime('%d-%m-%y'))

        if stores.get(item.store):
            stores.get(item.store).append(item.price)

        if not stores.get(item.store):
            stores[item.store] = [item.price]

    if len(ware_name) > 90:
        ware_name = ware_name[:90] + '...'

    return ware_name, date, stores


def build_plot(ware_id):

    ware_name, date, stores = get_info_for_build_plot(ware_id)
    plt.style.use('seaborn')
    plt.title(ware_name)

    min_price = min([x[-1] for x in stores.values() if x[-1]])
    min_prices = []

    for key, value in stores.items():
        current_price = value[-1]
        shop = Shop(key)

        if current_price and len(date) == len(value):
            product_info = shop.name + f' • {current_price}'
            alpha = 0.6

            if current_price == min_price:
                min_prices.append(product_info)
                alpha = 1

            plt.plot(date, value, 'o', linestyle='solid', label=product_info, color=shop.color, alpha=alpha)

    return customize_plot(plt, stores, min_prices)


def customize_plot(plt, stores, min_price):

    bottom_num = 0.11
    if len(stores) > 4:
        bottom_num = 0.17

    # for line in plt.gca().get_lines():
    #     prouct_info = line.get_label()
    #     if prouct_info in min_price:
    #         line.set_label(prouct_info)

    plt.subplots_adjust(bottom=bottom_num, top=0.92)
    legend = plt.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=5,
                        handlelength=0, labelspacing=1)

    for text in legend.get_texts():

        if text.get_text() in min_price:
            text.set_color("red")

    return plt


def save_image_into_png(plot_obj):
    with io.BytesIO() as file_object:
        plot_obj.savefig(file_object, format='png')
        file_object.seek(0)
        plot_obj.close()
        return file_object.read()
