"""
Вспомогательные функции для работы с редактированием товаров
"""

from aiogram import types
from aiogram.dispatcher import FSMContext

async def get_field_display_name(field: str) -> str:
    """Возвращает читаемое название поля для отображения пользователю"""
    field_names = {
        "name": "Название",
        "description": "Описание",
        "price": "Цена",
        "category": "Категория",
        "stock": "Количество на складе",
        "image": "Изображение"
    }
    return field_names.get(field, field.capitalize())

async def get_field_emoji(field: str) -> str:
    """Возвращает эмодзи для поля"""
    field_emojis = {
        "name": "📌",
        "description": "📝",
        "price": "💰",
        "category": "📁",
        "stock": "🔢",
        "image": "🖼"
    }
    return field_emojis.get(field, "📋")