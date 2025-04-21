from aiogram import types
from services.user_service import UserService
from .link_utils import generate_referral_link

async def admin_referral_link(message: types.Message):
    """Генерирует реферальную ссылку для администраторов"""
    user_id = message.chat.id
    
    # Генерируем реферальную ссылку
    referral_link = await generate_referral_link(user_id)
    
    # Получаем статистику
    user_service = UserService()
    referral_count = user_service.count_user_referrals(user_id)
    user_service.close_session()
    
    # Создаем клавиатуру
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton(
            "📤 Поделиться", 
            switch_inline_query=f"Приглашаю тебя в наш бот! {referral_link}"
        )
    )
    keyboard.add(
        types.InlineKeyboardButton("📊 Мои рефералы", callback_data="admin_my_refs")
    )
    keyboard.add(
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
    )
    
    await message.answer(
        f"🔗 <b>Ваша админская реферальная ссылка:</b>\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"Поделитесь этой ссылкой с друзьями! Вы пригласили: <b>{referral_count}</b> пользователей",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def admin_my_referrals(message: types.Message):
    """Показывает рефералов администратора"""
    user_id = message.chat.id
    
    user_service = UserService()
    referrals = user_service.get_user_referrals(user_id)
    
    if not referrals:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
        
        await message.answer("У вас пока нет приглашённых пользователей.", reply_markup=keyboard)
        user_service.close_session()
        return
    
    referral_text = "👥 <b>Ваши приглашённые пользователи:</b>\n\n"
    for i, ref in enumerate(referrals, 1):
        user = user_service.get_user_by_id(ref.user_id)
        if user:
            date_str = ref.created_at.strftime("%d.%m.%Y") if hasattr(ref, 'created_at') else "неизвестно"
            referral_text += f"{i}. {user.full_name} (@{user.username}) - {date_str}\n"
    
    user_service.close_session()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
    
    await message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)