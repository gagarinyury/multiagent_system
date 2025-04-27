#!/bin/bash

# Цвета для красивого вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Установка мультиагентной системы...${NC}"

# Проверка наличия Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 не найден. Пожалуйста, установите Python 3.9 или выше.${NC}"
    exit 1
fi

# Проверка версии Python
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
if (( $(echo "$python_version < 3.9" | bc -l) )); then
    echo -e "${RED}Требуется Python 3.9 или выше. У вас установлен Python $python_version${NC}"
    exit 1
fi

echo -e "${GREEN}Python $python_version найден${NC}"

# Создание виртуального окружения
echo -e "${YELLOW}Создание виртуального окружения...${NC}"
python3 -m venv venv
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при создании виртуального окружения${NC}"
    exit 1
fi

# Активация виртуального окружения
echo -e "${YELLOW}Активация виртуального окружения...${NC}"
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при активации виртуального окружения${NC}"
    exit 1
fi

# Обновление pip
echo -e "${YELLOW}Обновление pip...${NC}"
pip install --upgrade pip
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при обновлении pip${NC}"
    exit 1
fi

# Установка зависимостей
echo -e "${YELLOW}Установка зависимостей...${NC}"
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "${RED}Ошибка при установке зависимостей${NC}"
    exit 1
fi

# Создание необходимых директорий
echo -e "${YELLOW}Создание необходимых директорий...${NC}"
mkdir -p data logs

# Создание файла .env, если не существует
if [ ! -f .env ]; then
    echo -e "${YELLOW}Создание файла .env из шаблона...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Файл .env создан. Пожалуйста, отредактируйте его и добавьте свои API ключи.${NC}"
fi

echo -e "${GREEN}Установка завершена успешно!${NC}"
echo -e "${YELLOW}Для запуска приложения используйте:${NC}"
echo -e "source venv/bin/activate  # Активация виртуального окружения"
echo -e "streamlit run app.py       # Запуск приложения"