from aiogram import types
from services.channel_service import ChannelService
from utils.admin_utils import is_admin

async def list_channels(callback: types.CallbackQuery):
    """Показывает список всех каналов с кнопками управления"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await callback.message.delete()
    
    channel_service = ChannelService()
    channels = channel_service.get_all_channels()
    
    if not channels:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("➕ Добавить канал", callback_data="add_channel"),
            types.InlineKeyboardButton("◀️ Назад", callback_data="manage_channels")
        )
        await callback.message.answer("📂 Список каналов пуст.", reply_markup=keyboard)
        channel_service.close_session()
        return
    
    # Format channel list message
    text = "📋 <b>Список каналов:</b>\n\n"
    
    for i, channel in enumerate(channels, 1):
        status = "✅ Включен" if channel.is_enabled else "⭕ Отключен"
        text += f"{i}. <b>{channel.channel_name}</b> (<code>{channel.channel_id}</code>)\n   Статус: {status}\n\n"
    
    # Add controls for each channel
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    for channel in channels:
        # Add channel name as a label
        keyboard.add(types.InlineKeyboardButton(
            f"{channel.channel_name}",
            callback_data=f"channel_info_{channel.id}"
        ))
    
    # Add navigation buttons
    keyboard.add(
        types.InlineKeyboardButton("➕ Добавить канал", callback_data="add_channel"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="manage_channels")
    )
    
    await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
    channel_service.close_session()

async def channel_info(callback: types.CallbackQuery):
    """Показывает подробную информацию о канале"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    channel_id = int(callback.data.replace("channel_info_", ""))
    
    channel_service = ChannelService()
    channel = channel_service.get_channel_by_id_db(channel_id)
    
    if not channel:
        await callback.message.answer("Канал не найден.")
        channel_service.close_session()
        return
    
    # Format channel info
    status = "✅ Включен" if channel.is_enabled else "⭕ Отключен"
    added_date = channel.added_at.strftime("%d.%m.%Y %H:%M") if hasattr(channel, "added_at") else "Неизвестно"
    
    text = (
        f"📌 <b>Информация о канале:</b>\n\n"
        f"Название: <b>{channel.channel_name}</b>\n"
        f"ID: <code>{channel.channel_id}</code>\n"
        f"Статус: {status}\n"
        f"Добавлен: {added_date}\n"
    )
    
    # Create keyboard with actions
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    
    toggle_text = "Отключить ❌" if channel.is_enabled else "Включить ✅"
    keyboard.add(
        types.InlineKeyboardButton(toggle_text, callback_data=f"toggle_channel_{channel.id}"),
        types.InlineKeyboardButton("Удалить канал", callback_data=f"delete_channel_{channel.id}"),
        types.InlineKeyboardButton("◀️ Назад к списку", callback_data="list_channels")
    )
    
    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    channel_service.close_session()