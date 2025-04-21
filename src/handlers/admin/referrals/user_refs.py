from aiogram import types
from utils.admin_utils import is_admin
from services.referral_service import ReferralService

async def view_user_referrals(callback: types.CallbackQuery):
    """Просмотр рефералов, приглашенных конкретным пользователем"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Получаем ID пользователя из данных колбэка
    user_id = int(callback.data.replace("view_referrals_", ""))
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Создаем сервис для работы с реферальными данными
    ref_service = ReferralService()
    
    try:
        # Получаем пользователя, чьи рефералы нужно отобразить
        target_user = ref_service.get_user_by_id(user_id)
        if not target_user:
            await callback.message.answer("Пользователь не найден")
            return
        
        # Получаем всех рефералов этого пользователя
        referrals = ref_service.get_user_referrals(user_id)
        
        if not referrals or len(referrals) == 0:
            # Если рефералов нет, показываем сообщение с кнопкой возврата
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton(
                "◀️ Назад к пользователю", 
                callback_data=f"back_to_user_{user_id}"
            ))
            await callback.message.answer(
                f"Пользователь {target_user.full_name} (@{target_user.username}) не пригласил ни одного пользователя.",
                reply_markup=keyboard
            )
            return
        
        # Формируем информацию о рефералах
        total_referrals = len(referrals)
        referral_text = (
            f"👥 <b>Рефералы пользователя {target_user.full_name} (@{target_user.username}):</b>\n\n"
            f"Всего приглашено: <b>{total_referrals}</b> пользователей\n\n"
        )
        
        # Добавляем информацию о каждом реферале
        for i, ref in enumerate(referrals, 1):
            referred_user = ref_service.get_user_by_id(ref.user_id)
            if referred_user:
                date_str = ref.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(ref, 'created_at') else "неизвестно"
                status = "🚫 Заблокирован" if hasattr(referred_user, 'is_blocked') and referred_user.is_blocked else "✅ Активен"
                
                referral_text += (
                    f"{i}. <b>{referred_user.full_name}</b> (@{referred_user.username})\n"
                    f"   ID: <code>{referred_user.id}</code> | {status} | 📅 {date_str}\n"
                )
        
        # Создаем клавиатуру с кнопкой возврата
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton(
            "◀️ Назад к пользователю", 
            callback_data=f"back_to_user_{user_id}"
        ))
        
        await callback.message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        print(f"Error getting user referrals: {e}")
        await callback.message.answer(f"Ошибка при получении списка рефералов: {str(e)}")
    finally:
        ref_service.close_session()