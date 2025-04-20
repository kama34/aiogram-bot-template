from aiogram import Dispatcher
from .core import register_admin_handlers
from .user_management import register_user_management_handlers
from .statistics import register_statistics_handlers
from .referrals import register_referral_handlers
from .channels import register_channel_handlers
from .messaging import register_messaging_handlers
from .actions import register_all_action_handlers

def register_all_admin_handlers(dp: Dispatcher):
    """Регистрирует все обработчики для административной панели"""
    # Регистрация основных обработчиков
    register_admin_handlers(dp)
    
    # Регистрация обработчиков управления пользователями
    register_user_management_handlers(dp)
    
    # Регистрация обработчиков статистики
    register_statistics_handlers(dp)
    
    # Регистрация обработчиков реферальной системы
    register_referral_handlers(dp)
    
    # Регистрация обработчиков управления каналами
    register_channel_handlers(dp)
    
    # Регистрация обработчиков массовой рассылки
    register_messaging_handlers(dp)
    
    # Регистрация обработчиков действий с пользователями
    register_all_action_handlers(dp)