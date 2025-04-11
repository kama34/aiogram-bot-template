from aiogram import types
from aiogram.dispatcher.middlewares import BaseMiddleware
from aiogram.dispatcher.handler import CancelHandler
from services.database import get_database_session, User
from utils.admin_utils import is_admin

class UserRegistrationMiddleware(BaseMiddleware):
    """Middleware to automatically register users on any interaction"""
    
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Register user if it's a new user
        await self._register_user(message.from_user)
    
    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        # Register user if it's a new user
        await self._register_user(callback_query.from_user)
    
    async def _register_user(self, user: types.User):
        session = get_database_session()
        try:
            existing_user = session.query(User).filter(User.id == user.id).first()
            
            if not existing_user:
                # Auto register new user
                new_user = User(
                    id=user.id,
                    username=user.username or "unknown",
                    full_name=user.full_name or "Unknown User"
                )
                session.add(new_user)
                session.commit()
                print(f"New user registered: {user.username or 'unknown'} ({user.id})")
        finally:
            session.close()

class UserMiddleware(BaseMiddleware):
    """Middleware to check if users are blocked before processing messages"""
    
    async def on_pre_process_message(self, message: types.Message, data: dict):
        # Always allow help command and help button to pass through
        if message.text == "ℹ️ Помощь" or message.text == "/help":
            return  # Skip ALL checks for help
            
        # Check if user is blocked
        await self._check_user_blocked(message.from_user, message)
    
    async def on_pre_process_callback_query(self, callback_query: types.CallbackQuery, data: dict):
        # Allow help-related callbacks to pass through
        if callback_query.data == "help":
            return
            
        # Check if user is blocked
        await self._check_user_blocked(callback_query.from_user, callback_query)
    
    async def _check_user_blocked(self, user: types.User, event_obj):
        # Skip check for admins
        if is_admin(user.id):
            return
            
        session = get_database_session()
        try:
            db_user = session.query(User).filter(User.id == user.id).first()
            
            # If user doesn't exist, they'll be registered by the registration middleware
            if db_user and hasattr(db_user, 'is_blocked') and db_user.is_blocked:
                # If it's a message that's not help-related
                if isinstance(event_obj, types.Message) and event_obj.text not in ["ℹ️ Помощь", "/help"]:
                    await event_obj.answer("⛔️ Ваш аккаунт заблокирован. Используйте кнопку 'ℹ️ Помощь' для поддержки.")
                    raise CancelHandler()
                # If it's a callback query that's not help-related
                elif isinstance(event_obj, types.CallbackQuery) and event_obj.data != "help":
                    await event_obj.answer("⛔️ Ваш аккаунт заблокирован. Используйте кнопку 'ℹ️ Помощь' для поддержки.", show_alert=True)
                    raise CancelHandler()
        finally:
            session.close()