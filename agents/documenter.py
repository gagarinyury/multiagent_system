"""
Агент документатор - создает документацию для кода
"""

from .base_agent import BaseAgent

class DocumenterAgent(BaseAgent):
    """
    Агент для создания документации программного кода
    """
    def __init__(self, provider=None):
        """
        Инициализация агента документатора
        
        Args:
            provider: Провайдер LLM API
        """
        super().__init__("Documenter", provider)
    
    def process(self, input_text, context=None):
        """
        Создание документации для кода
        
        Args:
            input_text: Код и другие материалы для документирования
            context: Дополнительный контекст (архитектура, требования)
            
        Returns:
            str: Документация для кода
        """
        if not self.provider or not self.provider.is_configured():
            return "Ошибка: Провайдер LLM не настроен для агента Documenter"
        
        prompt = self.create_prompt(input_text, context)
        response = self.provider.complete(prompt)
        
        return response
    
    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для документатора
        
        Args:
            input_text: Код для документирования
            context: Дополнительный контекст
            
        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else ""
        
        return f"""
        Ты опытный технический писатель. Твоя задача - создать понятную и полную документацию
        для предоставленного кода и компонентов системы.
        
        # Код и материалы для документирования:
        {input_text}
        
        # Дополнительный контекст (архитектура, требования):
        {context_str}
        
        # Инструкции:
        1. Создай документацию следующих типов:
           - Документация API (если применимо)
           - Техническая документация для разработчиков
           - Руководство пользователя (если применимо)
           - Руководство по установке и настройке
        2. Для каждого компонента/модуля:
           - Опиши его назначение
           - Укажи его взаимодействие с другими компонентами
           - Документируй публичные методы и интерфейсы
           - Укажи параметры, возвращаемые значения и исключения
        3. Для руководства пользователя:
           - Опиши основные сценарии использования
           - Предоставь пошаговые инструкции
           - Включи примеры
        
        # Формат ответа:
        Представь документацию в формате Markdown с ясной структурой, включающей:
        - Оглавление
        - Разделы для разных типов документации
        - Примеры использования
        - Диаграммы или схемы (в текстовом формате), если это поможет пониманию
        
        Сделай документацию максимально понятной как для технических, так и для нетехнических пользователей.
        """
    
    def extract_api_docs(self, doc_text):
        """
        Извлечение документации API из полного текста документации
        
        Args:
            doc_text: Полный текст документации
            
        Returns:
            str: Документация API
        """
        api_doc = ""
        lines = doc_text.split('\n')
        
        in_api_section = False
        for line in lines:
            # Проверка начала раздела API
            if "# API" in line or "## API" in line or "### API" in line:
                in_api_section = True
                api_doc += line + "\n"
            # Проверка конца раздела API (начало другого раздела того же уровня)
            elif in_api_section and line.startswith('#') and "API" not in line:
                if line.count('#') <= line.count('#'):  # Если уровень заголовка такой же или выше
                    in_api_section = False
            # Добавление строки, если мы находимся в разделе API
            elif in_api_section:
                api_doc += line + "\n"
        
        return api_doc
    
    def extract_user_guide(self, doc_text):
        """
        Извлечение руководства пользователя из полного текста документации
        
        Args:
            doc_text: Полный текст документации
            
        Returns:
            str: Руководство пользователя
        """
        user_guide = ""
        lines = doc_text.split('\n')
        
        guide_keywords = ["руководство пользователя", "user guide", "manual", "guide"]
        in_guide_section = False
        
        for line in lines:
            line_lower = line.lower()
            
            # Проверка начала раздела руководства
            if line.startswith('#') and any(keyword in line_lower for keyword in guide_keywords):
                in_guide_section = True
                user_guide += line + "\n"
            # Проверка конца раздела руководства (начало другого раздела того же уровня)
            elif in_guide_section and line.startswith('#'):
                if not any(keyword in line_lower for keyword in guide_keywords):
                    current_level = line.count('#')
                    previous_level = user_guide.split('\n')[0].count('#')
                    if current_level <= previous_level:  # Если уровень заголовка такой же или выше
                        in_guide_section = False
                        
            # Добавление строки, если мы находимся в разделе руководства
            if in_guide_section:
                user_guide += line + "\n"
        
        return user_guide
    
    def generate_html_docs(self, markdown_docs):
        """
        Преобразование Markdown-документации в HTML
        
        Args:
            markdown_docs: Документация в формате Markdown
            
        Returns:
            str: Документация в формате HTML
        """
        try:
            import markdown
            html = markdown.markdown(markdown_docs)
            
            # Добавление базового CSS для красивого отображения
            html_doc = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Документация проекта</title>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; }}
                    h1, h2, h3, h4 {{ color: #333; margin-top: 30px; }}
                    code {{ background-color: #f4f4f4; padding: 2px 5px; border-radius: 3px; }}
                    pre {{ background-color: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                    a {{ color: #0366d6; text-decoration: none; }}
                    a:hover {{ text-decoration: underline; }}
                    blockquote {{ background-color: #f9f9f9; border-left: 4px solid #ddd; padding: 10px 15px; margin: 20px 0; }}
                </style>
            </head>
            <body>
                {html}
            </body>
            </html>
            """
            
            return html_doc
            
        except ImportError:
            # Если библиотека markdown не установлена
            return f"<html><body><pre>{markdown_docs}</pre></body></html>"