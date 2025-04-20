from aiogram import types
from services.database import get_database_session, User
from utils.admin_utils import is_admin

async def handle_user_action(callback: types.CallbackQuery):
    """Обрабатывает действия с пользователем (блокировка/разблокировка/исключения)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")
    
    callback_data = callback.data
    action = None
    user_id = None
    
    # Парсим callback_data для определения действия
    if callback_data.startswith("block_"):
        action = "block"
        user_id = callback_data.replace("block_", "")
    elif callback_data.startswith("unblock_"):
        action = "unblock"
        user_id = callback_data.replace("unblock_", "")
    elif callback_data.startswith("add_exception_"):
        action = "add_exception"
        user_id = callback_data.replace("add_exception_", "")
    elif callback_data.startswith("remove_exception_"):
        action = "remove_exception"
        user_id = callback_data.replace("remove_exception_", "")
    
    if not action or not user_id:
        print(f"Некорректный callback: {callback_data}")
        return
    
    # Получаем пользователя из БД
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            await callback.message.answer("Пользователь не найден")
            return
        
        # Применяем действие
        if action == "block":
            if hasattr(User, 'is_blocked'):
                user.is_blocked = True
                session.commit()
                
                # Уведомляем пользователя о блокировке
                try:
                    from bot import bot
                    await bot.send_message(
                        chat_id=user.id,
                        text="⛔️ Ваш аккаунт был заблокирован администратором. Вы можете использовать кнопку 'ℹ️ Помощь' для обращения в поддержку."
                    )
                except Exception as e:
                    print(f"Не удалось уведомить пользователя {user.id} о блокировке: {e}")
                
                action_text = f"✅ Пользователь @{user.username} заблокирован"
            else:
                action_text = "⚠️ Модель данных не поддерживает блокировку пользователей"
        
        elif action == "unblock":
            if hasattr(User, 'is_blocked'):
                user.is_blocked = False
                session.commit()
                action_text = f"✅ Пользователь @{user.username} разблокирован"
            else:
                action_text = "⚠️ Модель данных не поддерживает блокировку пользователей"
        
        elif action == "add_exception":
            if hasattr(User, 'is_exception'):
                user.is_exception = True
                session.commit()
                action_text = f"✅ Пользователь @{user.username} добавлен в исключения"
            else:
                action_text = "⚠️ Модель данных не поддерживает исключения"
        
        elif action == "remove_exception":
            if hasattr(User, 'is_exception'):
                user.is_exception = False
                session.commit()
                action_text = f"✅ Пользователь @{user.username} удален из исключений"
            else:
                action_text = "⚠️ Модель данных не поддерживает исключения"
        
        # Обновляем информацию о пользователе в сообщении
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
        
        # Создаем обновленную клавиатуру
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
        
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
        # Обновляем сообщение с информацией о пользователе
        await callback.message.edit_text(
            f"{user_info}\n\n{action_text}", 
            parse_mode="HTML", 
            reply_markup=keyboard
        )
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при выполнении действия: {str(e)}")
    finally:
        session.close()

async def back_to_user_handler(callback: types.CallbackQuery):
    """Обработчик возврата к информации о пользователе"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")
    
    user_id = callback.data.replace("back_to_user_", "")
    
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
            await callback.message.edit_text("Пользователь не найден.", reply_markup=keyboard)
            return
        
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
        
        # Создаем клавиатуру
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
        
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
        await callback.message.edit_text(user_info, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении информации о пользователе: {str(e)}")
    finally:
        session.close()

def register_action_handlers(dp):
    """Регистрирует обработчики действий с пользователями"""
    dp.register_callback_query_handler(
        handle_user_action, 
        lambda c: c.data and (
            c.data.startswith("block_") or 
            c.data.startswith("unblock_") or
            c.data.startswith("add_exception_") or
            c.data.startswith("remove_exception_")
        )
    )
    dp.register_callback_query_handler(
        back_to_user_handler,
        lambda c: c.data and c.data.startswith("back_to_user_")
    )