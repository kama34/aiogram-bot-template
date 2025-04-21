from aiogram import Dispatcher
from .stats import view_referral_statistics
from .admin import admin_referral_link, admin_my_referrals
from .user_refs import view_user_referrals
from .link_utils import copy_ref_link_callback

def register_referral_handlers(dp: Dispatcher):
    """Регистрирует обработчики для функций, связанных с реферальной системой"""
    # Обработчики для статистики
    dp.register_callback_query_handler(view_referral_statistics, lambda c: c.data == "referral_stats")
    
    # Обработчики для админа
    dp.register_callback_query_handler(admin_referral_link, lambda c: c.data == "admin_ref_link")
    dp.register_callback_query_handler(admin_my_referrals, lambda c: c.data == "admin_my_refs")
    
    # Обработчики для просмотра рефералов пользователя
    dp.register_callback_query_handler(view_user_referrals, 
                                     lambda c: c.data and c.data.startswith("view_referrals_"))
    
    # Обработчики для копирования ссылок
    dp.register_callback_query_handler(copy_ref_link_callback, 
                                     lambda c: c.data and c.data.startswith("copy_ref_"))

# Экспортируем основные функции
__all__ = [
    'register_referral_handlers',
    'view_referral_statistics',
    'admin_referral_link',
    'admin_my_referrals',
    'view_user_referrals',
    'copy_ref_link_callback'
]