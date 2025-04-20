# import asyncio
# from aiogram import Dispatcher, types
# from aiogram.dispatcher import FSMContext
# from sqlalchemy import func, desc, text
# from services.database import get_database_session, User
# from utils.admin_utils import is_admin
# from .core import AdminStates

# async def text_search_handler(callback: types.CallbackQuery, state: FSMContext):
#     """Обрабатывает поиск пользователя по тексту"""
#     if not is_admin(callback.from_user.id):
#         await callback.answer("У вас нет прав доступа!", show_alert=True)
#         return
    
#     try:
#         await callback.answer()
#     except Exception as e:
#         print(f"Error answering callback: {e}")
    
#     await callback.message.delete()
    
#     keyboard = types.InlineKeyboardMarkup()
#     keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="search_user"))
#     await callback.message.answer("Введите имя пользователя (username) для поиска или userid:", reply_markup=keyboard)
    
#     await AdminStates.waiting_for_search.set()

# async def letter_search_handler(callback: types.CallbackQuery, state: FSMContext):
#     """Обрабатывает поиск пользователя по первой букве"""
#     if not is_admin(callback.from_user.id):
#         await callback.answer("У вас нет прав доступа!", show_alert=True)
#         return
    
#     try:
#         await callback.answer()
#     except Exception as e:
#         print(f"Error answering callback: {e}")
    
#     current_state = await state.get_state()
#     if current_state is not None:
#         await state.finish()
    
#     await callback.message.delete()
    
#     session = get_database_session()
#     try:
#         users = session.query(User).all()
        
#         first_letters = set()
#         for user in users:
#             if user.username and len(user.username) > 0:
#                 first_letters.add(user.username[0].upper())
        
#         first_letters = sorted(list(first_letters))
        
#         keyboard = types.InlineKeyboardMarkup(row_width=4)
#         letter_buttons = []
        
#         for letter in first_letters:
#             letter_buttons.append(types.InlineKeyboardButton(letter, callback_data=f"letter_{letter}"))
        
#         for i in range(0, len(letter_buttons), 4):
#             row_buttons = letter_buttons[i:i+4]
#             keyboard.row(*row_buttons)
        
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="search_user"))
        
#         await callback.message.answer("Выберите первую букву имени пользователя:", reply_markup=keyboard)
        
#         await AdminStates.browsing_letters.set()
        
#     except Exception as e:
#         await callback.message.answer(f"Error getting users: {str(e)}")
#     finally:
#         session.close()

# async def letter_select_handler(callback: types.CallbackQuery, state: FSMContext):
#     """Обрабатывает выбор буквы для просмотра пользователей"""
#     if not is_admin(callback.from_user.id):
#         await callback.answer("У вас нет прав доступа!", show_alert=True)
#         return
    
#     try:
#         await callback.answer()
#     except Exception as e:
#         print(f"Error answering callback: {e}")
    
#     callback_data = callback.data
    
#     if not callback_data.startswith("letter_") or len(callback_data) < 8:
#         print(f"Invalid letter selection: {callback_data}")
#         return
    
#     letter = callback_data.replace("letter_", "")
    
#     if len(letter) != 1:
#         print(f"Invalid letter: {letter}")
#         return
    
#     await state.update_data(letter=letter, page=0)
    
#     await callback.message.delete()
    
#     await show_users_by_letter(callback.message, letter, 0, state)

# async def show_users_by_letter(message, letter, page, state):
#     """Показывает пользователей с именами, начинающимися на указанную букву"""
#     session = get_database_session()
#     try:
#         users_query = session.query(User).filter(
#             func.upper(func.substr(User.username, 1, 1)) == letter.upper()
#         ).order_by(User.username)
        
#         total_users = users_query.count()
        
#         users_per_page = 7
#         total_pages = max(1, (total_users + users_per_page - 1) // users_per_page)
        
#         page = max(0, min(page, total_pages - 1))
        
#         await state.update_data(page=page)
        
#         users = users_query.offset(page * users_per_page).limit(users_per_page).all()
        
#         keyboard = types.InlineKeyboardMarkup(row_width=1)
        
#         for user in users:
#             display_name = f"{user.full_name} (@{user.username})"
#             keyboard.add(types.InlineKeyboardButton(
#                 display_name, callback_data=f"view_user_{user.id}"
#             ))
        
#         nav_buttons = []
        
#         if page > 0:
#             nav_buttons.append(types.InlineKeyboardButton(
#                 "⬅️ Назад", callback_data="prev_page"
#             ))
        
#         nav_buttons.append(types.InlineKeyboardButton(
#             f"{page + 1}/{total_pages}", callback_data="page_info"
#         ))
        
#         if page < total_pages - 1:
#             nav_buttons.append(types.InlineKeyboardButton(
#                 "➡️ Далее", callback_data="next_page"
#             ))
        
#         keyboard.row(*nav_buttons)
        
#         keyboard.add(types.InlineKeyboardButton("🔤 К выбору буквы", callback_data="letter_search"))
#         keyboard.add(types.InlineKeyboardButton("🏠 В главное меню", callback_data="admin_back"))
        
#         await message.answer(
#             f"Пользователи на букву '{letter}':\n"
#             f"Страница {page + 1} из {total_pages}",
#             reply_markup=keyboard
#         )
        
#         await AdminStates.browsing_users_by_letter.set()
        
#     except Exception as e:
#         await message.answer(f"Error getting users: {str(e)}")
#     finally:
#         session.close()

# async def search_user(message: types.Message, state: FSMContext):
#     """Поиск пользователя по имени/ID"""
#     search_query = message.text.strip()
#     session = get_database_session()
    
#     try:
#         user = session.query(User).filter(
#             (func.lower(User.username) == func.lower(search_query)) |
#             (func.lower(User.full_name).like(f"%{search_query.lower()}%")) |
#             (User.id == search_query if search_query.isdigit() else False)
#         ).first()

#         if user:
#             user_info = (
#                 f"👤 <b>User Information:</b>\n\n"
#                 f"ID: <code>{user.id}</code>\n"
#                 f"Username: @{user.username}\n"
#                 f"Full Name: {user.full_name}\n"
#             )
            
#             if hasattr(User, 'is_blocked'):
#                 status = "🚫 Blocked" if user.is_blocked else "✅ Active"
#                 user_info += f"Status: {status}\n"
                
#             if hasattr(User, 'is_exception'):
#                 exception_status = "⭐️ Exception" if user.is_exception else "👤 Regular user"
#                 user_info += f"Access: {exception_status}\n"
                
#             if hasattr(User, 'created_at'):
#                 user_info += f"Registered: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
#             keyboard = types.InlineKeyboardMarkup(row_width=2)
            
#             if hasattr(User, 'is_blocked'):
#                 action = "Unblock" if user.is_blocked else "Block"
#                 keyboard.add(types.InlineKeyboardButton(
#                     action, callback_data=f"{'unblock' if user.is_blocked else 'block'}_{user.id}"
#                 ))
            
#             if hasattr(User, 'is_exception'):
#                 exception_action = "Remove Exception" if user.is_exception else "Make Exception"
#                 keyboard.add(types.InlineKeyboardButton(
#                     exception_action, callback_data=f"{'remove_exception' if user.is_exception else 'add_exception'}_{user.id}"
#                 ))
            
#             keyboard.add(types.InlineKeyboardButton(
#                 "👥 Рефералы", callback_data=f"view_referrals_{user.id}"
#             ))
            
#             keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
            
#             await message.answer(user_info, parse_mode="HTML", reply_markup=keyboard)
#         else:
#             keyboard = types.InlineKeyboardMarkup()
#             keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
#             await message.answer("User not found.", reply_markup=keyboard)
        
#         await state.finish()
        
#     except Exception as e:
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
#         await message.answer(f"Error searching for user: {str(e)}", reply_markup=keyboard)
#         await state.finish()
#     finally:
#         session.close()

# # async def block_user(message: types.Message, state: FSMContext):
# #     """Блокировка пользователя по имени"""
# #     username = message.text.strip()
# #     session = get_database_session()
    
# #     try:
# #         if not hasattr(User, 'is_blocked'):
# #             await message.answer("Database schema doesn't support user blocking. Please update your User model.")
# #             await state.finish()
# #             return
        
# #         user = session.query(User).filter(func.lower(User.username) == func.lower(username)).first()
# #         if user:
# #             user.is_blocked = True
# #             session.commit()
            
# #             try:
# #                 from bot import bot
# #                 await bot.send_message(
# #                     chat_id=user.id,
# #                     text="⛔️ Ваш аккаунт был заблокирован администратором. Вы можете использовать кнопку 'ℹ️ Помощь' для обращения в поддержку."
# #                 )
# #             except Exception as e:
# #                 print(f"Couldn't notify user {user.id} about being blocked: {e}")
                
# #             keyboard = types.InlineKeyboardMarkup()
# #             keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
# #             await message.answer(f"User @{username} has been blocked and notified.", reply_markup=keyboard)
# #         else:
# #             keyboard = types.InlineKeyboardMarkup()
# #             keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
# #             await message.answer("User not found.", reply_markup=keyboard)
        
# #         await state.finish()
        
# #     except Exception as e:
# #         keyboard = types.InlineKeyboardMarkup()
# #         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
# #         await message.answer(f"Error blocking user: {str(e)}", reply_markup=keyboard)
# #         await state.finish()
# #     finally:
# #         session.close()

# # async def unblock_user(message: types.Message, state: FSMContext):
# #     """Разблокировка пользователя по имени"""
# #     username = message.text.strip()
# #     session = get_database_session()
    
# #     try:
# #         if not hasattr(User, 'is_blocked'):
# #             await message.answer("Database schema doesn't support user blocking. Please update your User model.")
# #             await state.finish()
# #             return
            
# #         user = session.query(User).filter(func.lower(User.username) == func.lower(username)).first()
# #         if user:
# #             user.is_blocked = False
# #             session.commit()
# #             keyboard = types.InlineKeyboardMarkup()
# #             keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
# #             await message.answer(f"User @{username} has been unblocked.", reply_markup=keyboard)
# #         else:
# #             keyboard = types.InlineKeyboardMarkup()
# #             keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
# #             await message.answer("User not found.", reply_markup=keyboard)
        
# #         await state.finish()
        
# #     except Exception as e:
# #         keyboard = types.InlineKeyboardMarkup()
# #         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
# #         await message.answer(f"Error unblocking user: {str(e)}", reply_markup=keyboard)
# #         await state.finish()
# #     finally:
# #         session.close()

# async def mass_message(message: types.Message, state: FSMContext):
#     """Отправка массовой рассылки"""
#     mass_msg_text = message.text
#     session = get_database_session()
    
#     try:
#         from bot import bot
        
#         query = session.query(User)
#         if hasattr(User, 'is_blocked'):
#             query = query.filter(User.is_blocked == False)
        
#         users = query.all()
        
#         if not users:
#             await message.answer("No users to send messages to.")
#             await state.finish()
#             return
        
#         status_msg = await message.answer(f"Sending message to {len(users)} users... 0%")
        
#         success_count = 0
#         fail_count = 0
        
#         for i, user in enumerate(users):
#             try:
#                 if i % 10 == 0 and i > 0:
#                     progress = int((i / len(users)) * 100)
#                     await status_msg.edit_text(f"Sending message to {len(users)} users... {progress}%")
                
#                 await bot.send_message(chat_id=user.id, text=mass_msg_text)
#                 success_count += 1
                
#                 await asyncio.sleep(0.05)
                
#             except Exception:
#                 fail_count += 1
        
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
#         await status_msg.edit_text(
#             f"Message sending complete:\n"
#             f"✅ Successfully sent: {success_count}\n"
#             f"❌ Failed: {fail_count}",
#             reply_markup=keyboard
#         )
        
#         await state.finish()
        
#     except Exception as e:
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
#         await message.answer(f"Error sending mass message: {str(e)}", reply_markup=keyboard)
#         await state.finish()
#     finally:
#         session.close()

# async def view_user_handler(callback: types.CallbackQuery):
#     """Обрабатывает просмотр информации о пользователе по ID"""
#     if not is_admin(callback.from_user.id):
#         await callback.answer("У вас нет прав доступа!", show_alert=True)
#         return
    
#     try:
#         await callback.answer()
#     except Exception as e:
#         print(f"Ошибка при ответе на callback: {e}")
    
#     user_id = callback.data.replace("view_user_", "")
    
#     # Удаляем текущее сообщение с листингом пользователей
#     await callback.message.delete()
    
#     session = get_database_session()
#     try:
#         user = session.query(User).filter(User.id == user_id).first()
        
#         if not user:
#             keyboard = types.InlineKeyboardMarkup()
#             keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="letter_search"))
#             await callback.message.answer("Пользователь не найден.", reply_markup=keyboard)
#             return
        
#         # Формируем информацию о пользователе
#         user_info = (
#             f"👤 <b>Информация о пользователе:</b>\n\n"
#             f"ID: <code>{user.id}</code>\n"
#             f"Username: @{user.username}\n"
#             f"Полное имя: {user.full_name}\n"
#         )
        
#         if hasattr(User, 'is_blocked'):
#             status = "🚫 Заблокирован" if user.is_blocked else "✅ Активен"
#             user_info += f"Статус: {status}\n"
            
#         if hasattr(User, 'is_exception'):
#             exception_status = "⭐️ Исключение" if user.is_exception else "👤 Обычный пользователь"
#             user_info += f"Доступ: {exception_status}\n"
            
#         if hasattr(User, 'created_at'):
#             user_info += f"Зарегистрирован: {user.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
        
#         # Создаем клавиатуру с действиями
#         keyboard = types.InlineKeyboardMarkup(row_width=2)
        
#         if hasattr(User, 'is_blocked'):
#             action = "Разблокировать" if user.is_blocked else "Заблокировать"
#             keyboard.add(types.InlineKeyboardButton(
#                 action, callback_data=f"{'unblock' if user.is_blocked else 'block'}_{user.id}"
#             ))
        
#         if hasattr(User, 'is_exception'):
#             exception_action = "Убрать исключение" if user.is_exception else "Сделать исключением"
#             keyboard.add(types.InlineKeyboardButton(
#                 exception_action, callback_data=f"{'remove_exception' if user.is_exception else 'add_exception'}_{user.id}"
#             ))
        
#         keyboard.add(types.InlineKeyboardButton(
#             "👥 Рефералы", callback_data=f"view_referrals_{user.id}"
#         ))
        
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад к списку", callback_data="letter_search"))
        
#         await callback.message.answer(user_info, parse_mode="HTML", reply_markup=keyboard)
        
#     except Exception as e:
#         await callback.message.answer(f"Ошибка при просмотре пользователя: {str(e)}")
#     finally:
#         session.close()

# def register_user_management_handlers(dp: Dispatcher):
#     """Регистрирует обработчики для управления пользователями"""
#     dp.register_message_handler(search_user, state=AdminStates.waiting_for_search)
#     # dp.register_message_handler(block_user, state=AdminStates.waiting_for_block_username)
#     # dp.register_message_handler(unblock_user, state=AdminStates.waiting_for_unblock_username)
#     dp.register_message_handler(mass_message, state=AdminStates.waiting_for_mass_message)
    
#     dp.register_callback_query_handler(letter_select_handler, lambda c: c.data.startswith("letter_"), state=AdminStates.browsing_letters)
#     dp.register_callback_query_handler(view_user_handler, lambda c: c.data and c.data.startswith("view_user_"))
#     dp.register_callback_query_handler(page_info_handler, lambda c: c.data == "page_info", state=AdminStates.browsing_users_by_letter)
#     dp.register_callback_query_handler(prev_page_handler, lambda c: c.data == "prev_page", state=AdminStates.browsing_users_by_letter)
#     dp.register_callback_query_handler(next_page_handler, lambda c: c.data == "next_page", state=AdminStates.browsing_users_by_letter)

# # Эти функции должны быть реализованы для навигации по страницам
# async def page_info_handler(callback: types.CallbackQuery, state: FSMContext):
#     await callback.answer("Текущая страница", show_alert=True)

# async def prev_page_handler(callback: types.CallbackQuery, state: FSMContext):
#     # Здесь должна быть реализация перехода на предыдущую страницу
#     data = await state.get_data()
#     letter = data.get('letter', 'A')
#     page = max(0, data.get('page', 0) - 1)
    
#     await callback.message.delete()
#     await show_users_by_letter(callback.message, letter, page, state)

# async def next_page_handler(callback: types.CallbackQuery, state: FSMContext):
#     # Здесь должна быть реализация перехода на следующую страницу
#     data = await state.get_data()
#     letter = data.get('letter', 'A')
#     page = data.get('page', 0) + 1
    
#     await callback.message.delete()
#     await show_users_by_letter(callback.message, letter, page, state)