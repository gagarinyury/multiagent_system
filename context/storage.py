"""
Модуль для хранения и управления контекстом взаимодействия с LLM
"""

import os
import json
import sqlite3
from datetime import datetime

class ContextStorage:
    """
    Класс для хранения и оптимизации контекста взаимодействия с LLM
    """
    def __init__(self, db_path=None):
        """
        Инициализация хранилища контекста
        
        Args:
            db_path: Путь к файлу базы данных SQLite
        """
        self.db_path = db_path or os.getenv("DB_PATH", "data/db.sqlite")
        self._initialize_db()
    
    def _initialize_db(self):
        """
        Инициализация базы данных
        """
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Создание таблицы для хранения взаимодействий
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                user_input TEXT NOT NULL,
                system_response TEXT NOT NULL,
                tokens_used INTEGER,
                metadata TEXT
            )
            ''')
            
            # Создание таблицы для хранения сгенерированного кода
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                interaction_id INTEGER,
                language TEXT NOT NULL,
                code TEXT NOT NULL,
                description TEXT,
                FOREIGN KEY (interaction_id) REFERENCES interactions (id)
            )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Ошибка при инициализации базы данных: {str(e)}")
    
    def save_interaction(self, user_input, system_response, tokens_used=None, metadata=None):
        """
        Сохранение взаимодействия в базу данных
        
        Args:
            user_input: Запрос пользователя
            system_response: Ответ системы
            tokens_used: Количество использованных токенов
            metadata: Дополнительные метаданные (словарь)
            
        Returns:
            int: ID сохраненного взаимодействия
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Подсчет токенов, если не указано
            if tokens_used is None:
                tokens_used = len(user_input.split()) + len(system_response.split())
            
            # Сериализация метаданных
            metadata_json = json.dumps(metadata or {})
            
            # Вставка записи
            cursor.execute(
                "INSERT INTO interactions (timestamp, user_input, system_response, tokens_used, metadata) VALUES (?, ?, ?, ?, ?)",
                (datetime.now().isoformat(), user_input, system_response, tokens_used, metadata_json)
            )
            
            interaction_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return interaction_id
        except Exception as e:
            print(f"Ошибка при сохранении взаимодействия: {str(e)}")
            return None
    
    def save_code_snippet(self, interaction_id, language, code, description=None):
        """
        Сохранение сгенерированного кода
        
        Args:
            interaction_id: ID взаимодействия
            language: Язык программирования
            code: Код
            description: Описание кода
            
        Returns:
            int: ID сохраненного фрагмента кода
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO code_snippets (interaction_id, language, code, description) VALUES (?, ?, ?, ?)",
                (interaction_id, language, code, description)
            )
            
            snippet_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            return snippet_id
        except Exception as e:
            print(f"Ошибка при сохранении фрагмента кода: {str(e)}")
            return None
    
    def get_recent_interactions(self, limit=5):
        """
        Получение последних взаимодействий
        
        Args:
            limit: Максимальное количество взаимодействий
            
        Returns:
            list: Список взаимодействий
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM interactions ORDER BY id DESC LIMIT ?",
                (limit,)
            )
            
            interactions = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            return interactions
        except Exception as e:
            print(f"Ошибка при получении взаимодействий: {str(e)}")
            return []
    
    def get_optimized_context(self, current_input, max_tokens=2000):
        """
        Получение оптимизированного контекста для текущего запроса
        
        Args:
            current_input: Текущий запрос пользователя
            max_tokens: Максимальное количество токенов в контексте
            
        Returns:
            str: Оптимизированный контекст
        """
        try:
            # Получение последних взаимодействий
            recent_interactions = self.get_recent_interactions(10)
            
            # Базовый алгоритм для определения релевантности:
            # 1. Ищем ключевые слова из current_input в предыдущих взаимодействиях
            # 2. Выбираем наиболее релевантные
            # 3. Ограничиваем общее количество токенов
            
            # Извлечение ключевых слов из текущего запроса
            # (в реальной реализации здесь может быть TF-IDF или другие алгоритмы)
            keywords = set(current_input.lower().split())
            
            # Оценка релевантности каждого взаимодействия
            relevance_scores = []
            for interaction in recent_interactions:
                user_input = interaction["user_input"].lower()
                system_response = interaction["system_response"].lower()
                
                # Простой подсчет совпадающих слов
                matching_words = sum(1 for keyword in keywords if keyword in user_input)
                
                # Нормализация оценки
                score = matching_words / max(1, len(keywords))
                
                relevance_scores.append({
                    "interaction": interaction,
                    "score": score
                })
            
            # Сортировка по релевантности
            relevance_scores.sort(key=lambda x: x["score"], reverse=True)
            
            # Формирование оптимизированного контекста
            context_parts = []
            current_tokens = 0
            
            for item in relevance_scores:
                if item["score"] > 0.1:  # Минимальный порог релевантности
                    interaction = item["interaction"]
                    tokens_estimate = interaction["tokens_used"] or 0
                    
                    # Проверка, не превысим ли лимит токенов
                    if current_tokens + tokens_estimate <= max_tokens:
                        context_part = f"User: {interaction['user_input']}\nSystem: {interaction['system_response']}"
                        context_parts.append(context_part)
                        current_tokens += tokens_estimate
            
            # Объединение частей контекста
            if context_parts:
                return "\n\n".join(context_parts)
            else:
                return ""
        
        except Exception as e:
            print(f"Ошибка при оптимизации контекста: {str(e)}")
            return ""