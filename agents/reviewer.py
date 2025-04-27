"""
Агент ревьюер - проверяет написанный код на ошибки и улучшения
"""

from .base_agent import BaseAgent

class ReviewerAgent(BaseAgent):
    """
    Агент для ревью и улучшения программного кода
    """
    def __init__(self, provider=None):
        """
        Инициализация агента ревьюера
        
        Args:
            provider: Провайдер LLM API
        """
        super().__init__("Reviewer", provider)
    
    def process(self, input_text, context=None):
        """
        Ревью кода, поиск ошибок и предложение улучшений
        
        Args:
            input_text: Код от CoderAgent
            context: Дополнительный контекст (архитектура, план)
            
        Returns:
            str: Результаты ревью кода
        """
        if not self.provider or not self.provider.is_configured():
            return "Ошибка: Провайдер LLM не настроен для агента Reviewer"
        
        prompt = self.create_prompt(input_text, context)
        response = self.provider.complete(prompt)
        
        return response
    
    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для ревьюера
        
        Args:
            input_text: Код для ревью
            context: Дополнительный контекст
            
        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else ""
        
        return f"""
        Ты опытный ревьюер кода. Твоя задача - провести глубокое ревью предоставленного
        кода, найти ошибки, проблемы и предложить улучшения.
        
        # Код для ревью:
        {input_text}
        
        # Дополнительный контекст (архитектура, требования):
        {context_str}
        
        # Инструкции:
        1. Внимательно проанализируй предоставленный код
        2. Выяви проблемы следующих типов:
           - Синтаксические ошибки
           - Логические ошибки
           - Проблемы безопасности
           - Проблемы производительности
           - Проблемы с читаемостью и поддерживаемостью
           - Несоответствие стандартам и лучшим практикам
        3. Предложи конкретные улучшения для каждой найденной проблемы
        4. Оцени общее качество кода
        
        # Формат ответа:
        Твой ответ должен содержать:
        - Краткое резюме качества кода
        - Список найденных проблем с указанием строк кода и файлов
        - Предложения по исправлению каждой проблемы (с примером кода, где это применимо)
        - Общие рекомендации по улучшению кода
        - Оценку критичности каждой проблемы по шкале: Критичная, Серьезная, Средняя, Незначительная
        
        Для блоков с предлагаемыми исправлениями используй формат:
        ```[язык]
        исправленный код
        ```
        """
    
    def categorize_issues(self, review_text):
        """
        Категоризация проблем, найденных в коде
        
        Args:
            review_text: Текст ревью
            
        Returns:
            dict: Словарь с категориями проблем
        """
        categories = {
            "security": [],  # Безопасность
            "performance": [],  # Производительность
            "bugs": [],  # Ошибки
            "style": [],  # Стиль кода
            "architecture": []  # Архитектурные проблемы
        }
        
        # Ключевые слова для категоризации
        keywords = {
            "security": ["безопасност", "уязвимост", "инъекц", "security", "vulnerability", "injection", "xss", "csrf"],
            "performance": ["производительност", "оптимизац", "performance", "optimization", "slow", "memory leak"],
            "bugs": ["ошибк", "баг", "исключени", "bug", "error", "exception", "fail", "crash"],
            "style": ["стиль", "читаемост", "style", "readability", "convention", "pep8", "lint"],
            "architecture": ["архитектур", "дизайн", "structure", "architecture", "design pattern", "coupling"]
        }
        
        lines = review_text.split('\n')
        current_category = None
        
        for line in lines:
            line_lower = line.lower()
            
            # Определение категории по ключевым словам
            for category, words in keywords.items():
                if any(word in line_lower for word in words):
                    current_category = category
                    break
            
            # Добавление проблемы в соответствующую категорию
            if current_category and line.strip() and not line.startswith('#') and not '```' in line:
                categories[current_category].append(line.strip())
        
        return categories
    
    def calculate_quality_score(self, review_text):
        """
        Расчет приблизительной оценки качества кода на основе ревью
        
        Args:
            review_text: Текст ревью
            
        Returns:
            float: Оценка от 0.0 до 10.0
        """
        # Ищем упоминания критичных проблем
        issues_severity = {
            "critical": 0,
            "serious": 0,
            "medium": 0,
            "minor": 0
        }
        
        # Ключевые слова для определения серьезности
        severity_keywords = {
            "critical": ["критичн", "critical", "severe", "крайне серьезн"],
            "serious": ["серьезн", "serious", "major", "важн"],
            "medium": ["средн", "medium", "moderate", "умеренн"],
            "minor": ["незначительн", "minor", "trivial", "cosmetic", "низк"]
        }
        
        lines = review_text.lower().split('\n')
        for line in lines:
            for severity, keywords in severity_keywords.items():
                if any(keyword in line for keyword in keywords):
                    issues_severity[severity] += 1
        
        # Расчет оценки на основе найденных проблем
        # Критичные проблемы сильно снижают оценку, незначительные - слабо
        score = 10.0
        score -= issues_severity["critical"] * 2.0
        score -= issues_severity["serious"] * 1.0
        score -= issues_severity["medium"] * 0.5
        score -= issues_severity["minor"] * 0.1
        
        # Нормализация оценки в пределах от 0 до 10
        return max(0.0, min(10.0, score))