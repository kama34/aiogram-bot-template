from services.database import get_database_session, ProductInventory

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

def update_product_stock(product_id, quantity_change):
    """Обновление количества товара на складе"""
    try:
        with get_database_session() as session:
            # Проверяем наличие товара в таблице инвентаря
            inventory = session.query(ProductInventory).filter(
                ProductInventory.product_id == str(product_id)
            ).first()
            
            if inventory:
                inventory.stock += quantity_change
                # Не допускаем отрицательного количества
                if inventory.stock < 0:
                    inventory.stock = 0
            else:
                # Если товара нет в инвентаре, добавляем его
                new_stock = DEFAULT_STOCK + quantity_change
                if new_stock < 0:
                    new_stock = 0
                    
                new_inventory = ProductInventory(
                    product_id=str(product_id),
                    stock=new_stock
                )
                session.add(new_inventory)
            
            session.commit()
            return True
    except Exception as e:
        return False