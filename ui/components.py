"""
Компоненты пользовательского интерфейса для приложения Streamlit
"""

import streamlit as st
import datetime
import time
import pandas as pd
import plotly.express as px
import re # Импортируем регулярные выражения

# --- Новый рендер-селектор модели агента ---
def render_agent_model_selector(agent_name, available_models, default_model):
    """
    Отображает селектор модели для конкретного агента

    Args:
        agent_name: Имя агента
        available_models: Словарь доступных моделей {id: описание}
        default_model: Модель по умолчанию

    Returns:
        str: ID выбранной модели
    """
    agent_models = st.session_state.get("agent_models", {})
    current_model = agent_models.get(agent_name, default_model)

    key = f"model_selector_{agent_name}"

    selected_model = st.selectbox(
        f"Модель для {agent_name}:",
        options=list(available_models.keys()),
        format_func=lambda x: available_models.get(x, x),
        index=list(available_models.keys()).index(current_model) if current_model in available_models else 0,
        key=key
    )

    if "agent_models" not in st.session_state:
        st.session_state.agent_models = {}
    st.session_state.agent_models[agent_name] = selected_model

    return selected_model

# --- Рендер боковой панели ---
def render_sidebar(orchestrator=None):
    """
    Отрисовка боковой панели с настройками

    Args:
        orchestrator: Экземпляр оркестратора (опционально)
    """
    with st.sidebar:
        st.header("⚙️ Настройки")

        # Проверка API ключей (только отображение статуса)
        with st.expander("🔑 API Ключи", expanded=False):
             st.subheader("Статус API")
             if orchestrator and orchestrator.providers:
                  for provider_name, provider in orchestrator.providers.items():
                       status = "success" if provider.is_configured() else "error"
                       status_text = "Настроен" if provider.is_configured() else "Не настроен"
                       icon = "✅" if status == "success" else "❌"
                       st.markdown(f"{icon} **{provider_name.capitalize()}:** {status_text}")
                       if provider.is_configured() and hasattr(provider, 'model'):
                            st.caption(f"Модель по умолчанию: {getattr(provider, 'model', 'N/A')}")
             else:
                  st.info("Провайдеры API не инициализированы.")
             st.markdown("Перейдите в раздел 'Настройки' для управления ключами.")


        # Настройка агентов
        with st.expander("🤖 Агенты", expanded=True):
            st.write("Выберите агентов для использования:")

            agents = {
                "Planner": "📝 Планировщик",
                "Architect": "🏗️ Архитектор",
                "Coder": "💻 Программист",
                "Reviewer": "🔍 Ревьюер",
                "Tester": "🧪 Тестировщик",
                "Documenter": "📚 Документатор",
                "ProjectManager": "📁 Менеджер проектов"
            }
            agent_descriptions = {
                "Planner": "анализирует задачу и создает план",
                "Architect": "проектирует структуру решения",
                "Coder": "пишет код",
                "Reviewer": "проверяет код на ошибки",
                "Tester": "создает тесты",
                "Documenter": "пишет документацию",
                "ProjectManager": "создает файлы проекта на сервере"
            }


            active_agents = st.session_state.get("active_agents", {})

            # Отображаем чекбоксы в две колонки
            cols = st.columns(2)
            agent_list = list(agents.keys())
            for i, agent_key in enumerate(agent_list):
                 with cols[i % 2]: # Распределяем по колонкам
                    active_agents[agent_key] = st.checkbox(
                        f"{agents[agent_key]} - {agent_descriptions[agent_key]}",
                        value=active_agents.get(agent_key, True),
                        key=f"sidebar_agent_{agent_key}"
                    )

            st.session_state.active_agents = active_agents

            if orchestrator:
                orchestrator.configure_agents(active_agents)

        # Настройка моделей (только отображение общих настроек)
        with st.expander("🧠 Модели", expanded=False):
            st.subheader("Настройки моделей")
            st.write("Перейдите в раздел 'Настройки' для управления моделями агентов.")
            # Здесь можно отобразить текущие модели по умолчанию, если они доступны в session_state
            if "models" in st.session_state:
                st.write("**Модели по умолчанию:**")
                st.write(f"- Claude: {st.session_state.models.get('claude', 'Не задана')}")
                st.write(f"- GPT: {st.session_state.models.get('gpt', 'Не задана')}")


        # Настройка токенов
        with st.expander("💰 Токены и стоимость", expanded=False):
            if orchestrator:
                usage = orchestrator.get_token_usage()
                st.metric("Всего использовано токенов", f"{usage['total']:,}")
                st.metric("Приблизительная стоимость ($)", f"{usage['cost']:.6f}") # Отображаем больше знаков для точности

                # Отображение использования по агентам и моделям (кратко)
                if "per_agent" in usage and usage["per_agent"]:
                     st.caption("Использование по агентам:")
                     agent_usage_str = ", ".join([f"{a}: {t:,}" for a, t in usage["per_agent"].items()])
                     st.caption(agent_usage_str)

                if "per_model" in usage and usage["per_model"]:
                     st.caption("Использование по моделям:")
                     model_usage_str = ", ".join([f"{m}: {u.get('input',0)+u.get('output',0):,}" for m, u in usage["per_model"].items()])
                     st.caption(model_usage_str)

            else:
                st.info("Статистика токенов будет доступна после первого запроса.")

            st.write("Перейдите в раздел 'Настройки' для управления лимитами токенов.")


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

# --- Рендер истории чата ---
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
        # Токены отображаем только для ответов ассистента
        tokens = message.get("tokens", None)

        with st.chat_message(role):
            st.markdown(content)
            if role == "assistant" and tokens is not None:
                 st.caption(f"Токенов в ответе: {tokens}")


# --- НОВАЯ РЕАЛИЗАЦИЯ: Рендер потока работы агентов с прогрессом ---
def render_agent_workflow_progress(orchestrator):
    """
    Отрисовка потока работы агентов с индикатором прогресса и статусом.
    Использует детальный статус из оркестратора.
    """
    # Получаем полный статус активных агентов из оркестратора
    agent_statuses = orchestrator.get_agent_statuses() if orchestrator else []

    if not agent_statuses:
        # Если нет активных агентов (например, не выбран ни один в настройках)
        if orchestrator and not orchestrator.get_active_agents():
             st.warning("Не выбрано ни одного агента в настройках.")
        # Если оркестратор еще не инициализирован или статусы пусты по другой причине
        # st.info("Ожидание запуска рабочего процесса агентов...") # Это сообщение может быть избыточным, UI main.py сам показывает spinner

        return # Ничего не рендерим, если нет активных агентов

    st.subheader("🔄 Порядок работы и статус выполнения агентов")

    # Иконки агентов
    icons = {
        "Planner": "📝",
        "Architect": "🏗️",
        "Coder": "💻",
        "Reviewer": "🔍",
        "Tester": "🧪",
        "Documenter": "📚",
        "ProjectManager": "📁"
    }
    # Цвета и текст статусов
    status_colors = {
        "pending": "🟡 Ожидание",
        "running": "🟠 Выполняется...",
        "done": "🟢 Готово",
        "error": "🔴 Ошибка"
    }

    cols = st.columns(len(agent_statuses))

    for i, agent in enumerate(agent_statuses):
        name = agent.get("name", f"Агент {i+1}")
        status = agent.get("status", "pending")
        elapsed = agent.get("elapsed_time")
        model = agent.get("model", "N/A")
        provider = agent.get("provider", "N/A")

        icon = icons.get(name, "🤖")
        status_text = status_colors.get(status, "⚪️ Неизвестно")

        with cols[i]:
            # Отображаем иконку, имя и текущий статус
            st.markdown(f"### {icon} {name}")
            st.markdown(f"**Статус:** {status_text}")

            # Отображаем время выполнения, модель и провайдера, если доступно
            if status != "pending": # Показываем информацию только после начала выполнения
                details = []
                if elapsed is not None:
                    details.append(f"⏱ {elapsed:.2f} сек")
                # Отображаем модель и провайдера, если они определены для агента
                if model and model != "N/A":
                     details.append(f"🧠 {model}")
                if provider and provider != "N/A":
                     details.append(f"🔌 {provider}")

                if details:
                    st.caption(" | ".join(details))
                # Если статус "Ошибка", можно добавить индикатор
                if status == "error":
                     st.error("Смотрите подробности в результатах агента.")


# --- НОВАЯ РЕАЛИЗАЦИЯ: Рендер вывода агента ---
def render_agent_output(agent_name, output, elapsed_time=None, model=None, provider=None):
    """
    Рендер вывода агента в разворачивающемся блоке.
    Учитывает сообщения об ошибках и корректно отображает код-блоки.
    """
    icons = {
        "Planner": "📝",
        "Architect": "🏗️",
        "Coder": "💻",
        "Reviewer": "🔍",
        "Tester": "🧪",
        "Documenter": "📚",
        "ProjectManager": "📁"
    }
    icon = icons.get(agent_name, "🤖")

    # Формируем заголовок разворачивающегося блока
    title_parts = [f"{icon} **{agent_name}**"]
    details = []
    if elapsed_time is not None:
        details.append(f"⏱ {elapsed_time:.2f} сек")
    if model:
        details.append(f"🧠 {model}")
    if provider:
        details.append(f"🔌 {provider}")

    if details:
        title_parts.append(" | ".join(details))

    # Добавляем индикатор ошибки, если вывод начинается с "[Error]"
    is_error_output = isinstance(output, str) and output.strip().startswith("[Error]")
    if is_error_output:
        title_parts.insert(0, "🔴") # Добавляем красный кружок в начало

    title = " ".join(title_parts)


    # Открываем разворачивающийся блок
    with st.expander(title, expanded=True):
        if is_error_output:
             st.error(output) # Отображаем сообщение об ошибке как ошибку
        elif not output or output.strip() == "":
             st.info("Агент не вернул содержания.") # Сообщение, если вывод пуст
        else:
            # Пытаемся аккуратно разобрать блоки кода для корректного отображения Markdown
            code_pattern = re.compile(r"```([a-zA-Z0-9_+-]*)\n(.*?)```", re.DOTALL)
            last_end = 0
            code_blocks_found = False

            for m in code_pattern.finditer(output):
                code_blocks_found = True
                start, end = m.span()
                lang = m.group(1).strip()
                code = m.group(2).strip()

                # Выводим текст перед блоком кода
                if start > last_end:
                    st.markdown(output[last_end:start])

                # Выводим сам блок кода
                st.code(code, language=lang if lang else None, line_numbers=True)
                last_end = end

            # Выводим текст после последнего блока кода
            if last_end < len(output):
                st.markdown(output[last_end:])

            # Если блоки кода не найдены, выводим весь текст как Markdown
            if not code_blocks_found:
                 st.markdown(output)


# --- Специальный компонент для выбора или создания проекта ---
def render_project_selector(project_manager, with_creation=True):
    """
    Отображает селектор проекта с возможностью создания нового

    Args:
        project_manager: Экземпляр SecureProjectManager
        with_creation: Отображать ли форму создания нового проекта

    Returns:
        str: Название выбранного или созданного проекта
    """
    # Получаем список существующих проектов
    projects = project_manager.list_projects()
    
    selected_project = None
    
    if projects:
        st.subheader("Выберите существующий проект:")
        selected_project = st.selectbox(
            "Проект:",
            options=[""] + projects,
            format_func=lambda x: f"{x}" if x else "Выберите проект..."
        )
    
    # Если включена возможность создания проекта
    if with_creation:
        with st.expander("➕ Создать новый проект", expanded=not selected_project):
            with st.form("create_project_form"):
                new_project_name = st.text_input("Название проекта:")
                new_project_description = st.text_area("Описание проекта:")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    create_src = st.checkbox("Создать src/", value=True)
                with col2:
                    create_docs = st.checkbox("Создать docs/", value=True)
                with col3:
                    create_tests = st.checkbox("Создать tests/", value=True)
                
                submit_button = st.form_submit_button("Создать проект")
                
                if submit_button and new_project_name:
                    result = project_manager.create_project(new_project_name)
                    
                    if result["success"]:
                        st.success(result["message"])
                        
                        # Создаем README.md с описанием
                        if new_project_description:
                            readme_content = f"# {new_project_name}\n\n{new_project_description}\n\nПроект создан с помощью мультиагентной системы.\n"
                            project_manager.create_file(new_project_name, "README.md", readme_content)
                        
                        # Создаем базовую структуру
                        if create_src:
                            project_manager.create_file(new_project_name, "src/.gitkeep", "")
                        if create_docs:
                            project_manager.create_file(new_project_name, "docs/.gitkeep", "")
                        if create_tests:
                            project_manager.create_file(new_project_name, "tests/.gitkeep", "")
                        
                        # Устанавливаем новый проект как выбранный
                        selected_project = new_project_name
                    else:
                        st.error(result["message"])
    
    return selected_project


# --- Компонент для сохранения кода в проект ---
def render_save_to_project_button(code_blocks, project_manager):
    """
    Отображает кнопку и диалог для сохранения кода в проект

    Args:
        code_blocks: Словарь {имя_файла: содержимое} или текст с кодом
        project_manager: Экземпляр SecureProjectManager

    Returns:
        bool: True, если код был сохранен успешно
    """
    if st.button("💾 Сохранить в проект"):
        # Отображаем селектор проекта
        selected_project = render_project_selector(project_manager)
        
        if not selected_project:
            st.warning("Выберите или создайте проект для сохранения кода.")
            return False
        
        # Извлекаем блоки кода, если передан текст
        if isinstance(code_blocks, str):
            from agents.project_manager import ProjectManagerAgent
            temp_agent = ProjectManagerAgent()
            extracted_blocks = temp_agent.extract_file_blocks(code_blocks)
            if extracted_blocks:
                code_blocks = extracted_blocks
            else:
                # Если не удалось извлечь блоки, создаем один файл
                code_blocks = {"main.py": code_blocks}
        
        # Сохраняем каждый файл в проект
        with st.spinner("Сохранение файлов в проект..."):
            success_count = 0
            error_messages = []
            
            for file_path, content in code_blocks.items():
                result = project_manager.create_file(selected_project, file_path, content)
                if result["success"]:
                    success_count += 1
                else:
                    error_messages.append(f"Ошибка при создании {file_path}: {result['message']}")
            
            if success_count > 0:
                st.success(f"Успешно сохранено {success_count} файлов в проект '{selected_project}'")
            
            if error_messages:
                for error in error_messages:
                    st.error(error)
            
            return success_count > 0 and not error_messages
    
    return False


# Остальные компоненты UI (анимация, графики, индикаторы и т.д.)
def render_processing_animation():
    """
    Отрисовка анимации обработки запроса
    """
    # Эта функция может быть заменена более сложным индикатором на основе статусов агентов
    # пока оставляем базовую реализацию Streamlit spinner
    pass # Теперь прогресс отображается через render_agent_workflow_progress


def render_token_usage_chart(token_usage):
    """
    Отрисовка графика использования токенов (по агентам)
    """
    if "per_agent" in token_usage and token_usage["per_agent"]:
        agent_data = pd.DataFrame({
            "Агент": list(token_usage["per_agent"].keys()),
            "Токены": list(token_usage["per_agent"].values())
        })

        total = agent_data["Токены"].sum()
        if total > 0:
            agent_data["Процент"] = agent_data["Токены"] / total * 100
        else:
            agent_data["Процент"] = 0

        fig = px.bar(
            agent_data,
            x="Агент",
            y="Токены",
            text=agent_data["Процент"].apply(lambda x: f"{x:.1f}%") if total > 0 else "",
            color="Агент",
            title="Использование токенов по агентам"
        )

        fig.update_traces(textposition="outside")
        fig.update_layout(
            xaxis_title="Агент",
            yaxis_title="Количество токенов",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных об использовании токенов по агентам")

# Селекторы, индикаторы статуса, загрузчики и т.д.
def render_model_selector(models, provider_name, on_change=None):
     # ... (код остается прежним)
     pass

def render_workflow_selector(workflows, on_change=None):
     # ... (код остается прежним)
     pass

def render_status_indicator(status, text=None):
    icons = {
        "success": "✅",
        "warning": "⚠️",
        "error": "❌",
        "info": "ℹ️",
        "loading": "🔄",
        "pending": "🟡", # Добавлены иконки для новых статусов
        "running": "🟠",
        "done": "🟢",
    }

    icon = icons.get(status, "ℹ️")

    if text:
        st.markdown(f"{icon} {text}")
    else:
        st.markdown(icon)

def render_file_uploader(label, type, key, help=None):
     # ... (код остается прежним)
     pass

def render_download_button(content, file_name, label="Скачать файл", mime=None):
     # ... (код остается прежним)
     pass

def render_code_editor(code, language="python", height=300, key=None):
     # ... (код остается прежним)
     pass

def render_tabs_interface(tabs_content, default_tab=0):
     # ... (код остается прежним)
     pass

def render_metrics_panel(metrics):
     # ... (код остается прежним)
     pass

def render_agent_info(agent_name, description=None, capabilities=None):
     # ... (код остается прежним)
     pass

def render_api_status(providers):
     # ... (код остается прежним)
     pass

def render_settings_form(orchestrator, on_save=None):
     # ... (код остается прежним)
     pass