from aiogram import Dispatcher

# Ре-экспортируем функции для обратной совместимости
from .users import view_user_statistics, export_user_list
from .referrals.stats import view_referral_statistics
from .referrals.admin import admin_referral_link, admin_my_referrals

def register_statistics_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для статистики"""
    # Обработчики для статистики пользователей
    dp.register_callback_query_handler(view_user_statistics, lambda c: c.data == "user_stats")
    dp.register_callback_query_handler(export_user_list, lambda c: c.data == "export_users")
    
    # Регистрируем обработчики для реферальной системы
    from .referrals import register_referral_handlers
    register_referral_handlers(dp)

# Экспортируем основные функции
__all__ = [
    'register_statistics_handlers',
    'view_user_statistics',
    'export_user_list',
    'view_referral_statistics',
    'admin_referral_link',
    'admin_my_referrals'
]