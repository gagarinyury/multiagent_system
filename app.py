import os
import streamlit as st
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Настройка страницы Streamlit
st.set_page_config(
    page_title="Мультиагентная система разработки",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Заголовок приложения
st.title("🤖 Мультиагентная система разработки")

# Проверка наличия API ключей
with st.sidebar:
    st.header("Настройки")
    
    # Проверка API ключей из .env
    anthropic_key = os.getenv("ANTHROPIC_API_KEY", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    if not anthropic_key:
        st.warning("⚠️ API ключ Anthropic не настроен")
        anthropic_key = st.text_input("Введите API ключ Anthropic:", type="password")
    else:
        st.success("✅ API ключ Anthropic настроен")
        
    if not openai_key:
        st.warning("⚠️ API ключ OpenAI не настроен")
        openai_key = st.text_input("Введите API ключ OpenAI:", type="password")
    else:
        st.success("✅ API ключ OpenAI настроен")
    
    st.divider()
    
    # Выбор активных агентов (пока не функциональны)
    st.subheader("Агенты")
    agents = ["Planner", "Architect", "Coder", "Reviewer", "Tester", "Documenter"]
    active_agents = {}
    for agent in agents:
        active_agents[agent] = st.checkbox(agent, value=True)
    
    # Сохранение выбранных агентов в session_state
    if "active_agents" not in st.session_state:
        st.session_state.active_agents = active_agents

# Основная область приложения
st.subheader("Введите задачу для системы:")
user_input = st.text_area("Описание задачи:", height=150)

if st.button("Отправить задачу"):
    if not user_input:
        st.error("Пожалуйста, введите описание задачи!")
    else:
        with st.spinner("Обработка запроса..."):
            # Здесь будет обработка запроса через оркестратор
            st.info("Система настроена и готова к работе!")
            st.success(f"Получена задача: {user_input[:50]}...")
            
            # Заглушка для демонстрации работы
            st.subheader("План выполнения:")
            st.write("1. Анализ задачи")
            st.write("2. Создание архитектуры")
            st.write("3. Разработка кода")

# Отображение информации о системе
with st.expander("Информация о системе"):
    st.write("**Версия:** 0.1.0 (прототип)")
    st.write("**Статус:** Инициализация базовых компонентов")
    st.write("**Контекст:** Настройка базовой структуры проекта")
    
    # Информация о сервере
    try:
        import platform
        system_info = platform.uname()
        st.write(f"**Сервер:** {system_info.node}")
        st.write(f"**ОС:** {system_info.system} {system_info.release}")
    except:
        pass

# Сообщение о текущем статусе
st.info("🛠️ Система находится в стадии разработки. Выполняется настройка базовой структуры.")
