"""
Модуль для оптимизации контекста взаимодействия с LLM
"""

class ContextOptimizer:
    """
    Класс для оптимизации контекста и минимизации расхода токенов
    """
    def __init__(self, llm_provider=None):
        """
        Инициализация оптимизатора контекста
        
        Args:
            llm_provider: Провайдер LLM для помощи в оптимизации (опционально)
        """
        self.llm_provider = llm_provider
    
    def compress_history(self, messages, max_tokens=2000):
        """
        Сжатие истории сообщений для экономии токенов
        
        Args:
            messages: Список сообщений
            max_tokens: Максимальное количество токенов
            
        Returns:
            list: Сжатая история сообщений
        """
        if not messages:
            return []
        
        # Если провайдер LLM доступен, можно использовать его для сжатия
        if self.llm_provider and self.llm_provider.is_configured():
            return self._compress_with_llm(messages, max_tokens)
        else:
            return self._compress_simple(messages, max_tokens)
    
    def _compress_simple(self, messages, max_tokens):
        """
        Простое сжатие истории путем удаления старых сообщений
        
        Args:
            messages: Список сообщений
            max_tokens: Максимальное количество токенов
            
        Returns:
            list: Сжатая история сообщений
        """
        # Копия сообщений для работы
        compressed = messages.copy()
        
        # Оценка общего количества токенов
        total_tokens = sum(self._estimate_tokens(m.get("content", "")) for m in compressed)
        
        # Пока превышаем лимит, удаляем старые сообщения (кроме системных инструкций)
        while total_tokens > max_tokens and len(compressed) > 1:
            # Находим первое не-системное сообщение
            for i, msg in enumerate(compressed):
                if msg.get("role") != "system":
                    removed = compressed.pop(i)
                    total_tokens -= self._estimate_tokens(removed.get("content", ""))
                    break
        
        return compressed
    
    def _compress_with_llm(self, messages, max_tokens):
        """
        Сжатие истории с помощью LLM
        
        Args:
            messages: Список сообщений
            max_tokens: Максимальное количество токенов
            
        Returns:
            list: Сжатая история сообщений
        """
        # Сначала применяем простое сжатие, если сообщений очень много
        if len(messages) > 20:
            messages = self._compress_simple(messages, max_tokens * 2)  # Даем запас для лучшего сжатия
        
        # Формируем запрос для LLM
        history_text = "\n\n".join([
            f"{m.get('role', 'unknown')}: {m.get('content', '')}" 
            for m in messages if m.get('role') != 'system'
        ])
        
        prompt = f"""
        Ниже приведена история диалога. Пожалуйста, сожми её, сохранив все важные детали и информацию.
        
        {history_text}
        
        Краткое резюме важных моментов:
        """
        
        # Получаем сжатое резюме от LLM
        summary = self.llm_provider.complete(prompt, temperature=0.3, max_tokens=max_tokens // 2)
        
        # Сохраняем системные сообщения и добавляем резюме
        result = [m for m in messages if m.get("role") == "system"]
        result.append({
            "role": "system",
            "content": f"Резюме предыдущих взаимодействий:\n{summary}"
        })
        
        # Добавляем последние 2-3 сообщения для контекста
        result.extend(messages[-min(3, len(messages)):])
        
        return result
    
    def _estimate_tokens(self, text):
        """
        Оценка количества токенов в тексте
        
        Args:
            text: Текст для оценки
            
        Returns:
            int: Приблизительное количество токенов
        """
        # Простая эвристика: 1 токен ~ 4 символа
        return len(text) // 4 if text else 0
    
    def filter_relevant_context(self, query, context_items, max_items=5):
        """
        Фильтрация контекста по релевантности к запросу
        
        Args:
            query: Запрос пользователя
            context_items: Элементы контекста
            max_items: Максимальное количество элементов
            
        Returns:
            list: Отфильтрованные элементы контекста
        """
        # Векторизация запроса (простая)
        query_words = set(query.lower().split())
        
        # Оценка релевантности каждого элемента контекста
        scored_items = []
        for item in context_items:
            item_text = item.get("text", "").lower()
            
            # Подсчет совпадающих слов
            matching_words = sum(1 for word in query_words if word in item_text)
            score = matching_words / max(1, len(query_words))
            
            scored_items.append({
                "item": item,
                "score": score
            })
        
        # Сортировка по релевантности и выбор топ-N
        scored_items.sort(key=lambda x: x["score"], reverse=True)
        top_items = [item["item"] for item in scored_items[:max_items]]
        
        return top_items