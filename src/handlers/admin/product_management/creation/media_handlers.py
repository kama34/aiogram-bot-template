from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from utils.message_utils import safe_delete_message
from .utils import process_category_input

async def process_product_image(message: types.Message, state: FSMContext):
    """Обрабатывает загрузку изображения товара"""
    if message.photo:
        # Берем последнее фото (с наилучшим качеством)
        photo = message.photo[-1]
        file_id = photo.file_id
        
        async with state.proxy() as data:
            data['product_image'] = file_id
        
        await process_category_input(message, state)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(
            types.InlineKeyboardButton("⏩ Пропустить", callback_data="skip_product_image"),
            types.InlineKeyboardButton("◀️ Отмена", callback_data="cancel_state")
        )
        
        await message.answer(
            "❌ Пожалуйста, отправьте изображение или нажмите 'Пропустить':", 
            reply_markup=keyboard
        )

async def skip_product_image(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик пропуска загрузки изображения"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await safe_delete_message(callback.message)
    
    async with state.proxy() as data:
        data['product_image'] = None
    
    await process_category_input(callback.message, state)

def register_media_handlers(dp: Dispatcher):
    """Регистрирует обработчики для работы с медиа-контентом товара"""
    dp.register_message_handler(
        process_product_image, 
        content_types=types.ContentTypes.PHOTO, 
        state=AdminStates.waiting_for_product_image
    )
    
    dp.register_callback_query_handler(
        skip_product_image, 
        lambda c: c.data == "skip_product_image", 
        state=AdminStates.waiting_for_product_image
    )