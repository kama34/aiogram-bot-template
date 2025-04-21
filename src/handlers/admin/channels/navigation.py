from aiogram import types
from utils.admin_utils import is_admin
from .menu import manage_channels_menu

async def manage_channels_callback(callback: types.CallbackQuery):
    """Обработчик для возврата в меню управления каналами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
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

async def return_to_channels_menu_handler(callback: types.CallbackQuery):
    """Универсальный обработчик для возврата в меню управления каналами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
        
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")
    
    try:
        # Удаляем текущее сообщение
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Показываем меню управления каналами
    await manage_channels_menu(callback.message)