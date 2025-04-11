from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from config import BOT_TOKEN
from handlers import admin, user
from handlers.admin import register_admin_handlers
from utils.admin_utils import AdminFilter, AdminAccessFilter
from middlewares.user_registration import UserRegistrationMiddleware, UserMiddleware
from middlewares.subscription import SubscriptionMiddleware

bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.filters_factory.bind(AdminFilter)
dp.filters_factory.bind(AdminAccessFilter)

dp.middleware.setup(UserRegistrationMiddleware())  # This registers new users
dp.middleware.setup(UserMiddleware())  # This checks if users are blocked
dp.middleware.setup(SubscriptionMiddleware())  # This checks subscription status

async def on_startup(dp):
    print("Bot is online!")

def register_handlers():
    admin.register_admin_handlers(dp)
    user.register_user_handlers(dp)
    register_admin_handlers(dp)

if __name__ == '__main__':
    register_handlers()
    executor.start_polling(dp, on_startup=on_startup)