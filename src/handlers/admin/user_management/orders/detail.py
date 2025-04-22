from aiogram import types
from utils.admin_utils import is_admin
from services.order_service import OrderService
from services.product_service import get_product_by_id
import traceback

# Вспомогательная функция
def get_product_name(product_id):
    """Получает имя продукта по его ID"""
    # ИСПРАВЛЕНО: Используем данные из базы данных
    product = get_product_by_id(product_id)
    if product:
        return product.get('name', f"Товар #{product_id}")
    return f"Товар #{product_id}"  # Возвращаем заглушку только если товар не найден

async def view_order_details(callback: types.CallbackQuery):
    """Просмотр деталей конкретного заказа с улучшенной обработкой ошибок"""
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
    
    # Создаем сервис для работы с заказами
    order_service = OrderService()
    
    try:
        # Получаем данные заказа
        order = order_service.get_order_by_id(order_id)
        if not order:
            await callback.message.answer("Заказ не найден")
            return
        
        # Получаем данные пользователя и товаров
        user = order_service.get_user_by_id(order.user_id)
        items = order_service.get_order_items(order_id)
        
        # Форматируем данные для отображения
        order_date = order.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(order, "created_at") else "неизвестно"
        user_name = f"{user.full_name} (@{user.username})" if user and user.username else f"ID: {order.user_id}"
        
        # Статусы заказа
        status_display = {
            "new": "🆕 Новый",
            "paid": "💰 Оплачен",
            "processing": "⚙️ В обработке",
            "shipped": "🚚 Отправлен",
            "delivered": "✅ Доставлен",
            "cancelled": "❌ Отменён"
        }
        
        status = getattr(order, "status", "unknown")
        status_text = status_display.get(status, f"Неизвестный статус ({status})")
        
        # Формируем сообщение
        message_text = (
            f"📝 <b>Детали заказа #{order.id}</b>\n\n"
            f"📅 Дата: {order_date}\n"
            f"👤 Пользователь: {user_name}\n"
            f"💰 Сумма заказа: {order.total_amount*100:.2f} ⭐\n"
            f"🔖 Статус: {status_text}\n"
        )
        
        if hasattr(order, "payment_id") and order.payment_id:
            message_text += f"🆔 ID платежа: <code>{order.payment_id}</code>\n"
            
        if hasattr(order, "shipping_address") and order.shipping_address:
            message_text += f"📫 Адрес доставки: {order.shipping_address}\n"
        
        # Добавляем список товаров в заказе
        message_text += "\n<b>Содержимое заказа:</b>\n"
        
        if items:
            for i, item in enumerate(items, 1):
                product_name = get_product_name(item.product_id)
                item_total = item.price * item.quantity
                message_text += f"{i}. <b>{product_name}</b> - {item.quantity} шт. × {item.price:.2f} ⭐ = {item_total:.2f} ⭐\n"
        else:
            message_text += "Нет данных о товарах в этом заказе\n"
        
        # Создаем клавиатуру
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "◀️ К списку заказов",
            callback_data=f"view_orders_{order.user_id}"
        ))
        keyboard.add(types.InlineKeyboardButton(
            "👤 К профилю пользователя",
            callback_data=f"back_to_user_{order.user_id}"
        ))
        
        # Отправляем результат
        await callback.message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        error_text = f"Ошибка при получении деталей заказа: {str(e)}\n\n"
        error_text += traceback.format_exc()
        print(error_text)
        
        # Отправляем более короткое сообщение пользователю
        keyboard = types.InlineKeyboardMarkup()
        if order and hasattr(order, "user_id"):
            user_id = order.user_id
            keyboard.add(types.InlineKeyboardButton(
                "◀️ К списку заказов",
                callback_data=f"view_orders_{user_id}"
            ))
        else:
            keyboard.add(types.InlineKeyboardButton(
                "◀️ Назад в админ-панель",
                callback_data="admin_back"
            ))
        
        await callback.message.answer(
            f"❌ Произошла ошибка при загрузке деталей заказа: {type(e).__name__}",
            reply_markup=keyboard
        )
    finally:
        order_service.close_session()