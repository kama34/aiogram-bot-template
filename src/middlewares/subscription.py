from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware
from utils.admin_utils import is_admin
from services.database import get_database_session, User
from utils.subscription_utils import check_user_subscriptions
from utils.message_utils import show_subscription_message

class SubscriptionMiddleware(BaseMiddleware):
    """Check if user is subscribed to required channels before processing any message"""
    
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Always allow help command and help button to pass through
        if message.text == "ℹ️ Помощь" or message.text == "/help":
            return  # Skip ALL checks for help
        
        from bot import bot
        await self._check_subscription(bot, message.from_user.id, message)
    
    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        # Allow subscription check and help-related callbacks to pass through
        if callback_query.data == "check_subscription" or callback_query.data == "help":
            return
        
        from bot import bot
        await self._check_subscription(bot, callback_query.from_user.id, callback_query.message, callback_query)
    
    async def _check_subscription(self, bot, user_id: int, message_obj, callback_query=None):
        # Skip check for admins
        if is_admin(user_id):
            return
        
        # Проверка на исключения и блокировки...
        session = get_database_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                # Skip check for exception users
                if hasattr(user, 'is_exception') and user.is_exception:
                    return
                
                # Check if user is blocked
                if hasattr(user, 'is_blocked') and user.is_blocked:
                    if callback_query:
                        await callback_query.answer("Ваш аккаунт заблокирован. Используйте кнопку 'ℹ️ Помощь' для поддержки.", show_alert=True)
                    else:
                        await message_obj.answer("Ваш аккаунт заблокирован. Используйте кнопку 'ℹ️ Помощь' для поддержки.")
                    raise CancelHandler()
        finally:
            session.close()
        
        # Check subscriptions
        is_subscribed, not_subscribed_channels = await check_user_subscriptions(bot, user_id)
        
        if not is_subscribed:
            # User needs to subscribe to channels
            if callback_query:
                # For callback queries, answer first to avoid timeout
                await callback_query.answer()
                
            # Show subscription message
            await show_subscription_message(message_obj, not_subscribed_channels)
            
            # Cancel further processing - don't run the actual handler
            raise CancelHandler()