from aiogram import types
from utils.admin_utils import is_admin
from services.user_service import UserService

async def view_user_referrals(callback: types.CallbackQuery):
    """Просмотр рефералов, приглашенных конкретным пользователем"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    user_id = int(callback.data.replace("view_referrals_", ""))
    orig_message = callback.message
    
    user_service = UserService()
    
    try:
        target_user = user_service.get_user_by_id(user_id)
        if not target_user:
            await callback.message.answer("Пользователь не найден")
            return
        
        referrals = user_service.get_user_referrals(user_id)
        
        await orig_message.delete()
        
        if not referrals or len(referrals) == 0:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Назад к пользователю", callback_data=f"back_to_user_{user_id}"))
            await callback.message.answer(
                f"Пользователь {target_user.full_name} (@{target_user.username}) не пригласил ни одного пользователя.",
                reply_markup=keyboard
            )
            return
        
        total_referrals = len(referrals)
        referral_text = (
            f"👥 <b>Рефералы пользователя {target_user.full_name} (@{target_user.username}):</b>\n\n"
            f"Всего приглашено: <b>{total_referrals}</b> пользователей\n\n"
        )
        
        for i, ref in enumerate(referrals, 1):
            referred_user = user_service.get_user_by_id(ref.user_id)
            if referred_user:
                date_str = ref.created_at.strftime("%d.%m.%Y") if hasattr(ref, 'created_at') else "неизвестно"
                referral_text += f"{i}. {referred_user.full_name} (@{referred_user.username}) - {date_str}\n"
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад к пользователю", callback_data=f"back_to_user_{user_id}"))
        
        await callback.message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        print(f"Error getting user referrals: {e}")
        await callback.message.answer(f"Ошибка при получении списка рефералов: {str(e)}")
    finally:
        user_service.close_session()