"""
Основная страница приложения Streamlit
"""

import streamlit as st
import time
import threading # Импортируем потоки для обновления прогресса

# Импортируем доработанные компоненты
from ui.components import (
    render_sidebar, render_chat_history,
    render_agent_workflow_progress, render_agent_output # Используем обновленные компоненты
)

# import logging # Можно добавить логирование и сюда при необходимости
# logger = logging.getLogger("multiagent_system")


def render_main_page(orchestrator, workflow_manager):
    """
    Отрисовка главной страницы приложения

    Args:
        orchestrator: Экземпляр оркестратора
        workflow_manager: Экземпляр менеджера рабочих процессов
    """
    # Заголовок страницы (возможно, уже есть в app.py при использовании router)
    # st.title("🤖 Мультиагентная система разработки")

    # Отображение потока работы агентов (теперь с прогрессом)
    # render_agent_workflow_progress будет вызываться в потоке обновления статуса
    # Удаляем старый вызов здесь, так как он будет отрисовываться динамически

    # Чат-интерфейс для взаимодействия с системой
    st.subheader("💬 Диалог с системой")

    # Отображение истории чата
    if "messages" in st.session_state:
        render_chat_history(st.session_state.messages)

    # Ввод нового сообщения
    user_input = st.text_area("Опишите задачу или запрос:", height=100, key="user_input_main")

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
        format_func=lambda x: workflow_options.get(x, x),
        key="workflow_selector_main"
    )

    # Информация о выбранном рабочем процессе
    if selected_workflow:
        workflow_info = workflow_manager.get_workflow_info(selected_workflow)
        st.info(f"**{workflow_info.get('name', '')}**: {workflow_info.get('description', '')}")

    # Создаем пустой контейнер для отображения прогресса выполнения агентов
    # Этот контейнер будет обновляться в отдельном потоке
    progress_container = st.empty()


    # Отправка запроса
    if st.button("Отправить запрос", key="send_request_button"):
        if not user_input:
            st.error("Пожалуйста, введите описание задачи или запрос!")
        else:
            # Добавление сообщения пользователя в историю
            # Проверяем, чтобы избежать дублирования, если уже добавлено в app.py
            if "messages" not in st.session_state or \
               not st.session_state.messages or \
               st.session_state.messages[-1].get("role") != "user" or \
               st.session_state.messages[-1].get("content") != user_input:
                st.session_state.messages.append({"role": "user", "content": user_input})

            # Отображение сообщения пользователя
            with st.chat_message("user"):
                st.write(user_input)

            # Сбрасываем результаты предыдущего запуска и статусы агентов
            st.session_state.current_agent_results = None
            # Оркестратор сам сбросит статусы агентов при получении нового запроса

            # Обработка запроса через выбранный рабочий процесс
            # Используем spinner пока идет подготовка и первый агент не начал работать
            with st.spinner("Инициализация агентов и обработка запроса..."):

                # Проверка наличия настроенных API ключей перед запуском
                providers_configured = False
                if "providers" in st.session_state:
                    for provider in st.session_state.providers.values():
                        if provider.is_configured():
                            providers_configured = True
                            break

                if not providers_configured:
                    st.error("Пожалуйста, настройте хотя бы один API ключ в разделе настроек!")
                    # Добавляем сообщение об ошибке в историю чата
                    if "messages" not in st.session_state: st.session_state.messages = []
                    st.session_state.messages.append({"role": "assistant", "content": "[Error] Не настроены API ключи. Пожалуйста, перейдите в раздел 'Настройки'."})
                    # Отображаем сообщение об ошибке в чате
                    with st.chat_message("assistant"):
                        st.error("Не настроены API ключи. Пожалуйста, перейдите в раздел 'Настройки'.")

                else:
                    # Выполнение выбранного рабочего процесса
                    start_time = time.time()

                    # --- Запуск обновления прогресса в отдельном потоке ---
                    # Создаем флаг для управления потоком
                    stop_progress_thread = threading.Event()

                    def update_progress_ui():
                        """Функция для обновления прогресса в отдельном потоке"""
                        # Используем контейнер для обновления UI
                        while not stop_progress_thread.is_set():
                            # Получаем текущий статус из оркестратора
                            current_status = orchestrator.get_current_status()

                            # Обновляем отображение прогресса и статусов агентов
                            with progress_container:
                                render_agent_workflow_progress(orchestrator)

                            # Прекращаем обновление, если процесс завершен (прогресс 100%) или возникла ошибка
                            if current_status["progress"] >= 100 or \
                               any(s.get("status") == "error" for s in current_status.get("agents", {}).values()):
                                break

                            time.sleep(0.5) # Частота обновления UI


                    # Запускаем поток обновления прогресса перед вызовом оркестратора
                    progress_thread = threading.Thread(target=update_progress_ui)
                    # progress_thread.daemon = True # Daemon-поток завершится с основным, но может оборваться
                    progress_thread.start()


                    # --- Выполнение рабочего процесса оркестратором ---
                    # Этот вызов блокирует основной поток Streamlit до завершения оркестратора
                    results = workflow_manager.execute_workflow(selected_workflow, user_input)

                    # Сигнализируем потоку обновления прогресса остановиться
                    stop_progress_thread.set()
                    # Ждем завершения потока обновления UI, чтобы убедиться, что последнее обновление отобразилось
                    progress_thread.join(timeout=1) # Не блокируем основной поток надолго


                    total_time = time.time() - start_time
                    # Сохраняем результаты агентов в session_state для отображения ниже
                    st.session_state.current_agent_results = results

                    # Очищаем spinner после завершения
                    # Streamlit spinner в блоке with автоматически исчезнет
                    pass # Код спиннера уже завершился

            # --- Отображение результатов после выполнения ---
            # Эти результаты теперь берутся из session_state после завершения workflow
            st.subheader("🔍 Результаты работы агентов")
            if st.session_state.current_agent_results:
                for agent_name, agent_result in st.session_state.current_agent_results.items():
                    # Проверяем, есть ли у агента результат или ошибка для отображения
                    if "result" in agent_result or "error" in agent_result:
                        render_agent_output(
                            agent_name,
                            agent_result.get("result", agent_result.get("error", "Нет результата")), # Берем result или error
                            agent_result.get("elapsed_time"),
                            agent_result.get("model"),
                            agent_result.get("provider")
                        )
                    else:
                         # Если нет ни result, ни error, возможно, агент был пропущен или неактивен
                         # В текущей реализации render_agent_output уже обрабатывает пустой вывод
                         pass # Ничего не делаем, render_agent_output покажет "Нет результата" или пустой блок


            # Формирование итогового ответа для отображения в чате (это уже делает оркестратор)
            # Итоговый ответ уже добавлен в st.session_state.messages оркестратором


            # Отображение статистики выполнения
            st.info(f"Запрос обработан за {total_time:.2f} секунд")
            # TODO: Возможно, добавить здесь отображение суммарных токенов и стоимости за этот запрос


    # Информация о системе в раскрывающемся блоке
    with st.expander("📊 Информация о системе"):
        st.write("**Версия:** 0.1.0")
        st.write("**Дата сборки:** Апрель 2025") # Обновляем дату сборки
        st.write("**Разработчик:** Команда мультиагентной системы")

        # Отображение статистики использования токенов (берется из оркестратора)
        if orchestrator:
            token_usage = orchestrator.get_token_usage()

            col1, col2 = st.columns(2)
            with col1:
                st.metric("Использовано токенов (всего)", token_usage["total"])
            with col2:
                st.metric("Приблизительная стоимость ($)", f"{token_usage['cost']:.6f}") # Отображаем больше знаков

            # Отображение использования по агентам и моделям (детально)
            if "per_agent" in token_usage and token_usage["per_agent"]:
                st.subheader("Использование по агентам")
                # Используем dataframe для более наглядного отображения
                agent_usage_df = pd.DataFrame(list(token_usage["per_agent"].items()), columns=['Агент', 'Токены'])
                st.dataframe(agent_usage_df, use_container_width=True)


            if "per_model" in token_usage and token_usage["per_model"]:
                st.subheader("Использование по моделям")
                model_data = []
                for model, usage in token_usage["per_model"].items():
                    input_tokens = usage.get("input", 0)
                    output_tokens = usage.get("output", 0)
                    model_data.append({
                        "Модель": model,
                        "Входные токены": input_tokens,
                        "Выходные токены": output_tokens,
                        "Всего": input_tokens + output_tokens,
                        "Стоимость ($)": TokenCounter.estimate_cost(model, input_tokens, output_tokens) # Пересчитываем стоимость здесь для детального отображения
                    })
                model_usage_df = pd.DataFrame(model_data)
                st.dataframe(model_usage_df, use_container_width=True)


        # Информация о сервере
        try:
            import platform
            system_info = platform.uname()
            st.write(f"**Сервер:** {system_info.node}")
            st.write(f"**ОС:** {system_info.system} {system_info.release}")
        except:
            pass


# Этот блок используется только при прямом запуске страницы,
# в многостраничном приложении маршрутизация происходит в app_router.py
# if __name__ == "__main__":
#     # Для возможности запуска страницы напрямую
#     st.info("Эта страница должна запускаться через основное приложение.")
#     # TODO: Добавить здесь минимальную инициализацию для тестирования страницы напрямую