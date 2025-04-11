from aiogram import types
from aiogram.dispatcher import filters

class IsAdmin(filters.BaseFilter):
    async def __call__(self, message: types.Message):
        # Replace with your logic to check if the user is an admin
        return message.from_user.id in ["7808908162"]  # Example admin user ID

class IsUser(filters.BaseFilter):
    async def __call__(self, message: types.Message):
        # Replace with your logic to check if the user is a registered user
        return True  # Example logic, replace with actual user check

# Add more custom filters as needed for your bot's functionality