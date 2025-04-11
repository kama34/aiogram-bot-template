from dotenv import load_dotenv
import os

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")  # Default to SQLite if not set
ADMIN_IDS = list(map(int, filter(None, os.getenv("ADMIN_IDS", "").split(","))))  # Comma-separated list of admin IDs as integers
# Example: ADMIN_IDS=123456789,987654321
# Additional configuration settings can be added here as needed.