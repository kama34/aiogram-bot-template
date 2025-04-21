from aiogram import Dispatcher
from .core import register_admin_handlers
from .user_management import register_user_management_handlers
from .statistics import register_statistics_handlers
from .referrals import register_referral_handlers  # Изменено на новый модуль
from .channels import register_channel_handlers
from .messaging import register_messaging_handlers

def register_all_admin_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для административной панели"""
    register_admin_handlers(dp)
    register_user_management_handlers(dp)
    register_statistics_handlers(dp)
    register_referral_handlers(dp)
    register_channel_handlers(dp)
    register_messaging_handlers(dp)