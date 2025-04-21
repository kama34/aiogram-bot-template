from aiogram import types, Dispatcher
from services.database import get_database_session, User
from utils.admin_utils import is_admin
from ..display import show_user_info

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
        await show_user_info(callback.message, user)
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении информации о пользователе: {str(e)}")
    finally:
        session.close()

def register_navigation_handlers(dp: Dispatcher):
    """Регистрирует обработчики навигации"""
    dp.register_callback_query_handler(
        back_to_user_handler,
        lambda c: c.data and c.data.startswith("back_to_user_")
    )