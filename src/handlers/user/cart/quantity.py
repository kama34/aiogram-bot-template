from aiogram import types
from services.database import get_database_session, CartItem
from services.product_service import get_product_by_id
from utils.logger import setup_logger
from utils.message_utils import safe_delete_message

# Setup logger
logger = setup_logger('handlers.user.cart.quantity')

# Импортируем вспомогательные функции
from .keyboards import get_after_add_keyboard

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