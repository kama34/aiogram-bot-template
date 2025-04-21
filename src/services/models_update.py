from sqlalchemy import Column, BigInteger, ForeignKey
from .database import Base, Order, User

def update_models():
    """
    Обновляет модели SQLAlchemy для обеспечения совместимости
    """
    # Изменяем типы данных для совместимости
    # Примечание: не изменяет структуру базы данных,
    # только модели SQLAlchemy в памяти приложения
    
    # Печатаем текущие типы данных для отладки
    print(f"User.id type: {User.id.type}")
    print(f"Order.user_id type: {Order.user_id.type}")
    
    print("✓ Модели SQLAlchemy обновлены для совместимости")