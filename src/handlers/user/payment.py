from aiogram import types, Dispatcher
from aiogram.types import LabeledPrice, PreCheckoutQuery
from datetime import datetime
from math import ceil
import uuid

from services.database import get_database_session, CartItem, Order, OrderItem
from services.product_service import get_product_price, get_product_name, get_product_stock, update_product_stock
from config import PAYMENT_PROVIDER_TOKEN, PAYMENT_CURRENCY, ADMIN_IDS
from utils.logger import setup_logger

# Setup logger for this module
logger = setup_logger('handlers.payment')

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

async def pay_with_stars_callback(callback: types.CallbackQuery):
    """Обработка оплаты звездами Telegram"""
    user_id = callback.from_user.id
    await callback.answer()
    
    try:
        # Получаем сохраненные данные о заказе
        from bot import dp, bot
        
        user_data = await dp.storage.get_data(user=user_id)
        
        if not user_data or "total_cost_stars" not in user_data:
            await callback.message.answer("Ошибка: данные заказа не найдены. Пожалуйста, попробуйте снова.")
            return
        
        order_items = user_data.get("order_items", [])
        # Цена уже в звездах, конвертировать не нужно
        total_stars = user_data.get("total_cost_stars", 0)
        
        # Проверяем доступность товаров перед оплатой
        out_of_stock_items = []
        for item in order_items:
            available_stock = get_product_stock(item["product_id"])
            if available_stock < item["quantity"]:
                out_of_stock_items.append(f"{item['name']} (доступно: {available_stock} шт.)")
        
        if out_of_stock_items:
            # Если есть товары, которых нет в наличии
            error_text = "⚠️ <b>Некоторые товары отсутствуют в нужном количестве:</b>\n\n"
            error_text += "\n".join([f"• {item}" for item in out_of_stock_items])
            error_text += "\n\nПожалуйста, вернитесь в корзину и обновите заказ."
            
            await callback.message.answer(
                error_text,
                parse_mode="HTML",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("🧺 Вернуться в корзину", callback_data="view_cart")
                )
            )
            return
        
        # Для звезд используем одну общую позицию
        # Создаем уникальный идентификатор платежа
        payment_id = f"order_{user_id}_{uuid.uuid4().hex[:8]}"
        
        # Сохраняем ID платежа и сумму в звездах
        user_data["payment_id"] = payment_id
        user_data["total_cost_stars"] = total_stars
        await dp.storage.set_data(user=user_id, data=user_data)
        
        # Отправляем счет на оплату звездами
        await bot.send_invoice(
            chat_id=user_id,
            title=f"Оплата {total_stars} ⭐",
            description=f"Пожалуйста, завершите оплату в размере {total_stars} звезд для оформления заказа.",
            payload=payment_id,
            provider_token=PAYMENT_PROVIDER_TOKEN,
            currency=PAYMENT_CURRENCY,
            prices=[LabeledPrice(
                label=f"Оплата {total_stars} ⭐",
                amount=int(total_stars)
            )],
            start_parameter="stars_payment",
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            is_flexible=False
        )
        
    except Exception as e:
        logger.error(f"Error initiating payment for user {user_id}: {e}", exc_info=True)
        await callback.message.answer(
            f"Произошла ошибка при инициализации платежа: {str(e)}. Пожалуйста, попробуйте позже."
        )

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
        from bot import dp, bot
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
        
        # Отправляем сообщение о успешном заказе
        success_message = (
            "🎉 <b>Ваш заказ оформлен!</b>\n\n"
            f"Номер заказа: <code>{order_id}</code>\n"  # Используем сохраненный ID
            f"Оплачено: {total_stars} ⭐\n"
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            "Спасибо за покупку! Мы свяжемся с вами для уточнения деталей доставки."
        )
        
        # Создаем клавиатуру с дополнительными действиями
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("🛒 Перейти в магазин", callback_data="go_to_menu")
        )
        
        await message.answer(success_message, parse_mode="HTML", reply_markup=keyboard)
        
        # Уведомляем администраторов о новом заказе
        admin_notification = (
            "🔔 <b>Новый заказ!</b>\n\n"
            f"Заказ №: <code>{order_id}</code>\n"
            f"Пользователь: {message.from_user.full_name} (@{message.from_user.username})\n"
            f"ID пользователя: {user_id}\n"
            f"Оплачено: {total_stars} ⭐\n"
            f"Товаров: {len(order_items)}\n\n"
            "Детали заказа доступны в панели администратора."
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=admin_notification,
                    parse_mode="HTML"
                )
            except Exception as e:
                logger.error(f"Failed to notify admin {admin_id} about new order: {e}")
        
    except Exception as e:
        logger.error(f"Error processing successful payment for user {user_id}: {e}", exc_info=True)
        await message.answer(
            "Платеж успешно обработан, но возникла ошибка при оформлении заказа. "
            "Пожалуйста, свяжитесь с поддержкой и сообщите номер платежа: "
            f"<code>{payment_info.telegram_payment_charge_id}</code>",
            parse_mode="HTML"
        )

def register_payment_handlers(dp: Dispatcher):
    """Регистрация обработчиков платежей"""
    # Регистрация обработчика оформления заказа
    dp.register_callback_query_handler(checkout_callback, lambda c: c.data == "checkout")
    
    # Регистрация обработчика оплаты звездами
    dp.register_callback_query_handler(pay_with_stars_callback, lambda c: c.data == "pay_with_stars")
    
    # Регистрация обработчиков для Telegram Payments
    dp.register_pre_checkout_query_handler(process_pre_checkout_query)
    dp.register_message_handler(process_successful_payment, content_types=types.ContentTypes.SUCCESSFUL_PAYMENT)