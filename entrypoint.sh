#!/bin/sh
alembic upgrade head

# Наконец запускаем приложение
# Для разработки с авто-reload:
exec uvicorn app.main:app --host 0.0.0.0 --port 80 --reload

# Для продакшена замените строку выше на, например:
# exec gunicorn -k uvicorn.workers.UvicornWorker app.main:app -b 0.0.0.0:80 --workers 3
