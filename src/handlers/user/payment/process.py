from aiogram import types
from aiogram.types import LabeledPrice
import uuid

from services.product_service import get_product_stock
from config import PAYMENT_PROVIDER_TOKEN, PAYMENT_CURRENCY
from utils.logger import setup_logger

# Настройка логгера для этого модуля
logger = setup_logger('handlers.payment.process')

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