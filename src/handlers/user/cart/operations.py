from aiogram import types
from services.database import get_database_session, CartItem
from services.product_service import get_product_stock
from utils.logger import setup_logger
from utils.message_utils import safe_delete_message

# Setup logger
logger = setup_logger('handlers.user.cart.operations')

# Импортируем функцию отображения корзины из display.py
from .display import show_cart

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