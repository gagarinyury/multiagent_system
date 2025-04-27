"""
Управление рабочими процессами (workflows) мультиагентной системы
"""

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
            "docs_only": self.docs_only_workflow
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
            return self.available_workflows[workflow_name](user_input)
        else:
            return {"error": f"Неизвестный рабочий процесс: {workflow_name}"}
    
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
            "Documenter": True
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
            "Documenter": False
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
            "Documenter": False
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
            "Documenter": True
        }
        self.orchestrator.configure_agents(docs_agents)
        
        # Выполняем процесс
        results = self.orchestrator.process_request(user_input)
        
        # Восстанавливаем оригинальные настройки
        self.orchestrator.configure_agents(original_agents)
        
        return results
    
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
            }
        }
        
        if workflow_name:
            return workflows_info.get(workflow_name, {"error": "Неизвестный рабочий процесс"})
        
        return workflows_info