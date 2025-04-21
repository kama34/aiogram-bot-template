from aiogram import Dispatcher
from .view import view_user_orders
from .detail import view_order_details

def register_order_handlers(dp: Dispatcher):
    """Регистрирует обработчики для просмотра заказов пользователей"""
    # Просмотр списка заказов пользователя
    dp.register_callback_query_handler(
        view_user_orders, 
        lambda c: c.data and c.data.startswith("view_orders_"),
        state="*"
    )
    
    # Просмотр деталей конкретного заказа
    dp.register_callback_query_handler(
        view_order_details, 
        lambda c: c.data and c.data.startswith("order_details_"),
        state="*"
    )

__all__ = ['register_order_handlers', 'view_user_orders', 'view_order_details']