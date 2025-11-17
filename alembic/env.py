import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from dotenv import load_dotenv

load_dotenv()
# -----------------------------------------------------------------------------
# Настройка Python path (добавляем корень проекта)
# -----------------------------------------------------------------------------

sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..")
    )
)

# Теперь можно импортировать модули приложения
from app.db import Base
from app import models   # важно: импорт моделей, чтобы Alembic увидел таблицы

# -----------------------------------------------------------------------------
# Конфигурация Alembic
# -----------------------------------------------------------------------------

config = context.config

# Подключаем файл логирования
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные для автогенерации миграций
target_metadata = Base.metadata

# -----------------------------------------------------------------------------
# Установка DATABASE_URL
# -----------------------------------------------------------------------------

# Если в .ini ничего не указано — считаем из переменной окружения
DATABASE_URL = os.getenv("DATABASE_URL")
print(f"DATABASE_URL: {DATABASE_URL}")
if DATABASE_URL:
    config.set_main_option("sqlalchemy.url", DATABASE_URL)


# -----------------------------------------------------------------------------
# Offline режим
# -----------------------------------------------------------------------------

def run_migrations_offline():
    """Запуск миграций в режиме offline — без подключения к БД."""
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,         # сравнивать типы колонок
        compare_server_default=True  # сравнивать server_default
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------------------------------------------------------
# Online режим
# -----------------------------------------------------------------------------

def run_migrations_online():
    """Запуск миграций в режиме online — с подключением к БД."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------------------------------------------------------
# Выбор режима
# -----------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
