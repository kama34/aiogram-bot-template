from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates

async def process_stock_input(message: types.Message, state: FSMContext):
    """Запрашивает количество товара на складе"""
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state"))
    
    await message.answer(
        "🔢 Введите количество товара на складе (целое число):", 
        reply_markup=keyboard
    )
    
    await AdminStates.waiting_for_product_stock.set()

async def process_product_stock(message: types.Message, state: FSMContext):
    """Обрабатывает ввод количества товара"""
    try:
        stock = int(message.text)
        if stock < 0:
            raise ValueError("Количество не может быть отрицательным")
        
        async with state.proxy() as data:
            data['product_stock'] = stock
        
        # Показываем сводную информацию перед созданием
        product_info = (
            f"📋 <b>Информация о товаре</b>\n\n"
            f"📌 Название: {data['product_name']}\n"
            f"📝 Описание: {data['product_description']}\n"
            f"💰 Цена: {data['product_price']} ⭐\n"
            f"🖼 Изображение: {'Загружено' if data.get('product_image') else 'Не загружено'}\n"
            f"📁 Категория: {data.get('product_category', 'Не указана')}\n"
            f"🔢 Количество: {data['product_stock']} шт.\n\n"
            f"Подтверждаете создание товара?"
        )
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✅ Создать", callback_data="confirm_product_creation"),
            types.InlineKeyboardButton("❌ Отменить", callback_data="cancel_state")
        )
        
        await message.answer(product_info, reply_markup=keyboard, parse_mode="HTML")
        await AdminStates.product_creation_confirmation.set()
    
    except ValueError:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state"))
        
        await message.answer(
            "❌ Ошибка! Введите корректное количество (целое число):", 
            reply_markup=keyboard
        )

def register_inventory_handlers(dp: Dispatcher):
    """Регистрирует обработчики для работы с инвентарем товара"""
    dp.register_message_handler(
        process_product_stock, 
        state=AdminStates.waiting_for_product_stock
    )