from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utils.admin_utils import is_admin
from services.channel_service import ChannelService
from .core import AdminStates
from .helpers import create_error_message, return_to_channels_menu_handler

async def manage_channels_menu(message: types.Message):
    """Главное меню управления каналами"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📋 Список каналов", callback_data="list_channels"),
        types.InlineKeyboardButton("➕ Добавить канал", callback_data="add_channel"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
    )
    await message.answer("🔧 Управление каналами:", reply_markup=keyboard)

async def list_channels(callback: types.CallbackQuery):
    """Показывает список всех каналов с кнопками управления"""
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

async def add_channel_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса добавления нового канала"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await callback.message.delete()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_channel_add"))
    
    await callback.message.answer(
        "➕ <b>Добавление нового канала</b>\n\n"
        "Пожалуйста, введите ID канала (например: -1001234567890) или имя канала с @ (например: @channel_name).\n\n"
        "<i>❗ Бот должен быть администратором канала.</i>",
        parse_mode="HTML", 
        reply_markup=keyboard
    )
    
    await AdminStates.waiting_for_channel_input.set()

async def add_channel_process(message: types.Message, state: FSMContext):
    """Обработка добавления канала после получения ввода"""
    channel_input = message.text.strip()
    
    # Проверяем валидность ввода
    if not channel_input:
        await create_error_message(
            message,
            "Пожалуйста, введите корректный ID канала или @username.",
            state
        )
        return
    
    # Extract channel ID or username
    channel_id = None
    channel_username = None
    
    if channel_input.startswith('@'):
        channel_username = channel_input
        # Will resolve to ID later
    elif channel_input.startswith('-100'):
        # Likely a channel ID
        try:
            channel_id = int(channel_input)
        except ValueError:
            await create_error_message(
                message,
                "Некорректный формат ID канала.",
                state
            )
            return
    else:
        # Try to interpret as ID or use as username
        try:
            channel_id = int(channel_input)
        except ValueError:
            # Not a numeric ID, assume it's a username without @
            channel_username = f"@{channel_input}" if not channel_input.startswith('@') else channel_input
    
    # Get bot instance
    from bot import bot
    
    try:
        # Try to get channel info and check if bot is admin
        if channel_username:
            try:
                chat = await bot.get_chat(channel_username)
                channel_id = chat.id
                channel_name = chat.title or channel_username
            except Exception as e:
                await create_error_message(
                    message,
                    f"Не удалось найти канал {channel_username}.\nОшибка: {str(e)}",
                    state
                )
                return
        else:
            try:
                chat = await bot.get_chat(channel_id)
                channel_name = chat.title or str(channel_id)
            except Exception as e:
                await create_error_message(
                    message,
                    f"Не удалось найти канал с ID {channel_id}.\nОшибка: {str(e)}",
                    state
                )
                return
        
        # Check if bot is admin in the channel
        try:
            # Get bot's ID
            bot_info = await bot.get_me()
            bot_id = bot_info.id
            
            # Check if the bot is an admin
            bot_member = await bot.get_chat_member(chat.id, bot_id)
            is_admin = bot_member.status in ['administrator', 'creator']
            
            if not is_admin:
                await create_error_message(
                    message,
                    f"Бот не является администратором канала {channel_name}.\n" +
                    "Пожалуйста, добавьте бота в администраторы канала и попробуйте снова.",
                    state
                )
                return
        except Exception as e:
            await create_error_message(
                message,
                f"Не удалось проверить права бота в канале.\nОшибка: {str(e)}",
                state
            )
            return
        
        # Bot is admin, proceed to add the channel
        channel_service = ChannelService()
        
        # Check if channel already exists
        existing_channel = channel_service.get_channel_by_id(str(channel_id))
        if existing_channel:
            await create_error_message(
                message,
                f"Канал '{channel_name}' уже добавлен в список.",
                state
            )
            channel_service.close_session()
            return
        
        # Add channel to database
        try:
            new_channel = channel_service.add_channel(channel_name, str(channel_id))
            
            # Создаем новую клавиатуру с правильным callback_data после успешного добавления
            success_keyboard = types.InlineKeyboardMarkup()
            success_keyboard.add(types.InlineKeyboardButton("📋 Список каналов", callback_data="list_channels"))
            success_keyboard.add(types.InlineKeyboardButton("◀️ Назад в меню", callback_data="return_to_channels_menu"))
            
            await message.answer(
                f"✅ Канал <b>{channel_name}</b> успешно добавлен и включен!\n\n" +
                f"Теперь пользователям потребуется подписка на этот канал для использования бота.",
                parse_mode="HTML",
                reply_markup=success_keyboard
            )
            
            # Завершаем состояние только после успешного добавления
            await state.finish()
            
        except Exception as e:
            await create_error_message(
                message,
                f"Ошибка при добавлении канала в базу данных: {str(e)}",
                state
            )
            
        channel_service.close_session()
        
    except Exception as e:
        await create_error_message(
            message,
            f"Произошла ошибка: {str(e)}",
            state
        )

async def cancel_channel_add(callback: types.CallbackQuery, state: FSMContext):
    """Обработка кнопки отмены во время добавления канала"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Clear any active state
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    try:
        # Delete the current message 
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Show channel management menu
    await manage_channels_menu(callback.message)

async def toggle_channel(callback: types.CallbackQuery):
    """Переключение статуса канала (включен/выключен)"""
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

async def manage_channels_callback(callback: types.CallbackQuery):
    """Обработчик для возврата в меню управления каналами"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    try:
        # Удаляем текущее сообщение
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Показываем меню управления каналами
    await manage_channels_menu(callback.message)

def register_channel_handlers(dp: Dispatcher):
    """Регистрирует обработчики для управления каналами"""
    dp.register_callback_query_handler(list_channels, lambda c: c.data == "list_channels")
    dp.register_callback_query_handler(channel_info, lambda c: c.data and c.data.startswith("channel_info_"))
    dp.register_callback_query_handler(add_channel_start, lambda c: c.data == "add_channel")
    dp.register_callback_query_handler(manage_channels_callback, lambda c: c.data == "manage_channels")
    dp.register_message_handler(add_channel_process, state=AdminStates.waiting_for_channel_input)
    dp.register_callback_query_handler(toggle_channel, lambda c: c.data and c.data.startswith("toggle_channel_"))
    dp.register_callback_query_handler(delete_channel_confirm, lambda c: c.data and c.data.startswith("delete_channel_"))
    dp.register_callback_query_handler(delete_channel_process, lambda c: c.data and c.data.startswith("confirm_delete_channel_"))
    dp.register_callback_query_handler(cancel_channel_add, lambda c: c.data == "cancel_channel_add", state="*")
    dp.register_callback_query_handler(return_to_channels_menu_handler, lambda c: c.data == "return_to_channels_menu")