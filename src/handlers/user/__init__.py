# Импорты для внешнего доступа через точку

from .shop import register_shop_handlers
from .subscription import register_subscription_handlers
from .basic import register_basic_handlers
from .referral import register_referral_handlers
from .cart import register_cart_handlers
from .order import register_order_handlers
from .payment import register_payment_handlers
from .orders import register_user_orders_handlers  # Добавляем импорт

def register_all_user_handlers(dp):
    """Регистрирует все обработчики пользователей"""
    register_basic_handlers(dp)
    register_referral_handlers(dp)
    register_subscription_handlers(dp)
    register_shop_handlers(dp)
    register_cart_handlers(dp)
    register_payment_handlers(dp)
    register_order_handlers(dp)
    register_user_orders_handlers(dp)  # Добавляем регистрацию