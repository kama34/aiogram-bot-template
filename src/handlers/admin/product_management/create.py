from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from utils.admin_utils import is_admin
from services.product_service import create_product, update_product_stock
from utils.message_utils import safe_delete_message  # Добавляем импорт

async def start_product_creation(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс создания товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Заменяем прямое удаление на безопасное
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

async def process_product_image(message: types.Message, state: FSMContext):
    """Обрабатывает загрузку изображения товара"""
    if message.photo:
        # Берем последнее фото (с наилучшим качеством)
        photo = message.photo[-1]
        file_id = photo.file_id
        
        async with state.proxy() as data:
            data['product_image'] = file_id
        
        await process_category_input(message, state)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("⏩ Пропустить", callback_data="skip_product_image"),
            types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state")
        )
        
        await message.answer(
            "❌ Пожалуйста, отправьте изображение или нажмите 'Пропустить':", 
            reply_markup=keyboard
        )

async def skip_product_image(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пропуска загрузки изображения"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await callback.message.delete()
    
    async with state.proxy() as data:
        data['product_image'] = None
    
    await process_category_input(callback.message, state)

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
    
    await callback.message.delete()
    
    async with state.proxy() as data:
        data['product_category'] = None
    
    await process_stock_input(callback.message, state)

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

async def confirm_product_creation(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает подтверждение создания товара"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await callback.message.delete()
    
    async with state.proxy() as data:
        name = data['product_name']
        description = data['product_description']
        price = data['product_price']
        image_url = data.get('product_image')
        category = data.get('product_category')
        stock = data['product_stock']
    
    # Отправляем сообщение о процессе
    processing_message = await callback.message.answer("⏱ Создаем товар...")
    
    try:
        # Создаем товар
        product_id = create_product(name, description, price, image_url, category)
        
        if product_id:
            # Обновляем количество товара
            stock_success = update_product_stock(product_id, stock)
            
            # Удаляем сообщение о процессе
            await processing_message.delete()
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ К управлению товарами", callback_data="manage_products"))
            
            if stock_success:
                success_text = f"✅ Товар успешно создан!\n\nID товара: <code>{product_id}</code>"
            else:
                success_text = f"✅ Товар создан, но не удалось установить количество.\n\nID товара: <code>{product_id}</code>"
            
            await callback.message.answer(
                success_text, 
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Удаляем сообщение о процессе
            await processing_message.delete()
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ К управлению товарами", callback_data="manage_products"))
            
            await callback.message.answer(
                "❌ Ошибка при создании товара. Пожалуйста, попробуйте снова.", 
                reply_markup=keyboard
            )
    except Exception as e:
        # Удаляем сообщение о процессе
        await processing_message.delete()
        
        import traceback
        print(f"Error creating product: {e}")
        traceback.print_exc()
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ К управлению товарами", callback_data="manage_products"))
        
        await callback.message.answer(
            f"❌ Произошла ошибка при создании товара: {str(e)[:100]}...", 
            reply_markup=keyboard
        )
    
    await state.finish()

def register_create_handlers(dp: Dispatcher):
    """Регистрирует обработчики для создания товаров"""
    # Начало создания
    dp.register_callback_query_handler(
        start_product_creation, 
        lambda c: c.data == "create_product", 
        state="*"
    )
    
    # Ввод названия
    dp.register_message_handler(
        process_product_name, 
        state=AdminStates.waiting_for_product_name
    )
    
    # Ввод описания
    dp.register_message_handler(
        process_product_description, 
        state=AdminStates.waiting_for_product_description
    )
    
    # Ввод цены
    dp.register_message_handler(
        process_product_price, 
        state=AdminStates.waiting_for_product_price
    )
    
    # Загрузка изображения
    dp.register_message_handler(
        process_product_image, 
        content_types=types.ContentTypes.PHOTO, 
        state=AdminStates.waiting_for_product_image
    )
    
    # Пропуск изображения
    dp.register_callback_query_handler(
        skip_product_image, 
        lambda c: c.data == "skip_product_image", 
        state=AdminStates.waiting_for_product_image
    )
    
    # Ввод категории
    dp.register_message_handler(
        process_product_category, 
        state=AdminStates.waiting_for_product_category
    )
    
    # Пропуск категории
    dp.register_callback_query_handler(
        skip_product_category, 
        lambda c: c.data == "skip_product_category", 
        state=AdminStates.waiting_for_product_category
    )
    
    # Ввод количества
    dp.register_message_handler(
        process_product_stock, 
        state=AdminStates.waiting_for_product_stock
    )
    
    # Подтверждение создания
    dp.register_callback_query_handler(
        confirm_product_creation, 
        lambda c: c.data == "confirm_product_creation", 
        state=AdminStates.product_creation_confirmation
    )