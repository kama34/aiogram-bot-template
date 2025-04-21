from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates

async def process_product_name(message: types.Message, state: FSMContext):
    """Обрабатывает ввод названия товара"""
    async with state.proxy() as data:
        data['product_name'] = message.text
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state"))
    
    await message.answer(
        "✏️ Введите описание товара:", 
        reply_markup=keyboard
    )
    
    await AdminStates.waiting_for_product_description.set()

async def process_product_description(message: types.Message, state: FSMContext):
    """Обрабатывает ввод описания товара"""
    async with state.proxy() as data:
        data['product_description'] = message.text
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state"))
    
    await message.answer(
        "💰 Введите цену товара (только число):", 
        reply_markup=keyboard
    )
    
    await AdminStates.waiting_for_product_price.set()

async def process_product_price(message: types.Message, state: FSMContext):
    """Обрабатывает ввод цены товара"""
    try:
        price = float(message.text.replace(',', '.'))
        if price <= 0:
            raise ValueError("Цена должна быть больше нуля")
        
        async with state.proxy() as data:
            data['product_price'] = price
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("⏩ Пропустить", callback_data="skip_product_image"),
            types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state")
        )
        
        await message.answer(
            "🖼 Отправьте изображение товара или нажмите 'Пропустить':", 
            reply_markup=keyboard
        )
        
        await AdminStates.waiting_for_product_image.set()
    
    except ValueError:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state"))
        
        await message.answer(
            "❌ Ошибка! Введите корректную цену (только число):", 
            reply_markup=keyboard
        )

def register_basic_info_handlers(dp: Dispatcher):
    """Регистрирует обработчики для ввода основной информации о товаре"""
    dp.register_message_handler(
        process_product_name, 
        state=AdminStates.waiting_for_product_name
    )
    
    dp.register_message_handler(
        process_product_description, 
        state=AdminStates.waiting_for_product_description
    )
    
    dp.register_message_handler(
        process_product_price, 
        state=AdminStates.waiting_for_product_price
    )