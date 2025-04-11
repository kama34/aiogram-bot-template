from aiogram import types
import random
import string

def generate_referral_link(user_id: int) -> str:
    unique_code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    return f"https://t.me/your_bot?start={unique_code}_{user_id}"

def is_user_registered(user_id: int, registered_users: list) -> bool:
    return user_id in registered_users

def format_user_data(user_data: dict) -> str:
    return f"User ID: {user_data['id']}\nUsername: {user_data['username']}\nFull Name: {user_data['full_name']}"