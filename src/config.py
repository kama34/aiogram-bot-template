from dotenv import load_dotenv
import os

load_dotenv()

# BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_TOKEN = "5000608497:AAHvnLodDAZKMxz4ED9K6DZDp54Nk-ZCPZ0"
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")  # Default to SQLite if not set
# ADMIN_IDS = list(map(int, filter(None, os.getenv("ADMIN_IDS", "").split(","))))  # Comma-separated list of admin IDs as integers
ADMIN_IDS = [5000601280, 7808908162]

# Настройки платежной системы
PAYMENT_PROVIDER_TOKEN = ""  
PAYMENT_CURRENCY = "XTR"  # Валюта платежей - звезды Telegram
STAR_TO_RUB_RATE = 9  # Примерный курс: 1 звезда = 9 рублей (или укажите актуальный)