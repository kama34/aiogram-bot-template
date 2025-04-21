from sqlalchemy import func
from datetime import datetime
from .database import get_database_session, Order, OrderItem, User

class OrderService:
    """Сервисный класс для работы с заказами пользователей"""
    
    def __init__(self):
        self.session = get_database_session()
    
    def close_session(self):
        """Закрывает сессию с базой данных"""
        if self.session:
            self.session.close()
    
    def get_user_orders(self, user_id):
        """Получает все заказы пользователя, отсортированные по дате (новые в начале)"""
        return self.session.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).all()
    
    def get_order_by_id(self, order_id):
        """Получает заказ по его ID"""
        return self.session.query(Order).filter(Order.id == order_id).first()
    
    def get_order_items(self, order_id):
        """Получает элементы заказа по ID заказа"""
        return self.session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
    
    def get_order_stats(self, user_id):
        """Получает статистику заказов пользователя"""
        total_orders = self.session.query(func.count(Order.id)).filter(Order.user_id == user_id).scalar() or 0
        total_spent = self.session.query(func.sum(Order.total_amount)).filter(Order.user_id == user_id).scalar() or 0
        
        # Получение первого и последнего заказа для определения периода
        first_order = self.session.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.asc()).first()
        last_order = self.session.query(Order).filter(Order.user_id == user_id).order_by(Order.created_at.desc()).first()
        
        # Если есть заказы, вычисляем период
        if first_order and last_order:
            first_date = first_order.created_at
            last_date = last_order.created_at
        else:
            first_date = None
            last_date = None
        
        return {
            "total_orders": total_orders,
            "total_spent": total_spent,
            "first_date": first_date,
            "last_date": last_date
        }
    
    def get_user_by_id(self, user_id):
        """Получает пользователя по ID"""
        return self.session.query(User).filter(User.id == user_id).first()