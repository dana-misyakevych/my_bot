import asyncio
import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.schedulers.background import BackgroundScheduler

from bot.config import bot
from bot.database.models.goods import UsersOrders, OrdersPrices, Order
from bot.keyboards.custom_keyboards import Keyboard
from bot.middlewares.locale_middleware import get_text as _
from bot.misc.pars import Product


def scheduler():
    background_scheduler = BackgroundScheduler(timezone='Europe/Kiev')
    async_scheduler = AsyncIOScheduler(timezone='Europe/Kiev')
    today = datetime.date.today()

    background_scheduler.add_job(schedule_price_check,
                                 trigger='cron', hour='05', minute='30',
                                 replace_existing=True, start_date=today)
    async_scheduler.add_job(schedule_pars,
                            trigger='cron', hour='00', minute='57',
                            replace_existing=True, start_date=today)
    async_scheduler.add_job(users_notifier,
                            trigger='cron', hour='08', minute='0',
                            replace_existing=True, start_date=today)
    async_scheduler.add_job(ask_good_status,
                            trigger='cron', day='28', hour='22', minute='01',
                            replace_existing=True, start_date=today)

    background_scheduler.start()
    async_scheduler.start()


async def users_notifier():

    for user in UsersOrders.get_users_with_new_price_status():
        orders = Order.get_orders_with_new_prices(user.user_id)
        keyboard = Keyboard.show_shopping_cart(orders, 'order-name-new-price', price_status=True)
        await bot.send_message(user.user_id, text=_('The price of selected products has changed',
                                                    locale=user.language), reply_markup=keyboard)


def schedule_price_check():

    yesterday_today_price = OrdersPrices.get_yesterday_today_prices()

    previous_price = None
    previous_ware_id = None

    for price in yesterday_today_price:

        if previous_ware_id == price.ware_id:
            price_status = price.price - previous_price

            if price_status != 0:
                OrdersPrices.update_price_status(price_status, price.ware_id)

        previous_price = price.price
        previous_ware_id = price.ware_id


async def schedule_pars():
    orders = Order.get_following_orders()
    tasks = []

    for order in orders:
        await asyncio.sleep(0.001)
        task = asyncio.create_task(Product(order.url.url).save_from_others_stores(ware_id=order.ware_id))
        tasks.append(task)

    await asyncio.gather(*tasks)


async def ask_good_status():

    for user in UsersOrders.get_users_with_old_orders():
        orders = Order.get_second_last_month_orders(user.user_id)
        keyboard = show_shopping_cart(orders, price_status=False, callback_data='order-name-old-order')
        text = _("Hello, select the products you are still following, "
                 "Or leave it as it is", locale=user.language)

        await bot.send_message(user.user_id, text=text, reply_markup=keyboard)
