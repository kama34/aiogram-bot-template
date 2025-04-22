from aiogram import Dispatcher
from .commands import referral_command, my_referrals_command
from .callbacks import get_ref_link_callback, copy_ref_link_callback
from utils.logger import setup_logger

# Setup logger for this module
logger = setup_logger('handlers.referral.router')

def register_referral_handlers(dp: Dispatcher):
    """Регистрация обработчиков для реферальной системы"""
    logger.info("Registering referral handlers")
    
    # Регистрация обработчиков команд
    dp.register_message_handler(referral_command, commands=["referral"])
    dp.register_message_handler(my_referrals_command, commands=["myreferrals"])
    
    # Регистрация обработчиков callback-запросов
    dp.register_callback_query_handler(get_ref_link_callback, lambda c: c.data == "get_ref_link")
    dp.register_callback_query_handler(copy_ref_link_callback, lambda c: c.data and c.data.startswith("copy_ref_"))
    
    logger.info("Referral handlers registered successfully")