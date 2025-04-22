from aiogram import types
from services.database import get_database_session, CartItem
from services.product_service import get_product_price, get_product_name
from utils.logger import setup_logger

# Настройка логгера для этого модуля
logger = setup_logger('handlers.payment.checkout')

async def checkout_callback(callback: types.CallbackQuery):
    """Обработка нажатия на кнопку оформления заказа"""
    user_id = callback.from_user.id
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    try:
        with get_database_session() as session:
            # Получаем товары из корзины пользователя
            cart_items = session.query(CartItem).filter(
                CartItem.user_id == user_id
            ).all()
            
            if not cart_items:
                # Если корзина пуста, показываем сообщение
                await callback.message.answer(
                    "🧺 Ваша корзина пуста. Добавьте товары перед оформлением заказа."
                )
                return
            
            # Формируем сообщение с подтверждением заказа
            order_text = "📝 <b>Подтверждение заказа</b>\n\n"
            total_items = 0
            total_cost = 0
            order_items = []  # Для хранения информации о товарах в заказе
            
            for item in cart_items:
                product_name = get_product_name(item.product_id)
                price = get_product_price(item.product_id)
                item_cost = price * item.quantity
                total_items += item.quantity
                total_cost += item_cost
                
                # Сохраняем информацию о товаре в заказе
                order_items.append({
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": price,
                    "name": product_name
                })
                
                order_text += f"• {product_name} - {item.quantity} шт. × {price} ⭐ = {item_cost} ⭐\n"
            
            # Итоговая сумма в звездах
            order_text += f"\n<b>Всего товаров:</b> {total_items}\n"
            order_text += f"<b>Итоговая стоимость:</b> {total_cost} ⭐"
            
            # Сохраняем данные о заказе в контексте пользователя
            from bot import dp
            await dp.storage.set_data(user=user_id, data={
                "order_items": order_items,
                "total_cost_stars": total_cost,
                "total_items": total_items
            })
            
            # Создаем клавиатуру с кнопкой оплаты
            payment_kb = types.InlineKeyboardMarkup(row_width=1)
            payment_kb.add(
                types.InlineKeyboardButton(
                    f"⭐ Оплатить {total_cost} звезд", 
                    callback_data="pay_with_stars"
                )
            )
            payment_kb.add(
                types.InlineKeyboardButton(
                    "◀️ Вернуться в корзину", 
                    callback_data="view_cart"
                )
            )
            
            # Отправляем сообщение с подтверждением заказа
            await callback.message.answer(
                order_text,
                parse_mode="HTML",
                reply_markup=payment_kb
            )
            
    except Exception as e:
        logger.error(f"Error processing checkout for user {user_id}: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже."
        )