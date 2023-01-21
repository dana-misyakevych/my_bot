import datetime
import re
import logging
import requests
import tldextract as tldextract
from bs4 import BeautifulSoup
from fake_headers import Headers

from bot.database.models.goods import OrdersPrices


def big_parser(url: str, params: list):
    user_agent = Headers(headers=True).generate()
    resp = requests.get(url, headers=user_agent)

    if not resp.ok:
        logg.error(f'{url}, {params}, {resp.status_code}')

    try:

        f = BeautifulSoup(resp.text, "lxml")
        product_title = f.find(class_=params[0]).text
        product_price = f.find(class_=params[1]).text

        return clear_price(product_title.strip()), product_price.strip()

    except AttributeError as e:
        logg.exception(f'{e}, {url}, {params}')
        return False, False


async def small_parser(session, order):
    user_agent = Headers(headers=True).generate()
    url = order.url
    params = validate_shop(url)

    async with session.get(url, headers=user_agent) as response:
        response_text = await response.text()

        if not response.ok:
            logg.warning(url, params, response.status_code)

        try:
            f = BeautifulSoup(response_text, "lxml")

            product_price = f.find(class_=params[0]).text
            price = clear_price(product_price.strip())

        except AttributeError as e:
            logg.exception(f'{e}, {url}, {params}')

        if isinstance(price, int):
            OrdersPrices.create(ware_id=order.ware_id, date=datetime.date.today(), price=price).save()


def validate_shop(url):
    params = {
        'rozetka': ['product-prices__big', 'product__title'],
        'ctrs': ['price', re.compile("^title-0-2")],
        'telemart': ['b-i-product-topshort-buy-card-inner', 'b-page-title'],
        'aliexpress': ['uniform-banner-box-price', 'product-title-text'],
        'allo': ['sum', 'p-view__header-title'],
        'moyo': ['product_price_current', 'product_name'],
        'ktc': ['product__price', 'product__title'],
        'nashformat': ['product-price', 'col-lg-8'],
        'aks': ['prod-content-price', 'product-card-product-name-header'],
        'vseplus': ['price-box', 'product']
    }

    ext = tldextract.extract(url)
    return params.get(ext.domain)


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
