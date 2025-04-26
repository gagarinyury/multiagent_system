"""
Ядро оркестратора - центральный компонент, координирующий работу агентов
"""

class Orchestrator:
    """
    Основной класс оркестратора, управляющий агентами и контекстом
    """
    def __init__(self, context_storage=None, providers=None):
        """
        Инициализация оркестратора
        
        Args:
            context_storage: Хранилище контекста
            providers: Словарь с провайдерами API для LLM
        """
        self.context_storage = context_storage
        self.providers = providers or {}
        self.active_agents = {}
        self.messages = []
    
    def set_provider_key(self, provider_name, api_key):
        """
        Установка API ключа для провайдера
        
        Args:
            provider_name: Имя провайдера ('claude', 'gpt')
            api_key: API ключ
        """
        if provider_name in self.providers:
            self.providers[provider_name].set_api_key(api_key)
            return True
        return False
    
    def configure_agents(self, active_agents):
        """
        Настройка активных агентов
        
        Args:
            active_agents: Словарь с состоянием активности агентов
        """
        self.active_agents = active_agents
    
    def get_messages(self):
        """
        Получение истории сообщений
        
        Returns:
            list: История сообщений
        """
        return self.messages
    
    def get_token_usage(self):
        """
        Получение статистики использования токенов
        
        Returns:
            dict: Статистика использования токенов
        """
        # Получение статистики использования токенов
        total_tokens = sum(m.get("tokens", 0) for m in self.messages)
        cost = total_tokens / 1000 * 0.02  # Примерный расчет
        return {
            "total": total_tokens,
            "cost": round(cost, 2)
        }
    
    def process_request(self, user_input):
        """
        Обработка запроса пользователя
        
        Args:
            user_input: Текст запроса пользователя
        
        Returns:
            str: Ответ системы
        """
        # Добавление сообщения пользователя в историю
        self.messages.append({"role": "user", "content": user_input})
        
        # Заглушка для демонстрации работы (будет заменена на реальную логику)
        result = f"Получен запрос: {user_input}\n\nЭта функциональность еще разрабатывается."
        
        # Сохранение результата
        self.messages.append({"role": "assistant", "content": result, "tokens": len(result.split())})
        
        # Здесь будет вызов context_storage.save_interaction(user_input, result)
        
        return result
    
    def _create_agent_prompt(self, agent_name, input_text, context=""):
        """
        Создание промпта для конкретного агента
        
        Args:
            agent_name: Имя агента
            input_text: Входной текст
            context: Дополнительный контекст
            
        Returns:
            str: Промпт для агента
        """
        # Создание промпта для конкретного агента
        prompts = {
            "Planner": f"Действуй как планировщик проекта. Проанализируй задачу и создай план: {input_text}\nКонтекст: {context}",
            "Architect": f"Действуй как архитектор ПО. Спроектируй архитектуру для: {input_text}\nКонтекст: {context}",
            "Coder": f"Действуй как программист. Напиши код для: {input_text}\nКонтекст: {context}",
            "Reviewer": f"Действуй как код-ревьюер. Проанализируй код и найди проблемы: {input_text}\nКонтекст: {context}",
            "Tester": f"Действуй как тестировщик. Создай тесты для: {input_text}\nКонтекст: {context}",
            "Documenter": f"Действуй как технический писатель. Создай документацию для: {input_text}\nКонтекст: {context}"
        }
        return prompts.get(agent_name, f"Проанализируй: {input_text}")