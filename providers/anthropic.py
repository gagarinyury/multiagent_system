"""
Провайдер для работы с Anthropic Claude API
"""

import os
import requests
import json
from .base_provider import BaseProvider

class AnthropicProvider(BaseProvider):
    """
    Провайдер для работы с Anthropic Claude API
    """
    def __init__(self, api_key=None):
        """
        Инициализация провайдера Anthropic
        
        Args:
            api_key: API ключ Anthropic (по умолчанию берется из переменных окружения)
        """
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"))
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.model = "claude-3-sonnet-20240229"  # Модель по умолчанию
    
    def set_model(self, model):
        """
        Установка модели Claude
        
        Args:
            model: Название модели Claude (например, claude-3-opus-20240229)
        """
        self.model = model
    
    def complete(self, prompt, temperature=0.7, max_tokens=1000):
        """
        Выполнение запроса к Claude API
        
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
            return "[Error] API ключ Anthropic не настроен"
        
        # Проверка кэша
        cache_key = f"{prompt}_{temperature}_{max_tokens}_{self.model}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        try:
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
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
            result = response_data["content"][0]["text"]
            
            # Сохранение в кэш
            self.cache[cache_key] = result
            return result
            
        except Exception as e:
            return f"[Error] Ошибка при обращении к Anthropic API: {str(e)}"
    
    def count_tokens(self, text):
        """
        Подсчет количества токенов в тексте для Claude
        
        Args:
            text: Входной текст
            
        Returns:
            int: Приблизительное количество токенов
        """
        # Claude использует токены примерно по ~4 символа
        return len(text) // 4