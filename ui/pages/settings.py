"""
Страница настроек для приложения Streamlit
"""

import streamlit as st
import os
from dotenv import load_dotenv, set_key

def render_settings_page(orchestrator):
    """
    Отрисовка страницы настроек
    
    Args:
        orchestrator: Экземпляр оркестратора
    """
    st.title("⚙️ Настройки мультиагентной системы")
    
    # Загрузка переменных окружения
    load_dotenv()
    
    # Секция API ключей
    st.header("🔑 API ключи")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Anthropic Claude")
        claude_key = st.text_input(
            "API ключ Anthropic:",
            value=os.getenv("ANTHROPIC_API_KEY", ""),
            type="password"
        )
        
        if st.button("Сохранить ключ Claude"):
            if claude_key:
                # Сохранение в переменные окружения
                try:
                    set_key(".env", "ANTHROPIC_API_KEY", claude_key)
                    # Обновление ключа в оркестраторе
                    orchestrator.set_provider_key("claude", claude_key)
                    st.success("✅ Ключ Claude сохранен успешно!")
                except Exception as e:
                    st.error(f"❌ Ошибка при сохранении ключа: {str(e)}")
            else:
                st.warning("⚠️ Пожалуйста, введите ключ")
    
    with col2:
        st.subheader("OpenAI GPT")
        openai_key = st.text_input(
            "API ключ OpenAI:",
            value=os.getenv("OPENAI_API_KEY", ""),
            type="password"
        )
        
        if st.button("Сохранить ключ OpenAI"):
            if openai_key:
                # Сохранение в переменные окружения
                try:
                    set_key(".env", "OPENAI_API_KEY", openai_key)
                    # Обновление ключа в оркестраторе
                    orchestrator.set_provider_key("gpt", openai_key)
                    st.success("✅ Ключ OpenAI сохранен успешно!")
                except Exception as e:
                    st.error(f"❌ Ошибка при сохранении ключа: {str(e)}")
            else:
                st.warning("⚠️ Пожалуйста, введите ключ")
    
    st.divider()
    
    # Настройка моделей
    st.header("🧠 Настройка моделей")
    
    col1, col2 = st.columns(2)
    
    with col1:
        claude_models = {
            "claude-3-opus-20240229": "Claude 3 Opus (мощная, медленная)",
            "claude-3-sonnet-20240229": "Claude 3 Sonnet (сбалансированная)",
            "claude-3-haiku-20240307": "Claude 3 Haiku (быстрая, экономичная)",
            "claude-3.5-sonnet-20240425": "Claude 3.5 Sonnet (новейшая)"
        }
        
        selected_claude = st.selectbox(
            "Модель Claude:",
            options=list(claude_models.keys()),
            format_func=lambda x: claude_models.get(x, x),
            index=list(claude_models.keys()).index(
                os.getenv("DEFAULT_CLAUDE_MODEL", "claude-3-sonnet-20240229")
            ) if os.getenv("DEFAULT_CLAUDE_MODEL") in claude_models else 1
        )
        
        if st.button("Установить модель Claude"):
            # Сохранение в переменные окружения
            try:
                set_key(".env", "DEFAULT_CLAUDE_MODEL", selected_claude)
                # Обновление модели в оркестраторе
                orchestrator.set_provider_model("claude", selected_claude)
                # Обновление в session_state
                if "models" in st.session_state:
                    st.session_state.models["claude"] = selected_claude
                st.success(f"✅ Модель Claude установлена: {selected_claude}")
            except Exception as e:
                st.error(f"❌ Ошибка при установке модели: {str(e)}")
    
    with col2:
        gpt_models = {
            "gpt-4-turbo": "GPT-4 Turbo (мощная, медленная)",
            "gpt-4": "GPT-4 (стабильная версия)",
            "gpt-3.5-turbo": "GPT-3.5 Turbo (быстрая, экономичная)"
        }
        
        selected_gpt = st.selectbox(
            "Модель GPT:",
            options=list(gpt_models.keys()),
            format_func=lambda x: gpt_models.get(x, x),
            index=list(gpt_models.keys()).index(
                os.getenv("DEFAULT_GPT_MODEL", "gpt-4-turbo")
            ) if os.getenv("DEFAULT_GPT_MODEL") in gpt_models else 0
        )
        
        if st.button("Установить модель GPT"):
            # Сохранение в переменные окружения
            try:
                set_key(".env", "DEFAULT_GPT_MODEL", selected_gpt)
                # Обновление модели в оркестраторе
                orchestrator.set_provider_model("gpt", selected_gpt)
                # Обновление в session_state
                if "models" in st.session_state:
                    st.session_state.models["gpt"] = selected_gpt
                st.success(f"✅ Модель GPT установлена: {selected_gpt}")
            except Exception as e:
                st.error(f"❌ Ошибка при установке модели: {str(e)}")
    
    st.divider()
    
    # Настройка агентов
    st.header("🤖 Настройка агентов")
    
    st.write("Выберите агентов для использования в системе:")
    
    agents = {
        "Planner": "📝 Планировщик - анализирует задачу и создает план",
        "Architect": "🏗️ Архитектор - проектирует структуру решения",
        "Coder": "💻 Программист - пишет код",
        "Reviewer": "🔍 Ревьюер - проверяет код на ошибки",
        "Tester": "🧪 Тестировщик - создает тесты",
        "Documenter": "📚 Документатор - пишет документацию"
    }
    
    # Получение текущих настроек
    active_agents = st.session_state.get("active_agents", {})
    
    # Создание колонок для лучшего вида
    col1, col2 = st.columns(2)
    
    for i, (agent_key, agent_desc) in enumerate(agents.items()):
        with col1 if i < 3 else col2:
            active_agents[agent_key] = st.checkbox(
                agent_desc, 
                value=active_agents.get(agent_key, True),
                key=f"settings_agent_{agent_key}"
            )
    
    if st.button("Сохранить настройки агентов"):
        # Сохранение настроек в session_state
        st.session_state.active_agents = active_agents
        # Обновление оркестратора
        orchestrator.configure_agents(active_agents)
        st.success("✅ Настройки агентов сохранены!")
    
    st.divider()
    
    # Настройка параметров токенов
    st.header("💰 Настройка токенов")
    
    st.write("Настройка параметров использования токенов:")
    
    # Получение текущих настроек
    token_limits = st.session_state.get("token_limits", {"max_per_request": 4000})
    
    max_tokens = st.slider(
        "Максимальное количество токенов на запрос:", 
        min_value=1000, 
        max_value=8000, 
        value=token_limits.get("max_per_request", 4000),
        step=500
    )
    
    cache_enabled = st.checkbox(
        "Включить кэширование запросов", 
        value=os.getenv("ENABLE_CACHE", "true").lower() == "true"
    )
    
    if st.button("Сохранить настройки токенов"):
        # Сохранение настроек в session_state
        st.session_state.token_limits = {
            "max_per_request": max_tokens
        }
        
        # Сохранение в переменные окружения
        try:
            set_key(".env", "ENABLE_CACHE", str(cache_enabled).lower())
            set_key(".env", "MAX_TOKENS_PER_REQUEST", str(max_tokens))
            st.success("✅ Настройки токенов сохранены!")
        except Exception as e:
            st.error(f"❌ Ошибка при сохранении настроек: {str(e)}")
    
    st.divider()
    
    # Расширенные настройки
    st.header("🛠️ Расширенные настройки")
    
    with st.expander("Настройки логирования"):
        log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        current_log_level = os.getenv("LOG_LEVEL", "INFO")
        
        selected_log_level = st.selectbox(
            "Уровень логирования:",
            options=log_levels,
            index=log_levels.index(current_log_level) if current_log_level in log_levels else 1
        )
        
        if st.button("Сохранить настройки логирования"):
            try:
                set_key(".env", "LOG_LEVEL", selected_log_level)
                st.success(f"✅ Уровень логирования установлен: {selected_log_level}")
                st.info("⚠️ Изменения вступят в силу после перезапуска приложения")
            except Exception as e:
                st.error(f"❌ Ошибка при сохранении настроек: {str(e)}")
    
    with st.expander("Очистка данных"):
        st.warning("⚠️ Эти действия нельзя отменить!")
        
        if st.button("Очистить историю чата"):
            try:
                st.session_state.messages = []
                st.success("✅ История чата очищена!")
            except Exception as e:
                st.error(f"❌ Ошибка при очистке истории: {str(e)}")
        
        if st.button("Сбросить статистику токенов"):
            try:
                if "orchestrator" in st.session_state:
                    st.session_state.orchestrator.token_usage = {
                        "total": 0,
                        "per_model": {},
                        "per_agent": {}
                    }
                st.success("✅ Статистика токенов сброшена!")
            except Exception as e:
                st.error(f"❌ Ошибка при сбросе статистики: {str(e)}")

if __name__ == "__main__":
    # Для возможности запуска страницы напрямую
    st.info("Эта страница должна запускаться через основное приложение.")