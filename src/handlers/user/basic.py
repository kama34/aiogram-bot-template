from aiogram import types
from services.database import get_database_session, User
from keyboards.user_kb import user_kb
from keyboards.admin_kb import admin_reply_kb
from utils.admin_utils import is_admin
from utils.logger import setup_logger

# Setup logger for this module
logger = setup_logger('handlers.basic')

async def start_command(message: types.Message):
    """Handler for /start command"""
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
        from services.user_service import UserService
        from handlers.user.referral import process_referral
        
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

async def profile_command(message: types.Message):
    """Show user profile information with improved error handling"""
    user_id = message.from_user.id
    
    try:
        from services.user_service import UserService
        
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
        from handlers.user.referral import referral_command
        await referral_command(message)
    elif text == "👥 Мои рефералы":
        from handlers.user.referral import my_referrals_command
        await my_referrals_command(message)
    elif text == "🛒 Меню":
        from handlers.user.shop import menu_command
        await menu_command(message)
    elif text == "🧺 Корзина":
        from handlers.user.cart import cart_command
        await cart_command(message)
    elif text == "🔧 Панель администратора" and is_admin(message.from_user.id):
        from handlers.admin.core import admin_panel
        await admin_panel(message)

def register_basic_handlers(dp):
    """Регистрация основных обработчиков команд пользователя"""
    from aiogram import Dispatcher
    
    # Регистрация обработчиков команд
    dp.register_message_handler(start_command, commands=["start"])
    dp.register_message_handler(help_command, commands=["help"])
    dp.register_message_handler(profile_command, commands=["profile"])
    
    # Регистрация обработчика текстовых сообщений
    dp.register_message_handler(text_handler, 
                              lambda message: message.text in [
                                  "ℹ️ Помощь", 
                                  "🔍 Профиль", 
                                  "🔗 Реферальная ссылка", 
                                  "👥 Мои рефералы",
                                  "🛒 Магазин",
                                  "🧺 Корзина",
                                  "🔧 Панель администратора"
                              ])