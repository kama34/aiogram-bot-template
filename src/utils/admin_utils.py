from aiogram import types
from aiogram.dispatcher.filters import BoundFilter
from config import ADMIN_IDS

class AdminFilter(BoundFilter):
    key = 'is_admin'
    
    def __init__(self, is_admin=True):
        self.is_admin = is_admin
        
    async def check(self, obj):
        if isinstance(obj, types.Message):
            user_id = obj.from_user.id
        elif isinstance(obj, types.CallbackQuery):
            user_id = obj.from_user.id
        else:
            return False
        
        return is_admin(user_id) == self.is_admin

class AdminAccessFilter(BoundFilter):
    """Filter that allows admins to bypass block checks"""
    key = 'admin_access'
    
    def __init__(self, admin_access=True):
        self.admin_access = admin_access
        
    async def check(self, obj):
        if isinstance(obj, types.Message):
            user_id = obj.from_user.id
        elif isinstance(obj, types.CallbackQuery):
            user_id = obj.from_user.id
        else:
            return False
        
        # Admin IDs always pass through this filter
        return is_admin(user_id) == self.admin_access

def is_admin(user_id: int) -> bool:
    """Check if user is an admin by user_id"""
    admin_ids = ADMIN_IDS  # Add your Telegram user ID here
    return user_id in admin_ids