"""
Агент разработчик - пишет код на основе архитектуры
"""

from .base_agent import BaseAgent
import logging # Импортируем модуль логирования

logger = logging.getLogger("multiagent_system") # Получаем логгер

class CoderAgent(BaseAgent):
    """
    Агент для написания программного кода
    """
    def __init__(self, provider=None):
        """
        Инициализация агента разработчика

        Args:
            provider: Провайдер LLM API
        """
        super().__init__("Coder", provider)

    def process(self, input_text, context=None):
        """
        Генерация кода на основе архитектуры и требований

        Args:
            input_text: Описание архитектуры от ArchitectAgent
            context: Дополнительный контекст (план, требования)

        Returns:
            str: Сгенерированный код или сообщение об ошибке
        """
        logger.info("CoderAgent: Начат процесс генерации кода.")
        if not self.provider or not self.provider.is_configured():
            error_message = "Ошибка: Провайдер LLM не настроен для агента Coder"
            logger.error(error_message)
            return error_message

        prompt = self.create_prompt(input_text, context)
        # Используем базовый метод complete, который включает повторные попытки
        response = self.provider.complete(prompt)

        if isinstance(response, str) and response.startswith("[Error]"):
             logger.error(f"CoderAgent: Ошибка при получении ответа от LLM: {response}")
             return response # Возвращаем ошибку дальше по цепочке

        logger.info("CoderAgent: Генерация кода завершена успешно.")
        return response # Возвращаем сгенерированный код

    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для разработчика.
        Промпт усилен инструкциями для генерации более качественного кода.

        Args:
            input_text: Описание архитектуры или предыдущий результат
            context: Дополнительный контекст (план, требования и т.д.)

        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else "Дополнительный контекст отсутствует."

        # Улучшенный промпт с акцентом на качество, полноту и корректность
        return f"""
        Ты опытный и аккуратный разработчик программного обеспечения. Твоя основная задача - написать
        полный, корректный и работающий код на основе предоставленной архитектуры и требований.
        Уделяй особое внимание деталям и лучшим практикам.

        # Задача и Архитектура:
        {input_text}

        # Дополнительный Контекст (План, Требования и т.д.):
        {context_str}

        # Ключевые Инструкции по Написанию Кода:
        1.  **Строго следуй архитектуре и плану.** Убедись, что все основные компоненты и их взаимодействие реализованы.
        2.  **Пиши чистый, читаемый и поддерживаемый код.** Используй понятные имена переменных, функций и классов. Следуй стандартам кодирования для выбранного языка (например, PEP 8 для Python).
        3.  **Реализуй необходимую обработку ошибок.** Предвиди потенциальные ошибки (например, ошибки API, некорректный ввод) и добавь соответствующие механизмы их обработки (try-except блоки, проверка статусов ответов и т.д.).
        4.  **Добавляй валидацию входных данных** там, где это необходимо для предотвращения некорректного поведения или уязвимостей.
        5.  **Включай логирование** важных событий, ошибок и предупреждений, используя стандартные библиотеки логирования.
        6.  **Разбивай код на логические модули/файлы** в соответствии с архитектурой.
        7.  **Предоставляй полный код каждого файла.** Не оставляй заглушек или нереализованных частей, если это не явно указано в задаче. Убедись, что все импорты прописаны.
        8.  **Добавляй комментарии** к сложным участкам кода, функциям и классам, объясняя их назначение и логику.
        9.  **Включай инструкции по установке зависимостей и запуску** приложения, если это применимо.
        10. **Убедись, что генерируемый код полностью соответствует задаче** и готов к немедленному тестированию/ревью.

        # Формат вывода:
        Представь свой ответ в структурированном формате Markdown, включая:
        - Краткое описание реализованного кода.
        - Список основных файлов/модулей с их назначением.
        - **Полный и готовый к использованию код каждого файла** в отдельных блоках кода Markdown. Используй правильное обозначение языка (например, ```python, ```javascript).
        - Инструкции по сборке и запуску (если требуется).

        ```[язык]
        # КОД ПЕРВОГО ФАЙЛА
        ```

        ```[язык]
        # КОД ВТОРОГО ФАЙЛА
        ```
        ... и так далее для всех файлов.

        Генерируй только код и пояснения, запрошенные в формате вывода. Не включай лишний текст или размышления.
        """

    def extract_file_blocks(self, code_text):
        """
        Извлечение блоков кода из текста с указанием имен файлов.
        Может потребовать доработки, если формат вывода LLM изменится.
        """
        # Текущая реализация кажется достаточно гибкой для парсинга блоков Markdown.
        # Оставим ее пока без изменений. Если LLM будет часто отклоняться от формата,
        # возможно, потребуется ее доработать или добавить более строгий парсинг.
        file_blocks = {}
        lines = code_text.split('\n')

        current_file = None
        current_code = []
        in_code_block = False
        code_block_language = None

        for line in lines:
            # Ищем строки с указанием имени файла перед блоком кода
            if not in_code_block and '`' not in line:
                file_indicators = ['файл:', 'file:', 'module:', 'модуль:', 'путь:','path:']
                for indicator in file_indicators:
                    if indicator in line.lower():
                        parts = line.split(indicator, 1)
                        if len(parts) > 1:
                            # Пытаемся извлечь имя файла, очищая от лишних символов
                            potential_file = parts[1].strip().strip('`"\' \t:')
                            # Простая проверка, похоже ли это на имя файла (содержит точку)
                            if '.' in potential_file:
                                current_file = potential_file.replace('```', '').strip() # Удаляем '```' если он попал сюда
                                # Очищаем от относительных путей, которые могут указывать вверх по дереву
                                if current_file.startswith('/') or '..' in current_file:
                                     logger.warning(f"CoderAgent: Потенциально опасное имя файла обнаружено: {current_file}. Пропускаем.")
                                     current_file = None # Игнорируем потенциально опасные пути
                                else:
                                     logger.debug(f"CoderAgent: Извлечено имя файла: {current_file}")


            # Обработка блоков кода Markdown
            code_block_match = re.match(r'^\s*```([a-zA-Z0-9_+-]*)\s*$', line)
            if code_block_match:
                if in_code_block:
                    # Закрытие блока кода
                    in_code_block = False
                    if current_file and current_code:
                        file_blocks[current_file] = '\n'.join(current_code)
                        logger.debug(f"CoderAgent: Сохранен блок кода для файла: {current_file}")
                        current_code = []
                        current_file = None # Сбрасываем имя файла после сохранения блока
                    else:
                         # Если блок кода закрыт, но нет имени файла или кода, просто сбрасываем состояние
                         current_code = []
                         current_file = None
                    code_block_language = None # Сбрасываем язык
                else:
                    # Начало блока кода
                    in_code_block = True
                    code_block_language = code_block_match.group(1).strip() or None # Извлекаем язык, если указан
                    logger.debug(f"CoderAgent: Найден открывающий тег блока кода. Язык: {code_block_language}")

            elif in_code_block:
                # Внутри блока кода добавляем строки
                current_code.append(line)

        # Обработка последнего блока кода, если файл закончился внутри блока
        if in_code_block and current_file and current_code:
             file_blocks[current_file] = '\n'.join(current_code)
             logger.debug(f"CoderAgent: Сохранен последний блок кода для файла: {current_file}")


        return file_blocks


    def detect_language(self, filename):
        """
        Определение языка программирования по имени файла
        """
        # Эта функция используется для подсветки синтаксиса, текущая реализация хороша.
        # Оставим ее без изменений.
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
            '.yml': 'yaml', # Добавляем yaml
            '.yaml': 'yaml'
        }

        # Извлекаем расширение файла
        _, file_extension = os.path.splitext(filename)
        file_extension = file_extension.lower()

        return extensions.get(file_extension, 'plaintext') # Возвращаем 'plaintext' если расширение неизвестно