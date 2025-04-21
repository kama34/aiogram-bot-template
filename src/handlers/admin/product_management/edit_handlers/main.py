from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from utils.admin_utils import is_admin
from utils.message_utils import safe_delete_message
from services.product_service import get_product_by_id

async def edit_product(callback: types.CallbackQuery, state: FSMContext):
    """Инициирует редактирование товара"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Получаем ID товара из callback_data
    product_id = callback.data.replace("edit_product_", "")
    
    # Получаем информацию о товаре
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer(
            "❌ Товар не найден. Возможно, он был удален.", 
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
            )
        )
        return
    
    # Сохраняем ID товара в состоянии
    await state.update_data(editing_product_id=product_id)
    
    # Безопасно удаляем предыдущее сообщение
    await safe_delete_message(callback.message)
    
    # Формируем сообщение с информацией о товаре
    message_text = (
        f"📝 <b>Редактирование товара</b>\n\n"
        f"📌 <b>Название:</b> {product['name']}\n"
        f"📝 <b>Описание:</b> {product['description']}\n"
        f"💰 <b>Цена:</b> {product['price']} ₽\n"
        f"📁 <b>Категория:</b> {product.get('category', 'Не указана')}\n"
        f"🔢 <b>Количество на складе:</b> {product.get('stock', 0)} шт.\n"
    )
    
    # Формируем клавиатуру с опциями редактирования
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📌 Название", callback_data="edit_field_name"),
        types.InlineKeyboardButton("📝 Описание", callback_data="edit_field_description")
    )
    keyboard.add(
        types.InlineKeyboardButton("💰 Цена", callback_data="edit_field_price"),
        types.InlineKeyboardButton("📁 Категория", callback_data="edit_field_category")
    )
    keyboard.add(
        types.InlineKeyboardButton("🖼 Изображение", callback_data="edit_field_image"),
        types.InlineKeyboardButton("🔢 Количество", callback_data="edit_field_stock")
    )
    keyboard.add(
        types.InlineKeyboardButton("🚫 Удалить товар", callback_data=f"delete_product_{product_id}")
    )
    keyboard.add(
        types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
    )
    
    # Если есть изображение, показываем его
    if product.get("image_url"):
        await callback.message.answer_photo(
            photo=product["image_url"],
            caption=message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            message_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    # Устанавливаем состояние
    await AdminStates.product_editing.set()

def register_main_handlers(dp: Dispatcher):
    """Регистрирует основные обработчики для редактирования товара"""
    dp.register_callback_query_handler(
        edit_product, 
        lambda c: c.data and c.data.startswith("edit_product_"), 
        state="*"
    )