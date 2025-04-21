from sqlalchemy import func, desc, text
from .database import get_database_session, User, Referral

class ReferralService:
    """Сервис для работы с реферальной системой"""
    
    def __init__(self):
        self.session = get_database_session()
        
    def close_session(self):
        """Закрывает сессию с базой данных"""
        if self.session:
            self.session.close()
    
    def get_total_users_with_referrer(self):
        """Возвращает общее количество пользователей с рефералами"""
        return self.session.query(Referral).filter(Referral.referred_by != None).count()
    
    def get_top_referrers(self, limit=10):
        """Возвращает топ рефереров по количеству приглашенных"""
        top_referrers_query = self.session.query(
            Referral.referred_by, 
            func.count(Referral.id).label('count')
        ).filter(Referral.referred_by != None) \
         .group_by(Referral.referred_by) \
         .order_by(text('count DESC')) \
         .limit(limit)
        
        return top_referrers_query.all()
    
    def get_user_referrals(self, user_id):
        """Получает всех рефералов пользователя"""
        return self.session.query(Referral).filter(Referral.referred_by == user_id).all()
    
    def count_user_referrals(self, user_id):
        """Подсчитывает количество рефералов пользователя"""
        return self.session.query(Referral).filter(Referral.referred_by == user_id).count()
    
    def get_user_by_id(self, user_id):
        """Получает пользователя по ID"""
        return self.session.query(User).filter(User.id == user_id).first()
    
    def create_referral(self, user_id, referred_by):
        """Создает новую запись о реферале"""
        # Проверяем, существует ли уже такой реферал
        existing_referral = self.session.query(Referral).filter(Referral.user_id == user_id).first()
        if existing_referral:
            return existing_referral
        
        # Создаем новый реферал
        try:
            new_referral = Referral(user_id=user_id, referred_by=referred_by)
            self.session.add(new_referral)
            self.session.commit()
            return new_referral
        except Exception as e:
            self.session.rollback()
            print(f"Ошибка при создании реферала: {e}")
            raise
    
    def get_referral_by_user_id(self, user_id):
        """Получает информацию о реферале по ID пользователя"""
        return self.session.query(Referral).filter(Referral.user_id == user_id).first()