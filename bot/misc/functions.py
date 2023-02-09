import datetime
import io
import random
import re
import aiogram.types

from typing import Optional
import matplotlib.lines
from matplotlib.transforms import Bbox, TransformedBbox
from matplotlib.legend_handler import HandlerBase
from matplotlib.image import BboxImage
from matplotlib import pyplot as plt
from peewee import ModelSelect
import os
from bot.middlewares.locale_middleware import get_text as _
from bot.database.models.goods import Order, UsersOrders, OrdersPrices, User, Url
from bot.data.texts import reply_to_start_tracking
from bot.data import stores_info
import tldextract as tldextract

from bot.misc import pars


def save_to_db(user_id: int, name: str, url: str, price: int, domain: list) -> str:
    ware_id = my_hash(name)
    today = datetime.date.today()

    if not User.get_or_none(User.user_id == user_id):
        User.create(user_id=user_id).save()

    if not Order.get_or_none(Order.name == name):

        Order.create(ware_id=ware_id, name=name, date=today, url=url).save()
        UsersOrders.create(user_id=user_id, ware_id=ware_id, date=today).save()
        OrdersPrices.create(ware_id=ware_id, date=today, price=price, store=domain).save()
        Url.create(ware_id=ware_id, url=url)
        message = _(random.choice(reply_to_start_tracking))

    else:

        if UsersOrders.check_availability_on_user(user_id, ware_id):
            message = _('Already following 😎')

        else:

            UsersOrders.create(user_id=user_id, ware_id=ware_id, date=today).save()
            message = _('Started following 🫡')

    return message


async def save_urls_and_prices_to_db(urls, prices, name):
    today = datetime.date.today()
    ware_id = my_hash(name)
    for url, price in zip(urls, prices):

        store_name = tldextract.extract(url).domain

        Url.create(ware_id=ware_id, url=url).save()
        OrdersPrices.create(ware_id=ware_id, date=today, price=price, store=store_name).save()


def query_to_db(action: str, user_id=None) -> ModelSelect:

    if action == 'order-name':
        return Order.get_user_orders(user_id)

    elif action == 'new-price' or action == 'order-name-new-price':
        return Order.get_orders_with_new_prices(user_id)

    elif action == 'old-order' or action == 'order-name-old-order':
        return Order.get_second_last_month_orders(user_id)


def get_callback_data(callback: aiogram.types.CallbackQuery) -> list[int, Optional[str]]:

    callback_data = [callback.from_user.id]
    callback_d = callback.data.split('_')

    for data in callback_d:
        if data in ('order-name', 'order-name-new-price', 'order-name-old-order', 'buying'):
            callback_data.insert(6, data)

        if 'of' in data:
            start, end = data[3:].split('-')
            callback_data.insert(10, [int(start), int(end)])

        prefix = data[:2]
        data = data[3:]

        if prefix == 'wr':
            callback_data.insert(1, int(data))

        elif prefix == 'bt':
            callback_data.insert(2, int(data.strip('=')))

        elif prefix == 'pr':
            callback_data.insert(5, data)

    if 'of' not in callback.data:
        callback_data.insert(10, None)

    if 'wr' not in callback.data:
        callback_data.insert(1, None)

    if 'bt' not in callback.data:
        callback_data.insert(2, None)

    # print(callback_data)
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

    plt_main = build_plot(ware_id)

    return save_image_into_png(plt_main)


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


async def find_and_save_good(user_id, price, title, url, domain, message, bot):

    message_obj = await message.answer(_('Сheck the goods'))

    answer_text = save_to_db(user_id, title, url, price, domain)
    await bot.edit_message_text(text=answer_text, message_id=message_obj.message_id, chat_id=message.chat.id)


async def find_and_save_good_from_other_stores(title, domain, message, bot):

    message_obj = await message.answer(_('Looking for goods in other stores'))

    await pars.find_product_in_another_store(title, domain)
    await bot.edit_message_text(text=_('Here\'s what I found'), message_id=message_obj.message_id,
                                chat_id=message.chat.id)


def save_image_into_png(plot_obj):
    with io.BytesIO() as file_object:
        plot_obj.savefig(file_object, format='png')
        file_object.seek(0)
        plot_obj.close()
        return file_object.read()


def validate_shop(url):

    domain = tldextract.extract(url).domain
    params = stores_info.get(domain)

    if not params:
        return None, None

    second_params = params[1]
    if '0re' == second_params[:3]:
        second_params = re.compile(f"^{params[1]}")

    return domain, [params[0], second_params, params[2]]


def get_info_for_build_plot(ware_id):

    ware_info = OrdersPrices.get_last_moth_prices(ware_id)
    ware_name = Order.get_name(ware_id)

    if len(ware_name) > 90:
        ware_name = ware_name[:90] + '...'

    plt.style.use('seaborn')
    plt.title(ware_name)

    date = []
    for day in ware_info:
        if day.date.strftime('%d-%m-%y') not in date:
            date.append(day.date.strftime('%d-%m-%y'))

    prices = [[data.price, data.store] for data in ware_info]
    stores = {}
    for price in prices:
        if not stores.get(price[1]):
            stores[price[1]] = [price[0]]

        elif stores.get(price[1]):
            stores.get(price[1]).append(price[0])

    return date, stores


def build_plot(ware_id):
    date, stores = get_info_for_build_plot(ware_id)

    prev_price = 0
    min_price = None
    lines = []

    for key, value in stores.items():
        last_price = value[-1]
        if last_price:
            stores_data = stores_info.get(key)

            line = plt.plot(date, value, 'o', linestyle='solid',
                       label=stores_data[2] + ' ' + str(last_price), color=stores_data[4])

            if last_price < prev_price:
                min_price = stores_data[2] + ' ' + str(last_price), line

            lines.append([(line), stores_data[2] + ' ' + str(last_price)])
            prev_price = last_price

    plot = customize_plot(plt, stores, min_price, lines)
    return plot


def customize_plot(plot, stores, min_price, lines):

    bottom_num = 0.11
    if len(stores) > 4:
        bottom_num = 0.15

    plot.subplots_adjust(bottom=bottom_num, top=0.92)
    legend = plot.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), fancybox=True, shadow=True, ncol=5,
                             handlelength=0, labelspacing=2)

    for text in legend.get_texts():
        if min_price[0] in text.get_text():
            text.set_color("red")
            text.set_weight('bold')

    return plot


class HandlerLineImage(HandlerBase):

    def __init__(self, path, space=15, offset = 10 ):
        self.space=space
        self.offset=offset
        self.image_data = plt.imread(path)
        super(HandlerLineImage, self).__init__()

    def create_artists(self, legend, orig_handle,
                       xdescent, ydescent, width, height, fontsize, trans):

        l = matplotlib.lines.Line2D([xdescent+self.offset,xdescent+(width-self.space)/3.+self.offset],
                                     [ydescent+height/2., ydescent+height/2.])
        l.update_from(orig_handle)
        l.set_clip_on(False)
        l.set_transform(trans)

        bb = Bbox.from_bounds(xdescent +(width+self.space)/3.+self.offset,
                              ydescent,
                              height*self.image_data.shape[1]/self.image_data.shape[0],
                              height)

        tbb = TransformedBbox(bb, trans)
        image = BboxImage(tbb)
        image.set_data(self.image_data)

        self.update_prop(image, orig_handle, legend)
        return [l,image]