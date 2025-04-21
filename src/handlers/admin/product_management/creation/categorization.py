from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from utils.message_utils import safe_delete_message
from .utils import process_stock_input

async def process_category_input(message: types.Message, state: FSMContext):
    """Запрашивает категорию товара"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("⏩ Пропустить", callback_data="skip_product_category"),
        types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state")
    )
    
    await message.answer(
        "📁 Введите категорию товара или нажмите 'Пропустить':", 
        reply_markup=keyboard
    )
    
    await AdminStates.waiting_for_product_category.set()

async def process_product_category(message: types.Message, state: FSMContext):
    """Обрабатывает ввод категории товара"""
    async with state.proxy() as data:
        data['product_category'] = message.text
    
    await process_stock_input(message, state)

async def skip_product_category(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пропуска ввода категории"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await safe_delete_message(callback.message)
    
    async with state.proxy() as data:
        data['product_category'] = None
    
    await process_stock_input(callback.message, state)

def register_categorization_handlers(dp: Dispatcher):
    """Регистрирует обработчики для работы с категориями товара"""
    dp.register_message_handler(
        process_product_category, 
        state=AdminStates.waiting_for_product_category
    )
    
    dp.register_callback_query_handler(
        skip_product_category, 
        lambda c: c.data == "skip_product_category", 
        state=AdminStates.waiting_for_product_category
    )