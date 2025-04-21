from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from utils.admin_utils import is_admin
from utils.message_utils import safe_delete_message

async def start_product_creation(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс создания товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Безопасное удаление сообщения
    await safe_delete_message(callback.message)
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state"))
    
    await callback.message.answer(
        "📝 <b>Создание нового товара</b>\n\n"
        "Введите название товара:", 
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await AdminStates.waiting_for_product_name.set()

def register_start_handlers(dp: Dispatcher):
    """Регистрирует обработчики для начала создания товаров"""
    dp.register_callback_query_handler(
        start_product_creation, 
        lambda c: c.data == "create_product", 
        state="*"
    )