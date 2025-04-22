from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from services.product_service import get_product_by_id
from services.database import get_database_session, CartItem
from utils.message_utils import safe_delete_message
from utils.logger import setup_logger

# Настройка логгера
logger = setup_logger('handlers.shop.quantity_selection')

async def select_quantity(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик выбора количества товара для добавления в корзину"""
    await callback.answer()
    
    # Получаем ID товара
    product_id = int(callback.data.replace("select_quantity_", ""))
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Получаем информацию о товаре
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer(
            "❌ Товар не найден или был удален.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К списку товаров", callback_data="back_to_categories")
            )
        )
        return
    
    # Проверяем наличие товара на складе
    available_stock = product.get('stock', 0)
    if available_stock <= 0:
        await callback.message.answer(
            "❌ Данный товар отсутствует на складе.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К списку товаров", callback_data="back_to_categories")
            )
        )
        return
    
    # Сохраняем данные о товаре в состояние
    await state.update_data(selecting_product_id=product_id)
    
    # Создаем клавиатуру для выбора количества
    qty_keyboard = types.InlineKeyboardMarkup(row_width=5)
    
    # Ограничиваем максимальное количество для выбора (не более 10 или доступного количества)
    max_qty = min(10, available_stock)
    
    # Добавляем кнопки с количествами
    qty_buttons = []
    for i in range(1, max_qty + 1):
        qty_buttons.append(
            types.InlineKeyboardButton(
                str(i), 
                callback_data=f"add_to_cart_{product_id}_{i}"
            )
        )
    
    # Добавляем кнопки в клавиатуру группами по 5
    for i in range(0, len(qty_buttons), 5):
        qty_keyboard.row(*qty_buttons[i:i+5])
    
    # Добавляем кнопку отмены
    qty_keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data=f"product_{product_id}"))
    
    # Отправляем сообщение с выбором количества
    await callback.message.answer(
        f"<b>{product['name']}</b>\n\n"
        f"💰 Цена: {product['price']} ⭐\n"
        f"🔢 Доступно: {available_stock} шт.\n\n"
        f"Выберите количество товара для добавления в корзину:",
        reply_markup=qty_keyboard,
        parse_mode="HTML"
    )

async def add_to_cart(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик добавления товара в корзину с выбранным количеством"""
    # Парсим данные из callback
    parts = callback.data.split("_")
    product_id = int(parts[2])
    quantity = int(parts[3])
    
    await callback.answer()
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Получаем информацию о товаре из базы данных
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer(
            "❌ Товар не найден или был удален.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К списку товаров", callback_data="back_to_categories")
            )
        )
        return
    
    # Проверяем доступное количество
    available_stock = product.get('stock', 0)
    if quantity > available_stock:
        await callback.message.answer(
            f"⚠️ Извините, но на складе осталось только {available_stock} шт. этого товара. "
            f"Выбранное количество ({quantity}) недоступно.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ Назад", callback_data=f"select_quantity_{product_id}")
            )
        )
        return
    
    # Продолжаем с добавлением в корзину
    user_id = callback.from_user.id
    
    try:
        session = get_database_session()
        
        # Проверяем, есть ли уже такой товар в корзине
        cart_item = session.query(CartItem).filter(
            CartItem.user_id == user_id,
            CartItem.product_id == str(product_id)  # Преобразуем в строку, если в БД хранится как VARCHAR
        ).first()
        
        if cart_item:
            # Если товар уже есть, увеличиваем количество
            new_quantity = cart_item.quantity + quantity
            
            # Проверяем, не превышает ли новое количество доступный остаток
            if new_quantity > available_stock:
                await callback.message.answer(
                    f"⚠️ В вашей корзине уже есть {cart_item.quantity} шт. этого товара. "
                    f"На складе осталось {available_stock} шт. "
                    f"Вы не можете добавить еще {quantity} шт.",
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("🛒 Перейти в корзину", callback_data="view_cart"),
                        types.InlineKeyboardButton("◀️ Назад", callback_data=f"product_{product_id}")
                    )
                )
                session.close()
                return
            
            cart_item.quantity = new_quantity
        else:
            # Если товара нет, добавляем новую запись
            cart_item = CartItem(
                user_id=user_id,
                product_id=str(product_id),  # Преобразуем в строку, если в БД хранится как VARCHAR
                quantity=quantity
            )
            session.add(cart_item)
        
        session.commit()
        session.close()
        
        # Показываем сообщение об успешном добавлении
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton("🛒 Перейти в корзину", callback_data="view_cart"),
            types.InlineKeyboardButton("🔍 Продолжить покупки", callback_data="back_to_categories"),
            types.InlineKeyboardButton("📦 Показать товар", callback_data=f"product_{product_id}")
        )
        
        await callback.message.answer(
            f"✅ {product['name']} ({quantity} шт.) добавлен в корзину!",
            reply_markup=keyboard
        )
    
    except Exception as e:
        logger.error(f"Error adding product to cart: {e}", exc_info=True)
        await callback.message.answer(
            "❌ Произошла ошибка при добавлении товара в корзину.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ Назад", callback_data=f"product_{product_id}")
            )
        )

def register_quantity_handlers(dp: Dispatcher):
    """Регистрирует обработчики для выбора количества товара и добавления в корзину"""
    dp.register_callback_query_handler(
        select_quantity, 
        lambda c: c.data and c.data.startswith("select_quantity_"),
        state="*"
    )
    
    dp.register_callback_query_handler(
        add_to_cart, 
        lambda c: c.data and c.data.startswith("add_to_cart_"),
        state="*"
    )