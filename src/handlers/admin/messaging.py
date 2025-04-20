import asyncio
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from services.database import get_database_session, User
from .core import AdminStates

async def mass_message(message: types.Message, state: FSMContext):
    """Отправка массовой рассылки всем пользователям"""
    mass_msg_text = message.text
    session = get_database_session()
    
    try:
        # Get bot instance
        from bot import bot
        
        # Get all active users
        query = session.query(User)
        if hasattr(User, 'is_blocked'):
            query = query.filter(User.is_blocked == False)
        
        users = query.all()
        
        if not users:
            await message.answer("Нет пользователей для отправки сообщения.")
            await state.finish()
            return
        
        # Send progress report
        status_msg = await message.answer(f"Отправка сообщения {len(users)} пользователям... 0%")
        
        # Send messages
        success_count = 0
        fail_count = 0
        
        for i, user in enumerate(users):
            try:
                # Update progress every 10 users
                if i % 10 == 0 and i > 0:
                    progress = int((i / len(users)) * 100)
                    await status_msg.edit_text(f"Отправка сообщения {len(users)} пользователям... {progress}%")
                
                # Send message to user
                await bot.send_message(chat_id=user.id, text=mass_msg_text)
                success_count += 1
                
                # Small delay to avoid hitting rate limits
                await asyncio.sleep(0.05)
                
            except Exception:
                fail_count += 1
        
        # Final report with back button
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
        await status_msg.edit_text(
            f"Отправка сообщений завершена:\n"
            f"✅ Успешно отправлено: {success_count}\n"
            f"❌ Не удалось отправить: {fail_count}",
            reply_markup=keyboard
        )
        
        await state.finish()
        
    except Exception as e:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        await message.answer(f"Ошибка при отправке массового сообщения: {str(e)}", reply_markup=keyboard)
        await state.finish()
    finally:
        session.close()

def register_messaging_handlers(dp: Dispatcher):
    """Регистрирует обработчики для массовой рассылки"""
    dp.register_message_handler(mass_message, state=AdminStates.waiting_for_mass_message)