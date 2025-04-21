from aiogram import types
from sqlalchemy import func, desc, text
from services.database import get_database_session, User, Referral

async def view_referral_statistics(message: types.Message):
    """Показывает статистику рефералов"""
    session = get_database_session()
    try:
        total_referrals = session.query(Referral).count()
        
        top_referrers_query = session.query(
            Referral.referred_by, 
            func.count(Referral.id).label('count')
        ).group_by(Referral.referred_by).order_by(text('count DESC')).limit(5)
        
        top_referrers = top_referrers_query.all()
        
        stats = f"📊 <b>Статистика рефералов:</b>\n\n" \
                f"👥 Всего рефералов: <b>{total_referrals}</b>\n\n" \
                f"🏆 <b>Топ 5 пригласивших:</b>\n"
        
        for i, (referrer_id, count) in enumerate(top_referrers, 1):
            if referrer_id:
                referrer = session.query(User).filter(User.id == referrer_id).first()
                if referrer:
                    stats += f"{i}. {referrer.full_name} (@{referrer.username}): {count} приглашений\n"
        
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("◀️ Назад", callback_data="admin_back"))
        
        await message.answer(stats, parse_mode="HTML", reply_markup=keyboard)
        
    except Exception as e:
        await message.answer(f"Ошибка при получении статистики рефералов: {str(e)}")
    finally:
        session.close()