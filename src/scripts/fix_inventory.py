import sys
import os
import logging
from datetime import datetime

# Добавляем путь к корневой директории проекта
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.database import get_database_session, Product, ProductInventory
from utils.logger import setup_logger

logger = setup_logger('scripts.fix_inventory')

def fix_inventory():
    """Проверяет и исправляет запасы товаров"""
    session = None
    try:
        session = get_database_session()
        
        # Получаем все товары
        products = session.query(Product).all()
        
        print(f"Найдено товаров: {len(products)}")
        print("=" * 50)
        
        # Проверяем каждый товар
        for product in products:
            # Проверяем запись в инвентаре
            inventory = session.query(ProductInventory).filter(
                ProductInventory.product_id == product.id
            ).first()
            
            if not inventory:
                print(f"Товар #{product.id} '{product.name}' не имеет записи в инвентаре.")
                choice = input("Создать запись с запасом 100? (д/н): ")
                
                if choice.lower() in ['д', 'y', 'yes', 'да']:
                    new_inventory = ProductInventory(
                        product_id=product.id,
                        stock=100,
                        reserved=0
                    )
                    session.add(new_inventory)
                    print(f"Создана новая запись с запасом 100 для товара '{product.name}'")
            else:
                print(f"Товар #{product.id} '{product.name}' имеет запас: {inventory.stock}")
                if inventory.stock == 0:
                    choice = input("Запас равен нулю. Установить запас 100? (д/н): ")
                    
                    if choice.lower() in ['д', 'y', 'yes', 'да']:
                        inventory.stock = 100
                        print(f"Запас для товара '{product.name}' установлен на 100")
            
            print("-" * 50)
        
        # Сохраняем изменения
        choice = input("Сохранить все изменения? (д/н): ")
        if choice.lower() in ['д', 'y', 'yes', 'да']:
            session.commit()
            print("Изменения сохранены!")
        else:
            session.rollback()
            print("Изменения отменены.")
        
    except Exception as e:
        print(f"Произошла ошибка: {e}")
        if session:
            session.rollback()
    finally:
        if session:
            session.close()

if __name__ == "__main__":
    print("Утилита для проверки и исправления запасов товаров")
    print("=" * 50)
    fix_inventory()