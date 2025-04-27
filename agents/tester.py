"""
Агент тестировщик - создает и выполняет тесты для кода
"""

from .base_agent import BaseAgent
import logging # Импортируем модуль логирования
import subprocess # Для выполнения внешних команд (запуска тестов)
import tempfile # Для создания временных файлов
import os # Для работы с файловой системой
import re # Импортируем регулярные выражения

logger = logging.getLogger("multiagent_system") # Получаем логгер


class TesterAgent(BaseAgent):
    """
    Агент для создания и выполнения тестов программного кода
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
        Создание и выполнение тестов для кода

        Args:
            input_text: Код от CoderAgent (и, возможно, исправления от ReviewerAgent)
            context: Дополнительный контекст (архитектура, требования, план)

        Returns:
            str: Результаты создания и выполнения тестов или сообщение об ошибке
        """
        logger.info("TesterAgent: Начат процесс создания и выполнения тестов.")
        if not self.provider or not self.provider.is_configured():
            error_message = "Ошибка: Провайдер LLM не настроен для агента Tester"
            logger.error(error_message)
            return error_message

        if not input_text or input_text.strip() == "":
            warning_message = "TesterAgent: Входные данные для тестирования пусты. Нет кода для тестов."
            logger.warning(warning_message)
            return warning_message # Возвращаем предупреждение, если нет кода для тестирования


        # Шаг 1: Генерация кода тестов
        logger.info("TesterAgent: Генерация кода тестов...")
        test_code_prompt = self.create_prompt(input_text, context)
        generated_test_text = self.provider.complete(test_code_prompt)

        if isinstance(generated_test_text, str) and generated_test_text.startswith("[Error]"):
             logger.error(f"TesterAgent: Ошибка при генерации кода тестов LLM: {generated_test_text}")
             return f"[Error] Ошибка при генерации кода тестов: {generated_test_text}" # Возвращаем ошибку

        logger.info("TesterAgent: Код тестов сгенерирован.")

        # Шаг 2: Извлечение кода тестов из ответа LLM
        # Используем метод extract_test_files для парсинга
        try:
            test_files = self.extract_test_files(generated_test_text)
            if not test_files:
                warning_message = "TesterAgent: LLM сгенерировал ответ, но не удалось извлечь файлы тестов."
                logger.warning(warning_message)
                # Возвращаем сгенерированный текст на случай, если его можно проанализировать вручную
                return f"{warning_message}\n\n---\nСгенерированный текст:\n{generated_test_text}"
            logger.info(f"TesterAgent: Извлечено {len(test_files)} файлов тестов.")
        except Exception as e:
            error_message = f"TesterAgent: Ошибка при извлечении файлов тестов из ответа LLM: {str(e)}"
            logger.error(error_message, exc_info=True)
            return f"[Error] {error_message}\n\n---\nСгенерированный текст:\n{generated_test_text}"


        # Шаг 3: Выполнение тестов
        # Для выполнения тестов нам нужен код, который тестируется (input_text)
        # и сгенерированный код тестов (test_files).
        # На данном этапе мы не будем запускать тесты в реальной среде
        # из соображений безопасности и сложности настройки окружения.
        # Вместо этого, мы сымитируем процесс и вернем сообщение о готовности к выполнению.
        # TODO: Реализовать безопасный запуск тестов в изолированной среде в Фазе 2.

        # В рамках Фазы 1, просто подтверждаем, что тесты готовы к выполнению и
        # оцениваем приблизительное тестовое покрытие на основе сгенерированного кода тестов.

        test_execution_result = "Автоматическое выполнение тестов пока не реализовано. Сгенерированные тесты готовы к запуску.\n\n"

        # Оценка тестового покрытия (приблизительная)
        try:
            combined_test_code = "\n".join(test_files.values())
            coverage = self.calculate_test_coverage(input_text, combined_test_code)
            test_execution_result += f"**Приблизительное тестовое покрытие:** {coverage:.2f}%\n\n"
            logger.info(f"TesterAgent: Приблизительное тестовое покрытие: {coverage:.2f}%")
        except Exception as e:
            logger.warning(f"TesterAgent: Не удалось оценить тестовое покрытие: {str(e)}", exc_info=True)
            test_execution_result += "*(Не удалось оценить тестовое покрытие)*\n\n"


        # Шаг 4: Формирование финального ответа
        # Включаем в ответ сгенерированный код тестов и информацию о готовности к выполнению.
        final_output = f"**Результаты создания и выполнения тестов:**\n{test_execution_result}"
        final_output += "**Сгенерированные файлы тестов:**\n\n"

        for filename, code in test_files.items():
            lang = self.detect_language(filename)
            final_output += f"**Файл:** `{filename}`\n"
            final_output += f"```{lang}\n{code}\n```\n\n"

        logger.info("TesterAgent: Процесс завершен.")
        return final_output


    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для тестировщика.
        Промпт усилен инструкциями для генерации выполнимых тестов.

        Args:
            input_text: Код для тестирования (от CoderAgent/ReviewerAgent)
            context: Дополнительный контекст (требования, архитектура)

        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else "Дополнительный контекст отсутствует."

        # Улучшенный промпт для тестировщика с акцентом на создание выполнимых тестов
        return f"""
        Ты опытный QA специалист и тестировщик с глубокими знаниями в написании автоматизированных тестов.
        Твоя задача - создать полный набор выполняемых тестов для предоставленного кода,
        которые обеспечат надежную проверку его функциональности и соответствие требованиям.

        # Код для тестирования:
        {input_text}

        # Дополнительный Контекст (Требования, Архитектура):
        {context_str}

        # Ключевые Инструкции по Написанию Тестов:
        1.  **Проанализируй код** и выяви все функции, классы, модули и сценарии использования, которые требуют тестирования.
        2.  **Создай модульные тесты (unit tests)** для проверки отдельных функций и методов в изоляции.
        3.  **Создай интеграционные тесты**, если это применимо, для проверки взаимодействия между компонентами.
        4.  **Включи тесты граничных значений и особых случаев**, а также тесты для проверки **обработки ошибок**.
        5.  **Используй стандартный и широко используемый фреймворк тестирования** для соответствующего языка (например, `pytest` для Python, `Jest` или `Mocha` для JavaScript, `JUnit` для Java и т.д.). Убедись, что тесты написаны в формате, который легко выполнить с помощью выбранного фреймворка.
        6.  **Предоставляй полный код каждого файла тестов.** Убедись, что все необходимые импорты прописаны и тесты готовы к запуску.
        7.  **Добавляй комментарии** к тестам, объясняя, что именно каждый тест проверяет.
        8.  **Опиши тестовую стратегию** и структуру тестовых файлов.

        # Формат вывода:
        Представь свой ответ в структурированном формате Markdown:
        -   Начни с **Обзора тестовой стратегии** и структуры тестовых файлов.
        -   Затем предоставь **Полный код каждого файла тестов** в отдельных блоках кода Markdown. Укажи имя файла и используй правильное обозначение языка для блока кода (например, ```python).
        -   В конце предоставь **Инструкции по запуску тестов** с использованием выбранного фреймворка.
        -   (Опционально) Оцени приблизительное тестовое покрытие на основе созданных тестов.

        ```[язык]
        # КОД ПЕРВОГО ФАЙЛА ТЕСТОВ
        ```

        ```[язык]
        # КОД ВТОРОГО ФАЙЛА ТЕСТОВ
        ```
        ... и так далее.

        Генерируй только код тестов и пояснения, запрошенные в формате вывода.
        """

    def extract_test_files(self, test_text):
        """
        Извлечение блоков с тестами из текста с указанием имен файлов.
        Адаптировано для поиска имен файлов перед блоками кода Markdown.
        """
        logger.info("TesterAgent: Начато извлечение файлов тестов.")
        test_files = {}
        lines = test_text.split('\n')

        current_file = None
        current_code = []
        in_code_block = False
        code_block_language = None

        # Паттерн для поиска имени файла перед блоком кода
        file_name_pattern = re.compile(r'^\s*(\*\*Файл:\*\*\s*`?([^`]+)`?)\s*$', re.IGNORECASE)


        for line in lines:
            line_strip = line.strip()

            # Ищем строки с указанием имени файла (обычно перед блоком кода)
            # Используем адаптированный паттерн
            file_match = file_name_pattern.match(line_strip)
            if not in_code_block and file_match:
                 potential_file = file_match.group(2).strip()
                 # Простая проверка на то, похоже ли это на имя файла теста
                 if ('test' in potential_file.lower() or 'spec' in potential_file.lower() or '.' in potential_file) \
                     and not potential_file.startswith('/') and '..' not in potential_file:
                      current_file = potential_file
                      logger.debug(f"TesterAgent: Извлечено имя файла теста: {current_file}")
                 else:
                      logger.debug(f"TesterAgent: Строка похожа на имя файла, но не является файлом теста: {line_strip}")


            # Обработка блоков кода Markdown
            code_block_match = re.match(r'^\s*```([a-zA-Z0-9_+-]*)\s*$', line_strip)
            if code_block_match:
                if in_code_block:
                    # Закрытие блока кода
                    in_code_block = False
                    if current_file and current_code:
                        test_files[current_file] = '\n'.join(current_code)
                        logger.debug(f"TesterAgent: Сохранен блок кода для файла: {current_file}")
                        current_code = []
                        current_file = None # Сбрасываем имя файла после сохранения блока
                    else:
                         # Если блок кода закрыт, но нет имени файла или кода, просто сбрасываем состояние
                         current_code = []
                         current_file = None
                         logger.debug("TesterAgent: Блок кода закрыт без связанного файла.")
                    code_block_language = None # Сбрасываем язык
                else:
                    # Начало блока кода
                    in_code_block = True
                    code_block_language = code_block_match.group(1).strip() or None # Извлекаем язык, если указан
                    logger.debug(f"TesterAgent: Найден открывающий тег блока кода. Язык: {code_block_language}")

            elif in_code_block:
                # Внутри блока кода добавляем строки
                current_code.append(line)

        # Обработка последнего блока кода, если файл закончился внутри блока
        if in_code_block and current_file and current_code:
             test_files[current_file] = '\n'.join(current_code)
             logger.debug(f"TesterAgent: Сохранен последний блок кода для файла: {current_file}")


        logger.info("TesterAgent: Извлечение файлов тестов завершено.")
        return test_files


    def calculate_test_coverage(self, code_text, test_text):
        """
        Приблизительная оценка тестового покрытия.
        Основана на поиске имен функций/классов из основного кода в коде тестов.
        """
        logger.info("TesterAgent: Начата оценка тестового покрытия.")
        if not code_text or not test_text:
            logger.warning("TesterAgent: Невозможно оценить тестовое покрытие: отсутствует код или тесты.")
            return 0.0

        # Извлечение имен функций и классов из основного кода
        code_functions = set()
        # Простые паттерны для поиска функций и классов в Python, JS, Java (можно расширить)
        function_patterns = {
            'python': r'^\s*def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'javascript': r'^\s*function\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(',
            'java': r'.*\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(.*\)\s*\{' # Проще, может быть не совсем точно
        }
        class_patterns = {
             'python': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*[:\(]',
             'javascript': r'^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)',
             'java': r'^\s*(public|private|protected)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)'
        }


        code_lines = code_text.split('\n')
        # Пытаемся угадать язык по содержимому или контексту (можно было бы передавать язык)
        # Пока просто ищем по всем паттернам
        detected_lang = None # TODO: Передавать язык кода для более точного парсинга


        for line in code_lines:
            line_strip = line.strip()
            # Поиск функций
            for lang, pattern in function_patterns.items():
                 match = re.search(pattern, line_strip)
                 if match:
                      func_name = match.group(1)
                      code_functions.add(func_name)
                      # logger.debug(f"Найденa функция '{func_name}' в коде.")
                      # detected_lang = lang # Можно попробовать определить язык по первой находке
                      break # Переходим к следующей строке, если найдена функция

            # Поиск классов (если функция не найдена на этой строке)
            if not match:
                 for lang, pattern in class_patterns.items():
                      match = re.search(pattern, line_strip)
                      if match:
                           # Для Java паттерн класса может захватывать спецификатор доступа
                           class_name = match.group(2) if lang == 'java' else match.group(1)
                           code_functions.add(class_name) # Добавляем имя класса в тот же набор
                           # logger.debug(f"Найден класс '{class_name}' в коде.")
                           # detected_lang = lang
                           break


        logger.info(f"TesterAgent: Найдено {len(code_functions)} функций/классов в основном коде.")

        # Проверка упоминания этих функций и классов в тестах
        covered_functions = set()
        test_lines = test_text.split('\n')
        test_text_lower = test_text.lower() # Для поиска без учета регистра

        for item_name in code_functions:
            # Ищем имя функции/класса в тексте тестов (без учета регистра)
            if item_name.lower() in test_text_lower:
                # Дополнительная проверка, что это, скорее всего, не просто случайное совпадение слова
                # Например, ищем "test_имя", "имя()" или "имя."
                # Это очень приблизительная эвристика
                if re.search(r'test_' + re.escape(item_name).lower() + r'|' + re.escape(item_name).lower() + r'\(|' + re.escape(item_name).lower() + r'\.', test_text_lower):
                     covered_functions.add(item_name)
                     # logger.debug(f"Найдено покрытие для '{item_name}'.")


        logger.info(f"TesterAgent: Найдено покрытие для {len(covered_functions)} функций/классов.")

        # Расчет процента покрытия
        if not code_functions:
            return 0.0 # Если нет функций/классов в коде, покрытие 0%

        coverage = (len(covered_functions) / len(code_functions)) * 100.0
        logger.info(f"TesterAgent: Рассчитано тестовое покрытие: {coverage:.2f}%")
        return coverage

    def detect_language(self, filename):
        """
        Определение языка программирования по имени файла.
        Переиспользуем функцию из CoderAgent или Utils.
        """
        # Поскольку эта функция дублируется, возможно, стоит вынести ее в Utils.
        # Пока оставим здесь для самодостаточности агента.
        extensions = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.html': 'html',
            '.css': 'css',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.sh': 'bash',
            '.sql': 'sql',
            '.json': 'json',
            '.xml': 'xml',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml'
        }

        _, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lower()

        return extensions.get(file_extension, 'plaintext')