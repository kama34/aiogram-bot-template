from aiogram import Dispatcher
from .menu import register_menu_handlers
from .list import register_list_handlers
from .edit_handlers import register_edit_handlers  # Обновленный импорт
from .creation import register_product_creation_handlers  # Если уже реализован

def register_product_management_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для управления товарами"""
    register_menu_handlers(dp)
    register_list_handlers(dp)
    register_edit_handlers(dp)  # Использует новую структуру
    
    # Если уже реализована модульная структура для создания товаров
    if 'register_product_creation_handlers' in globals():
        register_product_creation_handlers(dp)

__all__ = ['register_product_management_handlers']