from sqlalchemy import inspect, text
from .database import engine

def check_database_structure():
    """Проверяет структуру базы данных и выводит информацию о таблицах"""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    print(f"Найдено таблиц в базе данных: {len(tables)}")
    
    for table in tables:
        print(f"\nТаблица: {table}")
        columns = inspector.get_columns(table)
        print(f"Колонки ({len(columns)}):")
        for column in columns:
            print(f"  - {column['name']} ({column['type']})")

def fix_inventory_table():
    """
    Исправляет таблицу инвентаря, создавая её с правильной структурой
    """
    # Используем современный подход с контекстным менеджером
    with engine.connect() as connection:
        try:
            # Проверяем существование таблицы
            result = connection.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='product_inventory'"))
            table_exists = result.fetchone() is not None
            
            if table_exists:
                # Получаем информацию о структуре таблицы
                try:
                    columns = connection.execute(text("PRAGMA table_info(product_inventory)")).fetchall()
                    column_names = [col[1] for col in columns]
                    
                    # Если структура не соответствует ожидаемой, пересоздаем таблицу
                    expected_columns = ['id', 'product_id', 'stock', 'reserved', 'updated_at']
                    missing_columns = [col for col in expected_columns if col not in column_names]
                    
                    if missing_columns:
                        print(f"Отсутствующие колонки в таблице product_inventory: {missing_columns}")
                        print("Пересоздание таблицы inventory...")
                        
                        # Начинаем транзакцию для модификации таблицы
                        with connection.begin() as transaction:
                            # Создаем временную таблицу для сохранения данных
                            connection.execute(text("CREATE TABLE IF NOT EXISTS product_inventory_backup AS SELECT * FROM product_inventory"))
                            
                            # Удаляем старую таблицу
                            connection.execute(text("DROP TABLE product_inventory"))
                            
                            # Создаем новую таблицу с правильной структурой
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
                            
                            # Пытаемся восстановить данные
                            try:
                                connection.execute(text("""
                                    INSERT INTO product_inventory (product_id, stock)
                                    SELECT product_id, stock FROM product_inventory_backup
                                """))
                            except Exception as e:
                                print(f"Не удалось восстановить данные из backup: {e}")
                            
                            # Удаляем временную таблицу
                            connection.execute(text("DROP TABLE IF EXISTS product_inventory_backup"))
                        
                        print("Таблица product_inventory успешно пересоздана")
                    else:
                        print("Структура таблицы product_inventory корректна")
                except Exception as e:
                    print(f"Ошибка при проверке структуры таблицы: {e}")
                    # Если произошла ошибка при проверке, пересоздаем таблицу в новой транзакции
                    with connection.begin() as transaction:
                        connection.execute(text("DROP TABLE IF EXISTS product_inventory"))
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
                    print("Таблица product_inventory создана заново из-за ошибки")
            else:
                # Создаем таблицу с нуля в отдельной транзакции
                with connection.begin() as transaction:
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
                print("Таблица product_inventory успешно создана")
            
        except Exception as e:
            print(f"Ошибка при исправлении таблицы inventory: {e}")