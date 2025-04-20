from aiogram import types, Dispatcher
from services.database import get_database_session, CartItem
from services.product_service import get_product_price, get_product_name, get_product_stock
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('handlers.cart')

async def cart_command(message: types.Message):
    """Показывает корзину пользователя"""
    await show_cart(message, message.from_user.id)

async def view_cart_callback(callback: types.CallbackQuery):
    """Обработка кнопки просмотра корзины"""
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Показываем корзину
    await show_cart(callback.message, callback.from_user.id)

async def show_cart(message, user_id):
    """Общий метод для отображения корзины"""
    try:
        with get_database_session() as session:
            # Получаем товары из корзины пользователя
            cart_items = session.query(CartItem).filter(
                CartItem.user_id == user_id
            ).all()
            
            if not cart_items:
                # Корзина пуста
                cart_kb = types.InlineKeyboardMarkup(row_width=1)
                cart_kb.add(
                    types.InlineKeyboardButton("🛒 Перейти к товарам", callback_data="go_to_menu")
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
            
            for item in cart_items:
                product_name = get_product_name(item.product_id)
                price = get_product_price(item.product_id)
                item_cost = price * item.quantity
                total_items += item.quantity
                total_cost += item_cost
                cart_text += f"• {product_name} - {item.quantity} шт. × {price} ⭐ = {item_cost} ⭐\n"
            
            cart_text += f"\n<b>Всего товаров:</b> {total_items}\n"
            cart_text += f"<b>Итоговая стоимость:</b> {total_cost} ⭐"
            
            # Создаем клавиатуру для управления корзиной и удаления товаров
            cart_kb = types.InlineKeyboardMarkup(row_width=3)
            
            # Добавляем кнопки для управления каждым товаром
            for item in cart_items:
                product_name = get_product_name(item.product_id)
                # Получаем доступные остатки товара
                available_stock = get_product_stock(item.product_id)
                # Добавляем кнопки уменьшения, увеличения и удаления товара
                cart_kb.row(
                    types.InlineKeyboardButton(
                        f"➖", 
                        callback_data=f"remove_one_{item.product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"{product_name} ({item.quantity})",
                        callback_data=f"product_info_{item.product_id}"
                    ),
                    types.InlineKeyboardButton(
                        f"➕", 
                        callback_data=f"add_one_{item.product_id}"
                    )
                )
                cart_kb.row(
                    types.InlineKeyboardButton(
                        f"❌ Удалить {product_name}", 
                        callback_data=f"remove_all_{item.product_id}"
                    )
                )
            
            # Добавляем общие кнопки управления
            cart_kb.row(types.InlineKeyboardButton("✅ Оформить заказ", callback_data="checkout"))
            cart_kb.row(types.InlineKeyboardButton("🗑️ Очистить корзину", callback_data="clear_cart"))
            cart_kb.row(types.InlineKeyboardButton("🛒 Продолжить покупки", callback_data="go_to_menu"))
            
            await message.answer(cart_text, parse_mode="HTML", reply_markup=cart_kb)
            
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
        await callback.message.delete()
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
    # Парсим данные из callback_data
    parts = callback.data.replace("add_qty_", "").split("_")
    product_id = parts[0]
    quantity = int(parts[1])
    user_id = callback.from_user.id
    
    # Получаем доступное количество товара
    available_stock = get_product_stock(product_id)
    
    # Проверяем, есть ли уже товар в корзине пользователя
    current_in_cart = 0
    try:
        with get_database_session() as session:
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                current_in_cart = cart_item.quantity
    except Exception as e:
        logger.error(f"Error checking cart: {e}", exc_info=True)
    
    # Проверяем, не превышаем ли мы доступное количество
    if quantity + current_in_cart > available_stock:
        await callback.answer(f"Недостаточно товара! Доступно: {available_stock} шт.")
        return
    
    # Получаем цену продукта в звездах
    price = get_product_price(product_id)
    total_price = price * quantity
    
    await callback.answer(f"Добавлено {quantity} шт. в корзину!")
    
    try:
        # Удаляем предыдущее сообщение с выбором количества
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    try:
        with get_database_session() as session:
            # Проверяем, есть ли уже товар в корзине
            cart_item = session.query(CartItem).filter(
                CartItem.user_id == user_id,
                CartItem.product_id == product_id
            ).first()
            
            if cart_item:
                # Если товар уже в корзине, увеличиваем количество
                cart_item.quantity += quantity
            else:
                # Если товара нет, добавляем новый
                new_item = CartItem(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity
                )
                session.add(new_item)
            
            session.commit()
            logger.info(f"User {user_id} added {quantity} of product {product_id} to cart")
            
            # Добавляем кнопку "Перейти в корзину"
            view_cart_kb = types.InlineKeyboardMarkup()
            view_cart_kb.add(
                types.InlineKeyboardButton("🧺 Перейти в корзину", callback_data="view_cart")
            )
            view_cart_kb.add(
                types.InlineKeyboardButton("◀️ Продолжить выбор", callback_data="back_to_menu")
            )
            
            await callback.message.answer(
                f"✅ В корзину добавлено: Продукт {product_id} - {quantity} шт.\n"
                f"💰 Стоимость: {total_price} ⭐", 
                reply_markup=view_cart_kb
            )
            
    except Exception as e:
        logger.error(f"Error adding item to cart: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при добавлении товара в корзину. Пожалуйста, попробуйте позже."
        )

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
            await callback.message.delete()
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
            await callback.message.delete()
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
            await callback.message.delete()
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
    dp.register_callback_query_handler(view_cart_callback, lambda c: c.data == "view_cart")
    dp.register_callback_query_handler(clear_cart_callback, lambda c: c.data == "clear_cart")
    dp.register_callback_query_handler(select_quantity_callback, lambda c: c.data.startswith("select_quantity_"))
    dp.register_callback_query_handler(add_to_cart_with_quantity_callback, lambda c: c.data.startswith("add_qty_"))
    dp.register_callback_query_handler(remove_one_item_callback, lambda c: c.data.startswith("remove_one_"))
    dp.register_callback_query_handler(remove_all_item_callback, lambda c: c.data.startswith("remove_all_"))
    dp.register_callback_query_handler(add_one_item_callback, lambda c: c.data.startswith("add_one_"))