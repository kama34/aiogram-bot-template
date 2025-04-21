from aiogram import types, Dispatcher
from services.database import get_database_session, User
from utils.admin_utils import is_admin
from ..display import show_user_info

async def handle_exception_action(callback: types.CallbackQuery):
    """Обрабатывает действия с исключениями пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    await callback.answer()
    
    # Определяем тип действия и ID пользователя
    callback_data = callback.data
    is_remove = callback_data.startswith("remove_exception_")
    user_id = callback_data.replace("remove_exception_" if is_remove else "add_exception_", "")
    
    # Получаем пользователя из БД
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            await callback.message.answer("Пользователь не найден")
            return
        
        # Выполняем действие с исключением
        if not hasattr(User, 'is_exception'):
            await callback.answer("Модель данных не поддерживает исключения", show_alert=True)
            return
            
        # Меняем статус исключения
        user.is_exception = not is_remove
        session.commit()
        
        # Формируем текст успешного действия
        action_text = f"✅ Пользователь @{user.username} {'удален из исключений' if is_remove else 'добавлен в исключения'}"
        
        # Удаляем текущее сообщение
        try:
            await callback.message.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
        
        # Показываем обновленную информацию о пользователе
        msg = await show_user_info(callback.message, user)
        
        # Добавляем уведомление о действии
        await callback.answer(action_text, show_alert=True)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при выполнении действия: {str(e)}")
    finally:
        session.close()

def register_exception_handlers(dp: Dispatcher):
    """Регистрирует обработчики для исключений"""
    dp.register_callback_query_handler(
        handle_exception_action, 
        lambda c: c.data and (
            c.data.startswith("add_exception_") or 
            c.data.startswith("remove_exception_")
        )
    )