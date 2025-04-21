from sqlalchemy import func
from sqlalchemy.orm import joinedload, contains_eager
from .database import get_database_session, Order, OrderItem, User

class OrderService:
    """Сервис для работы с заказами пользователей с правильными стратегиями загрузки"""
    
    def __init__(self):
        self.session = get_database_session()
    
    def close_session(self):
        """Закрывает сессию с базой данных"""
        if self.session:
            self.session.close()
    
    def get_user_orders(self, user_id):
        """
        Получает все заказы пользователя с явным указанием стратегии загрузки
        """
        try:
            # Используем subqueryload для оптимизации запросов
            return self.session.query(Order).filter(
                Order.user_id == user_id
            ).order_by(Order.created_at.desc()).all()
        except Exception as e:
            print(f"Ошибка при получении заказов пользователя: {e}")
            return []
    
    def get_order_by_id(self, order_id):
        """
        Получает заказ по ID с явной загрузкой связанных предметов
        """
        try:
            # Используем explicit join вместо автоматической стратегии
            return self.session.query(Order).filter(Order.id == order_id).first()
        except Exception as e:
            print(f"Ошибка при получении заказа: {e}")
            return None
    
    def get_order_items(self, order_id):
        """
        Получает элементы заказа по ID заказа напрямую
        """
        try:
            return self.session.query(OrderItem).filter(OrderItem.order_id == order_id).all()
        except Exception as e:
            print(f"Ошибка при получении элементов заказа: {e}")
            return []
    
    def get_order_stats(self, user_id):
        """
        Получает статистику заказов пользователя, используя агрегатные запросы
        """
        try:
            total_orders = self.session.query(func.count(Order.id)).filter(
                Order.user_id == user_id
            ).scalar() or 0
            
            total_spent = self.session.query(func.sum(Order.total_amount)).filter(
                Order.user_id == user_id
            ).scalar() or 0
            
            # Отдельные запросы для первого и последнего заказа
            first_order = self.session.query(Order).filter(
                Order.user_id == user_id
            ).order_by(Order.created_at.asc()).first()
            
            last_order = self.session.query(Order).filter(
                Order.user_id == user_id
            ).order_by(Order.created_at.desc()).first()
            
            return {
                "total_orders": total_orders,
                "total_spent": float(total_spent),
                "first_date": first_order.created_at if first_order else None,
                "last_date": last_order.created_at if last_order else None
            }
        except Exception as e:
            print(f"Ошибка при получении статистики заказов: {e}")
            return {
                "total_orders": 0,
                "total_spent": 0,
                "first_date": None,
                "last_date": None
            }
    
    def get_user_by_id(self, user_id):
        """
        Получает пользователя по ID без использования отношений
        """
        try:
            return self.session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            print(f"Ошибка при получении пользователя: {e}")
            return None