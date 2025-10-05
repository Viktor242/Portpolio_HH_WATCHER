# Используем официальный Python 3.13 образ
FROM python:3.13-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости для matplotlib и других библиотек
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libfreetype6-dev \
    libpng-dev \
    libjpeg-dev \
    libhdf5-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Копируем файл зависимостей
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Создаем директории для данных и отчётов
RUN mkdir -p data report_oct5 report_dynamics report_automated

# Устанавливаем права на выполнение Python скриптов
RUN chmod +x *.py

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порт (если понадобится для веб-интерфейса)
EXPOSE 8000

# Команда по умолчанию
CMD ["python", "sales_parser.py"]

