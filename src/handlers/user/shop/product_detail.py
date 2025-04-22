from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from services.product_service import get_product_by_id
from utils.message_utils import safe_delete_message
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('handlers.shop.product_detail')

async def show_product_detail(callback: types.CallbackQuery):
    """Показывает детальную информацию о товаре"""
    await callback.answer()
    
    # Получаем ID товара
    product_id = int(callback.data.replace("product_", ""))
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Получаем данные о товаре
    product = get_product_by_id(product_id)
    
    if not product:
        # Если товар не найден
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ К списку товаров", callback_data="back_to_categories"))
        
        await callback.message.answer(
            "❌ <b>Товар не найден</b>\n\n"
            "К сожалению, данный товар недоступен или был удален.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Формируем клавиатуру с кнопками действий
    product_kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Кнопка добавления в корзину
    if product.get('stock', 0) > 0:
        product_kb.add(
            types.InlineKeyboardButton(
                "🛒 Добавить в корзину", 
                callback_data=f"select_quantity_{product_id}"
            )
        )
    else:
        product_kb.add(
            types.InlineKeyboardButton(
                "❌ Нет в наличии", 
                callback_data="product_not_available"
            )
        )
    
    # Навигационные кнопки
    product_kb.row(
        types.InlineKeyboardButton("◀️ К списку товаров", callback_data="back_to_products"),
        types.InlineKeyboardButton("🛒 Корзина", callback_data="view_cart")
    )
    
    # Формируем текст с информацией о товаре
    product_text = (
        f"<b>{product['name']}</b>\n\n"
        f"{product['description']}\n\n"
        f"💰 <b>Цена:</b> {product['price']} ⭐\n"
        f"🔢 <b>В наличии:</b> {product.get('stock', 0)} шт.\n"
    )
    
    if product.get('category'):
        product_text += f"📁 <b>Категория:</b> {product['category']}\n"
    
    # Отправляем сообщение с информацией о товаре
    if product.get('image_url'):
        # С изображением
        await callback.message.answer_photo(
            photo=product['image_url'],
            caption=product_text,
            reply_markup=product_kb,
            parse_mode="HTML"
        )
    else:
        # Без изображения
        await callback.message.answer(
            product_text,
            reply_markup=product_kb,
            parse_mode="HTML"
        )

async def back_to_products_callback(callback: types.CallbackQuery):
    """Возврат к списку товаров"""
    await callback.answer()
    
    # Удаляем текущее сообщение
    await safe_delete_message(callback.message)
    
    # Используем импорт внутри функции для избежания циклических импортов
    from .products import show_products
    
    # Возвращаемся к списку товаров
    await show_products(callback.message)

async def product_not_available_callback(callback: types.CallbackQuery):
    """Обработка клика по кнопке 'Нет в наличии'"""
    await callback.answer("Извините, данный товар временно отсутствует на складе", show_alert=True)

async def select_quantity_callback(callback: types.CallbackQuery):
    """Показывает выбор количества товара"""
    product_id = callback.data.replace("select_quantity_", "")
    await callback.answer()
    
    try:
        # Удаляем предыдущее сообщение
        await safe_delete_message(callback.message)
    except Exception as e:
        logger.error(f"Error deleting message: {e}", exc_info=True)
    
    # Получаем информацию о товаре для отображения названия
    try:
        product = get_product_by_id(int(product_id))
        product_name = product['name'] if product else f"Товар {product_id}"
        
        # Создаем клавиатуру с выбором количества
        quantity_kb = types.InlineKeyboardMarkup(row_width=5)
        quantity_buttons = []
        
        # Ограничиваем максимальное количество доступным на складе
        max_quantity = min(5, product['stock'])
        
        for i in range(1, max_quantity + 1):  # Количество от 1 до max_quantity
            quantity_buttons.append(
                types.InlineKeyboardButton(str(i), callback_data=f"add_qty_{product_id}_{i}")
            )
        
        quantity_kb.add(*quantity_buttons)
        quantity_kb.add(types.InlineKeyboardButton("◀️ Назад", callback_data=f"product_{product_id}"))
        
        await callback.message.answer(f"Выберите количество товара \"{product_name}\":", reply_markup=quantity_kb)
    except Exception as e:
        logger.error(f"Error showing quantity selection: {e}", exc_info=True)
        await callback.message.answer(
            "Произошла ошибка при выборе количества товара.",
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К категориям", callback_data="back_to_categories")
            )
        )

def register_product_detail_handlers(dp: Dispatcher):
    """Регистрирует обработчики детальной информации о товаре"""
    dp.register_callback_query_handler(
        show_product_detail, 
        lambda c: c.data and c.data.startswith("product_") and not c.data == "product_not_available",
        state="*"
    )
    
    dp.register_callback_query_handler(
        back_to_products_callback, 
        lambda c: c.data == "back_to_products",
        state="*"
    )
    
    dp.register_callback_query_handler(
        product_not_available_callback, 
        lambda c: c.data == "product_not_available",
        state="*"
    )
    
    dp.register_callback_query_handler(
        select_quantity_callback, 
        lambda c: c.data and c.data.startswith("select_quantity_"),
        state="*"
    )