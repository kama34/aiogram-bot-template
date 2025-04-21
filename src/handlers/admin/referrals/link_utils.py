from aiogram import types
from utils.admin_utils import is_admin

async def generate_referral_link(user_id):
    """Генерирует реферальную ссылку для пользователя"""
    from bot import bot
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    
    return f"https://t.me/{bot_username}?start=ref_{user_id}"

async def copy_ref_link_callback(callback: types.CallbackQuery):
    """Обрабатывает кнопку копирования реферальной ссылки"""
    try:
        await callback.answer("Ссылка скопирована в сообщение ниже")
    except Exception as e:
        print(f"Error answering callback: {e}")
    
    # Извлекаем ID пользователя из callback-данных
    user_id = callback.data.replace("copy_ref_", "")
    
    # Генерируем ссылку
    referral_link = await generate_referral_link(user_id)
    
    # Создаем клавиатуру с кнопкой назад
    keyboard = types.InlineKeyboardMarkup()
    
    # Добавляем кнопку назад в зависимости от того, админ это или обычный пользователь
    if is_admin(callback.from_user.id):
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_ref_link"))
    else:
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="my_referrals"))
    
    # Отправляем ссылку отдельным сообщением для удобного копирования
    await callback.message.answer(
        f"<code>{referral_link}</code>\n\nСкопируйте эту ссылку и отправьте друзьям",
        parse_mode="HTML",
        reply_markup=keyboard
    )