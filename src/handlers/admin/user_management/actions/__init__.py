from aiogram import Dispatcher
from .blocking import register_blocking_handlers
from .exceptions import register_exception_handlers
from .navigation import register_navigation_handlers

def register_all_action_handlers(dp: Dispatcher):
    """Регистрирует все обработчики действий с пользователями"""
    register_blocking_handlers(dp)
    register_exception_handlers(dp)
    register_navigation_handlers(dp)

__all__ = ['register_all_action_handlers']