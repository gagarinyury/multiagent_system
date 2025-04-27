"""
Базовый класс провайдера LLM API
"""

import time
import requests # Импортируем requests, так как дочерние классы будут его использовать

class BaseProvider:
    """
    Базовый класс для всех провайдеров LLM API
    """
    def __init__(self, api_key=None, max_retries=3, initial_delay_sec=1):
        """
        Инициализация провайдера

        Args:
            api_key: API ключ (опционально)
            max_retries: Максимальное количество повторных попыток при ошибке API
            initial_delay_sec: Начальная задержка между попытками в секундах
        """
        self.api_key = api_key
        self.cache = {}  # Простой кэш для повторяющихся запросов
        self.max_retries = max_retries
        self.initial_delay_sec = initial_delay_sec

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
        Выполнение запроса к LLM с повторными попытками

        Args:
            prompt: Текст промпта
            temperature: Температура генерации (0.0-1.0)
            max_tokens: Максимальное количество токенов в ответе

        Returns:
            str: Ответ модели или сообщение об ошибке после исчерпания попыток

        Raises:
            NotImplementedError: Метод _make_api_request должен быть переопределен в дочернем классе
        """
        if not self.is_configured():
            return "[Error] Провайдер LLM не настроен."

        # Проверка кэша
        cache_key = f"{prompt}_{temperature}_{max_tokens}_{getattr(self, 'model', 'unknown')}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Делаем запрос к API (реализация в дочерних классах)
                response_data = self._make_api_request(prompt, temperature, max_tokens)

                # Проверяем ответ на наличие ошибок API по статус коду или структуре ответа
                # (Эта логика будет специфична для каждого провайдера и реализована в _process_response)
                processed_result = self._process_response(response_data)

                # Если нет ошибки, возвращаем результат
                if not isinstance(processed_result, str) or not processed_result.startswith("[Error]"):
                    # Сохранение в кэш только успешных ответов
                    self.cache[cache_key] = processed_result
                    return processed_result
                else:
                    last_error = processed_result
                    # Если получена ошибка API, но не та, которую нужно повторять, выходим
                    # (Это можно уточнить в дочерних классах, пока повторяем при любой ошибке)
                    pass # Продолжаем цикл для повторной попытки

            except requests.exceptions.RequestException as e:
                last_error = f"[Error] Ошибка запроса к API ({self.__class__.__name__}): {str(e)}"
            except Exception as e:
                last_error = f"[Error] Неизвестная ошибка при обращении к провайдеру ({self.__class__.__name__}): {str(e)}"

            # Если это не последняя попытка, ждем перед следующей
            if attempt < self.max_retries - 1:
                delay = self.initial_delay_sec * (2 ** attempt) # Экспоненциальная задержка
                time.sleep(delay)

        # Если все попытки исчерпаны и результат не получен, возвращаем последнюю ошибку
        return last_error if last_error else f"[Error] Не удалось получить ответ от API после {self.max_retries} попыток."

    def _make_api_request(self, prompt, temperature, max_tokens):
        """
        Внутренний метод для выполнения HTTP запроса к API.
        Должен быть переопределен в дочернем классе.
        Возвращает сырые данные ответа API.
        """
        raise NotImplementedError("Метод _make_api_request должен быть переопределен в дочернем классе")

    def _process_response(self, response_data):
        """
        Внутренний метод для обработки сырых данных ответа API.
        Должен быть переопределен в дочернем классе.
        Возвращает обработанный результат (строку) или сообщение об ошибке.
        """
        raise NotImplementedError("Метод _process_response должен быть переопределен в дочернем классе")


    def count_tokens(self, text):
        """
        Подсчет количества токенов в тексте.
        Может быть переопределен в дочернем классе для более точного подсчета.

        Args:
            text: Входной текст

        Returns:
            int: Приблизительное количество токенов
        """
        # Базовая простая оценка: 1 токен ~ 4 символа
        return len(text) // 4