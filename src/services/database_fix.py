from sqlalchemy import ForeignKey, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, configure_mappers
from .database import Order, User

def fix_database_relationships():
    """
    Исправляет отношения между моделями базы данных без создания дублирующих backref
    """
    try:
        # Проверяем существующие отношения
        print("Проверка существующих отношений...")
        
        # Получаем сущестсвующее отношение
        order_mapper = inspect(Order).mapper
        
        # Находим свойство 'user' из класса Order
        user_rel_property = None
        for prop in order_mapper.iterate_properties:
            if prop.key == 'user':
                user_rel_property = prop
                break
        
        # Модифицируем свойство вместо создания нового
        if user_rel_property:
            print("Обновление параметров существующего отношения...")
            
            # Модифицируем параметры отношения без изменения backref
            user_rel_property.primaryjoin = Order.user_id == User.id
            user_rel_property.foreign_keys = [Order.user_id]
            
            # Перестраиваем маппинги
            configure_mappers()
            
            print("✓ Отношения в базе данных исправлены")
        else:
            print("⚠ Не найдено отношение 'user' в классе Order")
            
    except Exception as e:
        print(f"❌ Ошибка при исправлении отношений: {e}")