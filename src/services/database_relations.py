from sqlalchemy import inspect, Column, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from .database import Order, User, Base, OrderItem

def setup_database_relationships():
    """
    Настраивает правильные отношения между таблицами с корректными стратегиями загрузки
    """
    try:
        print("Настройка отношений в базе данных...")
        
        # Настраиваем отношение между Order и User
        if hasattr(Order, 'user'):
            print("Переопределение отношения Order.user")
            Order.user = relationship(
                'User',
                primaryjoin="Order.user_id == User.id",
                foreign_keys=[Order.user_id],
                lazy='select',  # Используем простую стратегию загрузки
                innerjoin=False,
                backref=None  # Отключаем автоматический backref
            )
        
        # Отдельно настраиваем обратное отношение
        if hasattr(User, 'orders'):
            print("Переопределение отношения User.orders")
            User.orders = relationship(
                'Order',
                primaryjoin="User.id == Order.user_id",
                foreign_keys=[Order.user_id],
                lazy='select',  # Используем простую стратегию загрузки
                innerjoin=False
            )
        
        # Настраиваем отношение между Order и OrderItem
        if hasattr(Order, 'items'):
            print("Переопределение отношения Order.items")
            Order.items = relationship(
                'OrderItem',
                primaryjoin="Order.id == OrderItem.order_id",
                foreign_keys=[OrderItem.order_id],
                lazy='select',
                innerjoin=False,
                cascade="all, delete-orphan"
            )
        
        print("✓ Отношения в базе данных настроены успешно")
        
    except Exception as e:
        print(f"❌ Ошибка при настройке отношений: {e}")