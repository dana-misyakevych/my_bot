from .locale_middleware import i18n
from .throttling import ThrottlingMiddleware
from .user import UsersMiddleware


def setup_middleware(dp):
    dp.middleware.setup(ThrottlingMiddleware())
    dp.middleware.setup(UsersMiddleware())
    dp.middleware.setup(i18n)
