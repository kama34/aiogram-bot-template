from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from sqlalchemy import func
from services.database import get_database_session, User
from utils.admin_utils import is_admin
from ..states import AdminStates
from .display import show_user_info

async def text_search_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает поиск пользователя по тексту"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    await callback.message.delete()
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="search_user"))
    await callback.message.answer("Введите имя пользователя (username) для поиска или userid:", reply_markup=keyboard)
    
    await AdminStates.waiting_for_search.set()

async def letter_search_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает поиск пользователя по первой букве"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    current_state = await state.get_state()
    if current_state is not None:
        await state.finish()
    
    await callback.message.delete()
    
    session = get_database_session()
    try:
        users = session.query(User).all()
        
        first_letters = set()
        for user in users:
            if user.username and len(user.username) > 0:
                first_letters.add(user.username[0].upper())
        
        first_letters = sorted(list(first_letters))
        
        keyboard = types.InlineKeyboardMarkup(row_width=4)
        letter_buttons = []
        
        for letter in first_letters:
            letter_buttons.append(types.InlineKeyboardButton(letter, callback_data=f"letter_{letter}"))
        
        for i in range(0, len(letter_buttons), 4):
            row_buttons = letter_buttons[i:i+4]
            keyboard.row(*row_buttons)
        
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="search_user"))
        
        await callback.message.answer("Выберите первую букву имени пользователя:", reply_markup=keyboard)
        
        await AdminStates.browsing_letters.set()
        
    except Exception as e:
        await callback.message.answer(f"Ошибка при получении списка пользователей: {str(e)}")
    finally:
        session.close()

async def search_user(message: types.Message, state: FSMContext):
    """Поиск пользователя по имени/ID"""
    search_query = message.text.strip()
    session = get_database_session()
    
    try:
        user = session.query(User).filter(
            (func.lower(User.username) == func.lower(search_query)) |
            (func.lower(User.full_name).like(f"%{search_query.lower()}%")) |
            (User.id == search_query if search_query.isdigit() else False)
        ).first()

        if user:
            await show_user_info(message, user, back_callback="admin_back")
        else:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
            await message.answer("Пользователь не найден.", reply_markup=keyboard)
        
        await state.finish()
        
    except Exception as e:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        await message.answer(f"Ошибка при поиске пользователя: {str(e)}", reply_markup=keyboard)
        await state.finish()
    finally:
        session.close()

def register_search_handlers(dp: Dispatcher):
    """Регистрирует обработчики поиска пользователей"""
    dp.register_message_handler(search_user, state=AdminStates.waiting_for_search)
    dp.register_callback_query_handler(letter_search_handler, lambda c: c.data == "letter_search")