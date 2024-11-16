# Указываем базовый образ Python 3.10
FROM python:3.10.6-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл зависимостей requirements.txt в контейнер
COPY requirements.txt .

# Устанавливаем зависимости из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта в рабочую директорию контейнера
COPY . .

# Создаём точку для монтирования внешней директории
VOLUME ["/app/data"]

# Указываем команду для запуска бота
CMD ["python", "main.py"]