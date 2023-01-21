from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

cart = KeyboardButton(text='/cart')
stores = KeyboardButton(text='/stores')
help_b = KeyboardButton(text='/help')

start_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(cart)
help_kb = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(help_b)
