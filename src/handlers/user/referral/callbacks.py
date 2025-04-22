from aiogram import types
from utils.logger import setup_logger
from .commands import referral_command
from .utils import get_bot_username

# Setup logger for this module
logger = setup_logger('handlers.referral.callbacks')

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