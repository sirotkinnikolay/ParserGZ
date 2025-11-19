Generic single-database configuration.
Создание миграций при изменении/добавлении моделей
1. Запустить контейнер  `docker compose up -d`
2. Сделать миграции  `docker compose exec app alembic revision --autogenerate -m "add user table"`
3. Скопировать миграции из контейнера в проект  `docker cp fastapi_app:/app/alembic/versions/ ./alembic/versions/`
4. Остановить все контейнеры  `docker compose down`
5. Сборка контейнера  `docker compose build --no-cache`
6. Запуск контейнера  `docker compose up -d`
7. Просмотр логов приложения  `docker compose logs -f --timestamps app` (`db`, `selenium`)
8. Если возникли проблемы с остановкой и удалением контейнера: `sudo aa-remove-unknown` 