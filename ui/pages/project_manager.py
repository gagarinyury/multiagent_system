# Файл: ui/pages/project_manager.py
import streamlit as st
import os
import sys
from pathlib import Path
import json
import re

class SecureProjectManager:
    """
    Менеджер проектов с проверками безопасности
    """
    def __init__(self, projects_root="/app/projects"):
        """
        Инициализация менеджера проектов
        
        Args:
            projects_root: Корневая директория для проектов
        """
        self.projects_root = projects_root
        # Создаем корневую директорию, если не существует
        os.makedirs(self.projects_root, exist_ok=True)
    
    def _is_safe_path(self, path):
        """
        Проверка безопасности пути
        
        Args:
            path: Путь для проверки
            
        Returns:
            bool: True, если путь безопасен
        """
        # Проверка на отсутствие попыток обхода директории
        if ".." in path or "~" in path:
            return False
        
        # Проверка на допустимые символы в имени
        if not re.match(r'^[a-zA-Z0-9_\-/\.]+$', path):
            return False
        
        # Проверка на абсолютный путь
        if os.path.isabs(path):
            return False
        
        return True
    
    def _is_safe_content(self, content):
        """
        Проверка безопасности содержимого файла
        
        Args:
            content: Содержимое файла
            
        Returns:
            bool: True, если содержимое безопасно
        """
        # Пример проверки на наличие потенциально опасного кода
        dangerous_patterns = [
            r'import\s+os\s*;?\s*os\.system',
            r'subprocess\.(call|Popen|run)',
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, content):
                return False
        
        return True
    
    def create_project(self, project_name):
        """
        Создание нового проекта с проверками безопасности
        
        Args:
            project_name: Название проекта
            
        Returns:
            dict: Результат создания проекта
        """
        if not self._is_safe_path(project_name):
            return {
                "success": False,
                "message": "Недопустимое имя проекта"
            }
        
        project_path = os.path.join(self.projects_root, project_name)
        
        try:
            # Создаем директорию проекта
            os.makedirs(project_path, exist_ok=True)
            
            # Проверяем, что директория создана внутри projects_root
            real_project_path = os.path.realpath(project_path)
            real_projects_root = os.path.realpath(self.projects_root)
            
            if not real_project_path.startswith(real_projects_root):
                # Удаляем созданную директорию, если она вне projects_root
                if os.path.exists(project_path):
                    os.rmdir(project_path)
                
                return {
                    "success": False,
                    "message": "Недопустимое расположение проекта"
                }
            
            # Создаем безопасную структуру проекта
            Path(os.path.join(project_path, "src")).mkdir(exist_ok=True)
            Path(os.path.join(project_path, "docs")).mkdir(exist_ok=True)
            Path(os.path.join(project_path, "tests")).mkdir(exist_ok=True)
            
            # Создаем README.md
            readme_path = os.path.join(project_path, "README.md")
            with open(readme_path, "w") as f:
                f.write(f"# {project_name}\n\nПроект создан с помощью мультиагентной системы.\n")
            
            return {
                "success": True,
                "message": f"Проект {project_name} успешно создан",
                "project_path": project_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при создании проекта: {str(e)}"
            }
    
    def create_file(self, project_name, file_path, content):
        """
        Создание файла в проекте с проверками безопасности
        
        Args:
            project_name: Название проекта
            file_path: Путь к файлу внутри проекта
            content: Содержимое файла
            
        Returns:
            dict: Результат создания файла
        """
        if not self._is_safe_path(project_name) or not self._is_safe_path(file_path):
            return {
                "success": False,
                "message": "Недопустимый путь к файлу"
            }
        
        if not self._is_safe_content(content):
            return {
                "success": False,
                "message": "Содержимое файла содержит потенциально опасный код"
            }
        
        project_path = os.path.join(self.projects_root, project_name)
        full_file_path = os.path.join(project_path, file_path)
        
        # Проверяем, что проект существует
        if not os.path.exists(project_path) or not os.path.isdir(project_path):
            return {
                "success": False,
                "message": f"Проект {project_name} не существует"
            }
        
        try:
            # Создаем директории для файла, если их нет
            os.makedirs(os.path.dirname(full_file_path), exist_ok=True)
            
            # Проверяем, что путь к файлу находится внутри проекта
            real_file_path = os.path.realpath(full_file_path)
            real_project_path = os.path.realpath(project_path)
            
            if not real_file_path.startswith(real_project_path):
                return {
                    "success": False,
                    "message": "Недопустимое расположение файла"
                }
            
            # Записываем содержимое в файл
            with open(full_file_path, "w") as f:
                f.write(content)
                
            return {
                "success": True,
                "message": f"Файл {file_path} успешно создан в проекте {project_name}",
                "file_path": full_file_path
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Ошибка при создании файла: {str(e)}"
            }
    
    def list_projects(self):
        """
        Получение списка проектов
        
        Returns:
            list: Список проектов
        """
        try:
            return [name for name in os.listdir(self.projects_root) 
                  if os.path.isdir(os.path.join(self.projects_root, name))]
        except Exception:
            return []
    
    def list_files(self, project_name):
        """
        Получение списка файлов в проекте
        
        Args:
            project_name: Название проекта
            
        Returns:
            list: Список файлов в проекте
        """
        if not self._is_safe_path(project_name):
            return []
            
        project_path = os.path.join(self.projects_root, project_name)
        
        if not os.path.exists(project_path):
            return []
        
        result = []
        
        for root, _, files in os.walk(project_path):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_path)
                result.append(rel_path)
        
        return result
    
    def read_file(self, project_name, file_path):
        """
        Чтение содержимого файла из проекта
        
        Args:
            project_name: Название проекта
            file_path: Путь к файлу внутри проекта
            
        Returns:
            str: Содержимое файла или None в случае ошибки
        """
        if not self._is_safe_path(project_name) or not self._is_safe_path(file_path):
            return None
            
        project_path = os.path.join(self.projects_root, project_name)
        full_file_path = os.path.join(project_path, file_path)
        
        try:
            # Проверяем, что путь к файлу находится внутри проекта
            real_file_path = os.path.realpath(full_file_path)
            real_project_path = os.path.realpath(project_path)
            
            if not real_file_path.startswith(real_project_path):
                return None
                
            with open(full_file_path, "r") as f:
                return f.read()
        except Exception:
            return None


def render_project_manager_page():
    """
    Отрисовка страницы управления проектами
    """
    st.title("📁 Управление проектами")
    
    # Инициализация менеджера проектов
    projects_root = os.getenv("PROJECTS_ROOT", "projects")
    project_manager = SecureProjectManager(projects_root=projects_root)
    
    # Вкладки для разных функций
    tabs = ["Создание проекта", "Создание файлов", "Просмотр проектов"]
    selected_tab = st.tabs(tabs)
    
    # Вкладка создания проекта
    with selected_tab[0]:
        st.header("Создание нового проекта")
        
        with st.form("create_project_form"):
            project_name = st.text_input("Название проекта:")
            project_description = st.text_area("Описание проекта:")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                create_src = st.checkbox("Создать src/", value=True)
            with col2:
                create_docs = st.checkbox("Создать docs/", value=True)
            with col3:
                create_tests = st.checkbox("Создать tests/", value=True)
            
            submit_button = st.form_submit_button("Создать проект")
            
            if submit_button and project_name:
                result = project_manager.create_project(project_name)
                
                if result["success"]:
                    st.success(result["message"])
                    
                    # Создаем README.md с описанием
                    if project_description:
                        readme_content = f"# {project_name}\n\n{project_description}\n\nПроект создан с помощью мультиагентной системы.\n"
                        project_manager.create_file(project_name, "README.md", readme_content)
                else:
                    st.error(result["message"])
    
    # Вкладка создания файлов
    with selected_tab[1]:
        st.header("Создание файла в проекте")
        
        # Получаем список проектов
        projects = project_manager.list_projects()
        
        if not projects:
            st.info("Нет доступных проектов. Создайте новый проект на вкладке 'Создание проекта'.")
        else:
            with st.form("create_file_form"):
                selected_project = st.selectbox("Выберите проект:", projects)
                file_path = st.text_input("Путь к файлу (например, src/main.py):")
                
                # Предлагаем шаблоны для типичных файлов
                file_templates = {
                    "Пустой файл": "",
                    "Python скрипт": '"""\nОписание модуля\n"""\n\ndef main():\n    print("Hello, World!")\n\nif __name__ == "__main__":\n    main()',
                    "HTML страница": '<!DOCTYPE html>\n<html>\n<head>\n    <meta charset="UTF-8">\n    <title>Заголовок страницы</title>\n</head>\n<body>\n    <h1>Hello, World!</h1>\n</body>\n</html>',
                    "CSS файл": '/* Стили для страницы */\nbody {\n    font-family: Arial, sans-serif;\n    margin: 0;\n    padding: 20px;\n}',
                    "JavaScript файл": '// Описание скрипта\nfunction sayHello() {\n    console.log("Hello, World!");\n}\n\nsayHello();',
                    "README.md": '# Название проекта\n\n## Описание\n\nОписание проекта\n\n## Установка\n\nИнструкции по установке\n\n## Использование\n\nПримеры использования'
                }
                
                template = st.selectbox("Шаблон файла:", list(file_templates.keys()))
                file_content = st.text_area("Содержимое файла:", value=file_templates[template], height=300)
                
                submit_button = st.form_submit_button("Создать файл")
                
                if submit_button and selected_project and file_path and file_content is not None:
                    result = project_manager.create_file(selected_project, file_path, file_content)
                    
                    if result["success"]:
                        st.success(result["message"])
                    else:
                        st.error(result["message"])
    
    # Вкладка просмотра проектов
    with selected_tab[2]:
        st.header("Просмотр проектов и файлов")
        
        projects = project_manager.list_projects()
        
        if not projects:
            st.info("Нет доступных проектов.")
        else:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.subheader("Проекты")
                selected_project_view = st.selectbox("Выберите проект:", projects, key="view_project")
                
                if selected_project_view:
                    files = project_manager.list_files(selected_project_view)
                    
                    if not files:
                        st.info(f"В проекте {selected_project_view} нет файлов.")
                    else:
                        st.subheader("Файлы")
                        selected_file = st.selectbox("Выберите файл:", files)
            
            with col2:
                if selected_project_view and "selected_file" in locals() and selected_file:
                    st.subheader(f"Содержимое файла: {selected_file}")
                    
                    content = project_manager.read_file(selected_project_view, selected_file)
                    
                    if content is not None:
                        # Определение языка для подсветки синтаксиса
                        file_extension = selected_file.split(".")[-1] if "." in selected_file else ""
                        language_map = {
                            "py": "python",
                            "js": "javascript",
                            "html": "html",
                            "css": "css",
                            "md": "markdown",
                            "txt": "text",
                            "json": "json",
                            "xml": "xml"
                        }
                        language = language_map.get(file_extension, None)
                        
                        st.code(content, language=language)
                        
                        # Кнопка для редактирования файла в будущем
                        if st.button("Редактировать файл"):
                            st.session_state.editing_file = {
                                "project": selected_project_view,
                                "file": selected_file,
                                "content": content
                            }
                            st.info("Функция редактирования в разработке")
                    else:
                        st.error("Не удалось прочитать содержимое файла")


# Интеграция с основным приложением через multipage
if __name__ == "__main__":
    # Для возможности запуска страницы напрямую
    render_project_manager_page()