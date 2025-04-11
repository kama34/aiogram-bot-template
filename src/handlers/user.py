from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from services.database import get_database_session, User, Referral
from services.user_service import UserService
from keyboards.admin_kb import admin_inlin_kb
from keyboards.user_kb import user_kb  # Import the admin keyboard
from keyboards.admin_kb import admin_reply_kb  # Import the admin keyboard
from utils.admin_utils import is_admin
from config import ADMIN_IDS, BOT_TOKEN
from utils.subscription_utils import check_user_subscriptions  

import re

# Get bot username for referral links
async def get_bot_username():
    from bot import bot
    bot_info = await bot.get_me()
    return bot_info.username

async def start_command(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or "unknown"
    full_name = message.from_user.full_name or "Unknown User"
    
    # Check for referral parameter
    referrer_id = None
    args = message.get_args()
    
    if args and args.startswith("ref_"):
        try:
            referrer_id = int(args.replace("ref_", ""))
        except (ValueError, TypeError) as e:
            print(f"Error parsing referrer ID: {e}")
            referrer_id = None
    
    # Initialize services
    user_service = UserService()
    
    # Check if user already exists
    existing_user = user_service.get_user_by_id(user_id)
    is_new_user = not existing_user
    
    # Register new user if needed
    if is_new_user:
        try:
            new_user = User(
                id=user_id,
                username=username,
                full_name=full_name
            )
            user_service.session.add(new_user)
            user_service.session.commit()
            
            # Process referral for new users
            if referrer_id and referrer_id != user_id:
                await process_referral(user_service, user_id, referrer_id, full_name, username)
        except Exception as e:
            print(f"Error registering user: {e}")
    else:
        # Process referral even for existing users who haven't been referred before
        if referrer_id and referrer_id != user_id:
            # Check if this user already has a referrer
            existing_referral = user_service.get_referral_by_user_id(user_id)
            if not existing_referral:
                await process_referral(user_service, user_id, referrer_id, full_name, username)
    
    # Always close the session to avoid connection leaks
    user_service.close_session()
    
    # Show normal welcome message with appropriate keyboard based on user type
    welcome_message = "Добро пожаловать в бота!" if not is_new_user else "Добро пожаловать! Вы успешно зарегистрированы."
    
    # Choose the appropriate keyboard based on whether the user is an admin
    keyboard = admin_reply_kb if is_admin(user_id) else user_kb
    
    await message.answer(welcome_message, reply_markup=keyboard)

async def process_referral(user_service, user_id, referrer_id, full_name, username):
    """Process a referral and send notifications"""
    referrer = user_service.get_user_by_id(referrer_id)
    if referrer:
        try:
            # Create referral record with explicit commit
            new_referral = Referral(
                user_id=user_id,
                referred_by=referrer_id
            )
            user_service.session.add(new_referral)
            user_service.session.commit()
            print(f"Referral created: user {user_id} referred by {referrer_id}")
            
            # Get bot instance for messaging
            from bot import bot
            
            # Send notification to the new user (invitee)
            await bot.send_message(
                chat_id=user_id,
                text=f"Вы были приглашены пользователем {referrer.full_name}!"
            )
            
            # Send notification to the referrer
            await bot.send_message(
                chat_id=referrer_id, 
                text=f"По вашей реферальной ссылке пришёл пользователь: {full_name} (@{username})"
            )
            
            # Notify admin about the referral
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=f"🔔 Новый реферал!\n\n"
                            f"Пригласил: {referrer.full_name} (@{referrer.username}, ID: {referrer.id})\n"
                            f"Приглашён: {full_name} (@{username}, ID: {user_id})"
                    )
                except Exception as e:
                    print(f"Error notifying admin {admin_id}: {e}")
        except Exception as e:
            print(f"Error processing referral: {e}")

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
    user_service = UserService()
    referral_count = user_service.count_user_referrals(user_id)
    user_service.close_session()
    
    # Create share buttons with cleaner formatting
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    # Direct link button
    keyboard.add(
        types.InlineKeyboardButton("🔗 Скопировать ссылку", callback_data=f"copy_ref_{user_id}")
    )
    
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
    
    user_service = UserService()
    referrals = user_service.get_user_referrals(user_id)
    
    if not referrals:
        # Add a button to get referral link when no referrals found
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton("🔗 Получить реферальную ссылку", callback_data=f"get_ref_link")
        )
        await message.answer("У вас пока нет приглашённых пользователей.", reply_markup=keyboard)
        user_service.close_session()
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
    
    user_service.close_session()
    await message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)

# Add handler for the get_ref_link callback
async def get_ref_link_callback(callback: types.CallbackQuery):
    """Handle the get referral link button"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Just call the existing referral command
    await referral_command(callback.message)

async def check_subscription_command(message: types.Message):
    user_service = UserService()
    user = user_service.get_user_by_id(message.from_user.id)
    if user:
        await message.answer("You are subscribed!")
    else:
        await message.answer("You are not subscribed. Please subscribe to continue.")

async def text_handler(message: types.Message):
    """Handle text messages for keyboard buttons"""
    text = message.text
    
    # Always allow help regardless of user status
    if text == "ℹ️ Помощь":
        await help_command(message)
        return
    
    # For all other commands, check if user is blocked
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user and hasattr(user, 'is_blocked') and user.is_blocked:
            await message.answer("Ваш аккаунт заблокирован. Используйте кнопку 'ℹ️ Помощь' для поддержки.")
            return
    finally:
        session.close()
    
    # Process other commands for non-blocked users
    if text == "🔍 Профиль":
        await profile_command(message)
    elif text == "🔗 Реферальная ссылка":
        await referral_command(message)
    elif text == "👥 Мои рефералы":
        await my_referrals_command(message)
    elif text == "🔧 Панель администратора" and is_admin(message.from_user.id):
        from handlers.admin import admin_panel
        await admin_panel(message)

async def copy_ref_link_callback(callback: types.CallbackQuery):
    """Handle the copy referral link button"""
    try:
        await callback.answer("Ссылка скопирована в сообщение ниже")
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Extract user ID from callback
    user_id = callback.data.replace("copy_ref_", "")
    
    # Generate link
    bot_username = await get_bot_username()
    referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
    # Send as a separate message for easy copying
    await callback.message.answer(
        f"<code>{referral_link}</code>\n\nСкопируйте эту ссылку и отправьте друзьям",
        parse_mode="HTML"
    )

async def profile_command(message: types.Message):
    """Show user profile information"""
    user_id = message.from_user.id
    
    # Get user data from database
    user_service = UserService()
    user = user_service.get_user_by_id(user_id)
    
    if not user:
        await message.answer("Error: User profile not found!")
        user_service.close_session()
        return
    
    # Get referral counts
    referral_count = user_service.count_user_referrals(user_id)
    
    # Get referrer info if available
    referral_info = user_service.get_referral_by_user_id(user_id)
    referrer = None
    if referral_info and referral_info.referred_by:
        referrer = user_service.get_user_by_id(referral_info.referred_by)
    
    # Format registration date
    registered_date = user.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(user, "created_at") else "неизвестно"
    
    # Build profile text
    profile_text = (
        f"👤 <b>Ваш профиль</b>\n\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"👤 Имя: {user.full_name}\n"
        f"🔖 Username: @{user.username}\n"
        f"📅 Дата регистрации: {registered_date}\n\n"
        f"👥 Приглашено пользователей: <b>{referral_count}</b>\n"
    )
    
    # Add referrer info if available
    if referrer:
        profile_text += f"👨‍👦 Вас пригласил: {referrer.full_name} (@{referrer.username})\n"
    
    # Create keyboard with referral link button
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("🔗 Моя реферальная ссылка", callback_data="get_ref_link"))
    
    await message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)
    user_service.close_session()

async def help_command(message: types.Message):
    """Show help information"""
    help_text = (
        "ℹ️ <b>Помощь по использованию бота</b>\n\n"
        "<b>Доступные команды:</b>\n"
        "/start - Запустить бота\n"
        "/help - Показать эту справку\n"
        "/referral - Получить реферальную ссылку\n"
        "/myreferrals - Показать ваших рефералов\n\n"
        
        "<b>Как пользоваться ботом:</b>\n"
        "• Используйте <b>Профиль</b> чтобы увидеть информацию о вашем аккаунте\n"
        "• Нажмите <b>Реферальная ссылка</b> чтобы получить ссылку для приглашения друзей\n"
        "• В разделе <b>Мои рефералы</b> вы увидите список приглашённых вами пользователей\n\n"
        
        "<b>Система рефералов:</b>\n"
        "• Приглашайте друзей по вашей реферальной ссылке\n"
        "• Отслеживайте количество приглашённых пользователей\n\n"
        
        "Если у вас остались вопросы, свяжитесь с администратором."
    )
    
    await message.answer(help_text, parse_mode="HTML")

def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(help_command, commands=["help"])  # Add help command
    dp.register_message_handler(profile_command, commands=["profile"])  # Add profile command
    dp.register_message_handler(referral_command, commands=["referral", "ref"])
    dp.register_message_handler(my_referrals_command, commands=["myreferrals", "myref"])
    dp.register_message_handler(check_subscription_command, commands=["check_subscription"])
    dp.register_message_handler(text_handler, content_types=types.ContentTypes.TEXT)
    
    # Callback handlers
    dp.register_callback_query_handler(
        copy_ref_link_callback, 
        lambda c: c.data and c.data.startswith("copy_ref_")
    )
    dp.register_callback_query_handler(
        get_ref_link_callback,
        lambda c: c.data == "get_ref_link"
    )
    
    # Subscription check handler
    dp.register_callback_query_handler(
        check_subscription_callback,
        lambda c: c.data == "check_subscription"
    )

async def show_subscription_message(message_or_callback, not_subscribed_channels):
    """Show subscription requirement message with channel buttons"""
    # Create message text
    text = (
        "🔄 <b>Для продолжения работы с ботом, пожалуйста, подпишитесь на следующие каналы:</b>\n\n"
    )
    
    # Create keyboard with channel buttons
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    for i, channel in enumerate(not_subscribed_channels, 1):
        channel_name = channel['name']
        channel_link = channel['link']
        
        text += f"{i}. {channel_name}\n"
        
        if channel_link:
            keyboard.add(types.InlineKeyboardButton(f"Подписаться на {channel_name}", url=channel_link))
    
    # Add check button
    keyboard.add(types.InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_subscription"))
    
    # Send message based on the type of the incoming object
    if isinstance(message_or_callback, types.CallbackQuery):
        # It's a callback - edit the message if possible or send new one
        try:
            await message_or_callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await message_or_callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    else:
        # It's likely a message
        await message_or_callback.answer(text, parse_mode="HTML", reply_markup=keyboard)

async def check_subscription_callback(callback: types.CallbackQuery):
    """Handle the Check Subscription button"""
    try:
        await callback.answer("Проверяю статус...")
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    user_id = callback.from_user.id
    
    # Check if user is an exception first
    session = get_database_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user and hasattr(user, 'is_exception') and user.is_exception:
            # User is an exception, show special message
            await callback.message.delete()  # Delete the subscription check message
            
            # Send special message for exception users
            keyboard = user_kb  # Use regular user keyboard (or admin_user_kb if they're admin)
            if is_admin(user_id):
                keyboard = admin_reply_kb
                
            await callback.message.answer(
                "✨ <b>Вы являетесь исключительным пользователем!</b>\n\n"
                "Вам не требуется подписка на каналы для использования бота.",
                parse_mode="HTML",
                reply_markup=keyboard
            )
            return
    finally:
        session.close()
    
    # Regular subscription check for non-exception users
    is_subscribed, not_subscribed_channels = await check_user_subscriptions(user_id)
    
    if not is_subscribed:
        # User is still not subscribed to all channels
        await show_subscription_message(callback, not_subscribed_channels)
        return
    
    # User is subscribed to all channels, show welcome message
    await callback.message.edit_text(
        "✅ Спасибо за подписку! Теперь вы можете пользоваться ботом.",
        reply_markup=None
    )
    
    # Send main menu message with appropriate keyboard
    keyboard = admin_reply_kb if is_admin(user_id) else user_kb
    await callback.message.answer("Добро пожаловать в бота!", reply_markup=keyboard)