from aiogram import Dispatcher
from aiogram.types import ContentTypes

from .checkout import checkout_callback
from .process import pay_with_stars_callback
from .callbacks import process_pre_checkout_query, process_successful_payment

def register_payment_handlers(dp: Dispatcher):
    """Регистрация обработчиков платежей"""
    # Регистрация обработчика оформления заказа
    dp.register_callback_query_handler(checkout_callback, lambda c: c.data == "checkout")
    
    # Регистрация обработчика оплаты звездами
    dp.register_callback_query_handler(pay_with_stars_callback, lambda c: c.data == "pay_with_stars")
    
    # Регистрация обработчиков для Telegram Payments
    dp.register_pre_checkout_query_handler(process_pre_checkout_query)
    dp.register_message_handler(process_successful_payment, content_types=ContentTypes.SUCCESSFUL_PAYMENT)

# Экспортировать только нужные функции
__all__ = ['register_payment_handlers']