"""
Провайдер для работы с OpenAI GPT API
"""

import os
import requests
import json
from .base_provider import BaseProvider

class OpenAIProvider(BaseProvider):
    """
    Провайдер для работы с OpenAI GPT API
    """
    def __init__(self, api_key=None):
        """
        Инициализация провайдера OpenAI
        
        Args:
            api_key: API ключ OpenAI (по умолчанию берется из переменных окружения)
        """
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"))
        self.api_url = "https://api.openai.com/v1/chat/completions"
        self.model = "gpt-4-turbo-preview"  # Модель по умолчанию
    
    def set_model(self, model):
        """
        Установка модели GPT
        
        Args:
            model: Название модели GPT (например, gpt-4-turbo)
        """
        self.model = model
    
    def complete(self, prompt, temperature=0.7, max_tokens=1000):
        """
        Выполнение запроса к GPT API
        
        Args:
            prompt: Текст промпта
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе
            
        Returns:
            str: Ответ модели
            
        Raises:
            Exception: Если возникла ошибка при выполнении запроса
        """
        if not self.is_configured():
            return "[Error] API ключ OpenAI не настроен"
        
        # Проверка кэша
        cache_key = f"{prompt}_{temperature}_{max_tokens}_{self.model}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(self.api_url, headers=headers, json=payload)
            
            if response.status_code != 200:
                return f"[Error] API вернул ошибку: {response.status_code} - {response.text}"
            
            response_data = response.json()
            result = response_data["choices"][0]["message"]["content"]
            
            # Сохранение в кэш
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            return f"[Error] Ошибка при обращении к OpenAI API: {str(e)}"
    
    def count_tokens(self, text):
        """
        Подсчет количества токенов в тексте для GPT
        
        Args:
            text: Входной текст
            
        Returns:
            int: Приблизительное количество токенов
        """
        # GPT использует токены примерно по ~4 символа
        return len(text) // 4