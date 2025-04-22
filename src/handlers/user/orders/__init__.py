from aiogram import Dispatcher
from .list import view_my_orders
from .detail import view_my_order_detail

def register_user_orders_handlers(dp: Dispatcher):
    """Регистрирует обработчики для просмотра заказов пользователем"""
    # Обработчик для кнопки "Мои заказы" в основной клавиатуре
    dp.register_message_handler(
        view_my_orders,
        lambda message: message.text == "🛍️ Мои заказы",
        state="*"
    )
    
    # Просмотр списка своих заказов через inline-кнопку
    dp.register_callback_query_handler(
        view_my_orders,
        lambda c: c.data == "my_orders",
        state="*"
    )
    
    # Просмотр деталей конкретного заказа
    dp.register_callback_query_handler(
        view_my_order_detail,
        lambda c: c.data and c.data.startswith("my_order_detail_"),
        state="*"
    )

__all__ = ['register_user_orders_handlers']