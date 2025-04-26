"""
Базовый класс агента, от которого наследуются все остальные агенты
"""

class BaseAgent:
    """
    Базовый класс для всех агентов в системе
    """
    def __init__(self, name, provider=None):
        """
        Инициализация базового агента
        
        Args:
            name: Имя агента
            provider: Провайдер LLM API
        """
        self.name = name
        self.provider = provider
        self.context = {}
    
    def process(self, input_text, context=None):
        """
        Обработка запроса агентом
        
        Args:
            input_text: Входной текст для обработки
            context: Дополнительный контекст (если есть)
            
        Returns:
            str: Результат обработки
        """
        # Базовая реализация просто возвращает заглушку
        return f"[{self.name}] Заглушка. Этот метод должен быть переопределен в дочернем классе."
    
    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для LLM на основе входных данных
        
        Args:
            input_text: Входной текст
            context: Дополнительный контекст
            
        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else ""
        return f"Действуй как {self.name}. Выполни следующую задачу:\n\n{input_text}\n\nКонтекст:\n{context_str}"
    
    def set_provider(self, provider):
        """
        Установка провайдера LLM API
        
        Args:
            provider: Экземпляр провайдера
        """
        self.provider = provider
    
    def get_name(self):
        """
        Получение имени агента
        
        Returns:
            str: Имя агента
        """
        return self.name