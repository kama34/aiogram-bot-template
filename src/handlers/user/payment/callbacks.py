from aiogram import types
from aiogram.types import PreCheckoutQuery
from datetime import datetime

from services.database import get_database_session, CartItem, Order, OrderItem
from services.product_service import update_product_stock
from utils.logger import setup_logger
from .notifications import send_order_success_notification, notify_admins_about_order

# Настройка логгера для этого модуля
logger = setup_logger('handlers.payment.callbacks')

async def process_pre_checkout_query(pre_checkout_query: PreCheckoutQuery):
    """Обработка pre-checkout запроса"""
    user_id = pre_checkout_query.from_user.id
    
    try:
        # Получаем данные о заказе
        from bot import dp, bot
        user_data = await dp.storage.get_data(user=user_id)
        
        if not user_data or "payment_id" not in user_data:
            # Если данные о заказе не найдены, отклоняем платеж
            await bot.answer_pre_checkout_query(
                pre_checkout_query_id=pre_checkout_query.id,
                ok=False,
                error_message="Ошибка: данные заказа не найдены. Пожалуйста, попробуйте снова."
            )
            return
        
        # Проверяем, что платеж соответствует сохраненному заказу
        if pre_checkout_query.invoice_payload != user_data["payment_id"]:
            await bot.answer_pre_checkout_query(
                pre_checkout_query_id=pre_checkout_query.id,
                ok=False,
                error_message="Ошибка: несоответствие данных платежа."
            )
            return
        
        # Все проверки прошли успешно, подтверждаем pre-checkout
        await bot.answer_pre_checkout_query(
            pre_checkout_query_id=pre_checkout_query.id,
            ok=True
        )
        
    except Exception as e:
        logger.error(f"Error processing pre-checkout query for user {user_id}: {e}", exc_info=True)
        await bot.answer_pre_checkout_query(
            pre_checkout_query_id=pre_checkout_query.id,
            ok=False,
            error_message="Произошла ошибка при обработке платежа. Пожалуйста, попробуйте позже."
        )

async def process_successful_payment(message: types.Message):
    """Обработка успешного платежа"""
    user_id = message.from_user.id
    payment_info = message.successful_payment
    
    try:
        # Получаем данные о заказе
        from bot import dp
        user_data = await dp.storage.get_data(user=user_id)
        
        if not user_data or "order_items" not in user_data:
            logger.error(f"Order data not found for user {user_id} after payment")
            await message.answer("Платеж получен, но возникла проблема с данными заказа. Свяжитесь с поддержкой.")
            return
        
        order_items = user_data.get("order_items", [])
        total_stars = user_data.get("total_cost_stars", 0)
        order_id = None  # Создаем переменную для хранения ID заказа
        
        # Обновляем остатки товаров и создаем заказ в одной транзакции
        with get_database_session() as session:
            # Обновляем остатки товаров на складе
            for item in order_items:
                product_id = item["product_id"]
                quantity = item["quantity"]
                
                # Уменьшаем количество товара на складе
                update_product_stock(product_id, -quantity)  # отрицательное значение для уменьшения
            
            # Создаем запись о заказе в базе данных
            # Создаем заказ
            new_order = Order(
                user_id=user_id,
                total_amount=payment_info.total_amount / 100,  # переводим из сотых долей звезды
                payment_id=payment_info.telegram_payment_charge_id,
                shipping_address=f"{message.from_user.full_name}, {payment_info.order_info.phone_number if hasattr(payment_info, 'order_info') and payment_info.order_info else 'Не указан'}"
            )
            session.add(new_order)
            session.flush()  # чтобы получить ID заказа
            
            # Сохраняем ID заказа для использования вне блока with
            order_id = new_order.id
            
            # Добавляем товары в заказ
            for item in order_items:
                order_item = OrderItem(
                    order_id=order_id,
                    product_id=item["product_id"],
                    quantity=item["quantity"],
                    price=item["price"]
                )
                session.add(order_item)
            
            # Очищаем корзину пользователя
            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            
            session.commit()
        
        # Отправляем уведомление пользователю
        await send_order_success_notification(message, order_id, total_stars)
        
        # Уведомляем администраторов о новом заказе
        await notify_admins_about_order(order_id, message.from_user, total_stars, len(order_items))
        
    except Exception as e:
        logger.error(f"Error processing successful payment for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "Платеж успешно обработан, но возникла ошибка при оформлении заказа. "
            "Пожалуйста, свяжитесь с поддержкой и сообщите номер платежа: "
            f"<code>{payment_info.telegram_payment_charge_id}</code>",
            parse_mode="HTML"
        )