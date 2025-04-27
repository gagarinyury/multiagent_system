"""
Агент архитектор - проектирует архитектуру приложения
"""

from .base_agent import BaseAgent

class ArchitectAgent(BaseAgent):
    """
    Агент для проектирования архитектуры программного обеспечения
    """
    def __init__(self, provider=None):
        """
        Инициализация агента архитектора
        
        Args:
            provider: Провайдер LLM API
        """
        super().__init__("Architect", provider)
    
    def process(self, input_text, context=None):
        """
        Проектирование архитектуры программного обеспечения
        
        Args:
            input_text: Описание задачи или план от PlannerAgent
            context: Дополнительный контекст (если есть)
            
        Returns:
            str: Спроектированная архитектура
        """
        if not self.provider or not self.provider.is_configured():
            return "Ошибка: Провайдер LLM не настроен для агента Architect"
        
        prompt = self.create_prompt(input_text, context)
        response = self.provider.complete(prompt)
        
        return response
    
    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для архитектора
        
        Args:
            input_text: Описание задачи или план
            context: Дополнительный контекст
            
        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else ""
        
        return f"""
        Ты опытный архитектор программного обеспечения. Твоя задача - разработать 
        высокоуровневую архитектуру компонентов на основе описания задачи или плана.
        
        # Задача:
        {input_text}
        
        # Дополнительный контекст:
        {context_str}
        
        # Инструкции:
        1. Проанализируй требования и определи основные компоненты системы
        2. Спроектируй архитектуру, учитывая потребности в масштабируемости, безопасности и производительности
        3. Выбери подходящие технологии, библиотеки и паттерны проектирования
        4. Определи взаимодействие между компонентами
        5. Учитывай лучшие практики для выбранного стека технологий
        
        # Формат ответа:
        Твой ответ должен содержать:
        - Краткое описание архитектурного подхода
        - Диаграмму или описание основных компонентов
        - Выбор технологий с обоснованием
        - Описание взаимодействия между компонентами
        - Возможные проблемы и их решения
        
        Представь ответ в формате Markdown с ясной структурой.
        """
    
    def extract_components(self, architecture_text):
        """
        Извлечение компонентов из архитектурного описания
        
        Args:
            architecture_text: Текст архитектуры
            
        Returns:
            list: Список компонентов
        """
        components = []
        
        # Простая реализация - поиск строк с компонентами
        lines = architecture_text.split('\n')
        component_section = False
        
        for line in lines:
            line = line.strip()
            
            # Ищем раздел с компонентами
            if "компонент" in line.lower() or "component" in line.lower():
                component_section = True
                continue
                
            if component_section and line and (line.startswith('- ') or line.startswith('* ')):
                # Извлекаем название компонента
                component = line[2:].strip()
                if ':' in component:
                    component = component.split(':', 1)[0].strip()
                
                if component:
                    components.append(component)
        
        return components
    
    def get_technologies(self, architecture_text):
        """
        Извлечение используемых технологий из архитектурного описания
        
        Args:
            architecture_text: Текст архитектуры
            
        Returns:
            dict: Словарь с категориями технологий
        """
        technologies = {}
        
        # Ищем разделы с технологиями
        sections = ["front-end", "backend", "database", "devops", "технологии", "technologies"]
        tech_section = None
        
        lines = architecture_text.split('\n')
        for line in lines:
            line = line.strip().lower()
            
            # Проверяем, не начинается ли новый раздел с технологиями
            for section in sections:
                if section in line and (':' in line or '#' in line):
                    tech_section = section
                    technologies[tech_section] = []
                    break
            
            # Если мы в разделе технологий и это элемент списка
            if tech_section and line and (line.startswith('- ') or line.startswith('* ')):
                tech = line[2:].strip()
                technologies[tech_section].append(tech)
        
        return technologies