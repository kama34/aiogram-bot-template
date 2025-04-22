from aiogram import types
from services.order_service import OrderService
import traceback

async def view_my_orders(query_or_message):
    """Показывает пользователю список его заказов"""
    # Определяем тип входящего объекта
    if isinstance(query_or_message, types.CallbackQuery):
        # Это callback (нажатие на inline кнопку)
        user_id = query_or_message.from_user.id
        message = query_or_message.message
        
        # Освобождаем callback
        try:
            await query_or_message.answer()
        except Exception as e:
            print(f"Не удалось ответить на callback: {e}")
            
        # Пытаемся удалить предыдущее сообщение, если оно есть
        try:
            await message.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
    else:
        # Это сообщение (нажатие на reply кнопку)
        user_id = query_or_message.from_user.id
        message = query_or_message
    
    # Создаем экземпляр сервиса заказов
    order_service = OrderService()
    
    try:
        # Получаем статистику заказов
        stats = order_service.get_order_stats(user_id)
        
        # Получаем список заказов
        orders = order_service.get_user_orders(user_id)
        
        # Формируем заголовок с информацией и статистикой
        if stats["total_orders"] > 0:
            message_text = (
                f"🛍️ <b>Мои заказы</b>\n\n"
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
                    callback_data=f"my_order_detail_{order.id}"
                ))
        else:
            message_text = (
                f"🛍️ <b>Мои заказы</b>\n\n"
                f"У вас пока нет заказов.\n"
                f"Чтобы сделать заказ, перейдите в магазин."
            )
            keyboard = types.InlineKeyboardMarkup()
        
        # Добавляем кнопку возврата в меню
        keyboard.add(types.InlineKeyboardButton(
            "◀️ Вернуться в меню", 
            callback_data="back_to_menu"
        ))
        
        # Отправляем сообщение с результатом
        await message.answer(message_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        error_text = f"Ошибка при получении заказов: {str(e)}\n\n"
        error_text += traceback.format_exc()
        print(error_text)
        
        # Отправляем более короткое сообщение пользователю
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "◀️ Вернуться в меню", 
            callback_data="back_to_menu"
        ))
        await message.answer(
            f"❌ Произошла ошибка при загрузке заказов. Пожалуйста, попробуйте позже.", 
            reply_markup=keyboard
        )
    finally:
        order_service.close_session()
from aiogram import types, Dispatcher
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