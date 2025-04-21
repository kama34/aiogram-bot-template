from aiogram import Dispatcher
from .search import register_search_handlers
from .display import register_display_handlers
from .pagination import register_pagination_handlers
from .bulk_operations import register_bulk_operations_handlers
from .actions import register_all_action_handlers

def register_user_management_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для управления пользователями"""
    register_search_handlers(dp)
    register_display_handlers(dp)
    register_pagination_handlers(dp)
    register_bulk_operations_handlers(dp)
    register_all_action_handlers(dp)