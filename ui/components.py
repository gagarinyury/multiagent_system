"""
Компоненты пользовательского интерфейса для приложения Streamlit
"""

import streamlit as st
import datetime
import time

def render_sidebar(orchestrator=None):
    """
    Отрисовка боковой панели с настройками
    
    Args:
        orchestrator: Экземпляр оркестратора (опционально)
    """
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Проверка API ключей
        with st.expander("🔑 API Ключи", expanded=True):
            anthropic_key = st.text_input("API ключ Anthropic (Claude):", type="password")
            openai_key = st.text_input("API ключ OpenAI (GPT):", type="password")
            
            # Кнопка для сохранения ключей
            if st.button("Сохранить ключи"):
                # Сохранение ключей в оркестратор, если он предоставлен
                if orchestrator:
                    if anthropic_key:
                        orchestrator.set_provider_key("claude", anthropic_key)
                    if openai_key:
                        orchestrator.set_provider_key("gpt", openai_key)
                
                st.success("Ключи сохранены!")
        
        # Настройка агентов
        with st.expander("🤖 Агенты", expanded=True):
            st.write("Выберите агентов для использования:")
            
            agents = {
                "Planner": "📝 Планировщик - анализирует задачу и создает план",
                "Architect": "🏗️ Архитектор - проектирует структуру решения",
                "Coder": "💻 Программист - пишет код",
                "Reviewer": "🔍 Ревьюер - проверяет код на ошибки",
                "Tester": "🧪 Тестировщик - создает тесты",
                "Documenter": "📚 Документатор - пишет документацию"
            }
            
            active_agents = {}
            for agent_key, agent_desc in agents.items():
                active_agents[agent_key] = st.checkbox(agent_desc, value=True, key=f"agent_{agent_key}")
            
            # Сохранение настроек в session_state
            if "active_agents" not in st.session_state:
                st.session_state.active_agents = active_agents
            else:
                st.session_state.active_agents = active_agents
            
            # Обновление оркестратора, если он предоставлен
            if orchestrator:
                orchestrator.configure_agents(active_agents)
        
        # Настройка моделей
        with st.expander("🧠 Модели", expanded=False):
            claude_models = {
                "claude-3-opus-20240229": "Claude 3 Opus (мощная, медленная)",
                "claude-3-sonnet-20240229": "Claude 3 Sonnet (сбалансированная)",
                "claude-3-haiku-20240307": "Claude 3 Haiku (быстрая, экономичная)"
            }
            
            gpt_models = {
                "gpt-4-turbo": "GPT-4 Turbo (мощная, медленная)",
                "gpt-4": "GPT-4 (предыдущая версия)",
                "gpt-3.5-turbo": "GPT-3.5 Turbo (быстрая, экономичная)"
            }
            
            st.write("Модель Claude:")
            selected_claude = st.selectbox(
                "Выберите модель Claude:",
                options=list(claude_models.keys()),
                format_func=lambda x: claude_models.get(x, x),
                index=1  # По умолчанию Claude 3 Sonnet
            )
            
            st.write("Модель GPT:")
            selected_gpt = st.selectbox(
                "Выберите модель GPT:",
                options=list(gpt_models.keys()),
                format_func=lambda x: gpt_models.get(x, x),
                index=0  # По умолчанию GPT-4 Turbo
            )
            
            # Сохранение настроек в session_state
            if "models" not in st.session_state:
                st.session_state.models = {
                    "claude": selected_claude,
                    "gpt": selected_gpt
                }
            else:
                st.session_state.models = {
                    "claude": selected_claude,
                    "gpt": selected_gpt
                }
        
        # Настройка токенов
        with st.expander("💰 Токены и стоимость", expanded=False):
            if orchestrator:
                usage = orchestrator.get_token_usage()
                st.metric("Использовано токенов", usage["total"])
                st.metric("Стоимость ($)", usage["cost"])
            else:
                st.info("Статистика токенов будет доступна после первого запроса.")
            
            st.write("Лимиты токенов:")
            max_tokens_per_request = st.slider("Максимум токенов на запрос:", 100, 8000, 4000, 100)
            
            # Сохранение настроек в session_state
            if "token_limits" not in st.session_state:
                st.session_state.token_limits = {
                    "max_per_request": max_tokens_per_request
                }
            else:
                st.session_state.token_limits = {
                    "max_per_request": max_tokens_per_request
                }
        
        # Дополнительно
        with st.expander("📊 О системе", expanded=False):
            st.write("**Версия:** 0.1.0")
            st.write("**Дата сборки:** Апрель 2025")
            st.write("**Состояние:** Прототип")
            
            # Текущее время сервера
            st.write(f"**Время сервера:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Отображение информации о сервере
            try:
                import platform
                system_info = platform.uname()
                st.write(f"**Сервер:** {system_info.node}")
                st.write(f"**ОС:** {system_info.system} {system_info.release}")
            except:
                pass

def render_chat_history(messages):
    """
    Отрисовка истории чата
    
    Args:
        messages: Список сообщений для отображения
    """
    if not messages:
        st.info("История сообщений пуста. Начните диалог, отправив запрос.")
        return
    
    for message in messages:
        role = message.get("role", "unknown")
        content = message.get("content", "")
        
        with st.chat_message(role):
            st.write(content)

def render_agent_workflow(active_agents):
    """
    Отрисовка потока работы агентов
    
    Args:
        active_agents: Словарь с активными агентами
    """
    st.subheader("🔄 Порядок работы агентов")
    
    # Получение списка активных агентов
    active_agent_names = [name for name, active in active_agents.items() if active]
    
    if not active_agent_names:
        st.warning("Не выбрано ни одного агента. Пожалуйста, включите хотя бы одного агента в настройках.")
        return
    
    # Отображение потока работы
    cols = st.columns(len(active_agent_names))
    
    for i, agent_name in enumerate(active_agent_names):
        with cols[i]:
            st.write(f"**{i+1}. {agent_name}**")
            
            # Иконки агентов
            icons = {
                "Planner": "📝",
                "Architect": "🏗️",
                "Coder": "💻",
                "Reviewer": "🔍",
                "Tester": "🧪",
                "Documenter": "📚"
            }
            
            st.write(icons.get(agent_name, "🤖"))
    
    # Добавление стрелок между агентами
    if len(active_agent_names) > 1:
        st.markdown(
            """
            <style>
            .stHorizontalBlock {
                position: relative;
            }
            .stHorizontalBlock:after {
                content: "";
                position: absolute;
                top: 50%;
                left: 0;
                right: 0;
                height: 2px;
                background: #ccc;
                z-index: -1;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

def render_agent_output(agent_name, output, elapsed_time=None):
    """
    Отрисовка вывода от агента
    
    Args:
        agent_name: Имя агента
        output: Текст вывода
        elapsed_time: Время выполнения в секундах (опционально)
    """
    # Иконки агентов
    icons = {
        "Planner": "📝",
        "Architect": "🏗️",
        "Coder": "💻",
        "Reviewer": "🔍",
        "Tester": "🧪",
        "Documenter": "📚"
    }
    
    icon = icons.get(agent_name, "🤖")
    
    with st.expander(f"{icon} {agent_name}" + (f" ({elapsed_time:.2f} сек)" if elapsed_time else ""), expanded=True):
        st.write(output)

def render_processing_animation():
    """
    Отрисовка анимации обработки запроса
    """
    progress_text = "Обработка запроса..."
    my_bar = st.progress(0, text=progress_text)
    
    for percent_complete in range(100):
        time.sleep(0.01)
        my_bar.progress(percent_complete + 1, text=f"{progress_text} {percent_complete+1}%")
    
    my_bar.empty()