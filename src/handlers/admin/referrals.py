from aiogram import Dispatcher, types
from sqlalchemy import func, desc, text
from services.database import get_database_session, User, Referral
from utils.admin_utils import is_admin
from services.user_service import UserService

async def view_referral_statistics(message: types.Message):
    """Показывает статистику рефералов"""
    session = get_database_session()
    try:
        # Total referrals count
        total_referrals = session.query(Referral).count()
        
        # Top referrers
        top_referrers_query = session.query(
            Referral.referred_by, 
            func.count(Referral.id).label('count')
        ).group_by(Referral.referred_by).order_by(text('count DESC')).limit(5)
        
        top_referrers = top_referrers_query.all()
        
        # Format statistics message
        stats = f"📊 <b>Статистика рефералов:</b>\n\n" \
                f"👥 Всего рефералов: <b>{total_referrals}</b>\n\n" \
                f"🏆 <b>Топ 5 пригласивших:</b>\n"
        
        for i, (referrer_id, count) in enumerate(top_referrers, 1):
            if referrer_id:
                referrer = session.query(User).filter(User.id == referrer_id).first()
                if referrer:
                    stats += f"{i}. {referrer.full_name} (@{referrer.username}): {count} приглашений\n"
        
        # Add back button
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
        await message.answer(stats, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        await message.answer(f"Ошибка при получении статистики рефералов: {str(e)}")
    finally:
        session.close()

async def admin_referral_link(message: types.Message):
    """Генерирует реферальную ссылку для админов"""
    user_id = message.chat.id
    
    # Get bot username for proper link generation
    from bot import bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    # Create a referral link with admin ID
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Get how many users this admin has referred
    user_service = UserService()
    referral_count = user_service.count_user_referrals(user_id)
    user_service.close_session()
    
    # Create buttons for the admin
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
        # Add back button
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
        
        await message.answer("У вас пока нет приглашённых пользователей.", reply_markup=keyboard)
        user_service.close_session()
        return
    
    # Build referral list
    referral_text = "👥 <b>Ваши приглашённые пользователи:</b>\n\n"
    for i, ref in enumerate(referrals, 1):
        user = user_service.get_user_by_id(ref.user_id)
        if user:
            date_str = ref.created_at.strftime("%d.%m.%Y") if hasattr(ref, 'created_at') else "неизвестно"
            referral_text += f"{i}. {user.full_name} (@{user.username}) - {date_str}\n"
    
    user_service.close_session()
    
    # Add back button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
    
    await message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)

async def view_user_referrals(callback: types.CallbackQuery):
    """Просмотр рефералов, приглашенных конкретным пользователем"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Get user ID from callback data
    user_id = int(callback.data.replace("view_referrals_", ""))
    
    # Удаляем текущее сообщение
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    user_service = UserService()
    
    try:
        # Get the user whose referrals we're viewing
        target_user = user_service.get_user_by_id(user_id)
        if not target_user:
            await callback.message.answer("Пользователь не найден")
            return
        
        # Get all referrals by this user
        referrals = user_service.get_user_referrals(user_id)
        
        if not referrals or len(referrals) == 0:
            # No referrals found - show message with back button
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Назад к пользователю", callback_data=f"back_to_user_{user_id}"))
            await callback.message.answer(
                f"Пользователь {target_user.full_name} (@{target_user.username}) не пригласил ни одного пользователя.",
                reply_markup=keyboard
            )
            return
        
        # Format referral information
        total_referrals = len(referrals)
        referral_text = (
            f"👥 <b>Рефералы пользователя {target_user.full_name} (@{target_user.username}):</b>\n\n"
            f"Всего приглашено: <b>{total_referrals}</b> пользователей\n\n"
        )
        
        # List details of each referral
        for i, ref in enumerate(referrals, 1):
            referred_user = user_service.get_user_by_id(ref.user_id)
            if referred_user:
                date_str = ref.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(ref, 'created_at') else "неизвестно"
                status = "🚫 Blocked" if hasattr(referred_user, 'is_blocked') and referred_user.is_blocked else "✅ Active"
                
                referral_text += (
                    f"{i}. <b>{referred_user.full_name}</b> (@{referred_user.username})\n"
                    f"   ID: <code>{referred_user.id}</code> | {status} | 📅 {date_str}\n"
                )
        
        # Create keyboard with back button
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад к пользователю", callback_data=f"back_to_user_{user_id}"))
        
        # Send message without deleting (already deleted above)
        await callback.message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        print(f"Error getting user referrals: {e}")
        await callback.message.answer(f"Ошибка при получении списка рефералов: {str(e)}")
    finally:
        user_service.close_session()

async def copy_ref_link_callback(callback: types.CallbackQuery):
    """Обрабатывает кнопку копирования реферальной ссылки"""
    try:
        await callback.answer("Ссылка скопирована в сообщение ниже")
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Extract user ID from callback
    user_id = callback.data.replace("copy_ref_", "")
    
    # Generate link
    from bot import bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Create keyboard with back button
    keyboard = types.InlineKeyboardMarkup()
    
    # Add appropriate back button based on whether this is admin or user
    if is_admin(callback.from_user.id):
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
    
    # Send as a separate message for easy copying
    await callback.message.answer(
        f"<code>{referral_link}</code>\n\nСкопируйте эту ссылку и отправьте друзьям",
        parse_mode="HTML",
        reply_markup=keyboard
    )

def register_referral_handlers(dp: Dispatcher):
    """Регистрирует обработчики для функций, связанных с реферальной системой"""
    dp.register_callback_query_handler(view_user_referrals, lambda c: c.data and c.data.startswith("view_referrals_"))
    dp.register_callback_query_handler(copy_ref_link_callback, lambda c: c.data and c.data.startswith("copy_ref_"))