import traceback
from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from handlers.admin.states import AdminStates
from services.product_service import create_product, update_product_stock
from utils.message_utils import safe_delete_message

async def confirm_product_creation(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает подтверждение создания товара"""
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await safe_delete_message(callback.message)
    
    async with state.proxy() as data:
        name = data['product_name']
        description = data['product_description']
        price = data['product_price']
        image_url = data.get('product_image')
        category = data.get('product_category')
        stock = data['product_stock']
    
    # Отправляем сообщение о процессе
    processing_message = await callback.message.answer("⏱ Создаем товар...")
    
    try:
        # Создаем товар
        product_id = create_product(name, description, price, image_url, category)
        
        if product_id:
            # Обновляем количество товара
            stock_success = update_product_stock(product_id, stock)
            
            # Удаляем сообщение о процессе
            await safe_delete_message(processing_message)
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ К управлению товарами", callback_data="manage_products"))
            
            if stock_success:
                success_text = f"✅ Товар успешно создан!\n\nID товара: <code>{product_id}</code>"
            else:
                success_text = f"✅ Товар создан, но не удалось установить количество.\n\nID товара: <code>{product_id}</code>"
            
            await callback.message.answer(
                success_text, 
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Удаляем сообщение о процессе
            await safe_delete_message(processing_message)
            
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ К управлению товарами", callback_data="manage_products"))
            
            await callback.message.answer(
                "❌ Ошибка при создании товара. Пожалуйста, попробуйте снова.", 
                reply_markup=keyboard
            )
    except Exception as e:
        # Удаляем сообщение о процессе
        await safe_delete_message(processing_message)
        
        print(f"Error creating product: {e}")
        traceback.print_exc()
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ К управлению товарами", callback_data="manage_products"))
        
        await callback.message.answer(
            f"❌ Произошла ошибка при создании товара: {str(e)[:100]}...", 
            reply_markup=keyboard
        )
    
    await state.finish()

def register_confirmation_handlers(dp: Dispatcher):
    """Регистрирует обработчики для подтверждения создания товара"""
    dp.register_callback_query_handler(
        confirm_product_creation, 
        lambda c: c.data == "confirm_product_creation", 
        state=AdminStates.product_creation_confirmation
    )