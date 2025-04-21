from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils.message_utils import safe_delete_message
from services.product_service import get_product_by_id, delete_product

async def confirm_delete_product(callback: types.CallbackQuery, state: FSMContext):
    """Подтверждение удаления товара"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await safe_delete_message(callback.message)
    
    # Получаем ID товара из callback_data
    product_id = callback.data.replace("delete_product_", "")
    
    # Получаем информацию о товаре
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.message.answer(
            "❌ Товар не найден. Возможно, он был уже удален.", 
            reply_markup=types.InlineKeyboardMarkup().add(
                types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products")
            )
        )
        return
    
    # Запрашиваем подтверждение удаления
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("✅ Подтвердить удаление", callback_data=f"confirm_delete_{product_id}"),
        types.InlineKeyboardButton("❌ Отменить", callback_data=f"edit_product_{product_id}")
    )
    
    await callback.message.answer(
        f"⚠️ <b>Вы действительно хотите удалить товар?</b>\n\n"
        f"<b>{product['name']}</b> - {product['price']} ₽\n\n"
        f"Это действие нельзя отменить!",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def delete_product_handler(callback: types.CallbackQuery, state: FSMContext):
    """Удаляет товар после подтверждения"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await safe_delete_message(callback.message)
    
    # Получаем ID товара из callback_data
    product_id = callback.data.replace("confirm_delete_", "")
    
    # Удаляем товар
    success = delete_product(product_id)
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ К списку товаров", callback_data="list_products"))
    
    if success:
        await callback.message.answer(
            "✅ Товар успешно удален!", 
            reply_markup=keyboard
        )
    else:
        await callback.message.answer(
            "❌ Ошибка при удалении товара!", 
            reply_markup=keyboard
        )
    
    await state.finish()

def register_deletion_handlers(dp: Dispatcher):
    """Регистрирует обработчики для удаления товаров"""
    dp.register_callback_query_handler(
        confirm_delete_product, 
        lambda c: c.data and c.data.startswith("delete_product_"), 
        state="*"
    )
    
    dp.register_callback_query_handler(
        delete_product_handler, 
        lambda c: c.data and c.data.startswith("confirm_delete_"), 
        state="*"
    )