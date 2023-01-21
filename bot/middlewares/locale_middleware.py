from pathlib import Path
from typing import Tuple, Any, Optional

from aiogram import types
from aiogram.contrib.middlewares.i18n import I18nMiddleware
from babel.core import Locale
from bot.database.models.goods import User

I18N_DOMAIN = 'mybot'
BASE_DIR = Path(__file__).parent.parent.parent
LOCALES_DIR = BASE_DIR / 'locales'


class OwnMiddleware(I18nMiddleware):

    async def get_user_locale(self, action: str, args: Tuple[Any]) -> Optional[str]:
        """
        User locale getter
        You can override the method if you want to use different way of
        getting user language.

        :param action: event name
        :param args: event arguments
        :return: locale name or None
        """
        user: Optional[types.User] = types.User.get_current()
        locale: Optional[Locale] = User.get_user_locale(user.id)

        if locale and locale.language in self.locales:
            *_, data = args
            language = data['locale'] = locale.language
            return language
        return self.default


# Setup i18n middleware
i18n = OwnMiddleware(I18N_DOMAIN, LOCALES_DIR)
# Alias for gettext method
get_text = i18n.gettext
