from aiogram import types
from utils.admin_utils import is_admin
from services.channel_service import ChannelService
from .listing import list_channels

async def toggle_channel(callback: types.CallbackQuery):
    """Переключение статуса канала (включен/выключен)"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    channel_db_id = int(callback.data.replace("toggle_channel_", ""))
    
    channel_service = ChannelService()
    channel = channel_service.get_channel_by_id_db(channel_db_id)
    
    if not channel:
        await callback.message.answer("Канал не найден.")
        channel_service.close_session()
        return
    
    # Toggle channel status
    try:
        channel = channel_service.toggle_channel_by_id(channel_db_id)
        status = "включен ✅" if channel.is_enabled else "отключен ⭕"
        
        await callback.answer(f"Канал {status}", show_alert=True)
        
        # Return to list view with updated data
        await list_channels(callback)
    except Exception as e:
        await callback.message.answer(f"Ошибка при изменении статуса канала: {str(e)}")
    
    channel_service.close_session()

async def delete_channel_confirm(callback: types.CallbackQuery):
    """Запрос подтверждения перед удалением канала"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    channel_db_id = callback.data.replace("delete_channel_", "")
    
    # Get channel info for confirmation
    channel_service = ChannelService()
    channel = channel_service.get_channel_by_id_db(int(channel_db_id))
    
    if not channel:
        await callback.message.answer("Канал не найден.")
        channel_service.close_session()
        return
    
    # Create confirmation keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("❌ Да, удалить", callback_data=f"confirm_delete_channel_{channel_db_id}"),
        types.InlineKeyboardButton("✅ Нет, отмена", callback_data="list_channels")
    )
    
    await callback.message.edit_text(
        f"⚠️ <b>Подтверждение удаления</b>\n\n"
        f"Вы уверены, что хотите удалить канал <b>{channel.channel_name}</b>?",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    channel_service.close_session()

async def delete_channel_process(callback: types.CallbackQuery):
    """Обработка удаления канала после подтверждения"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    channel_db_id = int(callback.data.replace("confirm_delete_channel_", ""))
    
    channel_service = ChannelService()
    
    try:
        channel = channel_service.get_channel_by_id_db(channel_db_id)
        if not channel:
            await callback.message.answer("Канал не найден.")
            channel_service.close_session()
            return
        
        channel_name = channel.channel_name
        success = channel_service.delete_channel_by_id(channel_db_id)
        
        if success:
            await callback.answer(f"Канал {channel_name} удален.", show_alert=True)
        else:
            await callback.answer("Не удалось удалить канал.", show_alert=True)
        
        # Return to the updated channel list
        await list_channels(callback)
    except Exception as e:
        await callback.message.answer(f"Ошибка при удалении канала: {str(e)}")
    finally:
        channel_service.close_session()