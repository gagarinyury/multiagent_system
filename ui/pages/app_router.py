# Файл: app_router.py
# Маршрутизатор для многостраничного приложения Streamlit

import streamlit as st
import importlib
import os
import sys
from pathlib import Path

# Добавляем путь проекта в sys.path для корректной работы импортов
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Основной файл приложения
import app

# Страницы приложения
from ui.pages.project_manager import render_project_manager_page
# Сюда можно добавить импорт других страниц

def route():
    """
    Маршрутизация между разными страницами приложения
    """
    # Настройка страницы Streamlit
    st.set_page_config(
        page_title="Мультиагентная система разработки",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Создаем меню навигации в боковой панели
    with st.sidebar:
        st.title("🤖 Меню")
        page = st.radio(
            "Выберите раздел:",
            ["Главная страница", "Управление проектами"]
        )
    
    # Маршрутизация на соответствующую страницу
    if page == "Главная страница":
        # Запускаем основное приложение
        app.run_app()
    elif page == "Управление проектами":
        # Запускаем страницу управления проектами
        render_project_manager_page()
    # Здесь можно добавить другие страницы

# Модифицируем app.py для поддержки маршрутизации
# Файл: app.py (дополнение для маршрутизации)

def run_app():
    """
    Функция для запуска основного приложения
    """
    # Инициализация логгера
    logger = Logger(name="multiagent_system", level=os.getenv("LOG_LEVEL", "INFO"))
    logger.info("Запуск мультиагентной системы")
    
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
    
    # Заголовок приложения
    st.title("🤖 Мультиагентная система разработки")
    
    # Инициализация состояния сессии
    if "initialized" not in st.session_state:
        # ... код инициализации системы ...
        
        # Добавляем инициализацию менеджера проектов
        projects_root = os.getenv("PROJECTS_ROOT", "projects")
        from ui.pages.project_manager import SecureProjectManager
        st.session_state.project_manager = SecureProjectManager(projects_root=projects_root)
        
        # ... остальной код инициализации ...
    
    # ... основной код приложения ...

# Для запуска через маршрутизатор
if __name__ == "__main__":
    route()