def register_all_handlers(dp):
    # Импортируем и регистрируем обработчики заказов
    from handlers.user.order import register_order_handlers
    register_order_handlers(dp)