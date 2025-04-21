from aiogram import types
from aiogram.dispatcher import FSMContext
from utils.admin_utils import is_admin
from services.channel_service import ChannelService
from ..states import AdminStates
from ..helpers import create_error_message
from .menu import manage_channels_menu

async def add_channel_start(callback: types.CallbackQuery, state: FSMContext):
    """Начало процесса добавления нового канала"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
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