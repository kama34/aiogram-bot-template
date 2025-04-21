from aiogram import types, Dispatcher
from services.database import get_database_session, User
from utils.admin_utils import is_admin
from ..display import show_user_info

async def handle_block_action(callback: types.CallbackQuery):
    """Обрабатывает действия блокировки пользователя"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    await callback.answer()
    
    # Определяем тип действия и ID пользователя
    callback_data = callback.data
    is_unblock = callback_data.startswith("unblock_")
    user_id = callback_data.replace("unblock_" if is_unblock else "block_", "")
    
    # Получаем пользователя из БД
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        
        if not user:
            await callback.message.answer("Пользователь не найден")
            return
        
        # Выполняем действие блокировки/разблокировки
        if not hasattr(User, 'is_blocked'):
            await callback.answer("Модель данных не поддерживает блокировку пользователей", show_alert=True)
            return
            
        # Меняем статус блокировки
        user.is_blocked = not is_unblock
        session.commit()
        
        # Уведомляем пользователя о блокировке (только если блокируем)
        if not is_unblock:
            try:
                from bot import bot
                await bot.send_message(
                    chat_id=user.id,
                    text="⛔️ Ваш аккаунт был заблокирован администратором. "
                         "Вы можете использовать кнопку 'ℹ️ Помощь' для обращения в поддержку."
                )
            except Exception as e:
                print(f"Не удалось уведомить пользователя {user.id} о блокировке: {e}")
        
        # Формируем текст успешного действия
        action_text = f"✅ Пользователь @{user.username} {'разблокирован' if is_unblock else 'заблокирован'}"
        
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

def register_blocking_handlers(dp: Dispatcher):
    """Регистрирует обработчики блокировки/разблокировки"""
    dp.register_callback_query_handler(
        handle_block_action, 
        lambda c: c.data and (c.data.startswith("block_") or c.data.startswith("unblock_"))
    )