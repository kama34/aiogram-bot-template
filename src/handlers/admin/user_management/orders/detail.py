from aiogram import types
from utils.admin_utils import is_admin
from services.order_service import OrderService

# Вспомогательная функция
def get_product_name(product_id):
    """Получает имя продукта по его ID (заглушка)"""
    # Это заглушка, в реальном приложении здесь будет обращение к базе данных или сервису продуктов
    return f"Товар #{product_id}"

async def view_order_details(callback: types.CallbackQuery):
    """Просмотр деталей конкретного заказа"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при обработке callback: {e}")
    
    # Получаем ID заказа
    order_id = int(callback.data.replace("order_details_", ""))
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Получаем данные заказа
    order_service = OrderService()
    
    try:
        # Получаем заказ и его элементы
        order = order_service.get_order_by_id(order_id)
        if not order:
            await callback.message.answer("Заказ не найден")
            return
        
        # Получаем пользователя и товары заказа
        user = order_service.get_user_by_id(order.user_id)
        items = order_service.get_order_items(order_id)
        
        # Статусы заказа с эмодзи
        status_display = {
            "new": "🆕 Новый",
            "paid": "💰 Оплачен",
            "processing": "⚙️ В обработке",
            "shipped": "🚚 Отправлен",
            "delivered": "✅ Доставлен",
            "cancelled": "❌ Отменён"
        }
        
        # Формируем сообщение с деталями
        order_date = order.created_at.strftime("%d.%m.%Y %H:%M")
        message_text = (
            f"📝 <b>Детали заказа #{order.id}</b>\n\n"
            f"📅 Дата: {order_date}\n"
            f"👤 Пользователь: {user.full_name} (@{user.username})\n"
            f"💰 Сумма заказа: {order.total_amount:.2f} ₽\n"
            f"🔖 Статус: {status_display.get(order.status, order.status)}\n"
        )
        
        if order.payment_id:
            message_text += f"🆔 ID платежа: <code>{order.payment_id}</code>\n"
            
        if order.shipping_address:
            message_text += f"📫 Адрес доставки: {order.shipping_address}\n"
        
        # Добавляем список товаров
        message_text += "\n<b>Содержимое заказа:</b>\n"
        
        if items:
            for i, item in enumerate(items, 1):
                product_name = get_product_name(item.product_id)
                item_total = item.price * item.quantity
                message_text += f"{i}. <b>{product_name}</b> - {item.quantity} шт. × {item.price:.2f} ₽ = {item_total:.2f} ₽\n"
        else:
            message_text += "Нет данных о товарах в этом заказе\n"
        
        # Создаем клавиатуру
        keyboard = types.InlineKeyboardMarkup()
        
        # Кнопки навигации
        keyboard.add(types.InlineKeyboardButton(
            "◀️ К списку заказов",
            callback_data=f"view_orders_{order.user_id}"
        ))
        
        keyboard.add(types.InlineKeyboardButton(
            "👤 К профилю пользователя",
            callback_data=f"back_to_user_{order.user_id}"
        ))
        
        await callback.message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении деталей заказа: {str(e)}")
    finally:
        order_service.close_session()