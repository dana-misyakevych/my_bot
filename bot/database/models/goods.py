from babel.core import Locale
from peewee import CharField, DateTimeField, ForeignKeyField, IntegerField
from peewee import Model, SqliteDatabase
from bot.utils.date_func import last_month, get_yesterday_today_date

database = SqliteDatabase('/home/oleh/PycharmProjects/Tsinovyk/bot/database/all_data.db')


class BaseModel(Model):
    class Meta:
        database = database


class User(BaseModel):
    class Meta:
        table_name = 'users'

    user_id = IntegerField(primary_key=True)
    first_name = CharField(max_length=10, null=True)
    last_name = CharField(max_length=20, null=True)
    language = CharField(max_length=2, null=True)

    @classmethod
    def get_user_locale(cls, user_id):
        try:
            language_code = cls.get_or_none(cls.user_id == user_id).language
        except AttributeError:
            language_code = 'uk'

        return Locale(language_code)

    @classmethod
    def set_user_locale(cls, user_id, locale):
        if not cls.get_or_none(cls.user_id == user_id):
            cls.create(user_id=user_id, language=locale).save()

        cls.update(language=locale).where(cls.user_id == user_id).execute()


class Order(BaseModel):
    class Meta:
        table_name = 'orders'

    ware_id = IntegerField(primary_key=True)
    name = CharField(default=None)
    url = CharField(default=None)
    date = DateTimeField(default=None, null=True)

    @classmethod
    def get_url(cls, ware_id):
        return cls.get_or_none(cls.ware_id == ware_id).url

    @classmethod
    def get_name(cls, ware_id):
        return cls.get_or_none(cls.ware_id == ware_id).name

    @classmethod
    def get_following_orders(cls):
        return cls.select(cls.ware_id.distinct(), cls.url).join(UsersOrders, on=(UsersOrders.ware_id == cls.ware_id))

    @classmethod
    def get_second_last_month_orders(cls, user_id):
        return cls.select(cls.name.distinct(), cls.ware_id) \
            .join(UsersOrders, on=(UsersOrders.ware_id == cls.ware_id)) \
            .where((UsersOrders.date < last_month()) & (UsersOrders.user_id == user_id))

    @classmethod
    def get_orders_with_new_prices(cls, user_id):
        orders = cls.select(cls.name, cls.ware_id, cls.url, OrdersPrices.status, OrdersPrices.price) \
            .join(OrdersPrices, on=(cls.ware_id == OrdersPrices.ware_id)) \
            .join(UsersOrders, on=(UsersOrders.ware_id == OrdersPrices.ware_id)) \
            .where((UsersOrders.user_id == user_id) & (OrdersPrices.status)) \
            .group_by(OrdersPrices.status)

        return orders

    @classmethod
    def get_user_orders(cls, user_id):
        orders = cls.select(cls.name.distinct(), cls.ware_id, cls.ware_id,
                            UsersOrders.user_id, Order.url, OrdersPrices.status) \
            .join(OrdersPrices, on=(OrdersPrices.ware_id == cls.ware_id)) \
            .join(UsersOrders, on=(UsersOrders.ware_id == cls.ware_id)) \
            .where((UsersOrders.user_id == user_id))

        if not any(orders):
            return

        return orders


class UsersOrders(BaseModel):
    class Meta:
        table_name = 'users_orders'

    user_id = ForeignKeyField(User, field='user_id', unique=False)
    ware_id = ForeignKeyField(Order, field='ware_id', unique=False)
    date = DateTimeField(default=None)

    @classmethod
    def check_availability_on_user(cls, user_id, ware_id):
        return cls.get_or_none((cls.ware_id == ware_id) & (cls.user_id == user_id))

    @classmethod
    def check_user_cart(cls, user_id):
        return cls.get_or_none(cls.user_id == user_id)

    @classmethod
    def get_users_with_new_price_status(cls):
        return User.select(cls.user_id.distinct(), cls.ware_id, OrdersPrices.status, User.language) \
            .join(UsersOrders, on=(UsersOrders.user_id == cls.user_id)) \
            .join(OrdersPrices, on=(cls.ware_id == OrdersPrices.ware_id)) \
            .where(OrdersPrices.status) \
            .group_by(cls.user_id)

    @classmethod
    def get_users_with_old_orders(cls):
        return User.select(cls.user_id.distinct(), User.language) \
            .join(cls, on=(User.user_id == cls.user_id)) \
            .where(cls.date < last_month())

    @classmethod
    def del_user_order(cls, user_id, ware_id):
        cls.delete().where((cls.user_id == user_id) & (cls.ware_id == ware_id)).execute()


class OrdersPrices(BaseModel):
    class Meta:
        table_name = 'orders_prices'

    ware_id = ForeignKeyField(Order, field='ware_id')
    date = DateTimeField()
    price = IntegerField(default=None)
    status = IntegerField(unique=False, null=True)

    @classmethod
    def get_yesterday_today_prices(cls):
        yesterday, today = get_yesterday_today_date()

        return cls.select(cls.ware_id, cls.price, cls.date) \
            .where((cls.date == yesterday) | (cls.date == today)) \
            .order_by(cls.ware_id)

    @classmethod
    def get_last_moth_prices(cls, ware_id):
        return cls.select(cls.price.distinct(), cls.date) \
            .where((cls.ware_id == ware_id) & (cls.date > last_month()))

    @classmethod
    def update_price_status(cls, price_status, ware_id):
        cls.update(status=price_status).where(cls.ware_id == ware_id).execute()


def init_db():
    database.create_tables([User, Order, OrdersPrices, UsersOrders], safe=True)
