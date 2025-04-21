from aiogram import types
from utils.admin_utils import is_admin
from services.order_service import OrderService
from services.product_service import get_product_name

async def view_order_details(callback: types.CallbackQuery):
    """Просмотр деталей конкретного заказа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Получаем ID заказа из данных колбэка
    order_id = callback.data.replace("order_details_", "")
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Создаем экземпляр сервиса заказов
    order_service = OrderService()
    
    try:
        # Получаем заказ по ID
        order = order_service.get_order_by_id(order_id)
        if not order:
            await callback.message.answer("Заказ не найден")
            order_service.close_session()
            return
        
        # Получаем пользователя, сделавшего заказ
        user = order_service.get_user_by_id(order.user_id)
        user_name = f"{user.full_name} (@{user.username})" if user else f"ID: {order.user_id}"
        
        # Получаем элементы заказа
        order_items = order_service.get_order_items(order_id)
        
        # Форматируем дату создания заказа
        order_date = order.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(order, "created_at") else "неизвестно"
        
        # Формируем текст сообщения с деталями заказа
        message_text = (
            f"📝 <b>Детали заказа #{order.id}</b>\n\n"
            f"📅 Дата: {order_date}\n"
            f"👤 Пользователь: {user_name}\n"
            f"💰 Сумма заказа: {order.total_amount:.2f} ⭐\n"
            f"🆔 ID платежа: <code>{order.payment_id}</code>\n"
        )
        
        if hasattr(order, "shipping_address") and order.shipping_address:
            message_text += f"📫 Адрес доставки: {order.shipping_address}\n"
        
        if hasattr(order, "status") and order.status:
            message_text += f"🔖 Статус заказа: {order.status}\n"
        
        # Добавляем список товаров в заказе
        message_text += "\n<b>Содержимое заказа:</b>\n"
        
        if order_items:
            for i, item in enumerate(order_items, 1):
                product_name = get_product_name(item.product_id)
                item_total = item.price * item.quantity
                message_text += f"{i}. <b>{product_name}</b> - {item.quantity} шт. × {item.price:.2f} ⭐ = {item_total:.2f} ⭐\n"
        else:
            message_text += "Нет данных о товарах в этом заказе\n"
        
        # Создаем клавиатуру с кнопками навигации
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        # Кнопка возврата к списку заказов пользователя
        keyboard.add(types.InlineKeyboardButton(
            "◀️ Назад к списку заказов", 
            callback_data=f"view_orders_{order.user_id}"
        ))
        
        # Кнопка возврата к профилю пользователя
        keyboard.add(types.InlineKeyboardButton(
            "👤 К профилю пользователя", 
            callback_data=f"back_to_user_{order.user_id}"
        ))
        
        await callback.message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        print(f"Error getting order details: {e}")
        await callback.message.answer(f"Ошибка при получении деталей заказа: {str(e)}")
    finally:
        order_service.close_session()