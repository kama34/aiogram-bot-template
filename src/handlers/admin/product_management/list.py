from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils.admin_utils import is_admin
from services.product_service import get_all_products, get_product_by_id
from utils.message_utils import safe_delete_message  # Добавляем импорт

async def show_product_list(callback: types.CallbackQuery, state: FSMContext, page=0):
    """Отображает список товаров с пагинацией"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Заменяем прямое удаление на безопасное
    await safe_delete_message(callback.message)
    
    # Получаем все товары
    products = get_all_products(include_inactive=False)
    
    if not products:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("➕ Создать товар", callback_data="create_product"),
            types.InlineKeyboardButton("◀️ Назад", callback_data="manage_products")
        )
        
        await callback.message.answer(
            "📋 <b>Список товаров</b>\n\n"
            "В базе данных нет активных товаров.", 
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Настройки пагинации
    products_per_page = 5
    total_pages = (len(products) + products_per_page - 1) // products_per_page
    
    # Проверка корректности страницы
    page = max(0, min(page, total_pages - 1))
    
    # Выбираем товары для текущей страницы
    start_idx = page * products_per_page
    end_idx = min(start_idx + products_per_page, len(products))
    current_products = products[start_idx:end_idx]
    
    # Формируем сообщение
    message_text = f"📋 <b>Список товаров</b> (страница {page + 1} из {total_pages})\n\n"
    
    for i, product in enumerate(current_products, start=start_idx + 1):
        stock_info = f"({product.get('stock', 0)} шт.)" if product.get('stock') is not None else ""
        message_text += (
            f"{i}. <b>{product['name']}</b> - {product['price']} ₽ {stock_info}\n"
            f"   Категория: {product.get('category', 'Не указана')}\n"
        )
    
    # Формируем клавиатуру
    keyboard = types.InlineKeyboardMarkup(row_width=3)
    
    # Кнопки для пагинации
    pagination_buttons = []
    
    if page > 0:
        pagination_buttons.append(
            types.InlineKeyboardButton("⬅️", callback_data=f"products_page_{page-1}")
        )
    
    pagination_buttons.append(
        types.InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="ignore")
    )
    
    if page < total_pages - 1:
        pagination_buttons.append(
            types.InlineKeyboardButton("➡️", callback_data=f"products_page_{page+1}")
        )
    
    if pagination_buttons:
        keyboard.row(*pagination_buttons)
    
    # Кнопки для выбора товаров
    for product in current_products:
        keyboard.add(types.InlineKeyboardButton(
            f"✏️ {product['name']} ({product['price']} ₽)",
            callback_data=f"edit_product_{product['id']}"
        ))
    
    # Кнопки навигации
    keyboard.row(
        types.InlineKeyboardButton("➕ Создать", callback_data="create_product"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="manage_products")
    )
    
    await callback.message.answer(
        message_text, 
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def handle_pagination(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает навигацию по страницам товаров"""
    page = int(callback.data.replace("products_page_", ""))
    await show_product_list(callback, state, page)

def register_list_handlers(dp: Dispatcher):
    """Регистрирует обработчики для отображения списка товаров"""
    dp.register_callback_query_handler(
        show_product_list, 
        lambda c: c.data == "list_products", 
        state="*"
    )
    
    dp.register_callback_query_handler(
        handle_pagination, 
        lambda c: c.data and c.data.startswith("products_page_"), 
        state="*"
    )