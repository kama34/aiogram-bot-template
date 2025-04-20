from aiogram import types
from aiogram.dispatcher import FSMContext

async def create_error_message(message: types.Message, error_text: str, state: FSMContext = None):
    """
    Создаёт сообщение об ошибке с кнопкой возврата в меню управления каналами
    
    Args:
        message: Исходное сообщение
        error_text: Текст ошибки для отображения
        state: Объект состояния FSMContext, если нужно очистить состояние
    """
    # Если передан state, очищаем состояние
    if state:
        current_state = await state.get_state()
        if current_state:
            await state.finish()
    
    # Создаём клавиатуру с кнопкой возврата в меню
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Вернуться в меню", callback_data="return_to_channels_menu"))
    
    # Отправляем сообщение с ошибкой
    await message.answer(
        f"⚠️ {error_text}",
        reply_markup=keyboard
    )

async def return_to_channels_menu_handler(callback: types.CallbackQuery):
    """
    Универсальный обработчик для возврата в меню управления каналами
    """
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")
    
    try:
        # Удаляем текущее сообщение
        await callback.message.delete()
    except Exception as e:
        print(f"Не удалось удалить сообщение: {e}")
    
    # Импортируем здесь, чтобы избежать циклических импортов
    from .channels import manage_channels_menu
    
    # Показываем меню управления каналами
    await manage_channels_menu(callback.message)