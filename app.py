# Файл: app.py
# Полное обновление основного файла приложения с интеграцией новых компонентов

import sys
import os
# 👇 Добавляем сюда
os.environ["DEFAULT_CLAUDE_MODEL"] = "claude-3-7-sonnet-20250219"
# ДОБАВЛЯЕМ путь проекта в sys.path:
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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
    ReviewerAgent, TesterAgent, DocumenterAgent, ProjectManagerAgent
)
from utils.logger import Logger
from utils.token_counter import TokenCounter
from ui.components import (
    render_sidebar, render_chat_history, 
    render_agent_workflow_progress, render_agent_output  # Обновленные импорты
)

# Импорт для ProjectManager
from ui.pages.project_manager import SecureProjectManager

# Загрузка переменных окружения
load_dotenv()

# 🔒 Проверка пароля
SECRET_PASSWORD = os.getenv("STREAMLIT_PASSWORD", "default_password")

def check_password():
    def password_entered():
        if st.session_state["password"] == SECRET_PASSWORD:
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input(
            "Введите пароль", type="password", on_change=password_entered, key="password"
        )
        return False
    elif not st.session_state["password_correct"]:
        st.text_input(
            "Введите пароль", type="password", on_change=password_entered, key="password"
        )
        st.error("❌ Неверный пароль")
        return False
    else:
        return True

if not check_password():
    st.stop()

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
    
    # Инициализация проект-менеджера
    projects_root = os.getenv("PROJECTS_ROOT", "projects")
    project_manager = SecureProjectManager(projects_root=projects_root)
    logger.info(f"Инициализирован SecureProjectManager с корневой директорией: {projects_root}")
    
    # Инициализация оркестратора
    orchestrator = Orchestrator(context_storage, providers)
    # Добавляем проект-менеджер в оркестратор
    orchestrator.project_manager = project_manager
    
    # Инициализация менеджера рабочих процессов
    workflow_manager = WorkflowManager(orchestrator)
    
    # Сохранение в состоянии сессии
    st.session_state.context_storage = context_storage
    st.session_state.context_optimizer = context_optimizer
    st.session_state.providers = providers
    st.session_state.orchestrator = orchestrator
    st.session_state.workflow_manager = workflow_manager
    st.session_state.project_manager = project_manager  # Сохраняем проект-менеджер в состоянии сессии
    st.session_state.messages = []
    st.session_state.initialized = True
    
    # Настройка агентов по умолчанию
    default_active_agents = {
        "Planner": True,
        "Architect": True,
        "Coder": True,
        "Reviewer": True,
        "Tester": True,
        "Documenter": True,
        "ProjectManager": True  # Включаем ProjectManagerAgent по умолчанию
    }
    st.session_state.active_agents = default_active_agents
    orchestrator.configure_agents(default_active_agents)
    
    # Настройка моделей по умолчанию
    st.session_state.models = {
        "claude": os.getenv("DEFAULT_CLAUDE_MODEL", "claude-3-7-sonnet-20250219"),
        "gpt": os.getenv("DEFAULT_GPT_MODEL", "gpt-4-turbo")
    }
    
    # Инициализация моделей для каждого агента
    st.session_state.agent_models = {}
    
    # Инициализация провайдеров для каждого агента
    st.session_state.agent_providers = {}
    
    # Установка моделей для провайдеров
    for provider_name, model_name in st.session_state.models.items():
        if provider_name in providers:
            providers[provider_name].set_model(model_name)
    
    logger.info("Инициализация приложения завершена")

# Получение компонентов из состояния сессии
orchestrator = st.session_state.orchestrator
workflow_manager = st.session_state.workflow_manager
project_manager = st.session_state.project_manager  # Получаем проект-менеджер из состояния сессии

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
    
    # Обновление моделей для каждого агента
    if "agent_models" in st.session_state:
        orchestrator.set_agent_models(st.session_state.agent_models)
    
    # Обновление провайдеров для каждого агента
    if "agent_providers" in st.session_state:
        for agent_name, provider_name in st.session_state.agent_providers.items():
            orchestrator.set_agent_provider(agent_name, provider_name)

# Импорт функции для отрисовки основной страницы
from ui.pages.main import render_main_page

# Отрисовка основной страницы
render_main_page(orchestrator, workflow_manager)

# Проверка наличия нового агента в списке и его настройка, если нужно
if "ProjectManager" in orchestrator.agents:
    pm_agent = orchestrator.agents["ProjectManager"]
    if not hasattr(pm_agent, 'project_manager') or pm_agent.project_manager is None:
        pm_agent.project_manager = project_manager
        logger.info("ProjectManagerAgent настроен с доступом к SecureProjectManager")