from sqlalchemy import desc
from .database import get_database_session, Product, ProductInventory
import uuid
import traceback

# Словарь цен продуктов в звездах
PRODUCT_PRICES = {
    "1": 11,  # Цена Продукта 1 - 11 звезд
    "2": 17,  # Цена Продукта 2 - 17 звезд
    "3": 22,  # Цена Продукта 3 - 22 звезды
    "4": 28,  # Цена Продукта 4 - 28 звезд
}

# Начальное количество товаров (по умолчанию)
DEFAULT_STOCK = 10

def get_product_price(product_id):
    """Получение цены продукта по его ID в звездах"""
    return PRODUCT_PRICES.get(str(product_id), 0)

def get_product_name(product_id):
    """Получение названия продукта по его ID"""
    return f"Продукт {product_id}"

def get_product_stock(product_id):
    """Получение доступного количества товара на складе"""
    try:
        with get_database_session() as session:
            # Проверяем наличие товара в таблице инвентаря
            inventory = session.query(ProductInventory).filter(
                ProductInventory.product_id == str(product_id)
            ).first()
            
            if inventory:
                return inventory.stock
            else:
                # Если товара нет в инвентаре, добавляем его с начальным количеством
                new_inventory = ProductInventory(
                    product_id=str(product_id),
                    stock=DEFAULT_STOCK
                )
                session.add(new_inventory)
                session.commit()
                return DEFAULT_STOCK
    except Exception as e:
        # В случае ошибки, возвращаем значение по умолчанию
        return DEFAULT_STOCK

def update_product_stock(product_id, stock):
    """
    Обновляет количество товара на складе с использованием прямых SQL запросов
    
    Args:
        product_id (int): ID товара
        stock (int): Количество на складе
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = None
    try:
        session = get_database_session()
        
        # Проверяем, существует ли запись в инвентаре с защитой от ошибок схемы
        result = session.execute(
            "SELECT EXISTS(SELECT 1 FROM product_inventory WHERE product_id = :product_id)",
            {"product_id": product_id}
        ).scalar()
        
        if not result:
            # Если записи нет, создаем новую с использованием raw SQL
            session.execute(
                "INSERT INTO product_inventory (product_id, stock, reserved) VALUES (:product_id, :stock, 0)",
                {"product_id": product_id, "stock": stock}
            )
        else:
            # Если запись есть, обновляем количество
            session.execute(
                "UPDATE product_inventory SET stock = :stock WHERE product_id = :product_id",
                {"product_id": product_id, "stock": stock}
            )
        
        session.commit()
        return True
    except Exception as e:
        print(f"Error updating product stock: {e}")
        traceback.print_exc()
        if session:
            session.rollback()
        return False
    finally:
        if session:
            session.close()

def create_product(name, description, price, image_url=None, category=None):
    """
    Создает новый товар
    
    Args:
        name (str): Название товара
        description (str): Описание товара
        price (float): Цена товара
        image_url (str, optional): URL изображения товара
        category (str, optional): Категория товара
    
    Returns:
        int: ID созданного товара или None в случае ошибки
    """
    session = None
    try:
        session = get_database_session()
        
        # Создаем объект товара
        product = Product(
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            category=category
        )
        
        session.add(product)
        session.commit()
        
        product_id = product.id
        session.close()
        
        return product_id
    except Exception as e:
        print(f"Error creating product: {e}")
        traceback.print_exc()
        if session:
            session.rollback()
            session.close()
        return None

def get_all_products(include_inactive=False, category=None):
    """
    Получает список всех товаров с защитой от ошибок
    
    Args:
        include_inactive (bool): Включать ли неактивные товары
        category (str, optional): Фильтр по категории
    
    Returns:
        list: Список товаров
    """
    session = None
    try:
        session = get_database_session()
        
        # Строим запрос
        query = session.query(Product)
        
        # Применяем фильтры
        if not include_inactive:
            query = query.filter(Product.active == True)
        
        if category:
            query = query.filter(Product.category == category)
        
        # Сортируем по дате создания (сначала новые)
        query = query.order_by(Product.created_at.desc())
        
        # Выполняем запрос
        products = query.all()
        
        # Формируем результат
        result = []
        
        for product in products:
            # Получаем инвентарь с использованием raw SQL для защиты от ошибок схемы
            stock_result = session.execute(
                "SELECT stock FROM product_inventory WHERE product_id = :product_id",
                {"product_id": product.id}
            ).fetchone()
            
            stock = stock_result[0] if stock_result else 0
            
            # Добавляем товар в результат
            result.append({
                "id": product.id,
                "name": product.name,
                "description": product.description,
                "price": product.price,
                "image_url": product.image_url,
                "category": product.category,
                "stock": stock,
                "created_at": product.created_at,
                "updated_at": product.updated_at
            })
        
        return result
    except Exception as e:
        print(f"Error getting products: {e}")
        traceback.print_exc()
        return []
    finally:
        if session:
            session.close()

def get_product_by_id(product_id):
    """
    Получает информацию о товаре по его ID с защитой от ошибок
    
    Args:
        product_id (int): ID товара
    
    Returns:
        dict: Информация о товаре или None в случае ошибки
    """
    session = None
    try:
        session = get_database_session()
        
        # Получаем товар
        product = session.query(Product).filter(
            Product.id == product_id,
            Product.active == True
        ).first()
        
        if not product:
            return None
        
        # Получаем инвентарь с использованием raw SQL для защиты от ошибок схемы
        stock_result = session.execute(
            "SELECT stock FROM product_inventory WHERE product_id = :product_id",
            {"product_id": product_id}
        ).fetchone()
        
        stock = stock_result[0] if stock_result else 0
        
        # Формируем результат
        result = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "price": product.price,
            "image_url": product.image_url,
            "category": product.category,
            "stock": stock,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        }
        
        return result
    except Exception as e:
        print(f"Error getting product: {e}")
        traceback.print_exc()
        return None
    finally:
        if session:
            session.close()

def update_product(product_id, **kwargs):
    """
    Обновляет информацию о товаре
    
    Args:
        product_id (int): ID товара
        **kwargs: Параметры для обновления
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    try:
        session = get_database_session()
        
        # Получаем товар
        product = session.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            session.close()
            return False
        
        # Обновляем поля
        for key, value in kwargs.items():
            if hasattr(product, key):
                setattr(product, key, value)
        
        session.commit()
        session.close()
        
        return True
    except Exception as e:
        print(f"Error updating product: {e}")
        if session:
            session.rollback()
            session.close()
        return False

def delete_product(product_id):
    """
    Удаляет товар (помечает как неактивный)
    
    Args:
        product_id (int): ID товара
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    try:
        session = get_database_session()
        
        # Получаем товар
        product = session.query(Product).filter(Product.id == product_id).first()
        
        if not product:
            session.close()
            return False
        
        # Помечаем как неактивный
        product.active = False
        
        session.commit()
        session.close()
        
        return True
    except Exception as e:
        print(f"Error deleting product: {e}")
        if session:
            session.rollback()
            session.close()
        return False

def hard_delete_product(product_id):
    """Полное удаление товара из базы"""
    try:
        with get_database_session() as session:
            # Удаление из инвентаря
            session.query(ProductInventory).filter(
                ProductInventory.product_id == product_id
            ).delete()
            
            # Удаление товара
            product = session.query(Product).filter(Product.id == product_id).first()
            if product:
                session.delete(product)
                session.commit()
                return True
            return False
    except Exception as e:
        print(f"Error deleting product {product_id}: {e}")
        return False