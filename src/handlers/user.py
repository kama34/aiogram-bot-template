from aiogram import types
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from services.database import get_database_session, User, Referral
from services.user_service import UserService
from keyboards.admin_kb import admin_inlin_kb
from keyboards.user_kb import user_kb
from keyboards.admin_kb import admin_reply_kb
from utils.admin_utils import is_admin
from config import ADMIN_IDS, BOT_TOKEN
from utils.subscription_utils import check_user_subscriptions
from utils.logger import setup_logger
from utils.message_utils import show_subscription_message

import re

# Setup logger for this module
logger = setup_logger('handlers.user')

# Get bot username for referral links
async def get_bot_username():
    """Get bot username for referral links with improved error handling"""
    try:
        from bot import bot
        bot_info = await bot.get_me()
        logger.info(f"Successfully retrieved bot username: {bot_info.username}")
        return bot_info.username
    except ImportError as e:
        logger.critical(f"Failed to import bot module: {e}", exc_info=True)
        return "botusername"  # Fallback name
    except Exception as e:
        logger.error(f"Failed to get bot username: {e}", exc_info=True)
        return "botusername"  # Fallback name

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
            logger.error(f"Error parsing referrer ID: {e}", exc_info=True)
            referrer_id = None
    
    try:
        with UserService() as user_service:
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
                    logger.info(f"New user registered: {user_id} ({username})")
                    
                    # Process referral for new users
                    if referrer_id and referrer_id != user_id:
                        await process_referral(user_service, user_id, referrer_id, full_name, username)
                except Exception as e:
                    logger.error(f"Error registering user: {e}", exc_info=True)
                    user_service.session.rollback()
            else:
                # Process referral even for existing users who haven't been referred before
                if referrer_id and referrer_id != user_id:
                    # Check if this user already has a referrer
                    existing_referral = user_service.get_referral_by_user_id(user_id)
                    if not existing_referral:
                        await process_referral(user_service, user_id, referrer_id, full_name, username)
            
            # Show normal welcome message with appropriate keyboard based on user type
            welcome_message = "Добро пожаловать в бота!" if not is_new_user else "Добро пожаловать! Вы успешно зарегистрированы."
            
            # Choose the appropriate keyboard based on whether the user is an admin
            keyboard = admin_reply_kb if is_admin(user_id) else user_kb
            
            await message.answer(welcome_message, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error in start_command: {e}", exc_info=True)
        await message.answer("Произошла ошибка при обработке команды. Попробуйте позже.")

async def process_referral(user_service, user_id, referrer_id, full_name, username):
    """Process a referral and send notifications"""
    try:
        referrer = user_service.get_user_by_id(referrer_id)
        if not referrer:
            logger.warning(f"Referrer {referrer_id} not found when processing referral for user {user_id}")
            return
            
        # Create referral record with explicit commit
        try:
            new_referral = Referral(
                user_id=user_id,
                referred_by=referrer_id
            )
            user_service.session.add(new_referral)
            user_service.session.commit()
            logger.info(f"Referral created: user {user_id} referred by {referrer_id}")
            
            # Get bot instance for messaging
            from bot import bot
            
            # Send notification to the new user (invitee)
            try:
                await bot.send_message(
                    chat_id=user_id,
                    text=f"Вы были приглашены пользователем {referrer.full_name}!"
                )
            except Exception as e:
                logger.error(f"Failed to send notification to invitee {user_id}: {e}", exc_info=True)
            
            # Send notification to the referrer
            try:
                await bot.send_message(
                    chat_id=referrer_id, 
                    text=f"По вашей реферальной ссылке пришёл пользователь: {full_name} (@{username})"
                )
            except Exception as e:
                logger.error(f"Failed to send notification to referrer {referrer_id}: {e}", exc_info=True)
            
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
                    logger.error(f"Failed to notify admin {admin_id}: {e}", exc_info=True)
                    
        except Exception as e:
            logger.error(f"Error creating referral record: {e}", exc_info=True)
            user_service.session.rollback()
    except Exception as e:
        logger.error(f"Error processing referral: {e}", exc_info=True)
        
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

# Add handler for the get_ref_link callback
async def get_ref_link_callback(callback: types.CallbackQuery):
    """Handle the get referral link button"""
    try:
        await callback.answer()
    except Exception as e:
        logger.error(f"Error answering callback: {e}", exc_info=True)
    
    # Just call the existing referral command
    await referral_command(callback.message)

async def check_subscription_command(message: types.Message):
    with UserService() as user_service:
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
    with get_database_session() as session:
        user = session.query(User).filter(User.id == message.from_user.id).first()
        if user and hasattr(user, 'is_blocked') and user.is_blocked:
            await message.answer("Ваш аккаунт заблокирован. Используйте кнопку 'ℹ️ Помощь' для поддержки.")
            return
    
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
    """Handle the copy referral link button with improved error handling"""
    user_id = None
    
    try:
        # Ответ на callback должен быть как можно раньше, чтобы предотвратить ожидание у пользователя
        await callback.answer("Ссылка скопирована в сообщение ниже")
    except Exception as e:
        logger.error(f"Error answering callback: {e}", exc_info=True)
    
    try:
        # Extract user ID from callback data with validation
        user_id_str = callback.data.replace("copy_ref_", "")
        
        # Строгая валидация input данных
        if not user_id_str or not user_id_str.isdigit():
            logger.warning(f"Invalid user ID format in callback data: {callback.data}")
            await callback.message.answer(
                "Ошибка: неверный формат ID пользователя. Пожалуйста, попробуйте получить ссылку заново.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔄 Получить новую ссылку", callback_data="get_ref_link")
                )
            )
            return
            
        user_id = int(user_id_str)  # Убедимся, что это число
        
        # Generate link
        bot_username = await get_bot_username()
        if not bot_username or bot_username == "botusername":
            logger.warning(f"Using fallback bot username for user {user_id}")
            
        referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
        logger.info(f"Generated referral link for user {user_id}: {referral_link}")
        
        # Send as a separate message for easy copying
        await callback.message.answer(
            f"<code>{referral_link}</code>\n\nСкопируйте эту ссылку и отправьте друзьям",
            parse_mode="HTML"
        )
    except ValueError as e:
        # Специфическая обработка ошибки преобразования типов
        logger.error(f"Value error in copy_ref_link_callback: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при создании ссылки. Некорректный формат данных."
        )
    except Exception as e:
        # Контекстная информация для логирования
        context = {
            "user_id": user_id,
            "callback_data": callback.data,
            "from_user": callback.from_user.id
        }
        logger.error(f"Error in copy_ref_link_callback: {e}. Context: {context}", exc_info=True)
        
        # Информативное сообщение для пользователя с возможностью повторить
        await callback.message.answer(
            "Произошла ошибка при создании реферальной ссылки. Пожалуйста, попробуйте позже.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="get_ref_link")
            )
        )

async def profile_command(message: types.Message):
    """Show user profile information with improved error handling"""
    user_id = message.from_user.id
    
    try:
        with UserService() as user_service:
            # Get user data from database
            user = user_service.get_user_by_id(user_id)
            
            if not user:
                logger.warning(f"User profile not found for ID: {user_id}")
                await message.answer("Ошибка: Ваш профиль не найден! Пожалуйста, перезапустите бота с помощью команды /start")
                return
            
            # Get referral counts
            try:
                referral_count = user_service.count_user_referrals(user_id)
            except Exception as e:
                logger.error(f"Error getting referral count for user {user_id}: {e}", exc_info=True)
                referral_count = 0
            
            # Get referrer info if available
            referrer = None
            try:
                referral_info = user_service.get_referral_by_user_id(user_id)
                if referral_info and referral_info.referred_by:
                    referrer = user_service.get_user_by_id(referral_info.referred_by)
            except Exception as e:
                logger.error(f"Error getting referrer for user {user_id}: {e}", exc_info=True)
            
            # Format registration date safely
            try:
                registered_date = user.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(user, "created_at") and user.created_at else "неизвестно"
            except (AttributeError, ValueError) as e:
                logger.warning(f"Error formatting date for user {user_id}: {e}")
                registered_date = "неизвестно"
            
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
            
            logger.info(f"Successfully generated profile for user {user_id}")
            await message.answer(profile_text, parse_mode="HTML", reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Unexpected error in profile_command for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "Произошла ошибка при загрузке профиля. Пожалуйста, попробуйте позже или свяжитесь с администратором.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("ℹ️ Помощь", callback_data="help")
            )
        )

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

async def check_subscription_callback(callback: types.CallbackQuery):
    """Handle the Check Subscription button with improved error handling"""
    user_id = callback.from_user.id
    
    logger.info(f"User {user_id} initiated subscription check")
    
    # Сначала отвечаем на callback, чтобы убрать "часики" у пользователя
    try:
        await callback.answer("Проверяю статус...")
    except Exception as e:
        logger.error(f"Error answering callback for user {user_id}: {e}", exc_info=True)
    
    # Check if user is an exception first
    try:
        with get_database_session() as session:
            user = session.query(User).filter(User.id == user_id).first()
            
            if user and hasattr(user, 'is_exception') and user.is_exception:
                logger.info(f"User {user_id} is marked as exception, bypassing subscription checks")
                
                try:
                    # User is an exception, show special message
                    await callback.message.delete()  # Delete the subscription check message
                    
                    # Send special message for exception users
                    keyboard = user_kb
                    if is_admin(user_id):
                        keyboard = admin_reply_kb
                        
                    await callback.message.answer(
                        "✨ <b>Вы являетесь исключительным пользователем!</b>\n\n"
                        "Вам не требуется подписка на каналы для использования бота.",
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
                    return
                except Exception as e:
                    logger.error(f"Error handling exception user display for {user_id}: {e}", exc_info=True)
                    # Продолжаем выполнение, чтобы попробовать обычную проверку подписок
    except Exception as e:
        logger.error(f"Error checking if user {user_id} is an exception: {e}", exc_info=True)
    
    # Regular subscription check with improved error handling
    try:
        # Import bot inside the function for better dependency management
        try:
            from bot import bot
        except ImportError as e:
            logger.critical(f"Failed to import bot module: {e}", exc_info=True)
            await callback.message.answer("Критическая ошибка системы. Пожалуйста, сообщите администратору.")
            return
            
        try:
            is_subscribed, not_subscribed_channels = await check_user_subscriptions(bot, user_id)
        except Exception as e:
            logger.error(f"Error checking subscription status for user {user_id}: {e}", exc_info=True)
            await callback.message.answer(
                "Не удалось проверить статус подписки на каналы. Пожалуйста, попробуйте позже.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="check_subscription")
                )
            )
            return
        
        if not is_subscribed:
            # User is still not subscribed to all channels
            logger.info(f"User {user_id} is not subscribed to all required channels: {len(not_subscribed_channels)} channels remaining")
            await show_subscription_message(callback, not_subscribed_channels)
            return
        
        # User is subscribed to all channels, show welcome message
        logger.info(f"User {user_id} has subscribed to all required channels")
        
        try:
            # Пробуем отредактировать сообщение
            await callback.message.edit_text(
                "✅ Спасибо за подписку! Теперь вы можете пользоваться ботом.",
                reply_markup=None
            )
        except Exception as e:
            # Если не получилось отредактировать, отправляем новое
            logger.warning(f"Could not edit message for user {user_id}: {e}")
            await callback.message.answer(
                "✅ Спасибо за подписку! Теперь вы можете пользоваться ботом."
            )
        
        # Send main menu message with appropriate keyboard
        keyboard = admin_reply_kb if is_admin(user_id) else user_kb
        await callback.message.answer("Добро пожаловать в бота!", reply_markup=keyboard)
        
    except Exception as e:
        error_context = {
            "user_id": user_id,
            "callback_data": callback.data,
            "chat_id": callback.message.chat.id if callback.message else None
        }
        logger.error(f"Unexpected error in check_subscription_callback: {e}. Context: {error_context}", exc_info=True)
        
        try:
            # Информативное сообщение с возможностью повторить
            await callback.message.answer(
                "Произошла ошибка при проверке подписки. Пожалуйста, попробуйте позже.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🔄 Попробовать снова", callback_data="check_subscription")
                )
            )
        except Exception as inner_e:
            logger.error(f"Error sending error message to user {user_id}: {inner_e}", exc_info=True)