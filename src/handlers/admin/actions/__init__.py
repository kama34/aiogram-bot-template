from aiogram import Dispatcher
from .user_actions import register_user_action_handlers

def register_all_action_handlers(dp: Dispatcher):
    """Регистрирует все обработчики действий"""
    register_user_action_handlers(dp)