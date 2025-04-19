from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Regular user keyboard
user_kb = ReplyKeyboardMarkup(resize_keyboard=True)
user_kb.add(
    KeyboardButton("🛒 Меню"),
    KeyboardButton("🧺 Корзина")  # Добавляем кнопку корзины рядом с меню
)
user_kb.add(
    KeyboardButton("🔍 Профиль"), 
    KeyboardButton("ℹ️ Помощь")
)
user_kb.add(
    KeyboardButton("🔗 Реферальная ссылка"),
    KeyboardButton("👥 Мои рефералы")
)
