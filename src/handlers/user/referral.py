from aiogram import types
from services.database import Referral
from utils.logger import setup_logger
from utils.admin_utils import is_admin
from config import ADMIN_IDS

# Setup logger for this module
logger = setup_logger('handlers.referral')

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
    from services.user_service import UserService
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
    
    from services.user_service import UserService
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

async def get_ref_link_callback(callback: types.CallbackQuery):
    """Handle the get referral link button"""
    try:
        await callback.answer()
    except Exception as e:
        logger.error(f"Error answering callback: {e}", exc_info=True)
    
    # Just call the existing referral command
    await referral_command(callback.message)

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

def register_referral_handlers(dp):
    """Регистрация обработчиков для реферальной системы"""
    # Регистрация обработчиков команд
    dp.register_message_handler(referral_command, commands=["referral"])
    dp.register_message_handler(my_referrals_command, commands=["myreferrals"])
    
    # Регистрация обработчиков callback-запросов
    dp.register_callback_query_handler(get_ref_link_callback, lambda c: c.data == "get_ref_link")
    dp.register_callback_query_handler(copy_ref_link_callback, lambda c: c.data and c.data.startswith("copy_ref_"))