import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, level=logging.INFO):
    """
    Настраивает и возвращает логгер с указанным именем и уровнем логирования
    """
    # Создаем каталог для логов, если его нет
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Создаем логгер
    logger = logging.getLogger(name)
    
    # Если логгер уже настроен, просто возвращаем его
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Создаем обработчик для записи в файл с ротацией
    file_handler = RotatingFileHandler(
        os.path.join(log_dir, f'{name.replace(".", "_")}.log'),
        maxBytes=5*1024*1024,  # 5 MB
        backupCount=3
    )
    
    # Создаем обработчик для вывода в консоль
    console_handler = logging.StreamHandler()
    
    # Устанавливаем формат логов
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики в логгер
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create a default bot logger
bot_logger = setup_logger('bot')