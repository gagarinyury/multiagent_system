"""
Базовый класс провайдера LLM API
"""

class BaseProvider:
    """
    Базовый класс для всех провайдеров LLM API
    """
    def __init__(self, api_key=None):
        """
        Инициализация провайдера
        
        Args:
            api_key: API ключ (опционально)
        """
        self.api_key = api_key
        self.cache = {}  # Простой кэш для повторяющихся запросов
    
    def set_api_key(self, api_key):
        """
        Установка API ключа
        
        Args:
            api_key: API ключ
        """
        self.api_key = api_key
    
    def is_configured(self):
        """
        Проверка настройки провайдера
        
        Returns:
            bool: True, если провайдер настроен
        """
        return self.api_key is not None and len(self.api_key) > 0
    
    def complete(self, prompt, temperature=0.7, max_tokens=1000):
        """
        Выполнение запроса к LLM
        
        Args:
            prompt: Текст промпта
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            
        Returns:
            str: Ответ модели
            
        Raises:
            NotImplementedError: Метод должен быть переопределен в дочернем классе
        """
        raise NotImplementedError("Этот метод должен быть переопределен в дочернем классе")
    
    def count_tokens(self, text):
        """
        Подсчет количества токенов в тексте
        
        Args:
            text: Входной текст
            
        Returns:
            int: Приблизительное количество токенов
        """
        # Простая оценка: 1 токен ~ 4 символа
        return len(text) // 4