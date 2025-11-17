Generic single-database configuration.
1. Запустить контейнер  `docker compose up -d`
2. Сделать миграции  `docker compose exec app alembic revision --autogenerate -m "add user table"`
3. Скопировать миграции из контейнера в проект  `docker cp fastapi_app:/app/alembic/versions/ ./alembic/versions/`
4. Остановить все контейнеры  `docker compose down`
5. Сборка контейнера  `docker compose build --no-cache app`
6. Запуск контейнера  `docker compose up --detach`
7. Просмотр логов приложения  `docker compose logs -f --timestamps db` или `app`