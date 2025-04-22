from aiogram import Dispatcher, types
from .categories import register_category_handlers, show_categories
from .products import register_products_handlers
from .product_detail import register_product_detail_handlers
from ..cart import register_cart_handlers

async def menu_command(message: types.Message):
    """Обработчик команды /shop или кнопки 'Магазин'"""
    await show_categories(message)

def register_shop_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для функций магазина"""
    # Основной обработчик команды магазина
    dp.register_message_handler(menu_command, lambda message: message.text == "🛒 Магазин", state="*")
    dp.register_message_handler(menu_command, commands=["shop"], state="*")
    
    # Регистрируем обработчики для подмодулей
    register_category_handlers(dp)
    register_products_handlers(dp)
    register_product_detail_handlers(dp)
    
    # Регистрируем обработчики корзины
    register_cart_handlers(dp)

__all__ = [
    'register_shop_handlers',
    'menu_command',  # Экспортируем для импорта в basic.py
]