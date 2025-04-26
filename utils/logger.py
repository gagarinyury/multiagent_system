"""
Модуль для логирования действий и ошибок в мультиагентной системе
"""

import os
import logging
from datetime import datetime

class Logger:
    """
    Класс для логирования действий и ошибок
    """
    def __init__(self, name="multiagent_system", log_dir="logs", level=None):
        """
        Инициализация логгера
        
        Args:
            name: Имя логгера
            log_dir: Директория для хранения логов
            level: Уровень логирования (по умолчанию INFO)
        """
        # Создание директории для логов, если не существует
        os.makedirs(log_dir, exist_ok=True)
        
        # Имя файла лога с датой
        log_file = os.path.join(log_dir, f"{name}_{datetime.now().strftime('%Y%m%d')}.log")
        
        # Определение уровня логирования
        level = level or os.getenv("LOG_LEVEL", "INFO").upper()
        numeric_level = getattr(logging, level, logging.INFO)
        
        # Настройка логгера
        self.logger = logging.getLogger(name)
        self.logger.setLevel(numeric_level)
        
        # Обработчик для файла
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        
        # Обработчик для консоли
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        
        # Формат логов
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Добавление обработчиков
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def debug(self, message):
        """
        Логирование отладочного сообщения
        
        Args:
            message: Сообщение для логирования
        """
        self.logger.debug(message)
    
    def info(self, message):
        """
        Логирование информационного сообщения
        
        Args:
            message: Сообщение для логирования
        """
        self.logger.info(message)
    
    def warning(self, message):
        """
        Логирование предупреждения
        
        Args:
            message: Сообщение для логирования
        """
        self.logger.warning(message)
    
    def error(self, message, exc_info=False):
        """
        Логирование ошибки
        
        Args:
            message: Сообщение для логирования
            exc_info: Включать ли информацию об исключении
        """
        self.logger.error(message, exc_info=exc_info)
    
    def critical(self, message, exc_info=True):
        """
        Логирование критической ошибки
        
        Args:
            message: Сообщение для логирования
            exc_info: Включать ли информацию об исключении
        """
        self.logger.critical(message, exc_info=exc_info)
    
    def log_api_call(self, provider, model, tokens_in, tokens_out, duration_ms):
        """
        Логирование вызова API
        
        Args:
            provider: Провайдер API
            model: Модель
            tokens_in: Количество входных токенов
            tokens_out: Количество выходных токенов
            duration_ms: Длительность вызова в миллисекундах
        """
        self.info(f"API Call: {provider} | Model: {model} | Tokens: {tokens_in} in, {tokens_out} out | Duration: {duration_ms}ms")