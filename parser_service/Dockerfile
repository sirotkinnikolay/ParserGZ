FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /usr/src/app

# системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc curl netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Копируем код и миграции
COPY src /usr/src/app
COPY alembic.ini /usr/src/app/alembic.ini
COPY alembic /usr/src/app/alembic
COPY entrypoint.sh /usr/src/app/entrypoint.sh

RUN chmod +x /usr/src/app/entrypoint.sh

EXPOSE 80

CMD ["/usr/src/app/entrypoint.sh"]
