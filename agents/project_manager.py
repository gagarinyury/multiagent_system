"""
Агент менеджер проектов - создает файлы проекта на сервере или локальной машине
"""

from .base_agent import BaseAgent
import logging
import re
import os
import json
from pathlib import Path

logger = logging.getLogger("multiagent_system")

class ProjectManagerAgent(BaseAgent):
    """
    Агент для создания файлов проекта на сервере или локальной машине
    """
    def __init__(self, provider=None, project_manager=None):
        """
        Инициализация агента менеджера проектов

        Args:
            provider: Провайдер LLM API
            project_manager: Экземпляр SecureProjectManager
        """
        super().__init__("ProjectManager", provider)
        self.project_manager = project_manager

    def process(self, input_text, context=None):
        """
        Создание файлов проекта на основе сгенерированного кода

        Args:
            input_text: Код от CoderAgent (или другого агента)
            context: Дополнительный контекст или настройки проекта
                context может содержать:
                - 'project_name': имя проекта
                - 'project_path': путь к проекту (опционально)
                - 'create_structure': создавать ли стандартную структуру (по умолчанию True)

        Returns:
            str: Результаты создания проекта или сообщение об ошибке
        """
        logger.info("ProjectManagerAgent: Начат процесс создания файлов проекта.")
        
        # Проверка наличия проект-менеджера
        if not self.project_manager:
            error_message = "Ошибка: Менеджер проектов не настроен для агента ProjectManager"
            logger.error(error_message)
            return error_message

        # Получение настроек проекта из контекста
        project_settings = self._extract_project_settings(context)
        project_name = project_settings.get("project_name")
        
        if not project_name:
            # Если имя проекта не указано, создаем имя по умолчанию с временной меткой
            from datetime import datetime
            project_name = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            logger.info(f"ProjectManagerAgent: Имя проекта не указано, используется имя по умолчанию: {project_name}")
            project_settings["project_name"] = project_name

        # Извлечение блоков кода из текста
        logger.info(f"ProjectManagerAgent: Извлечение блоков кода для проекта '{project_name}'")
        try:
            file_blocks = self.extract_file_blocks(input_text)
            if not file_blocks:
                warning_message = "ProjectManagerAgent: Не удалось извлечь файлы из входных данных. Пробуем другой формат парсинга."
                logger.warning(warning_message)
                # Попробуем другой подход к извлечению - ищем блоки кода между ```
                file_blocks = self._extract_code_blocks_alternative(input_text)
                if not file_blocks:
                    return "Не удалось извлечь файлы из кода. Убедитесь, что код правильно форматирован с указанием имен файлов."
            logger.info(f"ProjectManagerAgent: Извлечено {len(file_blocks)} файлов.")
        except Exception as e:
            error_message = f"ProjectManagerAgent: Ошибка при извлечении файлов: {str(e)}"
            logger.error(error_message, exc_info=True)
            return f"[Error] {error_message}"

        # Создание проекта
        logger.info(f"ProjectManagerAgent: Создание проекта '{project_name}'")
        try:
            create_result = self.project_manager.create_project(project_name)
            if not create_result["success"]:
                error_message = f"ProjectManagerAgent: Ошибка при создании проекта: {create_result['message']}"
                logger.error(error_message)
                
                # Проверим, возможно проект уже существует
                existing_projects = self.project_manager.list_projects()
                if project_name in existing_projects:
                    logger.info(f"ProjectManagerAgent: Проект '{project_name}' уже существует, продолжаем работу с ним.")
                else:
                    return f"[Error] {error_message}"
            else:
                logger.info(f"ProjectManagerAgent: Проект '{project_name}' успешно создан.")
        except Exception as e:
            error_message = f"ProjectManagerAgent: Неожиданная ошибка при создании проекта: {str(e)}"
            logger.error(error_message, exc_info=True)
            return f"[Error] {error_message}"

        # Создание стандартной структуры, если требуется
        if project_settings.get("create_structure", True):
            logger.info(f"ProjectManagerAgent: Создание стандартной структуры для проекта '{project_name}'")
            self._create_standard_structure(project_name, file_blocks)

        # Создание файлов
        created_files = []
        errors = []

        for file_path, content in file_blocks.items():
            logger.info(f"ProjectManagerAgent: Создание файла '{file_path}' в проекте '{project_name}'")
            try:
                # Проверяем, существует ли директория для файла, и создаем её при необходимости
                file_dir = os.path.dirname(file_path)
                if file_dir and not self._directory_exists(project_name, file_dir):
                    # Создаем все необходимые директории
                    self._create_directory_with_parents(project_name, file_dir)
                
                result = self.project_manager.create_file(project_name, file_path, content)
                if result["success"]:
                    created_files.append(file_path)
                    logger.info(f"ProjectManagerAgent: Файл '{file_path}' успешно создан.")
                else:
                    errors.append(f"Ошибка при создании файла '{file_path}': {result['message']}")
                    logger.error(f"ProjectManagerAgent: {errors[-1]}")
            except Exception as e:
                error_msg = f"Неожиданная ошибка при создании файла '{file_path}': {str(e)}"
                errors.append(error_msg)
                logger.error(f"ProjectManagerAgent: {error_msg}", exc_info=True)

        # Создание файла README.md с описанием проекта, если его нет
        if "README.md" not in file_blocks and "readme.md" not in file_blocks:
            self._create_readme(project_name, project_settings, created_files)

        # Создание .gitignore, если его нет
        if ".gitignore" not in file_blocks:
            self._create_gitignore(project_name)

        # Формирование отчета о результатах
        success_count = len(created_files)
        error_count = len(errors)
        
        report = f"""## 📁 Результаты создания проекта '{project_name}'

### 📊 Общая информация:
- Создано файлов: {success_count}
- Ошибок: {error_count}
- Проект доступен по пути: `{self.project_manager.projects_root}/{project_name}`

### 📋 Список созданных файлов:
"""
        if created_files:
            for file_path in created_files:
                report += f"- `{file_path}`\n"
        else:
            report += "- *Файлы не были созданы*\n"

        if errors:
            report += "\n### ⚠️ Ошибки:\n"
            for error in errors:
                report += f"- {error}\n"

        report += f"\n### 🚀 Следующие шаги:
1. Перейдите на страницу 'Управление проектами' для просмотра и редактирования файлов.
2. Используйте команду `cd {self.project_manager.projects_root}/{project_name}` для доступа к проекту через терминал.
3. Инициализируйте Git-репозиторий: `git init`
"

        logger.info("ProjectManagerAgent: Процесс создания проекта завершен.")
        return report

    def _extract_project_settings(self, context):
        """
        Извлечение настроек проекта из контекста

        Args:
            context: Контекст с настройками проекта

        Returns:
            dict: Словарь с настройками проекта
        """
        logger.debug("ProjectManagerAgent: Извлечение настроек проекта из контекста")
        
        # Настройки по умолчанию
        default_settings = {
            "project_name": None,
            "project_description": "",
            "create_structure": True,
            "author": "MultiAgent System",
            "version": "0.1.0",
            "license": "MIT"
        }
        
        if not context:
            return default_settings
        
        # Если контекст - строка, пытаемся извлечь из нее имя проекта
        if isinstance(context, str):
            # Ищем строки, которые могут содержать имя проекта
            project_name_patterns = [
                r"проект:\s*([^,\n]+)", 
                r"project:\s*([^,\n]+)",
                r"название\s+проекта:\s*([^,\n]+)",
                r"project\s+name:\s*([^,\n]+)"
            ]
            
            for pattern in project_name_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    default_settings["project_name"] = match.group(1).strip()
                    break
            
            # Ищем описание проекта
            description_patterns = [
                r"описание:\s*([^\n]+)",
                r"description:\s*([^\n]+)"
            ]
            
            for pattern in description_patterns:
                match = re.search(pattern, context, re.IGNORECASE)
                if match:
                    default_settings["project_description"] = match.group(1).strip()
                    break
                    
            return default_settings

        # Если контекст - словарь, извлекаем настройки
        if isinstance(context, dict):
            # Если в контексте есть project_settings, используем его
            if "project_settings" in context:
                project_settings = context["project_settings"]
                if isinstance(project_settings, dict):
                    for key in default_settings.keys():
                        if key in project_settings:
                            default_settings[key] = project_settings[key]
            else:
                # Иначе проверяем ключи прямо в контексте
                for key in default_settings.keys():
                    if key in context:
                        default_settings[key] = context[key]
                
        return default_settings

    def extract_file_blocks(self, code_text):
        """
        Извлечение блоков кода из текста с указанием имен файлов.
        Адаптировано из CoderAgent.
        """
        logger.info("ProjectManagerAgent: Начато извлечение файловых блоков.")
        file_blocks = {}
        lines = code_text.split('\n')

        current_file = None
        current_code = []
        in_code_block = False
        code_block_language = None

        for line in lines:
            # Ищем строки с указанием имени файла перед блоком кода
            if not in_code_block and '`' not in line:
                file_indicators = ['файл:', 'file:', 'module:', 'модуль:', 'путь:', 'path:']
                for indicator in file_indicators:
                    if indicator in line.lower():
                        parts = line.split(indicator, 1)
                        if len(parts) > 1:
                            # Пытаемся извлечь имя файла, очищая от лишних символов
                            potential_file = parts[1].strip().strip('`"\' \t:')
                            # Простая проверка, похоже ли это на имя файла (содержит точку или слэш)
                            if '.' in potential_file or '/' in potential_file or '\\' in potential_file:
                                current_file = potential_file.replace('```', '').strip() # Удаляем '```' если он попал сюда
                                # Очищаем от относительных путей, которые могут указывать вверх по дереву
                                if current_file.startswith('/') or '..' in current_file:
                                     logger.warning(f"ProjectManagerAgent: Потенциально опасное имя файла обнаружено: {current_file}. Пропускаем.")
                                     current_file = None # Игнорируем потенциально опасные пути
                                else:
                                     logger.debug(f"ProjectManagerAgent: Извлечено имя файла: {current_file}")

            # Обработка блоков кода Markdown
            code_block_match = re.match(r'^\s*```([a-zA-Z0-9_+-]*)\s*$', line)
            if code_block_match:
                if in_code_block:
                    # Закрытие блока кода
                    in_code_block = False
                    if current_file and current_code:
                        file_blocks[current_file] = '\n'.join(current_code)
                        logger.debug(f"ProjectManagerAgent: Сохранен блок кода для файла: {current_file}")
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
                    logger.debug(f"ProjectManagerAgent: Найден открывающий тег блока кода. Язык: {code_block_language}")

            elif in_code_block:
                # Внутри блока кода добавляем строки
                current_code.append(line)

        # Обработка последнего блока кода, если файл закончился внутри блока
        if in_code_block and current_file and current_code:
             file_blocks[current_file] = '\n'.join(current_code)
             logger.debug(f"ProjectManagerAgent: Сохранен последний блок кода для файла: {current_file}")

        logger.info(f"ProjectManagerAgent: Извлечение файловых блоков завершено. Найдено {len(file_blocks)} блоков.")
        return file_blocks

    def _extract_code_blocks_alternative(self, code_text):
        """
        Альтернативный метод извлечения блоков кода, когда стандартный метод не работает.
        Ищет блоки кода между ``` и пытается определить имя файла из контекста.
        
        Args:
            code_text: Текст с кодом
            
        Returns:
            dict: Словарь {имя_файла: содержимое}
        """
        logger.info("ProjectManagerAgent: Использование альтернативного метода извлечения блоков кода.")
        file_blocks = {}
        
        # Ищем все блоки кода между ```
        code_pattern = re.compile(r'```([a-zA-Z0-9_+-]*)\n(.*?)\n```', re.DOTALL)
        code_matches = code_pattern.finditer(code_text)
        
        # Счетчик для блоков без имени
        unnamed_block_counter = 1
        
        # Словарь соответствия языков и типичных расширений файлов
        language_extensions = {
            'python': '.py',
            'javascript': '.js',
            'typescript': '.ts',
            'java': '.java',
            'cpp': '.cpp',
            'c': '.c',
            'go': '.go',
            'ruby': '.rb',
            'php': '.php',
            'rust': '.rs',
            'csharp': '.cs',
            'html': '.html',
            'css': '.css',
            'json': '.json',
            'yaml': '.yml',
            'shell': '.sh',
            'bash': '.sh',
            'sql': '.sql',
            'markdown': '.md',
            'text': '.txt'
        }
        
        for match in code_matches:
            language = match.group(1).strip()
            code_content = match.group(2)
            
            # Ищем имя файла в контексте до блока кода
            context_before = code_text[:match.start()]
            last_lines = context_before.split('\n')[-5:]  # Берем последние 5 строк перед блоком
            
            file_name = None
            
            # Ищем имя файла в последних строках перед блоком кода
            file_indicators = ['файл:', 'file:', 'module:', 'модуль:', 'путь:', 'path:']
            for line in reversed(last_lines):
                for indicator in file_indicators:
                    if indicator in line.lower():
                        parts = line.split(indicator, 1)
                        if len(parts) > 1:
                            potential_file = parts[1].strip().strip('`"\' \t:')
                            if potential_file and ('.' in potential_file or '/' in potential_file or '\\' in potential_file):
                                file_name = potential_file
                                break
                if file_name:
                    break
            
            # Если имя файла не найдено, генерируем имя на основе языка
            if not file_name:
                extension = language_extensions.get(language.lower(), '.txt') if language else '.txt'
                file_name = f"file_{unnamed_block_counter}{extension}"
                unnamed_block_counter += 1
            
            # Сохраняем блок кода
            file_blocks[file_name] = code_content
            logger.debug(f"ProjectManagerAgent: Извлечен блок кода для файла: {file_name} (альтернативный метод)")
        
        return file_blocks

    def _create_standard_structure(self, project_name, file_blocks):
        """
        Создание стандартной структуры проекта на основе языка программирования

        Args:
            project_name: Имя проекта
            file_blocks: Словарь с блоками кода
        """
        logger.info(f"ProjectManagerAgent: Создание стандартной структуры для проекта '{project_name}'")
        
        # Определение основного языка проекта
        language_type = self._detect_project_language(file_blocks)
        logger.info(f"ProjectManagerAgent: Определен основной язык проекта: {language_type}")

        # Создание стандартной структуры в зависимости от языка
        standard_dirs = {
            "python": ["src", "tests", "docs"],
            "javascript": ["src", "public", "tests"],
            "java": ["src/main/java", "src/main/resources", "src/test/java"],
            "csharp": ["src", "tests"],
            "go": ["cmd", "pkg", "internal", "docs"],
            "ruby": ["lib", "test", "docs"],
            "php": ["src", "public", "tests"],
            "unknown": ["src", "tests", "docs"]
        }

        dirs_to_create = standard_dirs.get(language_type, standard_dirs["unknown"])
        
        for directory in dirs_to_create:
            dir_path = os.path.join(directory, ".gitkeep")
            logger.info(f"ProjectManagerAgent: Создание директории '{directory}'")
            try:
                self.project_manager.create_file(project_name, dir_path, "")
                logger.info(f"ProjectManagerAgent: Директория '{directory}' создана.")
            except Exception as e:
                logger.error(f"ProjectManagerAgent: Ошибка при создании директории '{directory}': {str(e)}", exc_info=True)

    def _detect_project_language(self, file_blocks):
        """
        Определение основного языка проекта по расширениям файлов

        Args:
            file_blocks: Словарь с блоками кода

        Returns:
            str: Тип языка (python, javascript, java, csharp, go, ruby, php, unknown)
        """
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "javascript",
            ".jsx": "javascript",
            ".tsx": "javascript",
            ".java": "java",
            ".cs": "csharp",
            ".go": "go",
            ".rb": "ruby",
            ".php": "php",
            ".html": "javascript",  # Предполагаем, что HTML часто идет с JavaScript
            ".css": "javascript",
            ".json": "javascript"
        }
        
        # Подсчет файлов по языкам
        language_counts = {}
        
        for file_path in file_blocks.keys():
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            
            language = extensions.get(ext, "unknown")
            language_counts[language] = language_counts.get(language, 0) + 1
        
        # Определение языка с наибольшим количеством файлов
        max_language = max(language_counts.items(), key=lambda x: x[1], default=("unknown", 0))
        return max_language[0]

    def _directory_exists(self, project_name, directory):
        """
        Проверяет, существует ли директория в проекте
        
        Args:
            project_name: Имя проекта
            directory: Путь к директории относительно корня проекта
            
        Returns:
            bool: True, если директория существует
        """
        try:
            # Используем list_files для проверки наличия файлов в директории
            files = self.project_manager.list_files(project_name)
            for file_path in files:
                if file_path.startswith(directory + '/') or file_path == directory:
                    return True
            return False
        except Exception:
            return False
            
    def _create_directory_with_parents(self, project_name, directory):
        """
        Создает директорию и все родительские директории, если они не существуют
        
        Args:
            project_name: Имя проекта
            directory: Путь к директории относительно корня проекта
        """
        # Разбиваем путь на компоненты
        components = directory.split('/')
        current_path = ""
        
        for component in components:
            if component:
                if current_path:
                    current_path = f"{current_path}/{component}"
                else:
                    current_path = component
                
                # Проверяем существование текущей директории
                if not self._directory_exists(project_name, current_path):
                    try:
                        # Создаем пустой файл .gitkeep для обозначения директории
                        self.project_manager.create_file(project_name, f"{current_path}/.gitkeep", "")
                        logger.debug(f"ProjectManagerAgent: Создана директория '{current_path}' в проекте '{project_name}'")
                    except Exception as e:
                        logger.error(f"ProjectManagerAgent: Ошибка при создании директории '{current_path}': {str(e)}")

    def _create_readme(self, project_name, project_settings, created_files):
        """
        Создание README.md файла с описанием проекта

        Args:
            project_name: Имя проекта
            project_settings: Настройки проекта
            created_files: Список созданных файлов
        """
        logger.info(f"ProjectManagerAgent: Создание README.md для проекта '{project_name}'")
        
        description = project_settings.get("project_description", "")
        author = project_settings.get("author", "MultiAgent System")
        version = project_settings.get("version", "0.1.0")
        
        readme_content = f"""# {project_name}

{description}

## Структура проекта

```
{project_name}/
"""
        
        # Добавляем структуру файлов
        if created_files:
            for file_path in sorted(created_files):
                readme_content += f"├── {file_path}\n"
        else:
            readme_content += "└── (Пустой проект)\n"
        
        readme_content += "```\n\n"
        
        # Добавляем информацию о версии и авторе
        readme_content += f"""## Информация о проекте

- Версия: {version}
- Автор: {author}
- Создано: Мультиагентной системой

## Лицензия

{project_settings.get("license", "MIT")}
"""
        
        try:
            result = self.project_manager.create_file(project_name, "README.md", readme_content)
            if result["success"]:
                logger.info(f"ProjectManagerAgent: README.md для проекта '{project_name}' успешно создан.")
            else:
                logger.error(f"ProjectManagerAgent: Ошибка при создании README.md: {result['message']}")
        except Exception as e:
            logger.error(f"ProjectManagerAgent: Неожиданная ошибка при создании README.md: {str(e)}", exc_info=True)

    def _create_gitignore(self, project_name):
        """
        Создание .gitignore файла в зависимости от языка проекта

        Args:
            project_name: Имя проекта
        """
        logger.info(f"ProjectManagerAgent: Создание .gitignore для проекта '{project_name}'")
        
        # Получаем список файлов в проекте для определения языка
        files = self.project_manager.list_files(project_name)
        
        # Определяем язык проекта
        language_type = "unknown"
        extensions = {".py": "python", ".js": "javascript", ".java": "java", ".cs": "csharp", ".go": "go", ".rb": "ruby", ".php": "php"}
        
        for file_path in files:
            _, ext = os.path.splitext(file_path)
            ext = ext.lower()
            if ext in extensions:
                language_type = extensions[ext]
                break
        
        # Базовый .gitignore для всех проектов
        gitignore_content = """# Системные файлы
.DS_Store
Thumbs.db

# Логи
logs/
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Временные файлы
tmp/
temp/
.tmp/
.temp/

# Файлы редакторов
.idea/
.vscode/
*.swp
*.swo
*~
"""
        
        # Добавляем специфичные для языка записи
        if language_type == "python":
            gitignore_content += """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
*.egg-info/
.installed.cfg
*.egg
venv/
.venv/
.pytest_cache/
.coverage
htmlcov/
"""
        elif language_type == "javascript":
            gitignore_content += """
# JavaScript/Node.js
node_modules/
coverage/
.npm/
.yarn/
.pnp.*
.cache/
dist/
build/
.next/
.nuxt/
.vuepress/dist
.serverless/
.fusebox/
"""
        elif language_type == "java":
            gitignore_content += """
# Java
*.class
*.jar
*.war
*.ear
*.zip
*.tar.gz
*.rar
target/
.gradle/
build/
.mvn/
"""
        elif language_type == "csharp":
            gitignore_content += """
# C#
bin/
obj/
.vs/
*.user
*.suo
*.userprefs
*.sln.docstates
*.pidb
*.pdb
*.mdb
"""
        
        try:
            result = self.project_manager.create_file(project_name, ".gitignore", gitignore_content)
            if result["success"]:
                logger.info(f"ProjectManagerAgent: .gitignore для проекта '{project_name}' успешно создан.")
            else:
                logger.error(f"ProjectManagerAgent: Ошибка при создании .gitignore: {result['message']}")
        except Exception as e:
            logger.error(f"ProjectManagerAgent: Неожиданная ошибка при создании .gitignore: {str(e)}", exc_info=True)

    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для ProjectManagerAgent.
        В текущей реализации не используется, так как агент не требует
        обращения к LLM для создания файлов.

        Args:
            input_text: Код или результаты предыдущих агентов
            context: Дополнительный контекст

        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else "Дополнительный контекст отсутствует."
        
        return f"""
        Ты опытный менеджер проектов по разработке ПО. Твоя задача - проанализировать 
        предоставленный код и создать структуру проекта на сервере или локальной машине.
        
        # Код для анализа:
        {input_text}
        
        # Дополнительный контекст:
        {context_str}
        
        # Инструкции:
        1. Определи основной язык программирования проекта
        2. Создай подходящую структуру директорий
        3. Размести файлы с кодом в соответствующих директориях
        4. Создай необходимые конфигурационные файлы
        5. Убедись, что проект может быть запущен или собран
        
        # Формат ответа:
        Предоставь JSON-объект с информацией о структуре проекта:
        {
            "project_name": "имя_проекта",
            "language": "язык_программирования",
            "structure": [список файлов и директорий],
            "configs": [конфигурационные файлы],
            "commands": {
                "build": "команда для сборки",
                "run": "команда для запуска",
                "test": "команда для тестирования"
            }
        }
        """