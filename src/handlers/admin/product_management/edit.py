from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from utils.admin_utils import is_admin
from utils.message_utils import safe_delete_message  # Новый импорт
from utils.message_tracker import MessageTracker  # Новый импорт
from services.product_service import get_product_by_id, update_product, update_product_stock, delete_product

async def edit_product(callback: types.CallbackQuery, state: FSMContext):
    """Инициирует редактирование товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Получаем ID товара из callback_data
    product_id = callback.data.replace("edit_product_", "")
    
    # Получаем информацию о товаре
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer(
            "❌ Товар не найден. Возможно, он был удален.", 
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
            )
        )
        return
    
    # Сохраняем ID товара в состоянии
    await state.update_data(editing_product_id=product_id)
    
    # Безопасно удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Формируем сообщение с информацией о товаре
    message_text = (
        f"📝 <b>Редактирование товара</b>\n\n"
        f"📌 <b>Название:</b> {product['name']}\n"
        f"📝 <b>Описание:</b> {product['description']}\n"
        f"💰 <b>Цена:</b> {product['price']} ₽\n"
        f"📁 <b>Категория:</b> {product.get('category', 'Не указана')}\n"
        f"🔢 <b>Количество на складе:</b> {product.get('stock', 0)} шт.\n"
    )
    
    # Формируем клавиатуру с опциями редактирования
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📌 Название", callback_data="edit_field_name"),
        types.InlineKeyboardButton("📝 Описание", callback_data="edit_field_description")
    )
    keyboard.add(
        types.InlineKeyboardButton("💰 Цена", callback_data="edit_field_price"),
        types.InlineKeyboardButton("📁 Категория", callback_data="edit_field_category")
    )
    keyboard.add(
        types.InlineKeyboardButton("🖼 Изображение", callback_data="edit_field_image"),
        types.InlineKeyboardButton("🔢 Количество", callback_data="edit_field_stock")
    )
    keyboard.add(
        types.InlineKeyboardButton("🚫 Удалить товар", callback_data=f"delete_product_{product_id}")
    )
    keyboard.add(
        types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
    )
    
    # Если есть изображение, показываем его
    if product.get("image_url"):
        await callback.message.answer_photo(
            photo=product["image_url"],
            caption=message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    # Устанавливаем состояние
    await AdminStates.product_editing.set()

async def select_edit_field(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор поля для редактирования"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    field = callback.data.replace("edit_field_", "")
    
    # Сохраняем выбранное поле в состоянии
    await state.update_data(editing_field=field)
    
    # Удаляем предыдущее сообщение с меню редактирования
    await safe_delete_message(callback.message)
    
    # Определяем текст подсказки в зависимости от поля
    prompts = {
        "name": "📌 Введите новое название товара:",
        "description": "📝 Введите новое описание товара:",
        "price": "💰 Введите новую цену товара (только число):",
        "category": "📁 Введите новую категорию товара:",
        "stock": "🔢 Введите новое количество товара на складе (целое число):"
    }
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_editing"))
    
    # Отправляем сообщение с запросом на редактирование и отслеживаем его
    if field == "image":
        message = await callback.message.answer(
            "🖼 Загрузите новое изображение товара:", 
            reply_markup=keyboard
        )
    else:
        message = await callback.message.answer(
            prompts.get(field, "Введите новое значение:"), 
            reply_markup=keyboard
        )
    
    # Сохраняем сообщение для последующего удаления
    await MessageTracker.add_message_to_state(state, message)
    
    await AdminStates.waiting_for_edited_value.set()

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

async def cancel_editing(callback: types.CallbackQuery, state: FSMContext):
    """Отменяет текущее редактирование"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Безопасно удаляем сообщение
    await safe_delete_message(callback.message)
    
    async with state.proxy() as data:
        product_id = data["editing_product_id"]
    
    # Возвращаемся к редактированию товара
    callback.data = f"edit_product_{product_id}"
    await edit_product(callback, state)

async def confirm_delete_product(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await safe_delete_message(callback.message)
    
    # Получаем ID товара из callback_data
    product_id = callback.data.replace("delete_product_", "")
    
    # Получаем информацию о товаре
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer(
            "❌ Товар не найден. Возможно, он был уже удален.", 
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
            )
        )
        return
    
    # Запрашиваем подтверждение удаления
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ Подтвердить удаление", callback_data=f"confirm_delete_{product_id}"),
        types.InlineKeyboardButton("❌ Отменить", callback_data=f"edit_product_{product_id}")
    )
    
    await callback.message.answer(
        f"⚠️ <b>Вы действительно хотите удалить товар?</b>\n\n"
        f"<b>{product['name']}</b> - {product['price']} ₽\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def delete_product_handler(callback: types.CallbackQuery, state: FSMContext):
    """Удаляет товар после подтверждения"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await callback.message.delete()
    
    # Получаем ID товара из callback_data
    product_id = callback.data.replace("confirm_delete_", "")
    
    # Удаляем товар
    success = delete_product(product_id)
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products"))
    
    if success:
        await callback.message.answer(
            "✅ Товар успешно удален!", 
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при удалении товара!", 
            reply_markup=keyboard
        )
    
    await state.finish()

def register_edit_handlers(dp: Dispatcher):
    """Регистрирует обработчики для редактирования товаров"""
    # Редактирование товара
    dp.register_callback_query_handler(
        edit_product, 
        lambda c: c.data and c.data.startswith("edit_product_"), 
        state="*"
    )
    
    # Выбор поля для редактирования
    dp.register_callback_query_handler(
        select_edit_field, 
        lambda c: c.data and c.data.startswith("edit_field_"), 
        state=AdminStates.product_editing
    )
    
    # Отмена редактирования
    dp.register_callback_query_handler(
        cancel_editing, 
        lambda c: c.data == "cancel_editing", 
        state=AdminStates.waiting_for_edited_value
    )
    
    # Обработка нового значения поля
    dp.register_message_handler(
        process_edited_value, 
        state=AdminStates.waiting_for_edited_value,
        content_types=types.ContentTypes.TEXT
    )
    
    # Обработка нового изображения
    dp.register_message_handler(
        process_edited_image, 
        state=AdminStates.waiting_for_edited_value,
        content_types=types.ContentTypes.PHOTO
    )
    
    # Подтверждение удаления товара
    dp.register_callback_query_handler(
        confirm_delete_product, 
        lambda c: c.data and c.data.startswith("delete_product_"), 
        state="*"
    )
    
    # Удаление товара
    dp.register_callback_query_handler(
        delete_product_handler, 
        lambda c: c.data and c.data.startswith("confirm_delete_"), 
        state="*"
    )