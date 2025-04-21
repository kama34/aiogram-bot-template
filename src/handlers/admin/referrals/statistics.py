from aiogram import types
from services.referral_service import ReferralService
from utils.admin_utils import is_admin

async def view_referral_statistics(callback: types.CallbackQuery):
    """Показывает общую статистику по реферальной системе"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Удаляем текущее сообщение
    await callback.message.delete()
    
    # Создаем сервис для работы с реферальными данными
    ref_service = ReferralService()
    
    try:
        # Получаем статистические данные
        total_users_with_referrer = ref_service.get_total_users_with_referrer()
        top_referrers = ref_service.get_top_referrers(limit=10)
        
        # Форматируем текст со статистикой
        stats_text = f"📊 <b>Статистика реферальной системы</b>\n\n"
        stats_text += f"Всего пользователей с реферером: <b>{total_users_with_referrer}</b>\n\n"
        
        if top_referrers:
            stats_text += "<b>Топ рефереров:</b>\n"
            
            for i, (user_id, referral_count) in enumerate(top_referrers, 1):
                user = ref_service.get_user_by_id(user_id)
                user_name = f"@{user.username}" if user and user.username else f"ID: {user_id}"
                stats_text += f"{i}. {user_name} — <b>{referral_count}</b> рефералов\n"
        else:
            stats_text += "Пока нет активных рефереров.\n"
        
        # Создаем клавиатуру с кнопками навигации
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
        # Отправляем сообщение со статистикой
        await callback.message.answer(stats_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        # Обрабатываем возможные ошибки
        error_keyboard = types.InlineKeyboardMarkup()
        error_keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        await callback.message.answer(
            f"Ошибка при получении статистики: {str(e)}", 
            reply_markup=error_keyboard
        )
    finally:
        # Закрываем сессию
        ref_service.close_session()