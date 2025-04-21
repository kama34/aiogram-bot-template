from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from utils.admin_utils import is_admin

async def back_to_search_options(callback: types.CallbackQuery, state: FSMContext, skip_message_delete=False):
    """
    Обработчик для возврата к опциям поиска из любого состояния
    """
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Ошибка при ответе на callback: {e}")
    
    # Сбрасываем текущее состояние
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    # Удаляем текущее сообщение если нужно
    if not skip_message_delete:
        try:
            await callback.message.delete()
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")
    
    # Показываем варианты поиска
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(
        types.InlineKeyboardButton("🔍 Поиск по имени/ID", callback_data="text_search"),
        types.InlineKeyboardButton("🔤 Поиск по букве", callback_data="letter_search")
    )
    keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
    await callback.message.answer("Выберите метод поиска пользователя:", reply_markup=keyboard)

def register_navigation_handlers(dp: Dispatcher):
    """Регистрирует навигационные обработчики для админ-панели"""
    dp.register_callback_query_handler(
        back_to_search_options,
        lambda c: c.data == "search_user",
        state="*"
    )