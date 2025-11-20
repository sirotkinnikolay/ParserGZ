Создание миграций при изменении/добавлении моделей
1. Запустить контейнер  `docker compose up -d`
2. Сделать миграции  `docker compose exec app alembic revision --autogenerate -m "add user table"`
3. Скопировать миграции из контейнера в проект  `docker cp fastapi_app:/app/alembic/versions/ ./alembic/versions/`
4. Остановить контейнеры `docker compose stop`
5. Удалить все контейнеры  `docker compose down`
6. Сборка контейнера  `docker compose build --no-cache`
7. Запуск контейнера  `docker compose up -d`
8. Просмотр логов приложения  `docker compose logs -f --timestamps parser_service` 
   (`db`, `api_gateway`, `new_service`, `zookeeper`, `kafka`, `selenium`)
9. Если возникли проблемы с остановкой и удалением контейнера: `sudo aa-remove-unknown` 



# Зайти в контейнер Kafka
docker exec -it kafka bash

# Создать топики
kafka-topics --bootstrap-server localhost:9092 --create --topic user-events --partitions 3 --replication-factor 1
kafka-topics --bootstrap-server localhost:9092 --create --topic order-events --partitions 3 --replication-factor 1
kafka-topics --bootstrap-server localhost:9092 --create --topic notification-events --partitions 3 --replication-factor 1
kafka-topics --bootstrap-server localhost:9092 --create --topic dead-letter-queue --partitions 1 --replication-factor 1

# Посмотреть все топики
kafka-topics --bootstrap-server localhost:9092 --list

# Описать топик
kafka-topics --bootstrap-server localhost:9092 --describe --topic user-events

# Подключиться к контейнеру и запустить psql
docker compose exec db psql -U fastapi_user -d fastapidb