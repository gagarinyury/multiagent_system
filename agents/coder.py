"""
Агент разработчик - пишет код на основе архитектуры
"""

from .base_agent import BaseAgent

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
            str: Сгенерированный код
        """
        if not self.provider or not self.provider.is_configured():
            return "Ошибка: Провайдер LLM не настроен для агента Coder"
        
        prompt = self.create_prompt(input_text, context)
        response = self.provider.complete(prompt)
        
        return response
    
    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для разработчика
        
        Args:
            input_text: Описание архитектуры
            context: Дополнительный контекст
            
        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else ""
        
        return f"""
        Ты опытный разработчик программного обеспечения. Твоя задача - написать
        код на основе предоставленной архитектуры и требований.
        
        # Архитектура:
        {input_text}
        
        # Дополнительный контекст:
        {context_str}
        
        # Инструкции:
        1. Реализуй код в соответствии с предложенной архитектурой
        2. Используй современные практики и паттерны программирования
        3. Обеспечь хорошую структуру кода, разбив его на логические модули
        4. Добавь комментарии к сложным участкам кода и функциям
        5. Учитывай требования к безопасности и производительности
        
        # Формат ответа:
        Твой ответ должен содержать:
        - Краткое описание реализованного кода
        - Основные файлы/модули с указанием их назначения
        - Полный код каждого файла с комментариями
        - Инструкции по сборке и запуску (если применимо)
        
        Используй блоки кода Markdown для представления кода:
        ```[язык]
        код
        ```
        """
    
    def extract_file_blocks(self, code_text):
        """
        Извлечение блоков кода из текста с указанием имен файлов
        
        Args:
            code_text: Текст с блоками кода
            
        Returns:
            dict: Словарь {имя_файла: код}
        """
        file_blocks = {}
        lines = code_text.split('\n')
        
        current_file = None
        current_code = []
        in_code_block = False
        
        for line in lines:
            # Ищем строки с указанием имени файла (обычно перед блоком кода)
            if not in_code_block and '`' not in line:
                file_indicators = ['файл:', 'file:', 'module:', 'модуль:']
                for indicator in file_indicators:
                    if indicator in line.lower():
                        parts = line.split(indicator, 1)
                        if len(parts) > 1:
                            potential_file = parts[1].strip().strip('`" \t:')
                            if '.' in potential_file and '/' not in potential_file and ' ' not in potential_file:
                                current_file = potential_file
            
            # Обработка блоков кода
            if '```' in line:
                if in_code_block:
                    # Закрытие блока кода
                    in_code_block = False
                    if current_file and current_code:
                        file_blocks[current_file] = '\n'.join(current_code)
                        current_code = []
                else:
                    # Начало блока кода
                    in_code_block = True
                    # Если имя файла указано непосредственно в открывающем теге блока кода
                    if ':' in line and '`' in line:
                        before_backtick = line.split('```', 1)[0]
                        if ':' in before_backtick:
                            potential_file = before_backtick.split(':', 1)[1].strip()
                            if '.' in potential_file and ' ' not in potential_file:
                                current_file = potential_file
            elif in_code_block:
                # Внутри блока кода
                current_code.append(line)
        
        return file_blocks
    
    def detect_language(self, filename):
        """
        Определение языка программирования по имени файла
        
        Args:
            filename: Имя файла
            
        Returns:
            str: Язык программирования
        """
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
            '.md': 'markdown'
        }
        
        for ext, lang in extensions.items():
            if filename.endswith(ext):
                return lang
        
        return 'plaintext'  # если не удалось определить