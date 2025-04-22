from aiogram import types
from utils.admin_utils import is_admin
from services.order_service import OrderService
import traceback

async def view_user_orders(callback: types.CallbackQuery):
    """Просмотр списка заказов пользователя с улучшенной обработкой ошибок"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при обработке callback: {e}")
    
    # Получаем ID пользователя из данных колбэка
    user_id = int(callback.data.replace("view_orders_", ""))
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Создаем экземпляр сервиса заказов
    order_service = OrderService()
    
    try:
        # Получаем пользователя по ID
        user = order_service.get_user_by_id(user_id)
        if not user:
            await callback.message.answer("Пользователь не найден")
            order_service.close_session()
            return
        
        # Получаем статистику заказов
        stats = order_service.get_order_stats(user_id)
        
        # Получаем список заказов
        orders = order_service.get_user_orders(user_id)
        
        # Формируем заголовок с информацией о пользователе и статистикой
        if stats["total_orders"] > 0:
            message_text = (
                f"🛍️ <b>Заказы пользователя {user.full_name} (@{user.username}):</b>\n\n"
                f"Всего заказов: <b>{stats['total_orders']}</b>\n"
                f"Общая сумма покупок: <b>{stats['total_spent']*100:.2f} ⭐</b>\n"
            )
            
            if stats["first_date"] and stats["last_date"]:
                message_text += (
                    f"Первый заказ: {stats['first_date'].strftime('%d.%m.%Y')}\n"
                    f"Последний заказ: {stats['last_date'].strftime('%d.%m.%Y')}\n\n"
                )
            
            # Добавляем список заказов
            message_text += "<b>История заказов:</b>\n\n"
            
            # Создаем клавиатуру
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            
            for order in orders:
                order_date = order.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(order, "created_at") else "неизвестно"
                status_emojis = {
                    "new": "🆕",
                    "paid": "💰",
                    "processing": "⚙️",
                    "shipped": "🚚",
                    "delivered": "✅",
                    "cancelled": "❌"
                }
                status = getattr(order, "status", "new")
                status_emoji = status_emojis.get(status, "❓")
                
                message_text += f"{status_emoji} <b>Заказ #{order.id}</b> от {order_date} - <b>{order.total_amount*100:.2f} ⭐</b>\n"
                
                # Кнопка детализации заказа
                keyboard.add(types.InlineKeyboardButton(
                    f"📋 Детали заказа #{order.id} от {order_date}", 
                    callback_data=f"order_details_{order.id}"
                ))
        else:
            message_text = (
                f"🛍️ <b>Заказы пользователя {user.full_name} (@{user.username}):</b>\n\n"
                f"У пользователя нет заказов"
            )
            keyboard = types.InlineKeyboardMarkup()
        
        # Добавляем кнопку возврата
        keyboard.add(types.InlineKeyboardButton(
            "◀️ Вернуться к профилю", 
            callback_data=f"back_to_user_{user_id}"
        ))
        
        # Отправляем сообщение с результатом
        await callback.message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        error_text = f"Ошибка при получении заказов: {str(e)}\n\n"
        error_text += traceback.format_exc()
        print(error_text)
        
        # Отправляем более короткое сообщение пользователю
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "◀️ Вернуться к профилю", 
            callback_data=f"back_to_user_{user_id}"
        ))
        await callback.message.answer(
            f"❌ Произошла ошибка при загрузке заказов: {type(e).__name__}", 
            reply_markup=keyboard
        )
    finally:
        order_service.close_session()