from aiogram import types
from utils.admin_utils import is_admin
from services.referral_service import ReferralService
from .link_utils import generate_referral_link

async def admin_referral_link(message: types.Message):
    """Генерирует и показывает реферальную ссылку администратора"""
    # Клавиатура с действиями
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📋 Скопировать ссылку", callback_data=f"copy_ref_{message.chat.id}"),
        types.InlineKeyboardButton("👥 Мои рефералы", callback_data="admin_my_refs"),
        types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back")
    )
    
    # Генерируем реферальную ссылку
    ref_link = await generate_referral_link(message.chat.id)
    
    await message.answer(
        f"🔗 <b>Ваша реферальная ссылка:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        f"Отправьте эту ссылку другим пользователям. Когда они перейдут по ней и "
        f"запустят бота, они будут автоматически зарегистрированы как ваши рефералы.",
        parse_mode="HTML",
        reply_markup=keyboard
    )

async def admin_my_referrals(message: types.Message):
    """Показывает список рефералов администратора"""
    admin_id = message.chat.id
    
    ref_service = ReferralService()
    
    try:
        # Получаем список рефералов администратора
        referrals = ref_service.get_user_referrals(admin_id)
        
        if not referrals:
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(types.InlineKeyboardButton("🔗 Моя реферальная ссылка", callback_data="admin_ref_link"))
            keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
            
            await message.answer(
                "👥 У вас пока нет рефералов.\n\n"
                "Поделитесь своей реферальной ссылкой с другими пользователями.",
                reply_markup=keyboard
            )
            return
        
        # Формируем список рефералов с информацией
        referral_text = f"👥 <b>Ваши рефералы:</b>\n\n"
        referral_text += f"Всего рефералов: <b>{len(referrals)}</b>\n\n"
        
        for i, ref in enumerate(referrals, 1):
            referred_user = ref_service.get_user_by_id(ref.user_id)
            
            if referred_user:
                username = f"@{referred_user.username}" if referred_user.username else "без username"
                date_str = ref.created_at.strftime("%d.%m.%Y %H:%M") if hasattr(ref, 'created_at') else "неизвестно"
                status = "🚫 Заблокирован" if hasattr(referred_user, 'is_blocked') and referred_user.is_blocked else "✅ Активен"
                
                referral_text += (
                    f"{i}. <b>{referred_user.full_name}</b> ({username})\n"
                    f"   ID: <code>{referred_user.id}</code> | {status} | 📅 {date_str}\n"
                )
        
        # Создаем клавиатуру
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔗 Моя реферальная ссылка", callback_data="admin_ref_link"))
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
        await message.answer(referral_text, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        await message.answer(f"Ошибка при получении списка рефералов: {str(e)}", reply_markup=keyboard)
    finally:
        ref_service.close_session()