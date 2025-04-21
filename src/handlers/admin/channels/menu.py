from aiogram import types

async def manage_channels_menu(message: types.Message):
    """Главное меню управления каналами"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📋 Список каналов", callback_data="list_channels"),
        types.InlineKeyboardButton("➕ Добавить канал", callback_data="add_channel"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
    )
    await message.answer("🔧 Управление каналами:", reply_markup=keyboard)