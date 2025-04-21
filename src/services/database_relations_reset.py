from sqlalchemy import inspect
from sqlalchemy.orm import configure_mappers, relationship
from .database import Order, User, Base

def reset_order_user_relationship():
    """
    Полностью удаляет и пересоздает отношения между Order и User
    """
    try:
        # Удаляем существующие отношения
        order_mapper = inspect(Order).mapper
        
        # Удаляем отношение 'user' из Order
        if hasattr(Order, 'user'):
            # Удаляем свойство из маппера
            if 'user' in order_mapper._props:
                order_mapper._delete_prop('user')
            
            # Удаляем атрибут из класса
            delattr(Order, 'user')
            
            print("✓ Существующее отношение 'user' удалено из Order")
        
        # Удаляем отношение 'orders' из User если оно существует
        user_mapper = inspect(User).mapper
        if hasattr(User, 'orders'):
            if 'orders' in user_mapper._props:
                user_mapper._delete_prop('orders')
            
            delattr(User, 'orders')
            print("✓ Существующее отношение 'orders' удалено из User")
        
        # Создаем новые отношения без использования backref
        Order.user = relationship(
            'User',
            primaryjoin="Order.user_id == User.id",
            foreign_keys=[Order.user_id]
        )
        
        User.orders = relationship(
            'Order',
            primaryjoin="User.id == Order.user_id",
            foreign_keys=[Order.user_id]
        )
        
        # Перестраиваем маппинги
        configure_mappers()
        print("✓ Новые отношения между Order и User созданы")
        
    except Exception as e:
        print(f"❌ Ошибка при сбросе отношений: {e}")