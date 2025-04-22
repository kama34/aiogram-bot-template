from services.database import get_database_session
from utils.logger import setup_logger

# Настройка логгера
logger = setup_logger('services.inventory')

def decrease_stock(product_id, quantity):
    """
    Уменьшает количество товара на складе на указанное значение
    
    Args:
        product_id: ID товара
        quantity: Количество, которое нужно вычесть
    
    Returns:
        bool: True в случае успеха, False в случае ошибки
    """
    session = None
    try:
        # Преобразуем product_id в int, если он строка
        if isinstance(product_id, str) and product_id.isdigit():
            product_id = int(product_id)
            
        session = get_database_session()
        
        # Получаем текущее количество
        result = session.execute(
            "SELECT stock FROM product_inventory WHERE product_id = :product_id",
            {"product_id": product_id}
        ).fetchone()
        
        if not result:
            # Если записи нет, создаем новую с нулевым запасом
            session.execute(
                "INSERT INTO product_inventory (product_id, stock, reserved) VALUES (:product_id, 0, 0)",
                {"product_id": product_id}
            )
            current_stock = 0
        else:
            current_stock = result[0]
        print(f"Текущий запас для товара {product_id}: {current_stock}")
        print(f"Количество для вычитания: {quantity}")
        # Вычисляем новое количество (не меньше нуля)
        new_stock = max(0, current_stock - quantity)
        
        # Обновляем запись
        session.execute(
            "UPDATE product_inventory SET stock = :stock WHERE product_id = :product_id",
            {"product_id": product_id, "stock": new_stock}
        )
        
        # Логируем изменение для отладки
        logger.info(f"Decreased stock for product {product_id}: {current_stock} -> {new_stock} (-{quantity})")
        
        session.commit()
        return True
    except Exception as e:
        logger.error(f"Error decreasing stock: {e}", exc_info=True)
        if session:
            session.rollback()
        return False
    finally:
        if session:
            session.close()