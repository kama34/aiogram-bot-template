from aiogram import types
from datetime import datetime
from config import ADMIN_IDS
from utils.logger import setup_logger

# Настройка логгера для этого модуля
logger = setup_logger('handlers.payment.notifications')

async def send_order_success_notification(message: types.Message, order_id: int, total_stars: float):
    """Отправляет уведомление пользователю о успешном заказе"""
    # Отправляем сообщение о успешном заказе
    success_message = (
        "🎉 <b>Ваш заказ оформлен!</b>\n\n"
        f"Номер заказа: <code>{order_id}</code>\n"
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

async def notify_admins_about_order(order_id: int, user, total_stars: float, items_count: int):
    """Уведомляет администраторов о новом заказе"""
    from bot import bot
    
    admin_notification = (
        "🔔 <b>Новый заказ!</b>\n\n"
        f"Заказ №: <code>{order_id}</code>\n"
        f"Пользователь: {user.full_name} (@{user.username})\n"
        f"ID пользователя: {user.id}\n"
        f"Оплачено: {total_stars} ⭐\n"
        f"Товаров: {items_count}\n\n"
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