from aiogram import types
from utils.admin_utils import is_admin
from services.order_service import OrderService

async def view_user_orders(callback: types.CallbackQuery):
    """Просмотр списка заказов пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при обработке callback: {e}")
    
    # Получаем ID пользователя из данных callback
    user_id = int(callback.data.replace("view_orders_", ""))
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Получаем данные заказов
    order_service = OrderService()
    
    try:
        # Получаем пользователя
        user = order_service.get_user_by_id(user_id)
        if not user:
            await callback.message.answer("Пользователь не найден")
            return
        
        # Получаем статистику и список заказов
        stats = order_service.get_order_stats(user_id)
        orders = order_service.get_user_orders(user_id)
        
        # Формируем сообщение и клавиатуру
        if stats["total_orders"] > 0:
            message_text = (
                f"🛍️ <b>Заказы пользователя {user.full_name} (@{user.username}):</b>\n\n"
                f"Всего заказов: <b>{stats['total_orders']}</b>\n"
                f"Общая сумма покупок: <b>{stats['total_spent']:.2f} ₽</b>\n"
            )
            
            if stats["first_date"] and stats["last_date"]:
                message_text += (
                    f"Первый заказ: {stats['first_date'].strftime('%d.%m.%Y')}\n"
                    f"Последний заказ: {stats['last_date'].strftime('%d.%m.%Y')}\n\n"
                )
            
            message_text += "<b>История заказов:</b>\n\n"
            
            # Создаем клавиатуру для просмотра заказов
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            
            for order in orders:
                order_date = order.created_at.strftime("%d.%m.%Y %H:%M")
                status_emojis = {
                    "new": "🆕",
                    "paid": "💰",
                    "processing": "⚙️",
                    "shipped": "🚚",
                    "delivered": "✅",
                    "cancelled": "❌"
                }
                status_emoji = status_emojis.get(order.status, "❓")
                
                message_text += f"{status_emoji} <b>Заказ #{order.id}</b> от {order_date} - <b>{order.total_amount:.2f} ₽</b>\n"
                
                # Кнопка для просмотра деталей заказа
                keyboard.add(types.InlineKeyboardButton(
                    f"📋 Детали заказа #{order.id} ({order_date})", 
                    callback_data=f"order_details_{order.id}"
                ))
        else:
            message_text = (
                f"🛍️ <b>Заказы пользователя {user.full_name} (@{user.username}):</b>\n\n"
                f"У пользователя нет заказов"
            )
            keyboard = types.InlineKeyboardMarkup()
        
        # Добавляем кнопку возврата к профилю
        keyboard.add(types.InlineKeyboardButton(
            "◀️ Вернуться к профилю", 
            callback_data=f"back_to_user_{user_id}"
        ))
        
        # Отправляем результат
        await callback.message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении заказов: {str(e)}")
    finally:
        order_service.close_session()