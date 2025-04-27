"""
Ядро оркестратора - центральный компонент, координирующий работу агентов
"""

import time
import importlib
import logging # Импортируем модуль логирования

from agents import (
 BaseAgent, PlannerAgent, ArchitectAgent, CoderAgent,
 ReviewerAgent, TesterAgent, DocumenterAgent
)
from utils.token_counter import TokenCounter
from utils.logger import Logger # Импортируем наш Logger

# Получаем экземпляр логгера
logger = logging.getLogger("multiagent_system")


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
  self.messages = [] # История сообщений диалога
  self.token_usage = {
   "total": 0,
   "per_model": {},
   "per_agent": {}
  }
  self.agent_models = {} # Настройки моделей для каждого агента
  self.agent_providers = {} # Настройки провайдеров для каждого агента
  self.current_status = {
   "agent": None, # Текущий активный агент
   "model": None, # Модель текущего агента
   "provider": None, # Провайдер текущего агента
   "progress": 0, # Общий прогресс выполнения (0-100)
   "agents": {} # Статусы каждого агента в текущем workflow
  }
  self._initialize_agents()

 def _initialize_agents(self):
  """
  Инициализация экземпляров агентов
  """
  logger.info("Инициализация агентов...")
  self.agents = {
   "Planner": PlannerAgent(),
   "Architect": ArchitectAgent(),
   "Coder": CoderAgent(),
   "Reviewer": ReviewerAgent(),
   "Tester": TesterAgent(),
   "Documenter": DocumenterAgent()
  }

  # Назначение провайдера по умолчанию для всех агентов
  # Если провайдеры уже были переданы, используем их
  for agent_name, agent_instance in self.agents.items():
      # Проверяем, установлен ли уже провайдер для этого агента (например, через настройки UI)
      if agent_name not in self.agent_providers:
          # Если нет, устанавливаем первый доступный настроенный провайдер как провайдер по умолчанию
          default_provider = next((p_name for p_name, provider in self.providers.items() if provider.is_configured()), None)
          if default_provider:
              self.agent_providers[agent_name] = default_provider
              agent_instance.set_provider(self.providers[default_provider])
          else:
              logger.warning(f"Для агента {agent_name} не установлен провайдер по умолчанию. API ключи не настроены.")
              # Устанавливаем провайдер None, если нет настроенных
              agent_instance.set_provider(None)

  logger.info("Инициализация агентов завершена.")


 def set_agent_models(self, agent_models):
  """
  Установка моделей для агентов

  Args:
   agent_models: Словарь вида {agent_name: model_name}
  """
  self.agent_models = agent_models
  # Обновляем модели у экземпляров агентов, если провайдер уже назначен
  for agent_name, model_name in agent_models.items():
      if agent_name in self.agents and agent_name in self.agent_providers:
          provider_name = self.agent_providers[agent_name]
          if provider_name in self.providers:
              provider = self.providers[provider_name]
              if hasattr(provider, 'set_model'):
                  provider.set_model(model_name)
                  logger.info(f"Установлена модель {model_name} для агента {agent_name} ({provider_name})")


 def set_agent_provider(self, agent_name, provider_name):
  """
  Установка провайдера для конкретного агента

  Args:
   agent_name: Имя агента
   provider_name: Имя провайдера
  """
  if provider_name in self.providers and agent_name in self.agents:
   self.agent_providers[agent_name] = provider_name
   self.agents[agent_name].set_provider(self.providers[provider_name])
   # Обновляем модель для этого агента, если она уже была задана
   if agent_name in self.agent_models:
       model_name = self.agent_models[agent_name]
       provider = self.providers[provider_name]
       if hasattr(provider, 'set_model'):
           provider.set_model(model_name)
           logger.info(f"Установлен провайдер {provider_name} и модель {model_name} для агента {agent_name}")
   else:
        logger.info(f"Установлен провайдер {provider_name} для агента {agent_name}")
  else:
      logger.warning(f"Не удалось установить провайдер {provider_name} для агента {agent_name}. Провайдер или агент не найдены.")


 def get_agent_model(self, agent_name):
  """
  Получение модели агента

  Args:
   agent_name: Имя агента

  Returns:
   str or None: Название модели или None
  """
  # Сначала проверяем, установлена ли модель явно для этого агента
  if agent_name in self.agent_models:
      return self.agent_models.get(agent_name)
  # Если нет, пытаемся получить модель из назначенного провайдера
  provider_name = self.agent_providers.get(agent_name)
  if provider_name and provider_name in self.providers:
      provider = self.providers[provider_name]
      return getattr(provider, 'model', None) # Возвращаем атрибут 'model' провайдера

  return None # Если ни модель, ни провайдер не найдены


 def update_status(self, agent_name=None, model=None, provider=None, progress=None, agent_status=None):
  """
  Обновление текущего статуса выполнения

  Args:
   agent_name: Имя агента
   model: Название модели
   provider: Имя провайдера
   progress: Общий прогресс выполнения (0-100)
   agent_status: Словарь статуса для конкретного агента {status: str, elapsed_time: float, model: str, provider: str}
  """
  if agent_name is not None:
   self.current_status["agent"] = agent_name
  if model is not None:
   self.current_status["model"] = model
  if provider is not None:
   self.current_status["provider"] = provider
  if progress is not None:
   self.current_status["progress"] = progress
  if agent_status and self.current_status["agent"] is not None:
      self.current_status["agents"][self.current_status["agent"]] = agent_status
      logger.info(f"Статус агента {self.current_status['agent']} обновлен: {agent_status['status']}")


 def get_current_status(self):
  """
  Получение текущего статуса

  Returns:
   dict: Текущий статус
  """
  return self.current_status

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

   # Обновляем провайдера у агентов, которые используют этот провайдер
   # и были инициализированы до настройки ключа
   for agent_name, p_name in self.agent_providers.items():
    if p_name == provider_name and agent_name in self.agents:
     self.agents[agent_name].set_provider(self.providers[provider_name])
     logger.info(f"Обновлен провайдер {provider_name} для агента {agent_name} после настройки ключа.")

   logger.info(f"API ключ для провайдера {provider_name} установлен.")
   return True
  logger.warning(f"Не удалось установить API ключ для провайдера {provider_name}. Провайдер не найден.")
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
    logger.info(f"Установлена модель по умолчанию {model_name} для провайдера {provider_name}.")
    # TODO: Возможно, здесь нужно обновить модели для агентов, которые используют этот провайдер,
    # если для них явно не задана другая модель.
    return True
  logger.warning(f"Не удалось установить модель {model_name} для провайдера {provider_name}. Провайдер не найден или не поддерживает установку модели.")
  return False


 def configure_agents(self, active_agents):
  """
  Настройка активных агентов

  Args:
   active_agents: Словарь с состоянием активности агентов
  """
  self.active_agents = active_agents
  logger.info(f"Конфигурация активных агентов обновлена: {active_agents}")

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

  return round(total_cost, 6) # Округляем до 6 знаков для точности

 def process_request(self, user_input):
  """
  Обработка запроса пользователя через последовательность агентов

  Args:
   user_input: Текст запроса пользователя

  Returns:
   dict: Результаты работы агентов
  """
  logger.info(f"Получен запрос на обработку: {user_input[:100]}...") # Логируем начало запроса
  self.update_status(progress=0)

  # Сбрасываем статусы агентов для нового запроса
  self.current_status["agents"] = {}
  for agent_name in self.get_active_agents():
       self.current_status["agents"][agent_name] = {"status": "pending", "elapsed_time": None}


  # Добавление сообщения пользователя в историю (если еще не добавлено UI)
  # Проверяем последнее сообщение, чтобы избежать дублирования при вызове из UI
  if not self.messages or self.messages[-1].get("role") != "user" or self.messages[-1].get("content") != user_input:
       self.messages.append({"role": "user", "content": user_input})


  # Получение списка активных агентов
  active_agents = self.get_active_agents()

  if not active_agents:
   result = "Не выбран ни один агент. Пожалуйста, активируйте хотя бы одного агента в настройках."
   logger.warning(result)
   # Добавление сообщения системы в историю
   self.messages.append({"role": "assistant", "content": result})
   return {"error": result}


  # Получение оптимизированного контекста для текущего запроса
  context = ""
  if self.context_storage:
   try:
       context = self.context_storage.get_optimized_context(user_input, max_tokens=2000) # TODO: Сделать max_tokens контекста настраиваемым
       logger.info(f"Получен оптимизированный контекст ({len(context)} символов).")
   except Exception as e:
       logger.error(f"Ошибка при получении оптимизированного контекста: {str(e)}")
       context = "" # Продолжаем без контекста в случае ошибки


  # Результаты работы агентов
  results = {}
  current_input = user_input # Вход для первого агента - запрос пользователя

  total_agents = len(active_agents)
  for idx, agent_name in enumerate(active_agents):
   logger.info(f"Запуск агента: {agent_name}")
   if agent_name in self.agents:
    agent = self.agents[agent_name]

    # Выбор провайдера и модели для текущего агента
    provider_name = self.agent_providers.get(agent_name)
    provider = self.providers.get(provider_name) if provider_name else None
    model_name = self.get_agent_model(agent_name) # Используем новый метод для получения модели

    # Назначаем провайдер агенту непосредственно перед выполнением
    if provider and provider.is_configured():
         agent.set_provider(provider)
         # Устанавливаем модель для провайдера, если агент использует определенную модель
         if model_name and hasattr(provider, 'set_model'):
             provider.set_model(model_name)
         else:
             # Если модель для агента не задана явно, используем модель провайдера по умолчанию
             model_name = getattr(provider, 'model', 'unknown') # Обновляем model_name для статуса и подсчета токенов
    else:
         # Если провайдер не настроен или не найден
         error_message = f"Ошибка: Провайдер LLM ({provider_name if provider_name else 'Не указан'}) не настроен или не найден для агента {agent_name}."
         logger.error(error_message)
         results[agent_name] = {
             "result": error_message,
             "elapsed_time": 0,
             "tokens": 0,
             "model": model_name,
             "provider": provider_name
         }
         self.update_status(agent_name=agent_name, agent_status={"status": "error", "elapsed_time": 0, "model": model_name, "provider": provider_name})
         current_input = error_message # Передаем ошибку дальше по цепочке агентов
         continue # Переходим к следующему агенту


    self.update_status(agent_name=agent_name, model=model_name, provider=provider_name, progress=int(((idx) / total_agents) * 100))
    self.current_status["agents"][agent_name]["status"] = "running" # Обновляем статус конкретного агента на "выполняется"


    # Замер времени выполнения
    start_time = time.time()

    try:
        # Выполнение агента
        agent_result = agent.process(current_input, context)

        elapsed_time = time.time() - start_time
        logger.info(f"Агент {agent_name} завершен за {elapsed_time:.2f} сек.")


        # Проверка, является ли результат сообщением об ошибке от провайдера
        is_provider_error = isinstance(agent_result, str) and agent_result.startswith("[Error]")

        # Подсчет токенов только при успешном выполнении LLM запроса агентом
        input_tokens = 0
        output_tokens = 0
        if agent.provider and not is_provider_error:
            # TODO: Более точно считать токены с учетом контекста и промпта агента
            try:
                 input_tokens = agent.provider.count_tokens(agent.create_prompt(current_input, context))
                 output_tokens = agent.provider.count_tokens(agent_result)
                 logger.info(f"Агент {agent_name} использовал ~{input_tokens} in, ~{output_tokens} out токенов.")
            except Exception as e:
                 logger.warning(f"Ошибка при подсчете токенов для агента {agent_name}: {str(e)}")
                 pass # Продолжаем даже если подсчет токенов не удался


        # Обновление статистики токенов
        if agent.provider and agent.provider.is_configured(): # Убеждаемся, что провайдер был настроен и использован
            self._update_token_usage(agent_name, model_name, input_tokens, output_tokens)


        # Сохранение результата
        results[agent_name] = {
            "result": agent_result,
            "elapsed_time": elapsed_time,
            "tokens": input_tokens + output_tokens,
            "model": model_name,
            "provider": provider_name
        }

        # Обновляем статус конкретного агента на "готово" или "ошибка"
        agent_status = "error" if is_provider_error else "done"
        self.update_status(agent_name=agent_name, agent_status={"status": agent_status, "elapsed_time": elapsed_time, "model": model_name, "provider": provider_name})


        # Результат текущего агента становится входом для следующего,
        # если только это не была ошибка провайдера - в этом случае передаем ошибку
        current_input = agent_result if not is_provider_error else agent_result

    except Exception as e:
        # Неожиданная ошибка в логике самого агента
        error_message = f"[Error] Неожиданная ошибка в агенте {agent_name}: {str(e)}"
        logger.error(error_message, exc_info=True) # Логируем исключение полностью
        elapsed_time = time.time() - start_time
        results[agent_name] = {
             "result": error_message,
             "elapsed_time": elapsed_time,
             "tokens": 0,
             "model": model_name,
             "provider": provider_name
         }
        self.update_status(agent_name=agent_name, agent_status={"status": "error", "elapsed_time": elapsed_time, "model": model_name, "provider": provider_name})
        current_input = error_message # Передаем сообщение об ошибке дальше


  self.update_status(progress=100) # Общий прогресс 100% в конце


  # Объединение результатов всех агентов в один ответ
  final_result = self._combine_results(results)

  # Сохранение итогового результата в историю сообщений (если еще не добавлено)
  # Проверяем последнее сообщение, чтобы избежать дублирования при вызове из UI
  if not self.messages or self.messages[-1].get("role") != "assistant" or self.messages[-1].get("content") != final_result:
      self.messages.append({
          "role": "assistant",
          "content": final_result,
          "tokens": sum(r.get("tokens", 0) for r in results.values() if isinstance(r, dict))
      })

  # Сохранение взаимодействия в контекстное хранилище
  if self.context_storage:
   try:
       interaction_id = self.context_storage.save_interaction(
           user_input,
           final_result,
           sum(r.get("tokens", 0) for r in results.values() if isinstance(r, dict)), # Суммарные токены за workflow
           {"agent_results": {k: v.get("result", "") for k, v in results.items()}}
       )
       logger.info(f"Взаимодействие сохранено в DB с ID: {interaction_id}")
   except Exception as e:
       logger.error(f"Ошибка при сохранении взаимодействия в DB: {str(e)}")


  logger.info("Обработка запроса завершена.")
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
  # Проверяем, что model_name не None и не пустая строка
  if not model_name:
      model_name = "unknown"
      logger.warning(f"Обновление статистики токенов для агента {agent_name}: model_name не указан, используется 'unknown'.")


  total_tokens = input_tokens + output_tokens
  self.token_usage["total"] += total_tokens

  if agent_name not in self.token_usage["per_agent"]:
   self.token_usage["per_agent"][agent_name] = 0
  self.token_usage["per_agent"][agent_name] += total_tokens

  if model_name not in self.token_usage["per_model"]:
   self.token_usage["per_model"][model_name] = {"input": 0, "output": 0}
  self.token_usage["per_model"][model_name]["input"] += input_tokens
  self.token_usage["per_model"][model_name]["output"] += output_tokens

  logger.debug(f"Обновлена статистика токенов: Агент {agent_name}, Модель {model_name}, Вход: {input_tokens}, Выход: {output_tokens}")


 def _combine_results(self, results):
  """
  Объединение результатов работы агентов в один текст.
  Теперь учитываем возможность ошибок в результатах агентов.

  Args:
   results: Словарь с результатами работы агентов

  Returns:
   str: Объединенный результат или сообщение об ошибке
  """
  if not results:
   return "Не удалось получить результаты от агентов."

  active_agents = self.get_active_agents()
  combined_text = ""
  errors_found = False

  # Собираем результаты всех агентов в порядке их выполнения
  for agent_name in active_agents:
      if agent_name in results:
          agent_result = results[agent_name].get("result", "")
          elapsed_time = results[agent_name].get("elapsed_time", 0)
          model_name = results[agent_name].get("model", "N/A")
          provider_name = results[agent_name].get("provider", "N/A")

          header = f"### 🤖 {agent_name} ({elapsed_time:.2f} сек., Модель: {model_name}, Провайдер: {provider_name})\n"
          combined_text += header

          if isinstance(agent_result, str) and agent_result.startswith("[Error]"):
              combined_text += f"⚠️ **Ошибка выполнения агента:** {agent_result}\n\n"
              errors_found = True
          elif agent_result:
               # Проверяем, если результат содержит маркдаун заголовки, возможно, это уже структурированный ответ
               # В этом случае, просто добавляем результат
               if agent_result.strip().startswith('#'):
                   combined_text += agent_result + "\n\n"
               else:
                   # Если это просто текст, добавляем его с отступом или маркером
                   combined_text += agent_result + "\n\n"
          else:
               combined_text += "*(Агент не вернул результата)*\n\n" # Если результат пустой

  if errors_found:
      combined_text += "--- \n ⚠️ **ВНИМАНИЕ:** Во время выполнения рабочего процесса возникли ошибки. Пожалуйста, проверьте результаты отдельных агентов выше."

  # Возвращаем полный объединенный текст для отображения в UI
  return combined_text


 def get_agent_statuses(self):
  """
  Получение статусов всех активных агентов

  Returns:
   list: Список словарей с информацией о статусе агентов
  """
  statuses = []
  for agent_name in self.get_active_agents():
      # Используем статус, который мы сохраняем в self.current_status["agents"]
      status_info = self.current_status["agents"].get(agent_name, {"status": "pending", "elapsed_time": None, "model": None, "provider": None})
      statuses.append({
          "name": agent_name,
          "status": status_info.get("status", "pending"),
          "elapsed_time": status_info.get("elapsed_time"),
          "model": status_info.get("model"),
          "provider": status_info.get("provider")
      })
  return statuses