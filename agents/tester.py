"""
Агент тестировщик - создает тесты для кода
"""

from .base_agent import BaseAgent

class TesterAgent(BaseAgent):
    """
    Агент для создания тестов программного кода
    """
    def __init__(self, provider=None):
        """
        Инициализация агента тестировщика
        
        Args:
            provider: Провайдер LLM API
        """
        super().__init__("Tester", provider)
    
    def process(self, input_text, context=None):
        """
        Создание тестов для кода
        
        Args:
            input_text: Код от CoderAgent (и, возможно, исправления от ReviewerAgent)
            context: Дополнительный контекст (архитектура, требования)
            
        Returns:
            str: Тесты для кода
        """
        if not self.provider or not self.provider.is_configured():
            return "Ошибка: Провайдер LLM не настроен для агента Tester"
        
        prompt = self.create_prompt(input_text, context)
        response = self.provider.complete(prompt)
        
        return response
    
    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для тестировщика
        
        Args:
            input_text: Код для тестирования
            context: Дополнительный контекст
            
        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else ""
        
        return f"""
        Ты опытный QA специалист и тестировщик. Твоя задача - создать разнообразные тесты 
        для предоставленного кода, которые обеспечат надежное тестирование функциональности.
        
        # Код для тестирования:
        {input_text}
        
        # Дополнительный контекст (требования, архитектура):
        {context_str}
        
        # Инструкции:
        1. Проанализируй код и выяви основные функциональные блоки
        2. Создай следующие типы тестов:
           - Модульные тесты (unit tests) для отдельных функций и классов
           - Интеграционные тесты для взаимодействия компонентов (если применимо)
           - Тесты граничных значений и особых случаев
           - Тесты для проверки обработки ошибок
        3. Для каждого теста:
           - Опиши, что он проверяет
           - Укажи входные данные и ожидаемый результат
           - Напиши полный код теста
        4. Используй подходящие библиотеки тестирования для соответствующего языка
           (например, pytest для Python, Jest для JavaScript)
        
        # Формат ответа:
        Твой ответ должен содержать:
        - Обзор тестовой стратегии
        - Структуру тестовых файлов
        - Полный код каждого тестового файла с комментариями
        - Инструкции по запуску тестов
        - Оценку тестового покрытия
        
        Для блоков кода используй формат:
        ```[язык]
        код тестов
        ```
        """
    
    def extract_test_files(self, test_text):
        """
        Извлечение блоков с тестами из текста
        
        Args:
            test_text: Текст с тестами
            
        Returns:
            dict: Словарь {имя_файла: код_теста}
        """
        test_files = {}
        lines = test_text.split('\n')
        
        current_file = None
        current_code = []
        in_code_block = False
        
        for line in lines:
            # Ищем имя файла с тестами
            if not in_code_block and ('test_' in line.lower() or '_test' in line.lower() or 'spec.' in line.lower()):
                file_indicators = ['файл:', 'file:', 'тест:', 'test:']
                
                for indicator in file_indicators:
                    if indicator in line.lower():
                        parts = line.split(indicator, 1)
                        if len(parts) > 1:
                            potential_file = parts[1].strip().strip('`" \t:')
                            if ('test' in potential_file.lower() or 'spec' in potential_file.lower()) and '.' in potential_file:
                                current_file = potential_file
            
            # Обработка блоков кода
            if '```' in line:
                if in_code_block:
                    # Закрытие блока кода
                    in_code_block = False
                    
                    # Если имя файла не было определено, пытаемся определить его из кода
                    if not current_file and current_code:
                        for code_line in current_code:
                            if 'class Test' in code_line or 'describe(' in code_line:
                                test_name = code_line.split('Test', 1)[1].split('(', 1)[0].strip() if 'class Test' in code_line else \
                                            code_line.split('describe(', 1)[1].split(',', 1)[0].strip("' \"")
                                
                                if test_name:
                                    extension = '.py' if 'class Test' in code_line else '.js'
                                    current_file = f"test_{test_name.lower()}{extension}"
                    
                    if current_file and current_code:
                        test_files[current_file] = '\n'.join(current_code)
                        current_code = []
                        # Сброс имени файла только если мы сохранили код
                        current_file = None
                else:
                    # Начало блока кода
                    in_code_block = True
            elif in_code_block:
                # Внутри блока кода
                current_code.append(line)
        
        return test_files
    
    def calculate_test_coverage(self, code_text, test_text):
        """
        Приблизительная оценка тестового покрытия
        
        Args:
            code_text: Исходный код
            test_text: Код тестов
            
        Returns:
            float: Процент покрытия от 0.0 до 100.0
        """
        # Извлечение имен функций и классов из основного кода
        code_functions = set()
        code_lines = code_text.split('\n')
        
        for line in code_lines:
            line = line.strip()
            if line.startswith('def ') or line.startswith('function '):
                # Извлечение имени функции
                function_name = line.split(' ', 1)[1].split('(', 1)[0].strip()
                code_functions.add(function_name)
            elif line.startswith('class '):
                # Извлечение имени класса
                class_name = line.split(' ', 1)[1].split('(', 1)[0].split(':', 1)[0].strip()
                code_functions.add(class_name)
        
        # Проверка упоминания этих функций и классов в тестах
        covered_functions = set()
        test_lines = test_text.split('\n')
        
        for function in code_functions:
            for line in test_lines:
                if function in line:
                    covered_functions.add(function)
                    break
        
        # Расчет процента покрытия
        if not code_functions:
            return 0.0
        
        coverage = (len(covered_functions) / len(code_functions)) * 100.0
        return coverage