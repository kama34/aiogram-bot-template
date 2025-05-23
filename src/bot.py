from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
from config import BOT_TOKEN
from utils.admin_utils import AdminFilter, AdminAccessFilter
from middlewares.user_registration import UserRegistrationMiddleware, UserMiddleware
from middlewares.subscription import SubscriptionMiddleware
import server

# Импортируем новый регистратор обработчиков
from handlers.handler_register import register_all_handlers

# В начале файла после других импортов:
from services.database_relations import setup_database_relationships
from services.database import create_tables
from services.check_database import check_database_structure, fix_inventory_table
from services.db_migrations import run_migrations

# Перед созданием диспетчера:
setup_database_relationships()
create_tables()
check_database_structure()
fix_inventory_table()
run_migrations()

bot = Bot(token=BOT_TOKEN, server=server.TELEGRAM_TEST)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.filters_factory.bind(AdminFilter)
dp.filters_factory.bind(AdminAccessFilter)

dp.middleware.setup(UserRegistrationMiddleware())  # This registers new users
dp.middleware.setup(UserMiddleware())  # This checks if users are blocked
dp.middleware.setup(SubscriptionMiddleware())  # This checks subscription status

async def on_startup(dp):
    print("Bot is online!")

if __name__ == '__main__':
    # Регистрируем все обработчики через новую систему
    register_all_handlers(dp)
    executor.start_polling(dp, on_startup=on_startup)