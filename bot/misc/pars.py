import asyncio
import datetime
import logging

import aiohttp
import requests
from bs4 import BeautifulSoup
from fake_headers import Headers
from bot.database.models.goods import OrdersPrices, Url
from bot.misc.functions import Shop, my_hash, clear_price
from googlesearch import search as g_search


def big_parser(url: str, params: list):
    user_agent = Headers(headers=True).generate()
    user_agent['Accept-Encoding'] = 'identity'
    resp = requests.get(url, headers=user_agent)

    if not resp.ok:
        logg.error(f'{url}, {params}, {resp.status_code}')

    try:
        resp.encoding = resp.apparent_encoding
        f = BeautifulSoup(resp.text, "lxml")
        product_price = f.find(class_=params[0]).text
        product_title = f.find(class_=params[1]).text

        return clear_price(product_price.strip()), product_title.strip()

    except AttributeError as e:
        logg.exception(f'{e}, {url}, {params}')
        return False, False


async def small_parser(order):

    user_agent = Headers(headers=True).generate()
    user_agent['Accept-Encoding'] = 'identity'
    url = order.url.url

    shop = Shop(url)

    if shop:

        price = None
        connector = aiohttp.TCPConnector(force_close=True)

        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, headers=user_agent) as response:

                # if not response.ok:
                #     logg.warning(url, params, response.status_code)

                try:
                    f = BeautifulSoup(await response.text(), "lxml")

                    product_price = f.find(class_=shop.product_price_class)
                    if product_price and product_price != 0:
                        product_price = product_price.text

                        price = clear_price(product_price.strip())

                except AttributeError as e:
                    logg.exception(f'{e}, {url}, {shop.product_price_class, shop.product_title_class}')

                if not isinstance(price, int):
                    price = None

                OrdersPrices.create(ware_id=order.ware_id, date=datetime.date.today(), price=price, store=shop.domain).save()


async def save_from_others_stores(url, ware_id):
    user_agent = Headers(headers=True).generate()
    user_agent['Accept-Encoding'] = 'identity'
    shop = Shop(url)
    price = None
    connector = aiohttp.TCPConnector(force_close=True)

    async with aiohttp.ClientSession(connector=connector) as session:
        async with session.get(url, headers=user_agent) as response:


            # if not response.ok:
            #     logg.warning(url, params, response.status_code)

            try:
                f = BeautifulSoup(await response.text(), "lxml")

                product_price = f.find(class_=shop.product_price_class)
                if product_price and product_price != 0:
                    product_price = product_price.text

                    price = clear_price(product_price.strip())

            except AttributeError as e:
                logg.exception(f'{e}, {url}, {shop.product_price_class, shop.product_title_class}')

            if isinstance(price, int):
                Url.create(ware_id=ware_id, url=url).save()
                OrdersPrices.create(ware_id=ware_id, date=datetime.date.today(), price=price, store=shop.domain).save()


async def find_product_in_another_store(product_name, first_domain):

    ware_id = my_hash(product_name)
    domains = [first_domain]
    tasks = []

    for url in g_search(product_name, pause=5, stop=100, lang='uk'):
        await asyncio.sleep(0.01)
        shop = Shop(url)
        if shop and shop.domain not in domains:
            task = asyncio.create_task(save_from_others_stores(url, ware_id))
            tasks.append(task)

    await asyncio.gather(*tasks)


def log():
    # Create a custom logger
    logger = logging.getLogger(__name__)

    # Create handlers
    c_handler = logging.StreamHandler()
    f_handler = logging.FileHandler('file.log')
    c_handler.setLevel(logging.WARNING)
    f_handler.setLevel(logging.ERROR)

    # Create formatters and add it to handlers
    c_format = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
    f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    f_handler.setFormatter(f_format)

    # Add handlers to the logger
    logger.addHandler(c_handler)
    logger.addHandler(f_handler)

    return logger


logg = log()
