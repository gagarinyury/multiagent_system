"""
Компоненты пользовательского интерфейса для приложения Streamlit
"""

import streamlit as st
import datetime
import time
import pandas as pd
import plotly.express as px

def render_sidebar(orchestrator=None):
    """
    Отрисовка боковой панели с настройками
    
    Args:
        orchestrator: Экземпляр оркестратора (опционально)
    """
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Проверка API ключей
        with st.expander("🔑 API Ключи", expanded=False):
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
            
            # Получение текущих настроек агентов
            active_agents = st.session_state.get("active_agents", {})
            
            # Отображение чекбоксов для выбора агентов
            for agent_key, agent_desc in agents.items():
                active_agents[agent_key] = st.checkbox(
                    agent_desc, 
                    value=active_agents.get(agent_key, True),
                    key=f"sidebar_agent_{agent_key}"
                )
            
            # Сохранение настроек в session_state
            st.session_state.active_agents = active_agents
            
            # Обновление оркестратора, если он предоставлен
            if orchestrator:
                orchestrator.configure_agents(active_agents)
        
        # Настройка моделей
        with st.expander("🧠 Модели", expanded=False):
            claude_models = {
                "claude-3-opus-20240229": "Claude 3 Opus (мощная, медленная)",
                "claude-3-sonnet-20240224": "Claude 3 Sonnet (сбалансированная)",
                "claude-3-haiku-20240307": "Claude 3 Haiku (быстрая, экономичная)"
            }
            
            gpt_models = {
                "gpt-4-turbo-preview": "GPT-4 Turbo (мощная, медленная)",
                "gpt-4": "GPT-4 (предыдущая версия)",
                "gpt-3.5-turbo": "GPT-3.5 Turbo (быстрая, экономичная)"
            }
            
            # Получение текущих настроек моделей
            models = st.session_state.get("models", {
                "claude": "claude-3-sonnet-20240224", 
                "gpt": "gpt-4-turbo-preview"
            })
            
            st.write("Модель Claude:")
            selected_claude = st.selectbox(
                "Выберите модель Claude:",
                options=list(claude_models.keys()),
                format_func=lambda x: claude_models.get(x, x),
                index=list(claude_models.keys()).index(models.get("claude", "claude-3-sonnet-20240224")) if models.get("claude") in claude_models else 1
            )
            
            st.write("Модель GPT:")
            selected_gpt = st.selectbox(
                "Выберите модель GPT:",
                options=list(gpt_models.keys()),
                format_func=lambda x: gpt_models.get(x, x),
                index=list(gpt_models.keys()).index(models.get("gpt", "gpt-4-turbo-preview")) if models.get("gpt") in gpt_models else 0
            )
            
            # Сохранение настроек в session_state
            st.session_state.models = {
                "claude": selected_claude,
                "gpt": selected_gpt
            }
            
            # Обновление моделей в оркестраторе
            if orchestrator and "providers" in st.session_state:
                providers = st.session_state.providers
                for provider_name, model_name in st.session_state.models.items():
                    if provider_name in providers:
                        providers[provider_name].set_model(model_name)
        
        # Настройка токенов
        with st.expander("💰 Токены и стоимость", expanded=False):
            if orchestrator:
                usage = orchestrator.get_token_usage()
                st.metric("Использовано токенов", f"{usage['total']:,}")
                st.metric("Стоимость ($)", f"{usage['cost']:.4f}")
            else:
                st.info("Статистика токенов будет доступна после первого запроса.")
            
            st.write("Лимиты токенов:")
            
            # Получение текущих настроек лимитов токенов
            token_limits = st.session_state.get("token_limits", {"max_per_request": 4000})
            
            max_tokens_per_request = st.slider(
                "Максимум токенов на запрос:", 
                100, 8000, 
                token_limits.get("max_per_request", 4000), 
                100
            )
            
            # Сохранение настроек в session_state
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
            st.markdown(content)

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
    
    # Иконки агентов
    icons = {
        "Planner": "📝",
        "Architect": "🏗️",
        "Coder": "💻",
        "Reviewer": "🔍",
        "Tester": "🧪",
        "Documenter": "📚"
    }
    
    # Описания агентов
    descriptions = {
        "Planner": "Создает план выполнения задачи",
        "Architect": "Проектирует архитектуру решения",
        "Coder": "Пишет программный код",
        "Reviewer": "Проверяет код на ошибки",
        "Tester": "Создает тесты",
        "Documenter": "Готовит документацию"
    }
    
    for i, agent_name in enumerate(active_agent_names):
        with cols[i]:
            st.markdown(f"**{i+1}. {agent_name}**")
            st.markdown(f"{icons.get(agent_name, '🤖')}")
            st.caption(descriptions.get(agent_name, ""))
    
    # Добавление визуальных стрелок между агентами (CSS)
    if len(active_agent_names) > 1:
        st.markdown(
            """
            <style>
            .stHorizontalBlock > div {
                position: relative;
                text-align: center;
            }
            .stHorizontalBlock > div:not(:last-child)::after {
                content: "➡️";
                position: absolute;
                top: 50%;
                right: -10px;
                transform: translateY(-50%);
                font-size: 20px;
                opacity: 0.7;
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
        st.markdown(output)
        
        # Если это код от Coder, добавляем кнопку для копирования
        if agent_name == "Coder" and "```" in output:
            code_blocks = []
            in_code_block = False
            current_block = []
            
            for line in output.split("\n"):
                if line.startswith("```"):
                    if in_code_block:
                        # Конец блока кода
                        in_code_block = False
                        code_blocks.append("\n".join(current_block))
                        current_block = []
                    else:
                        # Начало блока кода
                        in_code_block = True
                elif in_code_block:
                    current_block.append(line)
            
            # Если есть блоки кода, добавляем кнопки для их копирования
            if code_blocks:
                for i, code in enumerate(code_blocks):
                    # Убираем идентификатор языка из первой строки, если он есть
                    if code.strip() and "\n" in code:
                        first_line, rest = code.split("\n", 1)
                        if first_line.strip() in ["python", "javascript", "html", "css", "java"]:
                            code = rest
                    
                    st.code(code, line_numbers=True)
                    st.button(f"Копировать блок кода {i+1}", key=f"copy_button_{agent_name}_{i}")

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

def render_token_usage_chart(token_usage):
    """
    Отрисовка графика использования токенов
    
    Args:
        token_usage: Словарь с данными об использовании токенов
    """
    if "per_agent" in token_usage and token_usage["per_agent"]:
        # Создание DataFrame для графика
        agent_data = pd.DataFrame({
            "Агент": list(token_usage["per_agent"].keys()),
            "Токены": list(token_usage["per_agent"].values())
        })
        
        # Расчет процентов
        total = agent_data["Токены"].sum()
        agent_data["Процент"] = agent_data["Токены"] / total * 100
        
        # Построение графика
        fig = px.bar(
            agent_data,
            x="Агент",
            y="Токены",
            text=agent_data["Процент"].apply(lambda x: f"{x:.1f}%"),
            color="Агент",
            title="Использование токенов по агентам"
        )
        
        # Настройка внешнего вида
        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_title="Агент",
            yaxis_title="Количество токенов",
            height=400
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных об использовании токенов по агентам")

def render_model_selector(models, provider_name, on_change=None):
    """
    Отрисовка селектора моделей с возможностью настройки
    
    Args:
        models: Словарь с моделями и их описанием
        provider_name: Имя провайдера ('claude', 'gpt')
        on_change: Функция обратного вызова при изменении (опционально)
    """
    # Получение текущих настроек моделей
    current_models = st.session_state.get("models", {})
    
    # Значение по умолчанию
    default_model = list(models.keys())[0]
    if provider_name in current_models:
        default_model = current_models[provider_name]
    
    # Создание селектора
    selected_model = st.selectbox(
        f"Выберите модель {provider_name.capitalize()}:",
        options=list(models.keys()),
        format_func=lambda x: models.get(x, x),
        index=list(models.keys()).index(default_model) if default_model in models else 0,
        key=f"model_selector_{provider_name}",
        on_change=on_change if on_change else None
    )
    
    # Обновление состояния
    if provider_name in current_models:
        current_models[provider_name] = selected_model
        st.session_state.models = current_models
    
    return selected_model

def render_workflow_selector(workflows, on_change=None):
    """
    Отрисовка селектора рабочих процессов
    
    Args:
        workflows: Словарь с рабочими процессами и их описанием
        on_change: Функция обратного вызова при изменении (опционально)
    """
    # Получение текущего рабочего процесса
    current_workflow = st.session_state.get("selected_workflow", "standard")
    
    # Создание селектора
    selected_workflow = st.selectbox(
        "Выберите рабочий процесс:",
        options=list(workflows.keys()),
        format_func=lambda x: workflows.get(x, x),
        index=list(workflows.keys()).index(current_workflow) if current_workflow in workflows else 0,
        key="workflow_selector",
        on_change=on_change if on_change else None
    )
    
    # Обновление состояния
    st.session_state.selected_workflow = selected_workflow
    
    return selected_workflow

def render_status_indicator(status, text=None):
    """
    Отрисовка индикатора статуса
    
    Args:
        status: Статус ('success', 'warning', 'error', 'info')
        text: Текст статуса (опционально)
    """
    icons = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "loading": "🔄"
    }
    
    icon = icons.get(status, "ℹ️")
    
    if text:
        st.markdown(f"{icon} {text}")
    else:
        st.markdown(icon)

def render_file_uploader(label, type, key, help=None):
    """
    Отрисовка загрузчика файлов с улучшенным UI
    
    Args:
        label: Метка загрузчика
        type: Тип файлов для загрузки ('py', 'txt', 'json', и т.д.)
        key: Ключ для идентификации загрузчика
        help: Текст подсказки (опционально)
    
    Returns:
        Загруженный файл или None
    """
    uploaded_file = st.file_uploader(
        label,
        type=type,
        key=key,
        help=help
    )
    
    if uploaded_file:
        file_details = {
            "Имя файла": uploaded_file.name,
            "Тип файла": uploaded_file.type,
            "Размер": f"{uploaded_file.size / 1024:.2f} KB"
        }
        
        with st.expander("📄 Детали файла", expanded=False):
            for key, value in file_details.items():
                st.write(f"**{key}:** {value}")
    
    return uploaded_file

def render_download_button(content, file_name, label="Скачать файл", mime=None):
    """
    Отрисовка кнопки для скачивания файла
    
    Args:
        content: Содержимое файла для скачивания
        file_name: Имя файла
        label: Метка кнопки (опционально)
        mime: MIME-тип файла (опционально)
    """
    st.download_button(
        label=label,
        data=content,
        file_name=file_name,
        mime=mime
    )

def render_code_editor(code, language="python", height=300, key=None):
    """
    Отрисовка редактора кода
    
    Args:
        code: Исходный код
        language: Язык программирования (опционально)
        height: Высота редактора в пикселях (опционально)
        key: Ключ для идентификации редактора (опционально)
    
    Returns:
        str: Отредактированный код
    """
    return st.text_area(
        "Редактор кода",
        value=code,
        height=height,
        key=key or f"code_editor_{hash(code)}"
    )

def render_tabs_interface(tabs_content, default_tab=0):
    """
    Отрисовка интерфейса с вкладками
    
    Args:
        tabs_content: Словарь {имя_вкладки: функция_отрисовки}
        default_tab: Индекс вкладки по умолчанию (опционально)
    """
    tab_names = list(tabs_content.keys())
    tabs = st.tabs(tab_names)
    
    for i, (tab_name, render_func) in enumerate(tabs_content.items()):
        with tabs[i]:
            render_func()

def render_metrics_panel(metrics):
    """
    Отрисовка панели с метриками
    
    Args:
        metrics: Словарь с метриками {имя_метрики: значение, ...}
    """
    cols = st.columns(len(metrics))
    
    for i, (metric_name, metric_value) in enumerate(metrics.items()):
        with cols[i]:
            st.metric(
                label=metric_name,
                value=metric_value
            )

def render_agent_info(agent_name, description=None, capabilities=None):
    """
    Отрисовка информации об агенте
    
    Args:
        agent_name: Имя агента
        description: Описание агента (опционально)
        capabilities: Список возможностей агента (опционально)
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
    
    st.markdown(f"### {icon} {agent_name}")
    
    if description:
        st.markdown(description)
    
    if capabilities:
        st.markdown("**Возможности:**")
        for capability in capabilities:
            st.markdown(f"- {capability}")

def render_api_status(providers):
    """
    Отрисовка статуса API
    
    Args:
        providers: Словарь с провайдерами
    """
    st.subheader("🔌 Статус API")
    
    for provider_name, provider in providers.items():
        status = "success" if provider.is_configured() else "error"
        status_text = "Настроен" if provider.is_configured() else "Не настроен"
        render_status_indicator(status, f"{provider_name.capitalize()}: {status_text}")
        
        if provider.is_configured():
            st.caption(f"Модель: {provider.model}")

def render_settings_form(orchestrator, on_save=None):
    """
    Отрисовка формы настроек
    
    Args:
        orchestrator: Экземпляр оркестратора
        on_save: Функция обратного вызова при сохранении (опционально)
    """
    with st.form("settings_form"):
        # API ключи
        st.subheader("🔑 API Ключи")
        anthropic_key = st.text_input("API ключ Anthropic (Claude):", type="password")
        openai_key = st.text_input("API ключ OpenAI (GPT):", type="password")
        
        # Модели
        st.subheader("🧠 Модели")
        claude_models = {
            "claude-3-opus-20240229": "Claude 3 Opus (мощная, медленная)",
            "claude-3-sonnet-20240224": "Claude 3 Sonnet (сбалансированная)",
            "claude-3-haiku-20240307": "Claude 3 Haiku (быстрая, экономичная)"
        }
        
        gpt_models = {
            "gpt-4-turbo-preview": "GPT-4 Turbo (мощная, медленная)",
            "gpt-4": "GPT-4 (предыдущая версия)",
            "gpt-3.5-turbo": "GPT-3.5 Turbo (быстрая, экономичная)"
        }
        
        # Получение текущих настроек моделей
        models = st.session_state.get("models", {
            "claude": "claude-3-sonnet-20240224", 
            "gpt": "gpt-4-turbo-preview"
        })
        
        selected_claude = st.selectbox(
            "Модель Claude:",
            options=list(claude_models.keys()),
            format_func=lambda x: claude_models.get(x, x),
            index=list(claude_models.keys()).index(models.get("claude", "claude-3-sonnet-20240224")) if models.get("claude") in claude_models else 1
        )
        
        selected_gpt = st.selectbox(
            "Модель GPT:",
            options=list(gpt_models.keys()),
            format_func=lambda x: gpt_models.get(x, x),
            index=list(gpt_models.keys()).index(models.get("gpt", "gpt-4-turbo-preview")) if models.get("gpt") in gpt_models else 0
        )
        
        # Настройка токенов
        st.subheader("💰 Токены")
        token_limits = st.session_state.get("token_limits", {"max_per_request": 4000})
        max_tokens_per_request = st.slider(
            "Максимум токенов на запрос:", 
            100, 8000, 
            token_limits.get("max_per_request", 4000), 
            100
        )
        
        # Кнопка сохранения
        submitted = st.form_submit_button("Сохранить настройки")
        
        if submitted:
            # Сохранение ключей
            if anthropic_key:
                orchestrator.set_provider_key("claude", anthropic_key)
            if openai_key:
                orchestrator.set_provider_key("gpt", openai_key)
            
            # Сохранение моделей
            st.session_state.models = {
                "claude": selected_claude,
                "gpt": selected_gpt
            }
            
            for provider_name, model_name in st.session_state.models.items():
                if provider_name in orchestrator.providers:
                    orchestrator.providers[provider_name].set_model(model_name)
            
            # Сохранение лимитов токенов
            st.session_state.token_limits = {
                "max_per_request": max_tokens_per_request
            }
            
            st.success("Настройки сохранены!")
            
            if on_save:
                on_save()