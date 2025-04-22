from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from services.database import get_database_session, Order, OrderItem, CartItem
import datetime
from utils.message_utils import safe_delete_message
from utils.logger import setup_logger
from services.product_service import get_product_by_id
from services.inventory_service import decrease_stock

# Setup logger
logger = setup_logger('handlers.order')

class OrderStates(StatesGroup):
    """Состояния для оформления заказа"""
    waiting_for_shipping_address = State()

async def checkout_callback(callback: types.CallbackQuery, state: FSMContext):
    """Начинает процесс оформления заказа"""
    await callback.answer()
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Запрашиваем адрес доставки
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Вернуться к корзине", callback_data="view_cart"))
    
    await callback.message.answer(
        "📦 <b>Оформление заказа</b>\n\n"
        "Пожалуйста, введите адрес доставки:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    
    await OrderStates.waiting_for_shipping_address.set()

async def process_shipping_address(message: types.Message, state: FSMContext):
    """Обрабатывает адрес доставки и оформляет заказ"""
    user_id = message.from_user.id
    shipping_address = message.text
    
    # Сохраняем адрес в состоянии
    await state.update_data(shipping_address=shipping_address)
    
    # Отправляем сообщение о процессе обработки
    status_message = await message.answer("⏳ Обрабатываем ваш заказ...")
    
    try:
        session = get_database_session()
        try:
            # Получаем товары из корзины
            cart_items = session.query(CartItem).filter(CartItem.user_id == user_id).all()
            
            if not cart_items:
                await status_message.edit_text(
                    "❌ Ваша корзина пуста. Невозможно оформить заказ.",
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("🛍️ Перейти в магазин", callback_data="back_to_categories")
                    )
                )
                await state.finish()
                return
            
            # Создаем новый заказ
            new_order = Order(
                user_id=user_id,
                total_amount=0,  # Пока установим 0, потом обновим
                shipping_address=shipping_address,
                status="pending",
                created_at=datetime.datetime.now(),
                updated_at=datetime.datetime.now()
            )
            session.add(new_order)
            session.flush()  # Чтобы получить ID заказа
            
            # Переносим товары из корзины в заказ и обновляем инвентарь
            total_amount = 0
            order_items = []
            inventory_updates = []
            
            for item in cart_items:
                # Получаем информацию о товаре
                product = get_product_by_id(item.product_id)
                
                if product and product.get('stock', 0) >= item.quantity:
                    price = product.get('price', 0)
                    
                    # Создаем элемент заказа
                    order_item = OrderItem(
                        order_id=new_order.id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        price=price
                    )
                    session.add(order_item)
                    order_items.append({
                        'name': product.get('name', f'Товар #{item.product_id}'),
                        'quantity': item.quantity,
                        'price': price,
                        'total': price * item.quantity
                    })
                    
                    # Обновляем общую сумму
                    total_amount += price * item.quantity
                    
                    # ИСПРАВЛЕНО: Корректно рассчитываем новое количество
                    current_stock = product.get('stock', 0)
                    inventory_updates.append({
                        'product_id': item.product_id,
                        'quantity_to_subtract': item.quantity  # Сохраняем количество для вычитания
                    })
            
            # Обновляем общую сумму заказа
            new_order.total_amount = total_amount
            
            # Очищаем корзину
            session.query(CartItem).filter(CartItem.user_id == user_id).delete()
            
            # Сохраняем изменения в БД
            session.commit()
            
            # Формируем сообщение с информацией о заказе
            order_message = (
                f"📝 <b>Подтверждение заказа</b>\n\n"
                f"📋 <b>Номер заказа:</b> #{new_order.id}\n"
                f"🏠 <b>Адрес доставки:</b> {shipping_address}\n\n"
                f"<b>Товары в заказе:</b>\n"
            )
            
            for item in order_items:
                order_message += (
                    f"• {item['name']} - {item['quantity']} шт. × {item['price']} ⭐️ = {item['total']} ⭐️\n"
                )
            
            order_message += f"\n<b>Всего товаров:</b> {sum(item['quantity'] for item in order_items)}\n"
            order_message += f"<b>Итоговая стоимость:</b> {total_amount} ⭐️"
            
            # Клавиатура для просмотра заказов или возврата в магазин
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("🛍️ Вернуться в магазин", callback_data="back_to_categories"))
            
            await status_message.edit_text(
                order_message,
                parse_mode="HTML",
                reply_markup=keyboard
            )
            
            # Обновляем инвентарь после успешного создания заказа
            for update in inventory_updates:
                try:
                    product_id = update['product_id']
                    quantity = update['quantity_to_subtract']
                    
                    # Используем новую функцию для уменьшения запаса
                    decrease_stock(product_id, quantity)
                    
                except Exception as e:
                    logger.error(f"Error updating inventory for product {update['product_id']}: {e}", exc_info=True)
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating order: {e}", exc_info=True)
            await status_message.edit_text(
                "❌ Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже.",
                reply_markup=types.InlineKeyboardMarkup().add(
                    types.InlineKeyboardButton("◀️ Вернуться к корзине", callback_data="view_cart")
                )
            )
        finally:
            session.close()
    
    except Exception as e:
        logger.error(f"Error processing order: {e}", exc_info=True)
        await status_message.edit_text(
            "❌ Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ Вернуться к корзине", callback_data="view_cart")
            )
        )
    
    await state.finish()

def register_order_handlers(dp: Dispatcher):
    """Регистрация обработчиков для заказов"""
    dp.register_callback_query_handler(checkout_callback, lambda c: c.data == "checkout", state="*")
    dp.register_message_handler(process_shipping_address, state=OrderStates.waiting_for_shipping_address)