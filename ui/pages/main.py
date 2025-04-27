"""
Основная страница приложения Streamlit
"""

import streamlit as st
import time
from ui.components import (
    render_sidebar, render_chat_history, 
    render_agent_workflow, render_agent_output
)

def render_main_page(orchestrator, workflow_manager):
    """
    Отрисовка главной страницы приложения
    
    Args:
        orchestrator: Экземпляр оркестратора
        workflow_manager: Экземпляр менеджера рабочих процессов
    """
    # Заголовок страницы
    st.title("🤖 Мультиагентная система разработки")
    
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
    
    # Информация о выбранном рабочем процессе
    if selected_workflow:
        workflow_info = workflow_manager.get_workflow_info(selected_workflow)
        st.info(f"**{workflow_info.get('name', '')}**: {workflow_info.get('description', '')}")
    
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
    
    # Информация о системе в раскрывающемся блоке
    with st.expander("📊 Информация о системе"):
        st.write("**Версия:** 0.1.0")
        st.write("**Дата сборки:** Апрель 2025")
        st.write("**Разработчик:** Команда мультиагентной системы")
        
        # Отображение статистики использования токенов
        if orchestrator:
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

if __name__ == "__main__":
    # Для возможности запуска страницы напрямую
    st.info("Эта страница должна запускаться через основное приложение.")