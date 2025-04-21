from aiogram import types, Dispatcher
from services.product_service import get_product_price, get_product_name
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('handlers.shop')

async def menu_command(message: types.Message):
    """Показывает меню с продуктами и их ценами в звездах"""
    # Создаем клавиатуру с продуктами
    products_kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем товары с ценами в звездах
    for product_id in range(1, 5):
        price = get_product_price(product_id)
        products_kb.add(
            types.InlineKeyboardButton(
                f"Продукт {product_id} - {price} ⭐", 
                callback_data=f"product_{product_id}"
            )
        )
    
    await message.answer("Вы перешли в раздел меню, выберите продукт:", reply_markup=products_kb)
    
async def product_callback(callback: types.CallbackQuery):
    """Обработка выбора продукта"""
    product_id = callback.data.replace("product_", "")
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение с меню
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Получаем цену продукта в звездах
    price = get_product_price(product_id)
    
    # Создаем клавиатуру с кнопками действий
    product_kb = types.InlineKeyboardMarkup(row_width=2)
    product_kb.add(
        types.InlineKeyboardButton("🛒 Добавить в корзину", callback_data=f"select_quantity_{product_id}")
    )
    product_kb.add(
        types.InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")
    )
    
    # Отправляем информацию о продукте с кнопками и ценой в звездах
    await callback.message.answer(
        f"Вы выбрали продукт {product_id}.\n\n"
        f"💰 Цена: {price} ⭐\n\n"
        f"Здесь будет подробная информация о продукте.",
        reply_markup=product_kb
    )

async def back_to_menu_callback(callback: types.CallbackQuery):
    """Обработка кнопки возврата в меню"""
    await callback.answer()
    
    try:
        # Удаляем сообщение с информацией о продукте
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Показываем меню снова
    products_kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем товары с ценами
    for product_id in range(1, 5):
        price = get_product_price(product_id)
        products_kb.add(
            types.InlineKeyboardButton(
                f"Продукт {product_id} - {price} ⭐", 
                callback_data=f"product_{product_id}"
            )
        )
    
    await callback.message.answer("Вы перешли в раздел меню, выберите продукт:", reply_markup=products_kb)

async def go_to_menu_callback(callback: types.CallbackQuery):
    """Обработка кнопки перехода в меню из корзины"""
    await callback.answer()
    
    # Удаляем сообщение с корзиной
    try:
        await callback.message.delete()
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Показываем меню с товарами
    await menu_command(callback.message)

def register_shop_handlers(dp: Dispatcher):
    """Регистрация всех обработчиков для функций магазина"""
    # Регистрация обработчика для кнопки меню
    dp.register_message_handler(menu_command, lambda message: message.text == "🛒 Магазин", state="*")
    
    # Регистрация обработчика выбора продукта
    dp.register_callback_query_handler(product_callback, lambda c: c.data.startswith("product_"))
    
    # Регистрация обработчика кнопки "Назад в меню"
    dp.register_callback_query_handler(back_to_menu_callback, lambda c: c.data == "back_to_menu")
    
    # Регистрация обработчика кнопки "Перейти к товарам" в корзине
    dp.register_callback_query_handler(go_to_menu_callback, lambda c: c.data == "go_to_menu")