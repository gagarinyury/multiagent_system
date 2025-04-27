import os
import time
import streamlit as st
from dotenv import load_dotenv
import importlib

# Импорт всех компонентов мультиагентной системы
from orchestrator.core import Orchestrator
from orchestrator.workflow import WorkflowManager
from context.storage import ContextStorage
from context.optimizer import ContextOptimizer
from providers.anthropic import AnthropicProvider
from providers.openai import OpenAIProvider
from agents import (
    PlannerAgent, ArchitectAgent, CoderAgent, 
    ReviewerAgent, TesterAgent, DocumenterAgent
)
from utils.logger import Logger
from utils.token_counter import TokenCounter
from ui.components import (
    render_sidebar, render_chat_history, 
    render_agent_workflow, render_agent_output
)

# Загрузка переменных окружения
load_dotenv()

# Инициализация логгера
logger = Logger(name="multiagent_system", level=os.getenv("LOG_LEVEL", "INFO"))
logger.info("Запуск мультиагентной системы")

# Настройка страницы Streamlit
st.set_page_config(
    page_title="Мультиагентная система разработки",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Инициализация состояния сессии
if "initialized" not in st.session_state:
    # Инициализация хранилища контекста
    context_storage = ContextStorage(os.getenv("DB_PATH", "data/db.sqlite"))
    context_optimizer = ContextOptimizer()
    
    # Инициализация провайдеров API
    providers = {
        "claude": AnthropicProvider(os.getenv("ANTHROPIC_API_KEY", "")),
        "gpt": OpenAIProvider(os.getenv("OPENAI_API_KEY", ""))
    }
    
    # Инициализация оркестратора
    orchestrator = Orchestrator(context_storage, providers)
    
    # Инициализация менеджера рабочих процессов
    workflow_manager = WorkflowManager(orchestrator)
    
    # Сохранение в состоянии сессии
    st.session_state.context_storage = context_storage
    st.session_state.context_optimizer = context_optimizer
    st.session_state.providers = providers
    st.session_state.orchestrator = orchestrator
    st.session_state.workflow_manager = workflow_manager
    st.session_state.messages = []
    st.session_state.initialized = True
    
    # Настройка агентов по умолчанию
    default_active_agents = {
        "Planner": True,
        "Architect": True,
        "Coder": True,
        "Reviewer": True,
        "Tester": True,
        "Documenter": True
    }
    st.session_state.active_agents = default_active_agents
    orchestrator.configure_agents(default_active_agents)
    
    # Настройка моделей по умолчанию
    st.session_state.models = {
        "claude": os.getenv("DEFAULT_CLAUDE_MODEL", "claude-3-sonnet-20240229"),
        "gpt": os.getenv("DEFAULT_GPT_MODEL", "gpt-4-turbo")
    }
    
    # Установка моделей для провайдеров
    for provider_name, model_name in st.session_state.models.items():
        if provider_name in providers:
            providers[provider_name].set_model(model_name)
    
    logger.info("Инициализация приложения завершена")

# Получение компонентов из состояния сессии
orchestrator = st.session_state.orchestrator
workflow_manager = st.session_state.workflow_manager

# Заголовок приложения
st.title("🤖 Мультиагентная система разработки")

# Отображение сайдбара с настройками
with st.sidebar:
    render_sidebar(orchestrator)
    
    # Обновление активных агентов в оркестраторе
    if "active_agents" in st.session_state:
        orchestrator.configure_agents(st.session_state.active_agents)
    
    # Обновление моделей в провайдерах
    if "models" in st.session_state and "providers" in st.session_state:
        providers = st.session_state.providers
        for provider_name, model_name in st.session_state.models.items():
            if provider_name in providers:
                providers[provider_name].set_model(model_name)

# Отображение потока работы агентов
if "active_agents" in st.session_state:
    render_agent_workflow(st.session_state.active_agents)

# Чат-интерфейс для взаимодействия с системой
st.subheader("💬 Диалог с системой")

# Отображение истории чата
if "messages" in st.session_state:
    render_chat_history(st.session_state.messages)

# Ввод нового сообщения
user_input = st.text_area("Опишите задачу или запрос:", height=100)

# Выбор рабочего процесса
workflow_options = {
    "standard": "Стандартный процесс",
    "code_only": "Только код",
    "review_only": "Только ревью",
    "docs_only": "Только документация"
}
selected_workflow = st.selectbox(
    "Выберите рабочий процесс:",
    options=list(workflow_options.keys()),
    format_func=lambda x: workflow_options.get(x, x)
)

# Отправка запроса
if st.button("Отправить запрос"):
    if not user_input:
        st.error("Пожалуйста, введите описание задачи или запрос!")
    else:
        # Добавление сообщения пользователя в историю
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        st.session_state.messages.append({"role": "user", "content": user_input})
        
        # Отображение сообщения пользователя
        with st.chat_message("user"):
            st.write(user_input)
        
        # Обработка запроса через выбранный рабочий процесс
        with st.spinner("Обработка запроса..."):
            # Проверка наличия настроенных API ключей
            providers_configured = False
            for provider in st.session_state.providers.values():
                if provider.is_configured():
                    providers_configured = True
                    break
            
            if not providers_configured:
                st.error("Пожалуйста, настройте хотя бы один API ключ в разделе настроек!")
            else:
                # Выполнение выбранного рабочего процесса
                start_time = time.time()
                results = workflow_manager.execute_workflow(selected_workflow, user_input)
                total_time = time.time() - start_time
                
                # Отображение результатов для каждого агента
                st.subheader("🔍 Результаты работы агентов")
                for agent_name, agent_result in results.items():
                    if "result" in agent_result:
                        render_agent_output(
                            agent_name, 
                            agent_result["result"], 
                            agent_result.get("elapsed_time")
                        )
                
                # Формирование итогового ответа
                final_result = orchestrator._combine_results(results)
                
                # Добавление ответа в историю сообщений
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": final_result,
                    "tokens": sum(r.get("tokens", 0) for r in results.values() if isinstance(r, dict))
                })
                
                # Отображение итогового ответа
                with st.chat_message("assistant"):
                    st.write(final_result)
                
                # Отображение статистики выполнения
                st.info(f"Запрос обработан за {total_time:.2f} секунд")

# Отображение информации о системе
with st.expander("📊 Информация о системе"):
    st.write("**Версия:** 0.1.0")
    st.write("**Дата сборки:** Апрель 2025")
    st.write("**Разработчик:** Команда мультиагентной системы")
    
    # Отображение статистики использования токенов
    if "orchestrator" in st.session_state:
        token_usage = orchestrator.get_token_usage()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Использовано токенов", token_usage["total"])
        with col2:
            st.metric("Стоимость ($)", token_usage["cost"])
        
        # Отображение использования по агентам
        if "per_agent" in token_usage and token_usage["per_agent"]:
            st.subheader("Использование по агентам")
            for agent, tokens in token_usage["per_agent"].items():
                st.write(f"**{agent}:** {tokens} токенов")
    
    # Информация о сервере
    try:
        import platform
        system_info = platform.uname()
        st.write(f"**Сервер:** {system_info.node}")
        st.write(f"**ОС:** {system_info.system} {system_info.release}")
    except:
        pass