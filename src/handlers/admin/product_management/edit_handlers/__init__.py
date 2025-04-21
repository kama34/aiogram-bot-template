from aiogram import Dispatcher

from .main import register_main_handlers
from .field_selection import register_field_selection_handlers
from .value_processing import register_value_processing_handlers
from .deletion import register_deletion_handlers

def register_edit_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для редактирования товаров"""
    register_main_handlers(dp)
    register_field_selection_handlers(dp)
    register_value_processing_handlers(dp)
    register_deletion_handlers(dp)

__all__ = ['register_edit_handlers']