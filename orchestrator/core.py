"""
Ядро оркестратора - центральный компонент, координирующий работу агентов
"""

import time
import importlib
from agents import (
    BaseAgent, PlannerAgent, ArchitectAgent, CoderAgent, 
    ReviewerAgent, TesterAgent, DocumenterAgent
)
from utils.token_counter import TokenCounter

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
        self.token_usage = {
            "total": 0,
            "per_model": {},
            "per_agent": {}
        }
        self._initialize_agents()
    
    def _initialize_agents(self):
        """
        Инициализация экземпляров агентов
        """
        self.agents = {
            "Planner": PlannerAgent(),
            "Architect": ArchitectAgent(),
            "Coder": CoderAgent(),
            "Reviewer": ReviewerAgent(),
            "Tester": TesterAgent(),
            "Documenter": DocumenterAgent()
        }
        
        # Назначение провайдера по умолчанию для всех агентов
        default_provider = next(iter(self.providers.values())) if self.providers else None
        if default_provider:
            for agent in self.agents.values():
                agent.set_provider(default_provider)
    
    def set_provider_key(self, provider_name, api_key):
        """
        Установка API ключа для провайдера
        
        Args:
            provider_name: Имя провайдера ('claude', 'gpt')
            api_key: API ключ
            
        Returns:
            bool: Успешность установки ключа
        """
        if provider_name in self.providers:
            self.providers[provider_name].set_api_key(api_key)
            
            # Обновляем провайдера у агентов, если он был обновлен
            for agent in self.agents.values():
                agent.set_provider(self.providers[provider_name])
            
            return True
        return False
    
    def set_provider_model(self, provider_name, model_name):
        """
        Установка модели для провайдера
        
        Args:
            provider_name: Имя провайдера ('claude', 'gpt')
            model_name: Название модели
            
        Returns:
            bool: Успешность установки модели
        """
        if provider_name in self.providers:
            provider = self.providers[provider_name]
            if hasattr(provider, 'set_model'):
                provider.set_model(model_name)
                return True
        return False
    
    def configure_agents(self, active_agents):
        """
        Настройка активных агентов
        
        Args:
            active_agents: Словарь с состоянием активности агентов
        """
        self.active_agents = active_agents
    
    def get_active_agents(self):
        """
        Получение списка активных агентов в правильном порядке
        
        Returns:
            list: Список имен активных агентов
        """
        # Определяем стандартный порядок агентов
        standard_order = ["Planner", "Architect", "Coder", "Reviewer", "Tester", "Documenter"]
        
        # Фильтруем только активных агентов, сохраняя порядок
        active_agents = [agent for agent in standard_order 
                        if agent in self.active_agents and self.active_agents.get(agent, False)]
        
        return active_agents
    
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
        return {
            "total": self.token_usage["total"],
            "cost": self._calculate_cost(),
            "per_agent": self.token_usage["per_agent"],
            "per_model": self.token_usage["per_model"]
        }
    
    def _calculate_cost(self):
        """
        Расчет стоимости использованных токенов
        
        Returns:
            float: Стоимость в долларах
        """
        total_cost = 0.0
        
        for model, usage in self.token_usage["per_model"].items():
            input_tokens = usage.get("input", 0)
            output_tokens = usage.get("output", 0)
            
            model_cost = TokenCounter.estimate_cost(model, input_tokens, output_tokens)
            total_cost += model_cost
        
        return round(total_cost, 4)
    
    def process_request(self, user_input):
        """
        Обработка запроса пользователя через последовательность агентов
        
        Args:
            user_input: Текст запроса пользователя
        
        Returns:
            dict: Результаты работы агентов
        """
        # Добавление сообщения пользователя в историю
        self.messages.append({"role": "user", "content": user_input})
        
        # Получение списка активных агентов
        active_agents = self.get_active_agents()
        
        if not active_agents:
            result = "Не выбран ни один агент. Пожалуйста, активируйте хотя бы одного агента в настройках."
            self.messages.append({"role": "assistant", "content": result})
            return {"error": result}
        
        # Получение оптимизированного контекста для текущего запроса
        context = ""
        if self.context_storage:
            context = self.context_storage.get_optimized_context(user_input)
        
        # Результаты работы агентов
        results = {}
        current_input = user_input
        
        # Последовательное выполнение агентов
        for agent_name in active_agents:
            if agent_name in self.agents:
                agent = self.agents[agent_name]
                
                # Замер времени выполнения
                start_time = time.time()
                
                # Проверка настройки провайдера
                if not agent.provider or not agent.provider.is_configured():
                    for provider in self.providers.values():
                        if provider.is_configured():
                            agent.set_provider(provider)
                            break
                
                # Выполнение агента
                if agent.provider and agent.provider.is_configured():
                    agent_result = agent.process(current_input, context)
                    
                    # Подсчет токенов
                    input_tokens = agent.provider.count_tokens(current_input + context)
                    output_tokens = agent.provider.count_tokens(agent_result)
                    
                    # Обновление статистики токенов
                    self._update_token_usage(agent_name, agent.provider.model, input_tokens, output_tokens)
                    
                    # Сохранение результата
                    elapsed_time = time.time() - start_time
                    results[agent_name] = {
                        "result": agent_result,
                        "elapsed_time": elapsed_time,
                        "tokens": input_tokens + output_tokens
                    }
                    
                    # Результат текущего агента становится входом для следующего
                    current_input = agent_result
                else:
                    results[agent_name] = {
                        "error": "Провайдер LLM не настроен для этого агента",
                        "elapsed_time": 0,
                        "tokens": 0
                    }
        
        # Объединение результатов всех агентов в один ответ
        final_result = self._combine_results(results)
        
        # Сохранение итогового результата в историю сообщений
        self.messages.append({
            "role": "assistant", 
            "content": final_result,
            "tokens": sum(r.get("tokens", 0) for r in results.values())
        })
        
        # Сохранение взаимодействия в контекстное хранилище
        if self.context_storage:
            interaction_id = self.context_storage.save_interaction(
                user_input, 
                final_result,
                sum(r.get("tokens", 0) for r in results.values()),
                {"agent_results": {k: v.get("result", "") for k, v in results.items()}}
            )
        
        return results
    
    def _update_token_usage(self, agent_name, model_name, input_tokens, output_tokens):
        """
        Обновление статистики использования токенов
        
        Args:
            agent_name: Имя агента
            model_name: Название модели
            input_tokens: Количество входных токенов
            output_tokens: Количество выходных токенов
        """
        # Общее количество токенов
        total_tokens = input_tokens + output_tokens
        self.token_usage["total"] += total_tokens
        
        # По агентам
        if agent_name not in self.token_usage["per_agent"]:
            self.token_usage["per_agent"][agent_name] = 0
        self.token_usage["per_agent"][agent_name] += total_tokens
        
        # По моделям
        if model_name not in self.token_usage["per_model"]:
            self.token_usage["per_model"][model_name] = {"input": 0, "output": 0}
        self.token_usage["per_model"][model_name]["input"] += input_tokens
        self.token_usage["per_model"][model_name]["output"] += output_tokens
    
    def _combine_results(self, results):
        """
        Объединение результатов работы агентов в один текст
        
        Args:
            results: Словарь с результатами работы агентов
            
        Returns:
            str: Объединенный результат
        """
        # Берем результат последнего агента как итоговый
        if not results:
            return "Не удалось получить результаты от агентов."
        
        active_agents = self.get_active_agents()
        
        if active_agents:
            last_agent = active_agents[-1]
            if last_agent in results:
                return results[last_agent].get("result", "")
        
        # Если по какой-то причине не удалось получить результат последнего агента,
        # берем первый доступный результат
        for agent_name, agent_result in results.items():
            if "result" in agent_result:
                return agent_result["result"]
        
        return "Не удалось получить результаты от агентов."