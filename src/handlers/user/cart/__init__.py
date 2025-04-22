from aiogram import Dispatcher
from .display import cart_command, view_cart
from .operations import clear_cart_callback, remove_one_item_callback, remove_all_item_callback, add_one_item_callback
from .quantity import select_quantity_callback, add_to_cart_with_quantity_callback

# Настройка логгера уже должна быть в каждом модуле отдельно

def register_cart_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков для корзины"""
    # Регистрация обработчика для команды корзины
    dp.register_message_handler(cart_command, lambda message: message.text == "🧺 Корзина", state="*")
    
    # Регистрация обработчиков для кнопок в корзине
    dp.register_callback_query_handler(view_cart, lambda c: c.data == "view_cart")
    dp.register_callback_query_handler(clear_cart_callback, lambda c: c.data == "clear_cart")
    dp.register_callback_query_handler(select_quantity_callback, lambda c: c.data.startswith("select_quantity_"))
    dp.register_callback_query_handler(add_to_cart_with_quantity_callback, lambda c: c.data.startswith("add_qty_"))
    dp.register_callback_query_handler(remove_one_item_callback, lambda c: c.data.startswith("remove_one_"))
    dp.register_callback_query_handler(remove_all_item_callback, lambda c: c.data.startswith("remove_all_"))
    dp.register_callback_query_handler(add_one_item_callback, lambda c: c.data.startswith("add_one_"))

# Экспортируем функцию регистрации для импорта в основном модуле
__all__ = ['register_cart_handlers']