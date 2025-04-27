"""
Страница аналитики для приложения Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

def render_analytics_page(orchestrator, context_storage=None):
    """
    Отрисовка страницы аналитики
    
    Args:
        orchestrator: Экземпляр оркестратора
        context_storage: Хранилище контекста (опционально)
    """
    st.title("📊 Аналитика мультиагентной системы")
    
    # Получение статистики использования токенов
    token_usage = orchestrator.get_token_usage()
    
    # Отображение основных метрик
    st.header("💡 Основные метрики")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Всего токенов",
            f"{token_usage['total']:,}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Стоимость",
            f"${token_usage['cost']:.2f}",
            delta=None
        )
    
    with col3:
        # Количество диалогов
        dialogs_count = len(st.session_state.get("messages", [])) // 2
        st.metric(
            "Количество диалогов",
            dialogs_count,
            delta=None
        )
    
    # Графики использования токенов
    st.header("📈 Использование токенов")
    
    # По агентам
    st.subheader("Использование по агентам")
    
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
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Нет данных об использовании токенов по агентам")
    
    # По моделям
    st.subheader("Использование по моделям")
    
    if "per_model" in token_usage and token_usage["per_model"]:
        # Создание данных для графика
        models = list(token_usage["per_model"].keys())
        input_tokens = [token_usage["per_model"][model].get("input", 0) for model in models]
        output_tokens = [token_usage["per_model"][model].get("output", 0) for model in models]
        
        # Создание DataFrame
        model_data = pd.DataFrame({
            "Модель": models,
            "Входные токены": input_tokens,
            "Выходные токены": output_tokens
        })
        
        # Преобразование для plotly
        model_data_melted = pd.melt(
            model_data,
            id_vars=["Модель"],
            value_vars=["Входные токены", "Выходные токены"],
            var_name="Тип токенов",
            value_name="Количество"
        )
        
        # Построение графика
        fig = px.bar(
            model_data_melted,
            x="Модель",
            y="Количество",
            color="Тип токенов",
            barmode="group",
            title="Использование токенов по моделям"
        )
        
        # Настройка внешнего вида
        fig.update_layout(
            xaxis_title="Модель",
            yaxis_title="Количество токенов",
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Дополнительная таблица с детальной информацией
        st.subheader("Детальная информация по моделям")
        
        # Расчет стоимости для каждой модели
        model_costs = {}
        for model in models:
            input_cost = token_usage["per_model"][model].get("input", 0) / 1000 * 0.01  # Примерный расчет
            output_cost = token_usage["per_model"][model].get("output", 0) / 1000 * 0.03  # Примерный расчет
            model_costs[model] = input_cost + output_cost
        
        # Создание детальной таблицы
        detail_data = pd.DataFrame({
            "Модель": models,
            "Входные токены": input_tokens,
            "Выходные токены": output_tokens,
            "Всего токенов": [i + o for i, o in zip(input_tokens, output_tokens)],
            "Стоимость ($)": [model_costs[model] for model in models]
        })
        
        st.dataframe(detail_data, use_container_width=True)
    else:
        st.info("Нет данных об использовании токенов по моделям")
    
    # История взаимодействий (если доступно хранилище контекста)
    if context_storage:
        st.header("📜 История взаимодействий")
        
        try:
            # Получение последних взаимодействий
            recent_interactions = context_storage.get_recent_interactions(10)
            
            if recent_interactions:
                # Создание DataFrame
                interactions_data = pd.DataFrame({
                    "Дата": [datetime.datetime.fromisoformat(i["timestamp"]) for i in recent_interactions],
                    "Запрос пользователя": [i["user_input"][:50] + "..." if len(i["user_input"]) > 50 else i["user_input"] for i in recent_interactions],
                    "Токены": [i["tokens_used"] for i in recent_interactions]
                })
                
                # Сортировка по дате
                interactions_data = interactions_data.sort_values("Дата", ascending=True)
                
                # График использования токенов по времени
                fig = px.line(
                    interactions_data,
                    x="Дата",
                    y="Токены",
                    markers=True,
                    title="Использование токенов по времени"
                )
                
                fig.update_layout(
                    xaxis_title="Дата и время",
                    yaxis_title="Количество токенов",
                    height=400
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Таблица с историей
                st.subheader("Последние запросы")
                st.dataframe(interactions_data, use_container_width=True)
            else:
                st.info("История взаимодействий пуста")
        except Exception as e:
            st.error(f"Ошибка при получении истории взаимодействий: {str(e)}")
    
    # Дополнительная информация
    with st.expander("ℹ️ Информация о стоимости"):
        st.markdown("""
        ### Стоимость использования API
        
        Приблизительная стоимость за 1000 токенов:
        
        | Модель | Входные токены | Выходные токены |
        |--------|----------------|-----------------|
        | Claude 3 Opus | $0.015 | $0.075 |
        | Claude 3 Sonnet | $0.003 | $0.015 |
        | Claude 3 Haiku | $0.0003 | $0.0015 |
        | GPT-4 Turbo | $0.01 | $0.03 |
        | GPT-4 | $0.03 | $0.06 |
        | GPT-3.5 Turbo | $0.0005 | $0.0015 |
        
        Обратите внимание, что фактическая стоимость может отличаться в зависимости от актуальных цен API.
        """)

if __name__ == "__main__":
    # Для возможности запуска страницы напрямую
    st.info("Эта страница должна запускаться через основное приложение.")