from aiogram import types
from utils.admin_utils import is_admin
from utils.logger import setup_logger
from services.user_service import UserService
from .utils import get_bot_username

# Setup logger for this module
logger = setup_logger('handlers.referral.commands')

async def referral_command(message: types.Message):
    """Generate a referral link for the user"""
    user_id = message.from_user.id
    
    # For admin users, redirect to the admin panel version
    if is_admin(user_id):
        # Create a "fake" message object that matches what admin_referral_link expects
        class AdminMessage:
            def __init__(self, chat_id):
                self.chat = types.Chat(id=chat_id, type="private")
                self.answer = message.answer
        
        admin_msg = AdminMessage(user_id)
        from handlers.admin import admin_referral_link
        await admin_referral_link(admin_msg)
        return
    
    # Regular user flow continues as before...
    bot_username = await get_bot_username()
    
    # Create a referral link with the user's ID
    # Make sure there's no space or other characters that could break the parameter
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Get how many users this user has referred
    with UserService() as user_service:
        referral_count = user_service.count_user_referrals(user_id)
    
    # Create share buttons with cleaner formatting
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Share button - make sure no extra spaces or characters
    keyboard.add(
        types.InlineKeyboardButton(
            "📤 Поделиться", 
            switch_inline_query=f"Приглашаю тебя в бота! {referral_link}"
        )
    )
    
    await message.answer(
        f"🔗 <b>Ваша реферальная ссылка:</b>\n\n"
        f"<code>{referral_link}</code>\n\n"
        f"Поделитесь этой ссылкой с друзьями! Вы пригласили: <b>{referral_count}</b> пользователей",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def my_referrals_command(message: types.Message):
    """Show the user's referrals"""
    user_id = message.from_user.id
    
    with UserService() as user_service:
        referrals = user_service.get_user_referrals(user_id)
        
        if not referrals:
            # Add a button to get referral link when no referrals found
            keyboard = types.InlineKeyboardMarkup(row_width=1)
            keyboard.add(
                types.InlineKeyboardButton("🔗 Получить реферальную ссылку", callback_data=f"get_ref_link")
            )
            await message.answer("У вас пока нет приглашённых пользователей.", reply_markup=keyboard)
            return
        
        # Count total referrals
        total_referrals = len(referrals)
        
        # Build referral list with more details
        referral_text = f"👥 <b>Ваши приглашённые пользователи</b> ({total_referrals}):\n\n"
        
        for i, ref in enumerate(referrals, 1):
            user = user_service.get_user_by_id(ref.user_id)
            if user:
                date_str = ref.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(ref, 'created_at') else "неизвестно"
                username_display = f"@{user.username}" if user.username else "без username"
                referral_text += f"{i}. <b>{user.full_name}</b> ({username_display})\n   📅 {date_str}\n"
        
        # Add statistics summary
        referral_text += f"\n<b>Всего приглашено:</b> {total_referrals} пользователей"
        
        # Create keyboard with useful actions
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton("🔗 Получить реферальную ссылку", callback_data="get_ref_link")
        )
    
    await message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)