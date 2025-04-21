from aiogram import Dispatcher
from .view import view_user_orders
from .detail import view_order_details

def register_order_handlers(dp: Dispatcher):
    """Регистрирует обработчики для функций, связанных с заказами"""
    # Обработчик для просмотра списка заказов пользователя
    dp.register_callback_query_handler(
        view_user_orders, 
        lambda c: c.data and c.data.startswith("view_orders_"),
        state="*"
    )
    
    # Обработчик для просмотра деталей заказа
    dp.register_callback_query_handler(
        view_order_details, 
        lambda c: c.data and c.data.startswith("order_details_"),
        state="*"
    )

# Экспортируем основные функции
__all__ = [
    'register_order_handlers',
    'view_user_orders',
    'view_order_details'
]