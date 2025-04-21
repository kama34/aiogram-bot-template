from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from utils.message_utils import safe_delete_message
from utils.message_tracker import MessageTracker

async def select_edit_field(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор поля для редактирования"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    field = callback.data.replace("edit_field_", "")
    
    # Сохраняем выбранное поле в состоянии
    await state.update_data(editing_field=field)
    
    # Удаляем предыдущее сообщение с меню редактирования
    await safe_delete_message(callback.message)
    
    # Определяем текст подсказки в зависимости от поля
    prompts = {
        "name": "📌 Введите новое название товара:",
        "description": "📝 Введите новое описание товара:",
        "price": "💰 Введите новую цену товара (только число):",
        "category": "📁 Введите новую категорию товара:",
        "stock": "🔢 Введите новое количество товара на складе (целое число):"
    }
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_editing"))
    
    # Отправляем сообщение с запросом на редактирование и отслеживаем его
    if field == "image":
        message = await callback.message.answer(
            "🖼 Загрузите новое изображение товара:", 
            reply_markup=keyboard
        )
    else:
        message = await callback.message.answer(
            prompts.get(field, "Введите новое значение:"), 
            reply_markup=keyboard
        )
    
    # Сохраняем сообщение для последующего удаления
    await MessageTracker.add_message_to_state(state, message)
    
    await AdminStates.waiting_for_edited_value.set()

async def cancel_editing(callback: types.CallbackQuery, state: FSMContext):
    """Отменяет текущее редактирование"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Безопасно удаляем сообщение
    await safe_delete_message(callback.message)
    
    async with state.proxy() as data:
        product_id = data["editing_product_id"]
    
    # Возвращаемся к редактированию товара
    callback.data = f"edit_product_{product_id}"
    
    # Импортируем функцию здесь, чтобы избежать циклического импорта
    from .main import edit_product
    await edit_product(callback, state)

def register_field_selection_handlers(dp: Dispatcher):
    """Регистрирует обработчики выбора полей для редактирования"""
    dp.register_callback_query_handler(
        select_edit_field, 
        lambda c: c.data and c.data.startswith("edit_field_"), 
        state=AdminStates.product_editing
    )
    
    dp.register_callback_query_handler(
        cancel_editing, 
        lambda c: c.data == "cancel_editing", 
        state=AdminStates.waiting_for_edited_value
    )