from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from services.product_service import update_product, update_product_stock

async def process_edited_value(message: types.Message, state: FSMContext):
    """Обрабатывает ввод нового значения поля"""
    async with state.proxy() as data:
        field = data["editing_field"]
        product_id = data["editing_product_id"]
        
        # Сохраняем последнее сообщение с промптом для последующего удаления
        if "prompt_message_id" in data:
            prompt_message_id = data["prompt_message_id"]
            try:
                await message.bot.delete_message(message.chat.id, prompt_message_id)
            except:
                pass
    
    # Проверки и обработка в зависимости от поля
    if field == "price":
        try:
            value = float(message.text.replace(',', '.'))
            if value <= 0:
                raise ValueError("Цена должна быть больше нуля")
        except ValueError:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_editing"))
            
            await message.answer(
                "❌ Ошибка! Введите корректную цену (только число):", 
                reply_markup=keyboard
            )
            return
    elif field == "stock":
        try:
            value = int(message.text)
            if value < 0:
                raise ValueError("Количество не может быть отрицательным")
        except ValueError:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_editing"))
            
            await message.answer(
                "❌ Ошибка! Введите корректное количество (целое число):", 
                reply_markup=keyboard
            )
            return
    else:
        value = message.text
    
    # Обновляем товар
    if field == "stock":
        success = update_product_stock(product_id, value)
    else:
        # Формируем словарь с обновляемыми полями
        update_data = {field: value}
        success = update_product(product_id, **update_data)
    
    if success:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✏️ Продолжить редактирование", callback_data=f"edit_product_{product_id}"),
            types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
        )
        
        await message.answer(
            f"✅ Поле '{field}' успешно обновлено!", 
            reply_markup=keyboard
        )
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✏️ К редактированию", callback_data=f"edit_product_{product_id}"),
            types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
        )
        
        await message.answer(
            "❌ Ошибка при обновлении товара!", 
            reply_markup=keyboard
        )
    
    await AdminStates.product_editing.set()

async def process_edited_image(message: types.Message, state: FSMContext):
    """Обрабатывает загрузку нового изображения товара"""
    if not message.photo:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_editing"))
        
        await message.answer(
            "❌ Пожалуйста, отправьте изображение!", 
            reply_markup=keyboard
        )
        return
    
    async with state.proxy() as data:
        product_id = data["editing_product_id"]
    
    # Берем последнее фото (с наилучшим качеством)
    photo = message.photo[-1]
    file_id = photo.file_id
    
    # Обновляем фото товара
    success = update_product(product_id, image_url=file_id)
    
    if success:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✏️ Продолжить редактирование", callback_data=f"edit_product_{product_id}"),
            types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
        )
        
        await message.answer(
            "✅ Изображение товара успешно обновлено!", 
            reply_markup=keyboard
        )
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("✏️ К редактированию", callback_data=f"edit_product_{product_id}"),
            types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
        )
        
        await message.answer(
            "❌ Ошибка при обновлении изображения товара!", 
            reply_markup=keyboard
        )
    
    await AdminStates.product_editing.set()

def register_value_processing_handlers(dp: Dispatcher):
    """Регистрирует обработчики для обработки новых значений полей товара"""
    dp.register_message_handler(
        process_edited_value, 
        state=AdminStates.waiting_for_edited_value,
        content_types=types.ContentTypes.TEXT
    )
    
    dp.register_message_handler(
        process_edited_image, 
        state=AdminStates.waiting_for_edited_value,
        content_types=types.ContentTypes.PHOTO
    )