"""
Управление рабочими процессами (workflows) мультиагентной системы
"""

import logging

logger = logging.getLogger("multiagent_system")

class WorkflowManager:
    """
    Класс для управления различными рабочими процессами мультиагентной системы
    """
    def __init__(self, orchestrator):
        """
        Инициализация менеджера рабочих процессов
        
        Args:
            orchestrator: Экземпляр оркестратора
        """
        self.orchestrator = orchestrator
        self.available_workflows = {
            "standard": self.standard_workflow,
            "code_only": self.code_only_workflow,
            "review_only": self.review_only_workflow,
            "docs_only": self.docs_only_workflow,
            "code_to_project": self.code_to_project_workflow  # Новый рабочий процесс
        }
    
    def execute_workflow(self, workflow_name, user_input):
        """
        Выполнение рабочего процесса по имени
        
        Args:
            workflow_name: Название рабочего процесса
            user_input: Входные данные от пользователя
            
        Returns:
            dict: Результаты выполнения процесса
        """
        if workflow_name in self.available_workflows:
            logger.info(f"Запуск рабочего процесса: {workflow_name}")
            return self.available_workflows[workflow_name](user_input)
        else:
            error_message = f"Неизвестный рабочий процесс: {workflow_name}"
            logger.error(error_message)
            return {"error": error_message}
    
    def standard_workflow(self, user_input):
        """
        Стандартный рабочий процесс: Planner -> Architect -> Coder -> Reviewer -> Tester -> Documenter
        
        Args:
            user_input: Входные данные от пользователя
            
        Returns:
            dict: Результаты выполнения процесса
        """
        # Сохраняем текущие настройки агентов
        original_agents = self.orchestrator.active_agents.copy()
        
        # Устанавливаем все агенты как активные для стандартного процесса
        all_agents = {
            "Planner": True,
            "Architect": True,
            "Coder": True,
            "Reviewer": True,
            "Tester": True,
            "Documenter": True,
            "ProjectManager": False  # По умолчанию отключен в стандартном процессе
        }
        self.orchestrator.configure_agents(all_agents)
        
        # Выполняем стандартный процесс
        results = self.orchestrator.process_request(user_input)
        
        # Восстанавливаем оригинальные настройки
        self.orchestrator.configure_agents(original_agents)
        
        return results
    
    def code_only_workflow(self, user_input):
        """
        Рабочий процесс только для создания кода: Planner -> Architect -> Coder
        
        Args:
            user_input: Входные данные от пользователя
            
        Returns:
            dict: Результаты выполнения процесса
        """
        # Сохраняем текущие настройки агентов
        original_agents = self.orchestrator.active_agents.copy()
        
        # Устанавливаем только необходимые агенты
        code_agents = {
            "Planner": True,
            "Architect": True,
            "Coder": True,
            "Reviewer": False,
            "Tester": False,
            "Documenter": False,
            "ProjectManager": False
        }
        self.orchestrator.configure_agents(code_agents)
        
        # Выполняем процесс
        results = self.orchestrator.process_request(user_input)
        
        # Восстанавливаем оригинальные настройки
        self.orchestrator.configure_agents(original_agents)
        
        return results
    
    def review_only_workflow(self, user_input):
        """
        Рабочий процесс только для ревью кода: Reviewer -> Tester
        
        Args:
            user_input: Входные данные от пользователя (код)
            
        Returns:
            dict: Результаты выполнения процесса
        """
        # Сохраняем текущие настройки агентов
        original_agents = self.orchestrator.active_agents.copy()
        
        # Устанавливаем только необходимые агенты
        review_agents = {
            "Planner": False,
            "Architect": False,
            "Coder": False,
            "Reviewer": True,
            "Tester": True,
            "Documenter": False,
            "ProjectManager": False
        }
        self.orchestrator.configure_agents(review_agents)
        
        # Выполняем процесс
        results = self.orchestrator.process_request(user_input)
        
        # Восстанавливаем оригинальные настройки
        self.orchestrator.configure_agents(original_agents)
        
        return results
    
    def docs_only_workflow(self, user_input):
        """
        Рабочий процесс только для создания документации: Documenter
        
        Args:
            user_input: Входные данные от пользователя (код)
            
        Returns:
            dict: Результаты выполнения процесса
        """
        # Сохраняем текущие настройки агентов
        original_agents = self.orchestrator.active_agents.copy()
        
        # Устанавливаем только необходимые агенты
        docs_agents = {
            "Planner": False,
            "Architect": False,
            "Coder": False,
            "Reviewer": False,
            "Tester": False,
            "Documenter": True,
            "ProjectManager": False
        }
        self.orchestrator.configure_agents(docs_agents)
        
        # Выполняем процесс
        results = self.orchestrator.process_request(user_input)
        
        # Восстанавливаем оригинальные настройки
        self.orchestrator.configure_agents(original_agents)
        
        return results
    
    def code_to_project_workflow(self, user_input):
        """
        Рабочий процесс для создания проекта из кода:
        Planner -> Architect -> Coder -> ProjectManager
        
        Args:
            user_input: Входные данные от пользователя
            
        Returns:
            dict: Результаты выполнения процесса
        """
        # Сохраняем текущие настройки агентов
        original_agents = self.orchestrator.active_agents.copy()
        
        # Устанавливаем агенты для создания проекта
        project_agents = {
            "Planner": True,
            "Architect": True,
            "Coder": True,
            "Reviewer": False,
            "Tester": False,
            "Documenter": False,
            "ProjectManager": True  # Включаем ProjectManager
        }
        self.orchestrator.configure_agents(project_agents)
        
        # Проверяем, установлен ли project_manager в оркестраторе
        if hasattr(self.orchestrator, 'project_manager'):
            # Если project_manager установлен в оркестраторе, передаем его в агент
            if "ProjectManager" in self.orchestrator.agents:
                self.orchestrator.agents["ProjectManager"].project_manager = self.orchestrator.project_manager
                logger.info("ProjectManager агент настроен с project_manager из оркестратора")
        
        # Извлекаем настройки проекта из user_input (если они есть)
        project_settings = self._extract_project_settings(user_input)
        
        # Сохраняем настройки проекта в контексте
        context = {"project_settings": project_settings}
        
        # Выполняем процесс
        results = self.orchestrator.process_request(user_input)
        
        # Восстанавливаем оригинальные настройки
        self.orchestrator.configure_agents(original_agents)
        
        return results
    
    def _extract_project_settings(self, user_input):
        """
        Извлечение настроек проекта из входных данных пользователя
        
        Args:
            user_input: Текст запроса пользователя
            
        Returns:
            dict: Настройки проекта
        """
        # Базовые настройки проекта по умолчанию
        settings = {
            "project_name": None,
            "project_description": "",
            "create_structure": True
        }
        
        # Извлечение имени проекта
        project_name_indicators = ["проект:", "project:", "назови проект", "создай проект"]
        lines = user_input.lower().split('\n')
        
        for line in lines:
            for indicator in project_name_indicators:
                if indicator in line:
                    # Пытаемся извлечь имя проекта после индикатора
                    parts = line.split(indicator, 1)
                    if len(parts) > 1:
                        potential_name = parts[1].strip().strip(':"\'')
                        if potential_name:
                            # Очищаем имя от недопустимых символов
                            import re
                            settings["project_name"] = re.sub(r'[^\w\-]', '_', potential_name)
                            break
        
        # Если имя проекта не найдено, используем имя по умолчанию
        if not settings["project_name"]:
            from datetime import datetime
            settings["project_name"] = f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        return settings
    
    def custom_workflow(self, user_input, agent_sequence):
        """
        Пользовательский рабочий процесс с указанной последовательностью агентов
        
        Args:
            user_input: Входные данные от пользователя
            agent_sequence: Список имен агентов в нужной последовательности
            
        Returns:
            dict: Результаты выполнения процесса
        """
        # Сохраняем текущие настройки агентов
        original_agents = self.orchestrator.active_agents.copy()
        
        # Создаем конфигурацию для указанных агентов
        custom_agents = {agent: False for agent in self.orchestrator.agents.keys()}
        for agent_name in agent_sequence:
            if agent_name in custom_agents:
                custom_agents[agent_name] = True
        
        # Устанавливаем конфигурацию
        self.orchestrator.configure_agents(custom_agents)
        
        # Выполняем процесс
        results = self.orchestrator.process_request(user_input)
        
        # Восстанавливаем оригинальные настройки
        self.orchestrator.configure_agents(original_agents)
        
        return results
    
    def get_workflow_info(self, workflow_name=None):
        """
        Получение информации о доступных рабочих процессах
        
        Args:
            workflow_name: Название конкретного процесса (опционально)
            
        Returns:
            dict: Информация о рабочих процессах
        """
        workflows_info = {
            "standard": {
                "name": "Стандартный процесс",
                "description": "Полный цикл разработки: планирование, архитектура, код, ревью, тесты, документация",
                "agents": ["Planner", "Architect", "Coder", "Reviewer", "Tester", "Documenter"]
            },
            "code_only": {
                "name": "Только код",
                "description": "Процесс генерации кода: планирование, архитектура, код",
                "agents": ["Planner", "Architect", "Coder"]
            },
            "review_only": {
                "name": "Только ревью",
                "description": "Ревью и тестирование существующего кода",
                "agents": ["Reviewer", "Tester"]
            },
            "docs_only": {
                "name": "Только документация",
                "description": "Создание документации для существующего кода",
                "agents": ["Documenter"]
            },
            "code_to_project": {
                "name": "Код в проект",
                "description": "Создание проекта на сервере: планирование, архитектура, код, создание файлов",
                "agents": ["Planner", "Architect", "Coder", "ProjectManager"]
            }
        }
        
        if workflow_name:
            return workflows_info.get(workflow_name, {"error": "Неизвестный рабочий процесс"})
        
        return workflows_info