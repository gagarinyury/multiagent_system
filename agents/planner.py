"""
Агент планировщик - анализирует запросы и создает план выполнения
"""

from .base_agent import BaseAgent

class PlannerAgent(BaseAgent):
    """
    Агент для анализа задачи и создания плана выполнения
    """
    def __init__(self, provider=None):
        """
        Инициализация агента планировщика
        
        Args:
            provider: Провайдер LLM API
        """
        super().__init__("Planner", provider)
    
    def process(self, input_text, context=None):
        """
        Создание плана выполнения задачи
        
        Args:
            input_text: Описание задачи
            context: Дополнительный контекст (если есть)
            
        Returns:
            str: План выполнения задачи
        """
        if not self.provider or not self.provider.is_configured():
            return "Ошибка: Провайдер LLM не настроен для агента Planner"
        
        prompt = self.create_prompt(input_text, context)
        response = self.provider.complete(prompt)
        
        return response
    
    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для планировщика
        
        Args:
            input_text: Описание задачи
            context: Дополнительный контекст
            
        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else ""
        
        return f"""
        Ты опытный планировщик проектов по разработке программного обеспечения. Твоя задача - проанализировать 
        требования и создать структурированный план выполнения задачи.
        
        # Задача:
        {input_text}
        
        # Дополнительный контекст:
        {context_str}
        
        # Инструкции:
        1. Проанализируй задачу и разбей её на логические этапы
        2. Для каждого этапа определи конкретные подзадачи
        3. Укажи, какие технологии, библиотеки или инструменты потребуются
        4. Определи приоритеты и последовательность выполнения
        5. Оцени сложность и приблизительное время выполнения каждого этапа
        
        # Формат ответа:
        Твой ответ должен содержать:
        - Краткое описание понимания задачи (1-2 предложения)
        - Основные этапы выполнения (пронумерованный список)
        - Для каждого этапа: подзадачи, технологии, время выполнения
        - Потенциальные риски и способы их смягчения
        - Общую оценку сложности проекта по шкале от 1 до 10
        
        Представь ответ в формате Markdown с ясной структурой.
        """
    
    def extract_tasks(self, plan_text):
        """
        Извлечение списка задач из сгенерированного плана
        
        Args:
            plan_text: Текст плана
            
        Returns:
            list: Список задач
        """
        tasks = []
        
        # Простая реализация - поиск строк, начинающихся с цифры и точки или дефиса
        lines = plan_text.split('\n')
        for line in lines:
            line = line.strip()
            # Поиск строк вида "1. Задача" или "- Задача"
            if (line and (line[0].isdigit() and '. ' in line[:4]) or line.startswith('- ')):
                # Удаление префикса нумерации или маркера списка
                if line[0].isdigit():
                    task = line[line.find('.')+1:].strip()
                else:
                    task = line[1:].strip()
                
                if task:
                    tasks.append(task)
        
        return tasks
    
    def estimate_complexity(self, plan_text):
        """
        Оценка сложности задачи на основе плана
        
        Args:
            plan_text: Текст плана
            
        Returns:
            int: Оценка сложности от 1 до 10
        """
        # Поиск строки с оценкой сложности
        for line in plan_text.split('\n'):
            if 'сложност' in line.lower() and 'шкал' in line.lower():
                # Поиск числа от 1 до 10 в строке
                import re
                complexity_matches = re.findall(r'\b([1-9]|10)\b', line)
                if complexity_matches:
                    return int(complexity_matches[0])
        
        # Если не нашли явную оценку, оцениваем по количеству задач
        tasks = self.extract_tasks(plan_text)
        tasks_count = len(tasks)
        
        if tasks_count <= 3:
            return 2
        elif tasks_count <= 5:
            return 4
        elif tasks_count <= 8:
            return 6
        elif tasks_count <= 12:
            return 8
        else:
            return 10