from aiogram import Dispatcher

# Импорты из модулей
from handlers.user.basic import register_basic_handlers
from handlers.user.referral import register_referral_handlers
from handlers.user.subscription import register_subscription_handlers
from handlers.user.shop import register_shop_handlers
from handlers.user.cart import register_cart_handlers
from handlers.user.payment import register_payment_handlers
from handlers.user.order import register_order_handlers
from handlers.admin import register_all_admin_handlers
from handlers.user import register_all_user_handlers

def register_all_handlers(dp: Dispatcher):
    """
    Регистрация всех обработчиков сообщений и callback-запросов бота
    """
    # Регистрация обработчиков пользователя
    register_all_user_handlers(dp)
    
    # Регистрация обработчиков администратора
    register_all_admin_handlers(dp)
    
    return dp