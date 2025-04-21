from sqlalchemy import inspect, text
from .database import engine, Base, Product, ProductInventory

def check_table_exists(table_name):
    """Проверяет, существует ли таблица в базе данных"""
    inspector = inspect(engine)
    return table_name in inspector.get_table_names()

def run_migrations():
    """Выполняет необходимые миграции базы данных"""
    print("Запуск миграций базы данных...")
    
    # Создаем таблицы, если они не существуют
    with engine.connect() as connection:
        if not check_table_exists('products'):
            print("Создание таблицы products...")
            with connection.begin():
                Product.__table__.create(engine)
        
        if not check_table_exists('product_inventory'):
            print("Создание таблицы product_inventory...")
            with connection.begin():
                ProductInventory.__table__.create(engine)
    
    print("Миграции успешно выполнены.")

def recreate_inventory_table():
    """
    Пересоздаёт таблицу инвентаря, если её структура некорректна
    ВНИМАНИЕ: Это приведет к потере данных инвентаря
    """
    print("Принудительное пересоздание таблицы инвентаря...")
    
    with engine.connect() as connection:
        with connection.begin():
            if check_table_exists('product_inventory'):
                connection.execute(text("DROP TABLE product_inventory"))
                print("Таблица product_inventory удалена.")
            
            # Создаем таблицу заново
            connection.execute(text("""
                CREATE TABLE product_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    stock INTEGER DEFAULT 0,
                    reserved INTEGER DEFAULT 0,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id)
                )
            """))
            
            print("Таблица product_inventory пересоздана.")