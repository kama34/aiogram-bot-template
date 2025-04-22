from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from services.product_service import get_product_categories
from utils.message_utils import safe_delete_message
from keyboards.user_kb import user_kb

async def show_categories(message: types.Message, edit=False):
    """Показывает список категорий товаров"""
    categories = get_product_categories()
    
    # Создаем клавиатуру с категориями и кнопкой "Все товары"
    categories_kb = types.InlineKeyboardMarkup(row_width=2)
    
    # Добавляем кнопку "Все товары"
    categories_kb.add(types.InlineKeyboardButton("🛍️ Все товары", callback_data="shop_category_all"))
    
    # Добавляем кнопки для каждой категории
    for category in categories:
        categories_kb.add(types.InlineKeyboardButton(
            f"📁 {category}", 
            callback_data=f"shop_category_{category}"
        ))
    
    # Добавляем кнопку для возврата в главное меню
    categories_kb.add(types.InlineKeyboardButton("◀️ В главное меню", callback_data="return_to_main_menu"))
    
    caption = "🏪 <b>Категории товаров</b>\n\nВыберите категорию или просмотрите все товары:"
    
    if edit and hasattr(message, 'edit_text'):
        try:
            await message.edit_text(caption, reply_markup=categories_kb, parse_mode="HTML")
        except:
            await message.answer(caption, reply_markup=categories_kb, parse_mode="HTML")
    else:
        await message.answer(caption, reply_markup=categories_kb, parse_mode="HTML")

async def category_callback(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор категории"""
    await callback.answer()
    
    # Удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Получаем выбранную категорию
    category_data = callback.data.replace("shop_category_", "")
    
    # Импортируем тут для избежания циклического импорта
    from .products import show_products
    
    # Если выбраны все товары, передаем None в качестве категории
    category = None if category_data == "all" else category_data
    
    # Показываем товары из выбранной категории
    await show_products(callback.message, category=category)

async def return_to_main_menu(callback: types.CallbackQuery):
    """Обработчик кнопки возврата в главное меню"""
    await callback.answer()
    
    # Удаляем сообщение магазина
    await safe_delete_message(callback.message)
    
    # Показываем главное меню
    await callback.message.answer(
        "Вы вернулись в главное меню. Выберите действие:",
        reply_markup=user_kb
    )

def register_category_handlers(dp: Dispatcher):
    """Регистрирует обработчики категорий"""
    dp.register_callback_query_handler(
        category_callback, 
        lambda c: c.data and c.data.startswith("shop_category_"),
        state="*"
    )
    
    # Добавляем обработчик возврата в главное меню
    dp.register_callback_query_handler(
        return_to_main_menu,
        lambda c: c.data == "return_to_main_menu",
        state="*"
    )