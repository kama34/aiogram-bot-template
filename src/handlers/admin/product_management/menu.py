from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils.admin_utils import is_admin

async def show_product_menu(callback: types.CallbackQuery):
    """Показывает меню управления товарами"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    try:
        await callback.message.delete()
    except Exception as e:
        print(f"Error deleting message: {e}")
    
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("➕ Создать товар", callback_data="create_product"),
        types.InlineKeyboardButton("📋 Список товаров", callback_data="list_products"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
    )
    
    await callback.message.answer(
        "🛒 <b>Управление товарами</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

def register_menu_handlers(dp: Dispatcher):
    """Регистрирует обработчики для меню управления товарами"""
    dp.register_callback_query_handler(
        show_product_menu, 
        lambda c: c.data == "manage_products", 
        state="*"
    )