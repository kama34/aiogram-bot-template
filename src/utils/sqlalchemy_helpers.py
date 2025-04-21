from sqlalchemy import inspect, event
from sqlalchemy.orm import configure_mappers

def inspect_relationships(model_class):
    """
    Вспомогательная функция для проверки всех отношений в модели
    """
    mapper = inspect(model_class).mapper
    relationships = []
    
    for prop in mapper.iterate_properties:
        if hasattr(prop, 'direction'):
            relationships.append({
                'key': prop.key,
                'direction': str(prop.direction),
                'target': prop.target.name if hasattr(prop, 'target') else None
            })
    
    return relationships

def print_model_relationships(model_class):
    """
    Выводит в консоль все отношения модели
    """
    relationships = inspect_relationships(model_class)
    
    print(f"\nОтношения для модели {model_class.__name__}:")
    for rel in relationships:
        print(f"  - {rel['key']} -> {rel['target']} ({rel['direction']})")

def print_relationship_info(model_class):
    """
    Выводит информацию о настроенных отношениях для модели
    """
    mapper = inspect(model_class).mapper
    print(f"\nОтношения для модели {model_class.__name__}:")
    
    for rel in mapper.relationships:
        print(f"- {rel.key}: {rel.target.name}")
        print(f"  Стратегия загрузки: {rel.strategy_class.__name__}")
        print(f"  Внешние ключи: {[c.name for c in rel.local_columns]}")
        print(f"  Обратная ссылка: {rel.backref}")
        print(f"  Опции: {rel.strategy_options}")

def debug_query(query):
    """
    Отладочная функция для печати SQL-запроса
    """
    print(f"\nSQL: {query.statement.compile(compile_kwargs={'literal_binds': True})}")
    return query

def listen_for_relationship_errors():
    """
    Устанавливает обработчики событий для отслеживания ошибок с отношениями
    """
    @event.listens_for(configure_mappers, "before")
    def before_configure(mapper_registry):
        print("Конфигурация маппера начинается...")
    
    @event.listens_for(configure_mappers, "after")
    def after_configure(mapper_registry):
        print("Конфигурация маппера завершена успешно")