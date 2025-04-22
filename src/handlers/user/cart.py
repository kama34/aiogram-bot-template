from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from services.database import get_database_session, CartItem
from services.product_service import get_product_price, get_product_name, get_product_stock, get_product_by_id
from utils.logger import setup_logger
from utils.message_utils import safe_delete_message

# Setup logger
logger = setup_logger('handlers.user.cart')

async def cart_command(message: types.Message):
    """Показывает корзину пользователя"""
    await show_cart(message, message.from_user.id)

async def view_cart(callback: types.CallbackQuery):
    """Показывает содержимое корзины"""
    await callback.answer()
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Отображаем корзину
    await show_cart(callback.message, callback.from_user.id)

async def show_cart(message, user_id):
    """Общий метод для отображения корзины"""
    try:
        session = get_database_session()
        try:
            # Получаем товары из корзины пользователя
            cart_items = session.query(CartItem).filter(
                CartItem.user_id == user_id
            ).all()
            
            if not cart_items:
                # Корзина пуста
                cart_kb = types.InlineKeyboardMarkup(row_width=1)
                cart_kb.add(
                    types.InlineKeyboardButton("🛍️ Перейти к товарам", callback_data="back_to_categories")
                )
                
                await message.answer(
                    "🧺 <b>Ваша корзина</b>\n\n"
                    "В данный момент ваша корзина пуста.\n"
                    "Выберите товары в нашем меню!",
                    parse_mode="HTML",
                    reply_markup=cart_kb
                )
                return
            
            # Формируем сообщение с товарами в корзине
            cart_text = "🧺 <b>Ваша корзина</b>\n\n"
            total_items = 0
            total_cost = 0
            
            valid_items = []  # Для отслеживания валидных товаров
            unavailable_products = []  # Для отслеживания недоступных товаров
            
            for item in cart_items:
                # ИСПРАВЛЕНО: Корректное получение ID товара с учетом типа данных
                product_id = item.product_id
                if isinstance(product_id, str) and product_id.isdigit():
                    product_id = int(product_id)
                
                # ИСПРАВЛЕНО: Получаем данные товара из базы данных
                product = get_product_by_id(product_id)
                
                # Проверяем, существует ли товар и доступен ли он
                if not product or not product.get('active', True):
                    unavailable_products.append(item)
                    continue
                
                available_stock = product.get('stock', 0)
                
                # Проверка наличия на складе
                if available_stock <= 0:
                    unavailable_products.append(item)
                    continue
                
                # Корректируем количество, если оно превышает доступное
                actual_quantity = min(item.quantity, available_stock)
                if actual_quantity != item.quantity:
                    # Обновляем количество в БД
                    item.quantity = actual_quantity
                    session.commit()
                
                # ИСПРАВЛЕНО: Используем реальное название товара
                product_name = product['name']
                price = product['price']
                item_cost = price * actual_quantity
                total_items += actual_quantity
                total_cost += item_cost
                cart_text += f"• {product_name} - {actual_quantity} шт. × {price} ⭐ = {item_cost} ⭐\n"
                
                valid_items.append(item)
                    
            # Если есть недоступные товары, удаляем их из корзины
            for item in unavailable_products:
                session.delete(item)
            
            if unavailable_products:
                session.commit()
            
            # Если все товары стали недоступны
            if not valid_items:
                cart_kb = types.InlineKeyboardMarkup(row_width=1)
                cart_kb.add(
                    types.InlineKeyboardButton("🛍️ Перейти к товарам", callback_data="back_to_categories")
                )
                
                await message.answer(
                    "🧺 <b>Ваша корзина</b>\n\n"
                    "Товары в вашей корзине больше недоступны.\n"
                    "Пожалуйста, выберите другие товары.",
                    parse_mode="HTML",
                    reply_markup=cart_kb
                )
                return
            
            # Добавляем информацию об итогах
            cart_text += f"\n<b>Всего товаров:</b> {total_items}\n"
            cart_text += f"<b>Итоговая стоимость:</b> {total_cost} ⭐"
            
            # Создаем клавиатуру для управления корзиной
            cart_kb = types.InlineKeyboardMarkup(row_width=3)
            
            # Добавляем кнопки для каждого товара
            for item in valid_items:
                try:
                    product_id = item.product_id
                    if isinstance(product_id, str) and product_id.isdigit():
                        product_id = int(product_id)
                    
                    product = get_product_by_id(product_id)
                    product_name = product['name'] if product else f"Товар {item.product_id}"
                    
                    # Добавляем кнопки управления количеством товара
                    cart_kb.row(
                        types.InlineKeyboardButton(
                            f"➖", 
                            callback_data=f"remove_one_{product_id}"
                        ),
                        types.InlineKeyboardButton(
                            f"{product_name} ({item.quantity})",
                            callback_data=f"product_{product_id}"
                        ),
                        types.InlineKeyboardButton(
                            f"➕", 
                            callback_data=f"add_one_{product_id}"
                        )
                    )
                    cart_kb.row(
                        types.InlineKeyboardButton(
                            f"❌ Удалить {product_name}", 
                            callback_data=f"remove_all_{product_id}"
                        )
                    )
                except Exception as e:
                    logger.error(f"Error creating button for cart item: {e}", exc_info=True)
            
            # Добавляем общие кнопки управления корзиной
            cart_kb.row(types.InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
            cart_kb.row(types.InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart"))
            cart_kb.row(types.InlineKeyboardButton("🛍️ Продолжить покупки", callback_data="back_to_categories"))
            
            await message.answer(cart_text, parse_mode="HTML", reply_markup=cart_kb)
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error displaying cart for user {user_id}: {e}", exc_info=True)
        await message.answer("Произошла ошибка при загрузке корзины. Пожалуйста, попробуйте позже.")

async def clear_cart_callback(callback: types.CallbackQuery):
    """Очистка корзины пользователя"""
    user_id = callback.from_user.id
    
    try:
        with get_database_session() as session:
            # Удаляем все товары из корзины пользователя
            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            session.commit()
            
        await callback.answer("Корзина очищена!")
        
        # Показываем пустую корзину
        cart_kb = types.InlineKeyboardMarkup(row_width=1)
        cart_kb.add(
            types.InlineKeyboardButton("🛒 Перейти к товарам", callback_data="go_to_menu")
        )
        
        await callback.message.edit_text(
            "🧺 <b>Ваша корзина</b>\n\n"
            "Корзина очищена!\n"
            "Выберите товары в нашем меню!",
            parse_mode="HTML",
            reply_markup=cart_kb
        )
        
    except Exception as e:
        logger.error(f"Error clearing cart for user {user_id}: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при очистке корзины")

async def select_quantity_callback(callback: types.CallbackQuery):
    """Показывает выбор количества товара"""
    product_id = callback.data.replace("select_quantity_", "")
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await safe_delete_message(callback.message)
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Создаем клавиатуру с выбором количества
    quantity_kb = types.InlineKeyboardMarkup(row_width=5)
    quantity_buttons = []
    
    for i in range(1, 6):  # Количество от 1 до 5
        quantity_buttons.append(
            types.InlineKeyboardButton(str(i), callback_data=f"add_qty_{product_id}_{i}")
        )
    
    quantity_kb.add(*quantity_buttons)
    quantity_kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data=f"product_{product_id}"))
    
    await callback.message.answer(f"Выберите количество товара:", reply_markup=quantity_kb)

async def add_to_cart_with_quantity_callback(callback: types.CallbackQuery):
    """Обработка добавления товара в корзину с выбранным количеством"""
    # Парсим данные из callback
    parts = callback.data.split("_")
    product_id = int(parts[2])  # Преобразуем в int, так как в БД ожидается числовой тип
    quantity = int(parts[3])
    
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await safe_delete_message(callback.message)
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Получаем информацию о товаре из базы данных
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer("❌ Товар не найден или был удален")
        return
    
    # Проверяем доступное количество
    available_stock = product.get('stock', 0)
    if quantity > available_stock:
        await callback.message.answer(
            f"⚠️ Извините, но на складе осталось только {available_stock} шт. этого товара. "
            f"Выбранное количество ({quantity}) недоступно."
        )
        return
    
    # Продолжаем с добавлением в корзину
    user_id = callback.from_user.id
    
    try:
        session = get_database_session()
        try:
            # Проверяем, есть ли уже такой товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                # Если товар уже есть, увеличиваем количество
                new_quantity = cart_item.quantity + quantity
                # Проверяем, не превышает ли новое количество доступный остаток
                if new_quantity > available_stock:
                    await callback.message.answer(
                        f"⚠️ В вашей корзине уже есть {cart_item.quantity} шт. этого товара. "
                        f"На складе осталось {available_stock} шт. "
                        f"Вы не можете добавить еще {quantity} шт."
                    )
                    return
                
                cart_item.quantity = new_quantity
            else:
                # Если товара нет, добавляем новую запись
                cart_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                session.add(cart_item)
            
            session.commit()
            
            # Показываем сообщение об успешном добавлении
            product_name = product['name']
            await callback.message.answer(
                f"✅ {product_name} ({quantity} шт.) добавлен в корзину!",
                reply_markup=get_after_add_keyboard(product_id)
            )
        
        except Exception as e:
            session.rollback()
            logger.error(f"DB Error adding product to cart: {e}", exc_info=True)
            await callback.message.answer("❌ Произошла ошибка при добавлении товара в корзину")
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Error adding product to cart: {e}", exc_info=True)
        await callback.message.answer("❌ Произошла ошибка при добавлении товара в корзину")

def get_after_add_keyboard(product_id):
    """Возвращает клавиатуру после добавления товара в корзину"""
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("🛒 Перейти в корзину", callback_data="view_cart"),
        types.InlineKeyboardButton("🔍 Продолжить покупки", callback_data="back_to_categories"),
        types.InlineKeyboardButton("📦 Показать товар", callback_data=f"product_{product_id}")
    )
    return keyboard

async def remove_one_item_callback(callback: types.CallbackQuery):
    """Удаление одной единицы товара из корзины"""
    product_id = callback.data.replace("remove_one_", "")
    user_id = callback.from_user.id
    
    try:
        with get_database_session() as session:
            # Находим товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                if cart_item.quantity > 1:
                    # Уменьшаем количество на 1
                    cart_item.quantity -= 1
                    session.commit()
                    await callback.answer(f"Удалена 1 шт. товара из корзины")
                else:
                    # Если остался 1 товар, удаляем его полностью
                    session.delete(cart_item)
                    session.commit()
                    await callback.answer("Товар удален из корзины")
            else:
                await callback.answer("Товар не найден в корзине")
                
        # Удаляем текущее сообщение с корзиной перед обновлением
        try:
            await safe_delete_message(callback.message)
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            
        # Обновляем отображение корзины
        await show_cart(callback.message, user_id)
        
    except Exception as e:
        logger.error(f"Error removing item from cart: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обновлении корзины")

async def remove_all_item_callback(callback: types.CallbackQuery):
    """Удаление всех единиц конкретного товара из корзины"""
    product_id = callback.data.replace("remove_all_", "")
    user_id = callback.from_user.id
    
    try:
        with get_database_session() as session:
            # Находим и удаляем товар из корзины
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                session.delete(cart_item)
                session.commit()
                await callback.answer("Товар удален из корзины")
            else:
                await callback.answer("Товар не найден в корзине")
                
        # Удаляем текущее сообщение с корзиной перед обновлением
        try:
            await safe_delete_message(callback.message)
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            
        # Обновляем отображение корзины
        await show_cart(callback.message, user_id)
        
    except Exception as e:
        logger.error(f"Error removing all items from cart: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обновлении корзины")

async def add_one_item_callback(callback: types.CallbackQuery):
    """Добавление одной единицы товара в корзину"""
    product_id = callback.data.replace("add_one_", "")
    user_id = callback.from_user.id
    
    try:
        # Проверяем доступные остатки товара
        available_stock = get_product_stock(product_id)
        
        with get_database_session() as session:
            # Находим товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                # Проверяем, не превышаем ли мы доступное количество
                if cart_item.quantity < available_stock:
                    # Увеличиваем количество на 1
                    cart_item.quantity += 1
                    session.commit()
                    await callback.answer(f"Добавлена 1 шт. товара в корзину")
                else:
                    await callback.answer(f"Нельзя добавить больше! Доступно: {available_stock} шт.")
            else:
                await callback.answer("Товар не найден в корзине")
        
        # Удаляем текущее сообщение с корзиной перед обновлением
        try:
            await safe_delete_message(callback.message)
        except Exception as e:
            logger.error(f"Error deleting message: {e}", exc_info=True)
            
        # Обновляем отображение корзины
        await show_cart(callback.message, user_id)
        
    except Exception as e:
        logger.error(f"Error adding item to cart: {e}", exc_info=True)
        await callback.answer("Произошла ошибка при обновлении корзины")

def register_cart_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков для корзины"""
    # Регистрация обработчика для команды корзины
    dp.register_message_handler(cart_command, lambda message: message.text == "🧺 Корзина", state="*")
    
    # Регистрация обработчиков для кнопок в корзине
    dp.register_callback_query_handler(view_cart, lambda c: c.data == "view_cart")
    dp.register_callback_query_handler(clear_cart_callback, lambda c: c.data == "clear_cart")
    dp.register_callback_query_handler(select_quantity_callback, lambda c: c.data.startswith("select_quantity_"))
    dp.register_callback_query_handler(add_to_cart_with_quantity_callback, lambda c: c.data.startswith("add_qty_"))
    dp.register_callback_query_handler(remove_one_item_callback, lambda c: c.data.startswith("remove_one_"))
    dp.register_callback_query_handler(remove_all_item_callback, lambda c: c.data.startswith("remove_all_"))
    dp.register_callback_query_handler(add_one_item_callback, lambda c: c.data.startswith("add_one_"))