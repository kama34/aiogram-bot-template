from .admin import register_all_admin_handlers
from .user import register_all_user_handlers

def register_all_handlers(dp):
    """Регистрирует все обработчики"""
    # Сначала регистрируем пользовательские обработчики
    register_all_user_handlers(dp)
    # Затем административные
    register_all_admin_handlers(dp)