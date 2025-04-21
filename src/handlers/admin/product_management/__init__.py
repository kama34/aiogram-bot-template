from aiogram import Dispatcher
from .menu import register_menu_handlers
from .create import register_create_handlers
from .edit import register_edit_handlers
from .list import register_list_handlers

def register_product_management_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для управления товарами"""
    register_menu_handlers(dp)
    register_create_handlers(dp)
    register_edit_handlers(dp)
    register_list_handlers(dp)

__all__ = ['register_product_management_handlers']