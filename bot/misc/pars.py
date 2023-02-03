import datetime
import re
import logging
import requests
import tldextract as tldextract
from bs4 import BeautifulSoup
from fake_headers import Headers
from bot.database.models.goods import OrdersPrices, Url


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


async def small_parser(session, order):
    user_agent = Headers(headers=True).generate()
    url = order.url.url
    params = validate_shop(url)
    if params[1]:
        user_agent['Accept-Encoding'] = 'identity'
        price = None
        async with session.get(url, headers=user_agent) as response:

            # if not response.ok:
            #     logg.warning(url, params, response.status_code)

            try:
                f = BeautifulSoup(await response.text(), "lxml")

                product_price = f.find(class_=params[1][0])
                if product_price and product_price != 0:
                    product_price = product_price.text

                    price = clear_price(product_price.strip())

            except AttributeError as e:
                logg.exception(f'{e}, {url}, {params}')

            if isinstance(price, int):
                OrdersPrices.create(ware_id=order.ware_id, date=datetime.date.today(), price=price, store=params[0]).save()


async def save_from_others_stores(session, url, ware_id):
    user_agent = Headers(headers=True).generate()
    params = validate_shop(url)
    price = None
    async with session.get(url, headers=user_agent) as response:

        user_agent['Accept-Encoding'] = 'identity'
        # if not response.ok:
        #     logg.warning(url, params, response.status_code)

        try:
            f = BeautifulSoup(await response.text(), "lxml")

            product_price = f.find(class_=params[1][0])
            if product_price and product_price != 0:
                product_price = product_price.text

                price = clear_price(product_price.strip())

        except AttributeError as e:
            logg.exception(f'{e}, {url}, {params}')

        if isinstance(price, int):
            Url.create(ware_id=ware_id, url=url).save()
            OrdersPrices.create(ware_id=ware_id, date=datetime.date.today(), price=price, store=params[1][2]).save()


def validate_shop(url):
    params = {
        'rozetka': ['product-prices__big', 'product__title', 'ROZETKA'],
        'ctrs': ['price', re.compile("^title-0-2"), 'Цитрус'],
        'telemart': ['b-i-product-topshort-buy-card-inner', 'b-page-title', 'Telemart'],
        'aliexpress': ['uniform-banner-box-price', 'product-title', 'Aliexpress'],
        'allo': ['sum', 'p-view__header-title', 'Алло'],
        'moyo': ['product_price_current', 'product_name', 'MOYO'],
        'nashformat': ['product-price', 'col-lg-8', 'Наш Формат'],
        'comfy': ['price__current', 'gen-tab__name', 'Comfy'],
        'foxtrot': ['product-box__main_price', 'page__title overflow', 'Foxtrot'],
        'epicentrk': ['p-price__main', 'p-header__title nc', 'Епіцентр'],
        'zhuk': ['product-price__item product-price__item--new', 'product-title', 'ЖЖУК'],
        'kvshop': ['ProductPrice ProductPrice_lg', 'h3', 'Комп\'ютерний Всесвіт'],
        'makeup': ['price_item', 'product-item__name', 'MAKEUP'],
        'apteka911': ['price-new', 'product-head-instr tl', 'Apteka911'],
        'add': ['price', 'base', 'ADD'],
        'kasta': ['p__price', 'p__pads', 'Kasta'],
        'yakaboo': ['ui-price-display__main', 'base-product__title', 'Yakaboo']

    }

    ext = tldextract.extract(url)
    return ext.domain, params.get(ext.domain)


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
