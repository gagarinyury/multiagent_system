"""
Модуль для подсчета токенов в тексте и оценки стоимости запросов к LLM
"""

import re

class TokenCounter:
    """
    Класс для подсчета токенов и оценки стоимости запросов к LLM
    """
    # Приблизительная стоимость за 1000 токенов для разных моделей
    MODEL_COSTS = {
        # Claude
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet-20240224": {"input": 0.003, "output": 0.015},
        "claude-3-haiku-20240307": {"input": 0.0003, "output": 0.0015},
        # OpenAI
        "gpt-4-turbo-preview": {"input": 0.01, "output": 0.03},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015}
    }
    
    @staticmethod
    def estimate_tokens(text):
        """
        Приблизительная оценка количества токенов в тексте
        
        Args:
            text: Входной текст
            
        Returns:
            int: Приблизительное количество токенов
        """
        if not text:
            return 0
        
        # Вариант 1: Простая эвристика (1 токен ~ 4 символа)
        return len(text) // 4
        
        # Вариант 2: Более сложная эвристика, учитывающая пробелы и пунктуацию
        # words = re.findall(r'\b\w+\b', text)
        # return int(len(words) * 1.3)  # Примерно 1.3 токена на слово
    
    @staticmethod
    def estimate_cost(model, input_tokens, output_tokens):
        """
        Расчет приблизительной стоимости запроса
        
        Args:
            model: Название модели
            input_tokens: Количество входных токенов
            output_tokens: Количество выходных токенов
            
        Returns:
            float: Приблизительная стоимость в долларах
        """
        if model not in TokenCounter.MODEL_COSTS:
            # Используем стоимость GPT-3.5 по умолчанию
            model = "gpt-3.5-turbo"
        
        costs = TokenCounter.MODEL_COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        
        return input_cost + output_cost
    
    @staticmethod
    def format_cost(cost):
        """
        Форматирование стоимости для отображения
        
        Args:
            cost: Стоимость в долларах
            
        Returns:
            str: Отформатированная строка стоимости
        """
        if cost < 0.01:
            return f"{cost * 100:.2f}¢"  # Центы
        else:
            return f"${cost:.4f}"  # Доллары