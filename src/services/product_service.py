from sqlalchemy import desc

from utils import logger
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
    product = get_product_by_id(product_id)
    if product:
        return product.get('price', 0)
    return 0

def get_product_name(product_id):
    """Получение названия продукта по его ID"""
    product = get_product_by_id(product_id)
    if product:
        return product.get('name', f"Товар #{product_id}")
    return f"Товар #{product_id}"

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

def update_product_stock(product_id, quantity_change):
    """
    Обновляет количество товара на складе
    
    Args:
        product_id: ID товара
        quantity_change: Изменение количества (положительное для увеличения, отрицательное для уменьшения)
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = None
    try:
        # Преобразуем product_id в int, если он строка
        if isinstance(product_id, str) and product_id.isdigit():
            product_id = int(product_id)
            
        session = get_database_session()
        
        # Проверяем, существует ли запись в инвентаре
        result = session.execute(
            "SELECT COUNT(*) FROM product_inventory WHERE product_id = :product_id",
            {"product_id": product_id}
        ).scalar()
        
        if result == 0:
            # Если записи нет, создаем новую с указанным количеством
            # Если изменение отрицательное, устанавливаем значение 0 или соответствующее положительное
            initial_stock = max(0, quantity_change)
            session.execute(
                "INSERT INTO product_inventory (product_id, stock, reserved) VALUES (:product_id, :stock, 0)",
                {"product_id": product_id, "stock": initial_stock}
            )
        else:
            # Если запись есть, изменяем количество инкрементально
            session.execute(
                "UPDATE product_inventory SET stock = stock + :quantity_change WHERE product_id = :product_id",
                {"product_id": product_id, "quantity_change": quantity_change}
            )
        
        session.commit()
        return True
    except Exception as e:
        print(f"Error updating product stock: {e}", exc_info=True)
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
        product_id (int или str): ID товара
    
    Returns:
        dict: Информация о товаре или None в случае ошибки
    """
    session = None
    try:
        # ИСПРАВЛЕНО: Обрабатываем случай, когда product_id передается как строка
        if isinstance(product_id, str) and product_id.isdigit():
            product_id = int(product_id)
        
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
            "active": product.active,
            "created_at": product.created_at,
            "updated_at": product.updated_at
        }
        
        return result
    except Exception as e:
        print(f"Error getting product: {e}")
        import traceback
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

def get_active_products(category=None, limit=None, offset=None):
    """
    Получает список активных товаров для пользователей
    """
    session = None
    try:
        session = get_database_session()
        
        # Строим запрос только для активных товаров
        query = session.query(Product).filter(
            Product.active == True
        )
        
        # Применяем фильтр категории, если указан
        if category and category != "all":
            query = query.filter(Product.category == category)
        
        # Получаем товары с сортировкой по имени
        query = query.order_by(Product.name)
        
        # Применяем пагинацию, если указаны параметры
        if offset is not None:
            query = query.offset(offset)
        if limit is not None:
            query = query.limit(limit)
        
        products = query.all()
        
        # Формируем результат
        result = []
        
        for product in products:
            # Получаем инвентарь с использованием raw SQL
            stock_result = session.execute(
                "SELECT stock FROM product_inventory WHERE product_id = :product_id",
                {"product_id": product.id}
            ).fetchone()
            
            stock = stock_result[0] if stock_result else 0
            
            # ИСПРАВЛЕНО: Добавляем товар только если он в наличии (stock > 0)
            if stock > 0:
                result.append({
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "image_url": product.image_url,
                    "category": product.category,
                    "stock": stock
                })
        
        return result
    except Exception as e:
        print(f"Error getting active products: {e}")
        import traceback
        traceback.print_exc()
        return []
    finally:
        if session:
            session.close()

def get_product_categories():
    """
    Получает список всех уникальных категорий продуктов
    
    Returns:
        list: Список категорий
    """
    session = None
    try:
        session = get_database_session()
        
        # Получаем только уникальные категории активных товаров
        categories = session.query(Product.category).filter(
            Product.active == True, 
            Product.category != None
        ).distinct().all()
        
        # Преобразуем результат в список строк
        return [cat[0] for cat in categories if cat[0]]
    except Exception as e:
        print(f"Error getting product categories: {e}")
        return []
    finally:
        if session:
            session.close()