from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from services.product_service import get_active_products
from utils.message_utils import safe_delete_message
from utils.logger import setup_logger

# Setup logger
logger = setup_logger('handlers.shop.products')

async def show_products(message: types.Message, category=None, page=0):
    """
    Отображает список товаров с пагинацией
    
    Args:
        message: Объект сообщения
        category: Категория товаров (или None для всех)
        page: Номер страницы (начиная с 0)
    """
    # Настройки пагинации
    products_per_page = 8
    offset = page * products_per_page
    
    # Получаем товары для указанной страницы и категории
    products = get_active_products(
        category=category, 
        limit=products_per_page, 
        offset=offset
    )
    
    # Если нет товаров
    if not products:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ К категориям", callback_data="back_to_categories"))
        
        await message.answer(
            "😔 <b>Нет доступных товаров</b>\n\n"
            "В данной категории пока нет товаров или они отсутствуют на складе.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Создаем клавиатуру с товарами
    products_kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем товары в клавиатуру
    product_buttons = []
    for product in products:
        product_buttons.append(types.InlineKeyboardButton(
            f"{product['name']} - {product['price']} ⭐", 
            callback_data=f"product_{product['id']}"
        ))
    
    # Добавляем кнопки товаров в сетку по 2 в ряд
    for i in range(0, len(product_buttons), 2):
        if i + 1 < len(product_buttons):
            products_kb.row(product_buttons[i], product_buttons[i+1])
        else:
            products_kb.add(product_buttons[i])
    
    # Добавляем пагинацию, если товаров много
    # Здесь нужна дополнительная проверка есть ли больше товаров
    check_more = get_active_products(
        category=category, 
        limit=1, 
        offset=offset + products_per_page
    )
    
    navigation_buttons = []
    
    if page > 0:
        category_param = f"_{category}" if category else ""
        navigation_buttons.append(
            types.InlineKeyboardButton("⬅️ Назад", callback_data=f"shop_page_{page-1}{category_param}")
        )
    
    if check_more:
        category_param = f"_{category}" if category else ""
        navigation_buttons.append(
            types.InlineKeyboardButton("➡️ Вперед", callback_data=f"shop_page_{page+1}{category_param}")
        )
    
    # Добавляем кнопки навигации
    if navigation_buttons:
        products_kb.row(*navigation_buttons)
    
    # Добавляем кнопку возврата к категориям
    products_kb.add(types.InlineKeyboardButton("◀️ К категориям", callback_data="back_to_categories"))
    # Добавляем кнопку корзины
    products_kb.add(types.InlineKeyboardButton("🛒 Корзина", callback_data="view_cart"))
    
    # Формируем заголовок
    category_title = f"📁 Категория: {category}" if category else "🛍️ Все товары"
    
    await message.answer(
        f"{category_title}\n\n"
        "Выберите товар для просмотра подробной информации:",
        reply_markup=products_kb
    )

async def pagination_callback(callback: types.CallbackQuery):
    """Обработка пагинации товаров"""
    await callback.answer()
    
    # Получаем данные о странице и возможной категории
    data_parts = callback.data.replace("shop_page_", "").split("_")
    page = int(data_parts[0])
    category = data_parts[1] if len(data_parts) > 1 else None
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Показываем следующую страницу
    await show_products(callback.message, category=category, page=page)

async def back_to_categories_callback(callback: types.CallbackQuery):
    """Обработка возврата к категориям"""
    await callback.answer()
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Импортируем здесь для избежания циклического импорта
    from .categories import show_categories
    
    # Показываем категории
    await show_categories(callback.message)

def register_products_handlers(dp: Dispatcher):
    """Регистрирует обработчики товаров"""
    dp.register_callback_query_handler(
        pagination_callback, 
        lambda c: c.data and c.data.startswith("shop_page_"),
        state="*"
    )
    
    dp.register_callback_query_handler(
        back_to_categories_callback, 
        lambda c: c.data == "back_to_categories",
        state="*"
    )