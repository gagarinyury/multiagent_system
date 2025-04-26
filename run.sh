#!/bin/bash

# Цвета для красивого вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    echo -e "${RED}Виртуальное окружение не найдено. Сначала запустите ./setup.sh${NC}"
    exit 1
fi

# Активация виртуального окружения
echo -e "${YELLOW}Активация виртуального окружения...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при активации виртуального окружения${NC}"
    exit 1
fi

# Проверка установки Streamlit
if ! command -v streamlit &> /dev/null; then
    echo -e "${RED}Streamlit не установлен. Запустите ./setup.sh для установки зависимостей.${NC}"
    exit 1
fi

# Запуск Streamlit приложения
echo -e "${GREEN}Запуск мультиагентной системы...${NC}"
streamlit run app.py "$@"