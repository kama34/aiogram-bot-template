# import os
# import openpyxl
# from openpyxl.styles import Font
# from datetime import datetime, timedelta
# from aiogram import Dispatcher, types
# from sqlalchemy import func, desc, text
# from services.database import get_database_session, User, Referral
# from services.user_service import UserService
# from utils.admin_utils import is_admin

# async def view_user_statistics(message: types.Message):
#     """Показывает статистику пользователей"""
#     session = get_database_session()
#     try:
#         total_users = session.query(User).count()
        
#         has_blocked_field = hasattr(User, 'is_blocked')
        
#         blocked_users = 0
#         if has_blocked_field:
#             blocked_users = session.query(User).filter(User.is_blocked == True).count()
        
#         new_users_24h = 0
#         if hasattr(User, 'created_at'):
#             new_users_24h = session.query(User).filter(
#                 User.created_at >= (datetime.now() - timedelta(days=1))
#             ).count()
        
#         stats = f"📊 <b>Статистика пользователей:</b>\n\n" \
#                 f"👥 Всего пользователей: <b>{total_users}</b>\n"
        
#         if has_blocked_field:
#             stats += f"🚫 Заблокированных пользователей: <b>{blocked_users}</b>\n"
        
#         if hasattr(User, 'created_at'):
#             stats += f"🆕 Новых пользователей за 24ч: <b>{new_users_24h}</b>\n"
        
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
#         await message.answer(stats, parse_mode="HTML", reply_markup=keyboard)
        
#     except Exception as e:
#         await message.answer(f"Ошибка при получении статистики: {str(e)}")
#     finally:
#         session.close()

# async def export_user_list(message: types.Message):
#     """Экспортирует список пользователей в Excel-файл"""
#     try:
#         session = get_database_session()
#         users = session.query(User).all()
        
#         wb = openpyxl.Workbook()
#         ws = wb.active
#         ws.title = "Users"
        
#         headers = ["ID", "Username", "Full Name"]
#         if hasattr(User, 'is_blocked'):
#             headers.append("Blocked")
#         if hasattr(User, 'is_exception'):
#             headers.append("Exception")
#         if hasattr(User, 'created_at'):
#             headers.append("Registration Date")
            
#         for col_num, header in enumerate(headers, 1):
#             cell = ws.cell(row=1, column=col_num)
#             cell.value = header
#             cell.font = Font(bold=True)
        
#         for row_num, user in enumerate(users, 2):
#             ws.cell(row=row_num, column=1).value = user.id
#             ws.cell(row=row_num, column=2).value = user.username
#             ws.cell(row=row_num, column=3).value = user.full_name
            
#             col = 4
#             if hasattr(User, 'is_blocked'):
#                 ws.cell(row=row_num, column=col).value = "Yes" if user.is_blocked else "No"
#                 col += 1
#             if hasattr(User, 'is_exception'):
#                 ws.cell(row=row_num, column=col).value = "Yes" if user.is_exception else "No"
#                 col += 1
#             if hasattr(User, 'created_at'):
#                 ws.cell(row=row_num, column=col).value = user.created_at.strftime("%Y-%m-%d %H:%M:%S") if user.created_at else ""
        
#         filename = f"users_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
#         filepath = os.path.join(os.getcwd(), filename)
#         wb.save(filepath)
        
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
#         with open(filepath, 'rb') as file:
#             await message.answer_document(
#                 types.InputFile(file, filename=filename),
#                 caption=f"Exported {len(users)} users",
#                 reply_markup=keyboard
#             )
        
#         os.remove(filepath)
#         session.close()
        
#     except Exception as e:
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
#         await message.answer(f"Error exporting users: {str(e)}", reply_markup=keyboard)

# async def view_referral_statistics(message: types.Message):
#     """Показывает статистику рефералов"""
#     session = get_database_session()
#     try:
#         total_referrals = session.query(Referral).count()
        
#         top_referrers_query = session.query(
#             Referral.referred_by, 
#             func.count(Referral.id).label('count')
#         ).group_by(Referral.referred_by).order_by(text('count DESC')).limit(5)
        
#         top_referrers = top_referrers_query.all()
        
#         stats = f"📊 <b>Статистика рефералов:</b>\n\n" \
#                 f"👥 Всего рефералов: <b>{total_referrals}</b>\n\n" \
#                 f"🏆 <b>Топ 5 пригласивших:</b>\n"
        
#         for i, (referrer_id, count) in enumerate(top_referrers, 1):
#             if referrer_id:
#                 referrer = session.query(User).filter(User.id == referrer_id).first()
#                 if referrer:
#                     stats += f"{i}. {referrer.full_name} (@{referrer.username}): {count} приглашений\n"
        
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
#         await message.answer(stats, parse_mode="HTML", reply_markup=keyboard)
        
#     except Exception as e:
#         await message.answer(f"Ошибка при получении статистики рефералов: {str(e)}")
#     finally:
#         session.close()

# async def admin_referral_link(message: types.Message):
#     """Генерирует реферальную ссылку для администраторов"""
#     user_id = message.chat.id
    
#     from bot import bot
#     bot_info = await bot.get_me()
#     bot_username = bot_info.username
    
#     referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
#     user_service = UserService()
#     referral_count = user_service.count_user_referrals(user_id)
#     user_service.close_session()
    
#     keyboard = types.InlineKeyboardMarkup(row_width=1)
#     keyboard.add(
#         types.InlineKeyboardButton(
#             "📤 Поделиться", 
#             switch_inline_query=f"Приглашаю тебя в наш бот! {referral_link}"
#         )
#     )
#     keyboard.add(
#         types.InlineKeyboardButton("📊 Мои рефералы", callback_data="admin_my_refs")
#     )
#     keyboard.add(
#         types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
#     )
    
#     await message.answer(
#         f"🔗 <b>Ваша админская реферальная ссылка:</b>\n\n"
#         f"<code>{referral_link}</code>\n\n"
#         f"Поделитесь этой ссылкой с друзьями! Вы пригласили: <b>{referral_count}</b> пользователей",
#         parse_mode="HTML",
#         reply_markup=keyboard
#     )

# async def admin_my_referrals(message: types.Message):
#     """Показывает рефералов администратора"""
#     user_id = message.chat.id
    
#     user_service = UserService()
#     referrals = user_service.get_user_referrals(user_id)
    
#     if not referrals:
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
        
#         await message.answer("У вас пока нет приглашённых пользователей.", reply_markup=keyboard)
#         user_service.close_session()
#         return
    
#     referral_text = "👥 <b>Ваши приглашённые пользователи:</b>\n\n"
#     for i, ref in enumerate(referrals, 1):
#         user = user_service.get_user_by_id(ref.user_id)
#         if user:
#             date_str = ref.created_at.strftime("%d.%m.%Y") if hasattr(ref, 'created_at') else "неизвестно"
#             referral_text += f"{i}. {user.full_name} (@{user.username}) - {date_str}\n"
    
#     user_service.close_session()
    
#     keyboard = types.InlineKeyboardMarkup()
#     keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
    
#     await message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)

# async def view_user_referrals(callback: types.CallbackQuery):
#     """Просмотр рефералов, приглашенных конкретным пользователем"""
#     if not is_admin(callback.from_user.id):
#         await callback.answer("У вас нет прав доступа!", show_alert=True)
#         return
    
#     try:
#         await callback.answer()
#     except Exception as e:
#         print(f"Error answering callback: {e}")
    
#     user_id = int(callback.data.replace("view_referrals_", ""))
#     orig_message = callback.message
    
#     user_service = UserService()
    
#     try:
#         target_user = user_service.get_user_by_id(user_id)
#         if not target_user:
#             await callback.message.answer("Пользователь не найден")
#             return
        
#         referrals = user_service.get_user_referrals(user_id)
        
#         await orig_message.delete()
        
#         if not referrals or len(referrals) == 0:
#             keyboard = types.InlineKeyboardMarkup()
#             keyboard.add(types.InlineKeyboardButton("◀️ Назад к пользователю", callback_data=f"back_to_user_{user_id}"))
#             await callback.message.answer(
#                 f"Пользователь {target_user.full_name} (@{target_user.username}) не пригласил ни одного пользователя.",
#                 reply_markup=keyboard
#             )
#             return
        
#         total_referrals = len(referrals)
#         referral_text = (
#             f"👥 <b>Рефералы пользователя {target_user.full_name} (@{target_user.username}):</b>\n\n"
#             f"Всего приглашено: <b>{total_referrals}</b> пользователей\n\n"
#         )
        
#         for i, ref in enumerate(referrals, 1):
#             referred_user = user_service.get_user_by_id(ref.user_id)
#             if referred_user:
#                 date_str = ref.created_at.strftime("%d.%m.%Y") if hasattr(ref, 'created_at') else "неизвестно"
#                 referral_text += f"{i}. {referred_user.full_name} (@{referred_user.username}) - {date_str}\n"
        
#         keyboard = types.InlineKeyboardMarkup()
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад к пользователю", callback_data=f"back_to_user_{user_id}"))
        
#         await callback.message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)
        
#     except Exception as e:
#         print(f"Error getting user referrals: {e}")
#         await callback.message.answer(f"Ошибка при получении списка рефералов: {str(e)}")
#     finally:
#         user_service.close_session()

# async def copy_ref_link_callback(callback: types.CallbackQuery):
#     """Обрабатывает кнопку копирования реферальной ссылки"""
#     try:
#         await callback.answer("Ссылка скопирована в сообщение ниже")
#     except Exception as e:
#         print(f"Error answering callback: {e}")
    
#     user_id = callback.data.replace("copy_ref_", "")
    
#     from bot import bot
#     bot_info = await bot.get_me()
#     bot_username = bot_info.username
    
#     referral_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    
#     keyboard = types.InlineKeyboardMarkup()
    
#     if is_admin(callback.from_user.id):
#         keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
    
#     await callback.message.answer(
#         f"<code>{referral_link}</code>\n\nСкопируйте эту ссылку и отправьте друзьям",
#         parse_mode="HTML",
#         reply_markup=keyboard
#     )

# def register_statistics_handlers(dp: Dispatcher):
#     """Регистрирует обработчики для статистики и экспорта данных"""
#     dp.register_callback_query_handler(view_user_referrals, lambda c: c.data.startswith("view_referrals_"))
#     dp.register_callback_query_handler(copy_ref_link_callback, lambda c: c.data.startswith("copy_ref_"))