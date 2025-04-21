from sqlalchemy import ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .database import Order, User

def fix_database_relationships():
    """
    Исправляет отношения между моделями базы данных
    """
    # Исправляем отношение Order -> User
    Order.user = relationship(
        'User', 
        primaryjoin="Order.user_id == User.id",
        backref='orders',
        foreign_keys=[Order.user_id]
    )
    
    print("✓ Отношения в базе данных исправлены")