from aiogram import types
from aiogram.utils.exceptions import MessageToDeleteNotFound, MessageCantBeDeleted, BotBlocked
from utils.logger import setup_logger
import functools

# Setup logger for this module
logger = setup_logger('utils.message_utils')

def safe_telegram_operation(func):
    """
    Декоратор для безопасного выполнения операций с Telegram API
    Обрабатывает стандартные исключения и логирует их
    """
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except MessageToDeleteNotFound:
            print(f"Warning: Message to delete not found in {func.__name__}")
        except MessageCantBeDeleted:
            print(f"Warning: Message can't be deleted in {func.__name__}")
        except BotBlocked:
            print(f"Warning: Bot was blocked by user in {func.__name__}")
        except Exception as e:
            print(f"Error in {func.__name__}: {e}")
        return None
    
    return wrapper

async def show_subscription_message(message_or_callback, not_subscribed_channels):
    """Show subscription requirement message with channel buttons and error handling"""
    try:
        # Create message text
        text = (
            "🔄 <b>Для продолжения работы с ботом, пожалуйста, подпишитесь на следующие каналы:</b>\n\n"
        )
        
        # Create keyboard with channel buttons
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        # Безопасная проверка на корректность данных каналов
        if not isinstance(not_subscribed_channels, list):
            logger.error(f"Invalid channels data type: {type(not_subscribed_channels)}")
            not_subscribed_channels = []
            
        for i, channel in enumerate(not_subscribed_channels, 1):
            if not isinstance(channel, dict):
                logger.warning(f"Invalid channel data format at index {i-1}: {channel}")
                continue
                
            channel_name = channel.get('name', 'Неизвестный канал')
            channel_link = channel.get('link')
            
            text += f"{i}. {channel_name}\n"
            
            if channel_link:
                keyboard.add(types.InlineKeyboardButton(f"Подписаться на {channel_name}", url=channel_link))
            else:
                logger.warning(f"Missing link for channel {channel_name}")
        
        # Add check button
        keyboard.add(types.InlineKeyboardButton("🔄 Проверить подписку", callback_data="check_subscription"))
        
        # Get user_id for logging
        user_id = None
        if isinstance(message_or_callback, types.CallbackQuery):
            user_id = message_or_callback.from_user.id
        elif hasattr(message_or_callback, 'from_user'):
            user_id = message_or_callback.from_user.id
            
        # Send message based on the type of the incoming object
        try:
            if isinstance(message_or_callback, types.CallbackQuery):
                # It's a callback - edit the message if possible or send new one
                try:
                    await message_or_callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
                    logger.info(f"Successfully edited subscription message for user {user_id}")
                except Exception as edit_error:
                    logger.warning(f"Could not edit message, sending new one: {edit_error}")
                    await message_or_callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
            else:
                # It's likely a message
                await message_or_callback.answer(text, parse_mode="HTML", reply_markup=keyboard)
                logger.info(f"Sent new subscription message to user {user_id}")
        except Exception as send_error:
            logger.error(f"Failed to send subscription message to user {user_id}: {send_error}", exc_info=True)
            # Пытаемся отправить упрощенное сообщение с общей инструкцией
            if isinstance(message_or_callback, types.CallbackQuery):
                await message_or_callback.message.answer(
                    "Пожалуйста, подпишитесь на все необходимые каналы для использования бота."
                )
            else:
                await message_or_callback.answer(
                    "Пожалуйста, подпишитесь на все необходимые каналы для использования бота."
                )
    except Exception as e:
        # Общая обработка неожиданных ошибок
        logger.error(f"Unexpected error in show_subscription_message: {e}", exc_info=True)

@safe_telegram_operation
async def safe_delete_message(message):
    """
    Безопасно удаляет сообщение, обрабатывая возможные исключения
    
    Args:
        message (types.Message): Сообщение для удаления
    
    Returns:
        bool: True если удаление прошло успешно, False в случае ошибки
    """
    if not message:
        return False
        
    try:
        await message.delete()
        return True
    except MessageToDeleteNotFound:
        # Сообщение уже удалено или недоступно
        return False
    except MessageCantBeDeleted:
        # У бота нет прав на удаление сообщения
        return False
    except BotBlocked:
        # Пользователь заблокировал бота
        return False
    except Exception as e:
        # Другие ошибки
        print(f"Ошибка при удалении сообщения: {e}")
        return False