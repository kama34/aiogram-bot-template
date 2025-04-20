from aiogram import Dispatcher, types
from services.database import get_database_session, User
from utils.admin_utils import is_admin
from ..user_management.display import show_user_info

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
    
    # Определяем тип действия и ID пользователя
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
    
    # Получаем пользователя из БД и применяем действие
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            await callback.message.answer("Пользователь не найден")
            return
        
        # Удаляем текущее сообщение
        try:
            await callback.message.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
        
        action_text = await apply_user_action(user, action, session)
        
        # Формируем обновленную информацию без удаления (т.к. уже удалили)
        from ..user_management.display import show_user_info
        await show_user_info(callback.message, user, back_callback="letter_search")
        
        # Показываем сообщение об успешном действии
        await callback.answer(action_text, show_alert=True)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при выполнении действия: {str(e)}")
    finally:
        session.close()

async def apply_user_action(user, action, session):
    """Применяет действие к пользователю и возвращает текст результата"""
    if action == "block":
        if hasattr(User, 'is_blocked'):
            user.is_blocked = True
            session.commit()
            
            # Уведомляем пользователя о блокировке
            try:
                from bot import bot
                await bot.send_message(
                    chat_id=user.id,
                    text="⛔️ Ваш аккаунт был заблокирован администратором. "
                         "Вы можете использовать кнопку 'ℹ️ Помощь' для обращения в поддержку."
                )
            except Exception as e:
                print(f"Не удалось уведомить пользователя {user.id} о блокировке: {e}")
            
            return f"Пользователь @{user.username} заблокирован"
        else:
            return "Модель данных не поддерживает блокировку пользователей"
    
    elif action == "unblock":
        if hasattr(User, 'is_blocked'):
            user.is_blocked = False
            session.commit()
            return f"Пользователь @{user.username} разблокирован"
        else:
            return "Модель данных не поддерживает блокировку пользователей"
    
    elif action == "add_exception":
        if hasattr(User, 'is_exception'):
            user.is_exception = True
            session.commit()
            return f"Пользователь @{user.username} добавлен в исключения"
        else:
            return "Модель данных не поддерживает исключения"
    
    elif action == "remove_exception":
        if hasattr(User, 'is_exception'):
            user.is_exception = False
            session.commit()
            return f"Пользователь @{user.username} удален из исключений"
        else:
            return "Модель данных не поддерживает исключения"
    
    return "Неизвестное действие"

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
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
            await callback.message.answer("Пользователь не найден.", reply_markup=keyboard)
            return
        
        # Используем общую функцию для отображения информации о пользователе
        from ..user_management.display import show_user_info
        await show_user_info(callback.message, user)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении информации о пользователе: {str(e)}")
    finally:
        session.close()

def register_user_action_handlers(dp: Dispatcher):
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