from aiogram import types
from services.order_service import OrderService
from services.product_service import get_product_by_id
import traceback
from utils.message_utils import safe_delete_message

# Вспомогательная функция
def get_product_name(product_id):
    """Получает имя продукта по его ID"""
    try:
        product = get_product_by_id(product_id)
        if product:
            return product.get('name', f"Товар #{product_id}") if isinstance(product, dict) else getattr(product, 'name', f"Товар #{product_id}")
    except Exception as e:
        print(f"Ошибка при получении имени продукта: {e}")
    return f"Товар #{product_id}"

async def view_my_order_detail(callback: types.CallbackQuery):
    """Показывает пользователю детали конкретного заказа"""
    user_id = callback.from_user.id
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при обработке callback: {e}")
    
    # Получаем ID заказа
    order_id = int(callback.data.replace("my_order_detail_", ""))
    
    print(f"Получен запрос на просмотр заказа #{order_id} от пользователя {user_id}")
    
    # Удаляем текущее сообщение
    try:
        await safe_delete_message(callback.message)
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Создаем сервис для работы с заказами
    order_service = OrderService()
    
    try:
        # Получаем данные заказа
        order = order_service.get_order_by_id(order_id)
        
        print(f"Получены данные заказа: {order}")
        
        # Проверяем, существует ли заказ и принадлежит ли он пользователю
        if not order:
            await callback.message.answer("❌ Заказ не найден")
            order_service.close_session()
            return
            
        if order.user_id != user_id:
            await callback.message.answer("⛔ У вас нет доступа к этому заказу")
            order_service.close_session()
            return
        
        # Получаем товары в заказе
        items = order_service.get_order_items(order_id)
        
        print(f"Получены товары заказа: {items}")
        
        # Форматируем данные для отображения
        order_date = order.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(order, "created_at") else "неизвестно"
        
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
                message_text += f"{i}. <b>{product_name}</b> - {item.quantity} шт. × {item.price*100:.2f} ⭐ = {item_total*100:.2f} ⭐\n"
        else:
            message_text += "Нет данных о товарах в этом заказе\n"
        
        # Создаем клавиатуру
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "◀️ К списку заказов",
            callback_data="my_orders"
        ))
        
        # Добавляем кнопку для возврата в меню
        keyboard.add(types.InlineKeyboardButton(
            "🏠 Вернуться в меню",
            callback_data="back_to_menu"
        ))
        
        # Отправляем результат
        await callback.message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        error_text = f"Ошибка при получении деталей заказа: {str(e)}\n\n"
        error_text += traceback.format_exc()
        print(error_text)
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "◀️ К списку заказов",
            callback_data="my_orders"
        ))
        await callback.message.answer(
            f"❌ Произошла ошибка при загрузке деталей заказа. Пожалуйста, попробуйте позже.", 
            reply_markup=keyboard
        )
    finally:
        order_service.close_session()