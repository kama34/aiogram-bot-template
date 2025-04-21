from aiogram import Dispatcher

from .start import register_start_handlers
from .basic_info import register_basic_info_handlers
from .media_handlers import register_media_handlers
from .categorization import register_categorization_handlers
from .inventory import register_inventory_handlers
from .confirmation import register_confirmation_handlers

def register_product_creation_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для создания товаров"""
    register_start_handlers(dp)
    register_basic_info_handlers(dp)
    register_media_handlers(dp)
    register_categorization_handlers(dp)
    register_inventory_handlers(dp)
    register_confirmation_handlers(dp)

__all__ = ['register_product_creation_handlers']