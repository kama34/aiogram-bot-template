from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from sqlalchemy import func
from services.database import get_database_session, User
from utils.admin_utils import is_admin
from ..core import AdminStates

async def letter_select_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор буквы для просмотра пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("У вас нет прав доступа!", show_alert=True)
        return
    
    try:
        await callback.answer()
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    callback_data = callback.data
    
    if not callback_data.startswith("letter_") or len(callback_data) < 8:
        print(f"Invalid letter selection: {callback_data}")
        return
    
    letter = callback_data.replace("letter_", "")
    
    if len(letter) != 1:
        print(f"Invalid letter: {letter}")
        return
    
    await state.update_data(letter=letter, page=0)
    
    await callback.message.delete()
    
    await show_users_by_letter(callback.message, letter, 0, state)

async def show_users_by_letter(message, letter, page, state):
    """Показывает пользователей с именами, начинающимися на указанную букву"""
    session = get_database_session()
    try:
        users_query = session.query(User).filter(
            func.upper(func.substr(User.username, 1, 1)) == letter.upper()
        ).order_by(User.username)
        
        total_users = users_query.count()
        
        users_per_page = 7
        total_pages = max(1, (total_users + users_per_page - 1) // users_per_page)
        
        page = max(0, min(page, total_pages - 1))
        
        await state.update_data(page=page)
        
        users = users_query.offset(page * users_per_page).limit(users_per_page).all()
        
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        
        for user in users:
            display_name = f"{user.full_name} (@{user.username})"
            keyboard.add(types.InlineKeyboardButton(
                display_name, callback_data=f"view_user_{user.id}"
            ))
        
        nav_buttons = []
        
        if page > 0:
            nav_buttons.append(types.InlineKeyboardButton(
                "⬅️ Назад", callback_data="prev_page"
            ))
        
        nav_buttons.append(types.InlineKeyboardButton(
            f"{page + 1}/{total_pages}", callback_data="page_info"
        ))
        
        if page < total_pages - 1:
            nav_buttons.append(types.InlineKeyboardButton(
                "➡️ Далее", callback_data="next_page"
            ))
        
        keyboard.row(*nav_buttons)
        
        keyboard.add(types.InlineKeyboardButton("🔤 К выбору буквы", callback_data="letter_search"))
        keyboard.add(types.InlineKeyboardButton("🏠 В главное меню", callback_data="admin_back"))
        
        await message.answer(
            f"Пользователи на букву '{letter}':\n"
            f"Страница {page + 1} из {total_pages}",
            reply_markup=keyboard
        )
        
        await AdminStates.browsing_users_by_letter.set()
        
    except Exception as e:
        await message.answer(f"Ошибка при получении списка пользователей: {str(e)}")
    finally:
        session.close()

async def page_info_handler(callback: types.CallbackQuery, state: FSMContext):
    """Показывает информацию о текущей странице"""
    await callback.answer("Текущая страница", show_alert=True)

async def prev_page_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик перехода на предыдущую страницу"""
    data = await state.get_data()
    letter = data.get('letter', 'A')
    page = max(0, data.get('page', 0) - 1)
    
    await callback.message.delete()
    await show_users_by_letter(callback.message, letter, page, state)

async def next_page_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик перехода на следующую страницу"""
    data = await state.get_data()
    letter = data.get('letter', 'A')
    page = data.get('page', 0) + 1
    
    await callback.message.delete()
    await show_users_by_letter(callback.message, letter, page, state)

def register_pagination_handlers(dp: Dispatcher):
    """Регистрирует обработчики для пагинации"""
    dp.register_callback_query_handler(letter_select_handler, lambda c: c.data.startswith("letter_"), 
                                      state=AdminStates.browsing_letters)
    dp.register_callback_query_handler(page_info_handler, lambda c: c.data == "page_info", 
                                      state=AdminStates.browsing_users_by_letter)
    dp.register_callback_query_handler(prev_page_handler, lambda c: c.data == "prev_page", 
                                      state=AdminStates.browsing_users_by_letter)
    dp.register_callback_query_handler(next_page_handler, lambda c: c.data == "next_page", 
                                      state=AdminStates.browsing_users_by_letter)