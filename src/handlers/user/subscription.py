from aiogram import types
from services.database import get_database_session, User
from utils.logger import setup_logger
from utils.admin_utils import is_admin
from keyboards.user_kb import user_kb
from keyboards.admin_kb import admin_reply_kb
from utils.subscription_utils import check_user_subscriptions
from utils.message_utils import show_subscription_message

# Setup logger for this module
logger = setup_logger('handlers.subscription')

async def check_subscription_command(message: types.Message):
    """Check if a user is subscribed"""
    from services.user_service import UserService
    
    with UserService() as user_service:
        user = user_service.get_user_by_id(message.from_user.id)
        if user:
            await message.answer("You are subscribed!")
        else:
            await message.answer("You are not subscribed. Please subscribe to continue.")

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

def register_subscription_handlers(dp):
    """Регистрация обработчиков для системы подписок"""
    # Регистрация команды проверки подписки
    dp.register_message_handler(check_subscription_command, commands=["subscription", "check_subscription"])
    
    # Регистрация обработчика callback-запросов для проверки подписки
    dp.register_callback_query_handler(check_subscription_callback, lambda c: c.data == "check_subscription")