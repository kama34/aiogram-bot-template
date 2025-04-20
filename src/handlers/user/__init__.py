# Импорты для внешнего доступа через точку

from handlers.user.basic import register_basic_handlers
from handlers.user.referral import register_referral_handlers
from handlers.user.subscription import register_subscription_handlers
from handlers.user.shop import register_shop_handlers
from handlers.user.cart import register_cart_handlers
from handlers.user.payment import register_payment_handlers