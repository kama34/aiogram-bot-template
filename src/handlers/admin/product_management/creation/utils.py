from aiogram import types
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates

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

async def process_stock_input(message: types.Message, state: FSMContext):
    """Запрашивает количество товара на складе"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state"))
    
    await message.answer(
        "🔢 Введите количество товара на складе (целое число):", 
        reply_markup=keyboard
    )
    
    await AdminStates.waiting_for_product_stock.set()