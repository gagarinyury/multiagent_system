"""
Провайдер для работы с OpenAI GPT API
"""

import os
import requests
import json
from .base_provider import BaseProvider # Убеждаемся, что импортируем базовый класс
# Для более точного подсчета токенов OpenAI использует библиотеку tiktoken
# Если она установлена в окружении, можно ее импортировать и использовать.
# try:
# import tiktoken
# except ImportError:
# tiktoken = None


class OpenAIProvider(BaseProvider):
    """
    Провайдер для работы с OpenAI GPT API
    """
    def __init__(self, api_key=None, **kwargs):
        """
        Инициализация провайдера OpenAI

        Args:
            api_key: API ключ OpenAI (по умолчанию берется из переменных окружения)
            **kwargs: Дополнительные аргументы для базового класса (например, max_retries)
        """
        # Передаем api_key и другие параметры в конструктор базового класса
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"), **kwargs)
        self.api_url = "https://api.openai.com/v1/chat/completions"
        # Берем модель из .env или используем по умолчанию OpenAI-специфичную модель
        self.model = os.getenv("DEFAULT_GPT_MODEL", "gpt-4-turbo-preview")
        # self.encoding = tiktoken.encoding_for_model(self.model) if tiktoken else None


    def set_model(self, model):
        """
        Установка модели GPT

        Args:
            model: Название модели GPT (например, gpt-4-turbo)
        """
        self.model = model
        # if tiktoken:
        # try:
        # self.encoding = tiktoken.encoding_for_model(self.model)
        # except KeyError:
        # self.encoding = None # Неизвестная модель


    def _make_api_request(self, prompt, temperature, max_tokens):
        """
        Внутренний метод для выполнения HTTP запроса к OpenAI API.
        Реализует специфику запроса к GPT.
        """
        if not self.is_configured():
            # Этот случай должен быть обработан в complete базового класса
            raise ConnectionRefusedError("API ключ OpenAI не настроен")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
            # TODO: Добавить другие параметры API OpenAI при необходимости
        }

        # Выполняем запрос. Исключения requests.exceptions.RequestException
        # будут перехвачены в базовом классе.
        response = requests.post(self.api_url, headers=headers, json=payload)

        # Возвращаем объект ответа requests для дальнейшей обработки статуса и данных
        return response


    def _process_response(self, response):
        """
        Внутренний метод для обработки объекта ответа от requests.
        Парсит ответ API OpenAI и проверяет на ошибки.
        """
        try:
            # Проверка HTTP статуса.
            response.raise_for_status() # Поднимает HTTPError для плохих ответов (4xx или 5xx)

            response_data = response.json()

            # Проверка специфических ошибок в теле ответа OpenAI
            if "error" in response_data:
                error_type = response_data["error"].get("type", "unknown_error")
                error_message = response_data["error"].get("message", "Неизвестная ошибка API")
                # OpenAI часто возвращает ошибки с кодом 200, но с полем 'error' в теле
                return f"[Error] API вернул ошибку ({response.status_code}, {error_type}): {error_message}"


            # Извлечение успешного результата
            # У OpenAI ответ в choices
            if "choices" in response_data and len(response_data["choices"]) > 0:
                result = response_data["choices"][0].get("message", {}).get("content", "")
                # TODO: При необходимости обработать usage statistics: response_data.get("usage")
                return result
            else:
                # Неожиданный формат ответа
                return f"[Error] API вернул неожиданный формат ответа: {response.text}"

        except requests.exceptions.HTTPError as http_err:
            # Обработка специфических HTTP ошибок
            return f"[Error] HTTP ошибка API OpenAI: {http_err}"
        except json.JSONDecodeError:
            # Ошибка парсинга JSON
            return f"[Error] Некорректный JSON ответ от API OpenAI: {response.text}"
        except Exception as e:
            # Любые другие неожиданные ошибки при обработке ответа
            return f"[Error] Ошибка при обработке ответа API OpenAI: {str(e)}"


    def count_tokens(self, text):
        """
        Подсчет количества токенов в тексте для GPT.
        Если установлена библиотека tiktoken, используется она. Иначе - базовая оценка.

        Args:
            text: Входной текст

        Returns:
            int: Количество токенов
        """
        # TODO: Раскомментировать этот блок и установить tiktoken для более точного подсчета
        # if self.encoding:
        # try:
        # return len(self.encoding.encode(text))
        # except Exception:
        # pass # В случае ошибки используем базовую оценку

        # Базовая простая оценка, если tiktoken недоступен или произошла ошибка
        return super().count_tokens(text)