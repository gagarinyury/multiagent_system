"""
Агент ревьюер - проверяет написанный код на ошибки и улучшения
"""

from .base_agent import BaseAgent
import logging # Импортируем модуль логирования
import re # Импортируем регулярные выражения

logger = logging.getLogger("multiagent_system") # Получаем логгер


class ReviewerAgent(BaseAgent):
    """
    Агент для ревью и улучшения программного кода
    """
    def __init__(self, provider=None):
        """
        Инициализация агента ревьюера

        Args:
            provider: Провайдер LLM API
        """
        super().__init__("Reviewer", provider)

    def process(self, input_text, context=None):
        """
        Ревью кода, поиск ошибок и предложение улучшений

        Args:
            input_text: Код от CoderAgent (или предыдущего агента)
            context: Дополнительный контекст (архитектура, план, требования)

        Returns:
            str: Результаты ревью кода или сообщение об ошибке
        """
        logger.info("ReviewerAgent: Начат процесс ревью кода.")
        if not self.provider or not self.provider.is_configured():
            error_message = "Ошибка: Провайдер LLM не настроен для агента Reviewer"
            logger.error(error_message)
            return error_message

        if not input_text or input_text.strip() == "":
             warning_message = "ReviewerAgent: Входные данные для ревью пусты."
             logger.warning(warning_message)
             return warning_message # Возвращаем предупреждение, если нет кода для ревью

        prompt = self.create_prompt(input_text, context)
        # Используем базовый метод complete, который включает повторные попытки
        response = self.provider.complete(prompt)

        if isinstance(response, str) and response.startswith("[Error]"):
             logger.error(f"ReviewerAgent: Ошибка при получении ответа от LLM: {response}")
             return response # Возвращаем ошибку дальше по цепочке

        logger.info("ReviewerAgent: Ревью кода завершено.")
        return response # Возвращаем результаты ревью

    def create_prompt(self, input_text, context=None):
        """
        Создание промпта для ревьюера.
        Промпт усилен инструкциями для более детального и структурированного ревью.

        Args:
            input_text: Код для ревью
            context: Дополнительный контекст (архитектура, план, требования)

        Returns:
            str: Сформированный промпт
        """
        context_str = str(context) if context else "Дополнительный контекст отсутствует."

        # Улучшенный промпт для ревьюера с более четкими инструкциями
        return f"""
        Ты опытный ревьюер программного кода с глубокими знаниями в области безопасности,
        производительности, читаемости и лучших практик разработки. Твоя задача - провести
        тщательное ревью предоставленного кода, выявить все проблемы и предложить
        конкретные, actionable улучшения.

        # Код для ревью:
        {input_text}

        # Дополнительный Контекст (Архитектура, План, Требования):
        {context_str}

        # Ключевые Инструкции для Ревью:
        1.  **Проведи комплексный анализ кода:**
            -   Синтаксические и логические ошибки.
            -   Проблемы безопасности (потенциальные уязвимости, небезопасные практики).
            -   Проблемы производительности (неэффективные алгоритмы, избыточные операции).
            -   Читаемость и поддерживаемость (сложность кода, соответствие соглашениям).
            -   Корректность реализации согласно предоставленной архитектуре и контексту.
            -   Наличие и качество обработки ошибок и валидации входных данных в коде.
            -   Наличие и качество логирования.
            -   Полнота реализации (отсутствуют ли части, которые должны были быть написаны).
        2.  **Для каждой выявленной проблемы:**
            -   Четко опиши проблему и ее потенциальные последствия.
            -   Укажи **файл и номер строки (или диапазон строк)**, где находится проблема (если применимо).
            -   Оцени **критичность** проблемы по шкале: `Критичная`, `Серьезная`, `Средняя`, `Незначительная`.
            -   Предложи **конкретное решение или улучшение**. Если возможно, предоставь пример исправленного кода.
        3.  **Оцени общее качество кода** по шкале от 1 до 10 и предоставь краткое резюме.
        4.  **Предложи общие рекомендации** по улучшению стиля кодирования или архитектуры, если это необходимо.

        # Формат вывода:
        Твой ответ должен быть хорошо структурированным и легким для чтения. Используй Markdown.
        -   Начни с **Краткого резюме качества кода** (оценка и общее впечатление).
        -   Затем предоставь **Список найденных проблем**. Для каждой проблемы используй четкий формат:
            ```markdown
            ### [Критичность] Краткое описание проблемы
            **Файл:** [имя файла] (Строка: [номер строки/диапазон])
            **Описание:** Полное описание проблемы.
            **Предлагаемое исправление:** Конкретные шаги или примеры кода для решения проблемы.
            ```
            Используй блоки кода Markdown (```[язык]\nкод\n```) для примеров исправленного кода.
        -   Заверши **Общими рекомендациями по улучшению**.
        """

    def categorize_issues(self, review_text):
        """
        Категоризация проблем, найденных в коде.
        Может потребовать доработки, если формат вывода LLM изменится.
        """
        # Текущая реализация использует ключевые слова,
        # возможно, потребуется адаптация под новый формат вывода LLM.
        # Например, искать заголовки по критичности (Критичная, Серьезная и т.д.)
        # и парсить информацию под ними.
        logger.info("ReviewerAgent: Начата категоризация проблем.")
        categories = {
            "Критичная": [],
            "Серьезная": [],
            "Средняя": [],
            "Незначительная": [],
            "Общие рекомендации": []
        }

        current_category = None
        lines = review_text.strip().split('\n')
        issue_text = []

        # Простая машина состояний для парсинга структурированного вывода
        parsing_issue = False
        current_issue = {}

        for line in lines:
             line_strip = line.strip()

             # Ищем заголовки критичности
             severity_match = re.match(r'^### \[(Критичная|Серьезная|Средняя|Незначительная)\](.*)$', line_strip)
             if severity_match:
                 if parsing_issue and current_issue:
                     # Сохраняем предыдущую проблему перед началом новой
                     category = current_issue.get("Критичность", "Незначительная")
                     if category in categories:
                         categories[category].append(current_issue)
                     else:
                         categories["Незначительная"].append(current_issue) # Fallback
                     current_issue = {} # Сбрасываем для новой проблемы

                 parsing_issue = True
                 current_issue["Критичность"] = severity_match.group(1)
                 current_issue["Заголовок"] = severity_match.group(2).strip()
                 current_issue["Описание"] = []
                 logger.debug(f"ReviewerAgent: Найден заголовок критичности: {current_issue['Критичность']}")
                 continue # Переходим к следующей строке

             # Ищем другие поля проблемы, если находимся внутри блока проблемы
             if parsing_issue:
                 if line_strip.lower().startswith('**файл:**'):
                     current_issue['Файл'] = line_strip.split(':', 1)[1].strip()
                     logger.debug(f"ReviewerAgent: Найден Файл: {current_issue['Файл']}")
                 elif line_strip.lower().startswith('**описание:**'):
                     current_issue['Описание'].append(line_strip.split(':', 1)[1].strip()) # Добавляем остаток строки
                     # Далее все строки до следующего поля или заголовка считаем частью описания
                     parsing_description = True
                 elif line_strip.lower().startswith('**предлагаемое исправление:**'):
                      # Сбрасываем флаг описания перед обработкой исправления
                     parsing_description = False
                     current_issue['Предлагаемое исправление'] = []
                     current_issue['Предлагаемое исправление'].append(line_strip.split(':', 1)[1].strip()) # Добавляем остаток строки
                      # Далее все строки до следующего заголовка/поля считаем частью исправления
                     parsing_fix = True
                 elif line_strip.startswith('```'):
                     # Начало или конец блока кода внутри описания или исправления
                     if 'Код' not in current_issue:
                         current_issue['Код'] = []
                     current_issue['Код'].append(line) # Добавляем всю строку с ```
                 elif parsing_description:
                      current_issue['Описание'].append(line_strip)
                 elif parsing_fix:
                      current_issue['Предлагаемое исправление'].append(line_strip)
                 else:
                      # Строка, которая не является известным полем, но находится внутри блока проблемы
                      # Можно добавить ее к последнему активному полю (Описание или Исправление)
                      if 'Предлагаемое исправление' in current_issue:
                           current_issue['Предлагаемое исправление'].append(line_strip)
                      elif 'Описание' in current_issue:
                           current_issue['Описание'].append(line_strip)


        # Сохраняем последнюю проблему, если она была найдена
        if parsing_issue and current_issue:
            category = current_issue.get("Критичность", "Незначительная")
            if category in categories:
                categories[category].append(current_issue)
            else:
                categories["Незначительная"].append(current_issue) # Fallback

        # Собираем общие рекомендации после всех проблем
        collecting_general_recs = False
        for line in lines:
            line_strip = line.strip()
            if line_strip == "Общие рекомендации по улучшению": # Ищем заголовок
                 collecting_general_recs = True
                 continue
            if collecting_general_recs and line_strip and not line_strip.startswith('#'):
                 categories["Общие рекомендации"].append(line_strip)


        logger.info(f"ReviewerAgent: Категоризация завершена. Найдено проблем: Критичных={len(categories['Критичная'])}, Серьезных={len(categories['Серьезная'])}, Средних={len(categories['Средняя'])}, Незначительных={len(categories['Незначительная'])}")
        return categories


    def calculate_quality_score(self, review_text):
        """
        Расчет приблизительной оценки качества кода на основе ревью.
        Адаптировано под новый формат вывода критичности.
        """
        logger.info("ReviewerAgent: Расчет оценки качества кода.")
        issues_severity = {
            "Критичная": 0,
            "Серьезная": 0,
            "Средняя": 0,
            "Незначительная": 0
        }

        # Ищем заголовки с критичностью
        lines = review_text.strip().split('\n')
        for line in lines:
            severity_match = re.match(r'^### \[(Критичная|Серьезная|Средняя|Незначительная)\].*$', line.strip())
            if severity_match:
                severity = severity_match.group(1)
                issues_severity[severity] += 1

        # Расчет оценки на основе найденных проблем
        # Учитываем количество проблем каждой критичности
        score = 10.0
        score -= issues_severity["Критичная"] * 2.5 # Критичные ошибки сильно снижают балл
        score -= issues_severity["Серьезная"] * 1.5
        score -= issues_severity["Средняя"] * 0.7
        score -= issues_severity["Незначительная"] * 0.2

        # Добавляем небольшой бонус, если нет критичных и серьезных ошибок
        if issues_severity["Критичная"] == 0 and issues_severity["Серьезная"] == 0:
            score += 1.0 # Небольшой бонус за относительную чистоту кода

        # Нормализация оценки в пределах от 0 до 10
        final_score = max(0.0, min(10.0, score))
        logger.info(f"ReviewerAgent: Оценка качества кода: {final_score:.2f}/10")
        return final_score