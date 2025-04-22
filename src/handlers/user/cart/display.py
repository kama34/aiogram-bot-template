from aiogram import types
from services.database import get_database_session, CartItem
from services.product_service import get_product_by_id
from utils.logger import setup_logger
from utils.message_utils import safe_delete_message

# Setup logger
logger = setup_logger('handlers.user.cart.display')

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
                # Корректное получение ID товара с учетом типа данных
                product_id = item.product_id
                if isinstance(product_id, str) and product_id.isdigit():
                    product_id = int(product_id)
                
                # Получаем данные товара из базы данных
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
                
                # Используем реальное название товара
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
            from .keyboards import create_cart_keyboard
            cart_kb = create_cart_keyboard(valid_items)
            
            await message.answer(cart_text, parse_mode="HTML", reply_markup=cart_kb)
        finally:
            session.close()
            
    except Exception as e:
        logger.error(f"Error displaying cart for user {user_id}: {e}", exc_info=True)
        await message.answer("Произошла ошибка при загрузке корзины. Пожалуйста, попробуйте позже.")