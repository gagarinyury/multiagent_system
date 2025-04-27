"""
Провайдер для работы с Anthropic Claude API
"""

import os
import requests
import json
from .base_provider import BaseProvider # Убеждаемся, что импортируем базовый класс

class AnthropicProvider(BaseProvider):
    """
    Провайдер для работы с Anthropic Claude API
    """
    def __init__(self, api_key=None, **kwargs):
        """
        Инициализация провайдера Anthropic

        Args:
            api_key: API ключ Anthropic (по умолчанию берется из переменных окружения)
            **kwargs: Дополнительные аргументы для базового класса (например, max_retries)
        """
        # Передаем api_key и другие параметры в конструктор базового класса
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"), **kwargs)
        self.api_url = "https://api.anthropic.com/v1/messages"
        # Берем модель из .env или используем по умолчанию Anthropic-специфичную модель
        self.model = os.getenv("DEFAULT_CLAUDE_MODEL", "claude-3-7-sonnet-20250219")

    def set_model(self, model):
        """
        Установка модели Claude

        Args:
            model: Название модели Claude (например, claude-3-opus-20240229)
        """
        self.model = model

    def _make_api_request(self, prompt, temperature, max_tokens):
        """
        Внутренний метод для выполнения HTTP запроса к Anthropic API.
        Реализует специфику запроса к Claude.
        """
        if not self.is_configured():
             # Этот случай должен быть обработан в complete базового класса, но на всякий случай
            raise ConnectionRefusedError("API ключ Anthropic не настроен")

        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01" # Использование рекомендуемой версии API
        }

        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        # Выполняем запрос. Исключения requests.exceptions.RequestException
        # будут перехвачены в базовом классе.
        response = requests.post(self.api_url, headers=headers, json=payload)

        # Возвращаем объект ответа requests для дальнейшей обработки статуса и данных
        return response

    def _process_response(self, response):
        """
        Внутренний метод для обработки объекта ответа от requests.
        Парсит ответ API Anthropic и проверяет на ошибки.
        """
        try:
            # Проверка HTTP статуса. Базовый класс повторяет при исключениях,
            # но здесь мы можем обработать специфические статусы ошибок API
            # и вернуть сообщение об ошибке.
            response.raise_for_status() # Поднимает HTTPError для плохих ответов (4xx или 5xx)

            response_data = response.json()

            # Проверка специфических ошибок в теле ответа Anthropic (если они есть)
            if "error" in response_data:
                 # Формат ошибки может варьироваться, адаптируйте при необходимости
                error_type = response_data["error"].get("type", "unknown_error")
                error_message = response_data["error"].get("message", "Неизвестная ошибка API")
                return f"[Error] API вернул ошибку ({response.status_code}, {error_type}): {error_message}"


            # Извлечение успешного результата
            # У Anthropic ответ в content является списком блоков
            if "content" in response_data and isinstance(response_data["content"], list):
                 # Объединяем все текстовые блоки
                result = "".join([block["text"] for block in response_data["content"] if block.get("type") == "text"])
                return result
            else:
                 # Неожиданный формат ответа
                 return f"[Error] API вернул неожиданный формат ответа: {response.text}"

        except requests.exceptions.HTTPError as http_err:
            # Обработка специфических HTTP ошибок (например, 401, 404, 529)
             return f"[Error] HTTP ошибка API Anthropic: {http_err}"
        except json.JSONDecodeError:
            # Ошибка парсинга JSON
             return f"[Error] Некорректный JSON ответ от API Anthropic: {response.text}"
        except Exception as e:
            # Любые другие неожиданные ошибки при обработке ответа
             return f"[Error] Ошибка при обработке ответа API Anthropic: {str(e)}"


    def count_tokens(self, text):
        """
        Подсчет количества токенов в тексте для Claude.
        Anthropic предоставляет утилиты для более точного подсчета токенов.
        Для простоты пока оставим базовую оценку.
        """
        # TODO: Интегрировать более точный подсчет токенов от Anthropic, если доступно
        return super().count_tokens(text)