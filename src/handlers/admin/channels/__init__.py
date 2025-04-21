from aiogram import Dispatcher
from .menu import manage_channels_menu
from .listing import list_channels, channel_info
from .add import add_channel_start, add_channel_process, cancel_channel_add
from .management import toggle_channel, delete_channel_confirm, delete_channel_process
from .navigation import manage_channels_callback, return_to_channels_menu_handler

def register_channel_handlers(dp: Dispatcher):
    """Регистрирует обработчики для управления каналами"""
    from ..states import AdminStates
    
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

# Экспортируем основные функции и обработчики
__all__ = [
    'register_channel_handlers',
    'manage_channels_menu',
    'list_channels',
    'channel_info',
    'add_channel_start',
    'add_channel_process',
    'cancel_channel_add',
    'toggle_channel',
    'delete_channel_confirm',
    'delete_channel_process',
    'manage_channels_callback'
]