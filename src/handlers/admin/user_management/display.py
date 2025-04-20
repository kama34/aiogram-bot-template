from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from services.database import User
from utils.admin_utils import is_admin

async def show_user_info(message, user, back_callback="letter_search", delete_prev=False):
    """Отображает информацию о пользователе с кнопками действий
    
    Args:
        message: Сообщение или колбэк
        user: Объект пользователя
        back_callback: Строка с callback_data для кнопки "Назад"
        delete_prev: Удалить предыдущее сообщение перед отправкой нового
    """
    # Проверяем, нужно ли удалить предыдущее сообщение
    if delete_prev and hasattr(message, 'delete'):
        try:
            await message.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
    
    # Формируем информацию о пользователе
    user_info = (
        f"👤 <b>Информация о пользователе:</b>\n\n"
        f"ID: <code>{user.id}</code>\n"
        f"Username: @{user.username}\n"
        f"Полное имя: {user.full_name}\n"
    )
    
    if hasattr(User, 'is_blocked'):
        status = "🚫 Заблокирован" if user.is_blocked else "✅ Активен"
        user_info += f"Статус: {status}\n"
        
    if hasattr(User, 'is_exception'):
        exception_status = "⭐️ Исключение" if user.is_exception else "👤 Обычный пользователь"
        user_info += f"Доступ: {exception_status}\n"
        
    if hasattr(User, 'created_at'):
        user_info += f"Зарегистрирован: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    # Создаем клавиатуру с действиями
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    if hasattr(User, 'is_blocked'):
        action = "Разблокировать" if user.is_blocked else "Заблокировать"
        keyboard.add(types.InlineKeyboardButton(
            action, callback_data=f"{'unblock' if user.is_blocked else 'block'}_{user.id}"
        ))
    
    if hasattr(User, 'is_exception'):
        exception_action = "Убрать исключение" if user.is_exception else "Сделать исключением"
        keyboard.add(types.InlineKeyboardButton(
            exception_action, callback_data=f"{'remove_exception' if user.is_exception else 'add_exception'}_{user.id}"
        ))
    
    keyboard.add(types.InlineKeyboardButton(
        "👥 Рефералы", callback_data=f"view_referrals_{user.id}"
    ))
    
    keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data=back_callback))
    
    # Определяем метод для отправки сообщения в зависимости от типа входного объекта
    if hasattr(message, 'answer'):
        # Это сообщение или объект с методом answer
        return await message.answer(user_info, parse_mode="HTML", reply_markup=keyboard)
    elif hasattr(message, 'message') and hasattr(message.message, 'answer'):
        # Это callback_query
        return await message.message.answer(user_info, parse_mode="HTML", reply_markup=keyboard)
    else:
        # Неизвестный тип, попытаемся использовать bot.send_message
        from bot import bot
        chat_id = message.chat.id if hasattr(message, 'chat') else message.message.chat.id
        return await bot.send_message(chat_id, user_info, parse_mode="HTML", reply_markup=keyboard)

async def view_user_handler(callback: types.CallbackQuery, state: FSMContext = None, skip_message_delete=False):
    """Обрабатывает просмотр информации о пользователе по ID"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")
    
    # Очистим текущее состояние, если оно есть
    if state:
        current_state = await state.get_state()
        if current_state:
            await state.finish()
    
    user_id = callback.data.replace("view_user_", "")
    
    # Удаляем текущее сообщение только если его не удалили ранее
    if not skip_message_delete:
        try:
            await callback.message.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
    
    from services.database import get_database_session
    session = get_database_session()
    
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="letter_search"))
            await callback.message.answer("Пользователь не найден.", reply_markup=keyboard)
            return
        
        await show_user_info(callback.message, user)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при просмотре пользователя: {str(e)}")
    finally:
        session.close()

def register_display_handlers(dp: Dispatcher):
    """Регистрирует обработчики отображения пользователей"""
    # Регистрируем для всех состояний, используя state="*"
    dp.register_callback_query_handler(
        view_user_handler, 
        lambda c: c.data and c.data.startswith("view_user_"),
        state="*"
    )