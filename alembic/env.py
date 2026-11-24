"""Alembic environment: connects migrations to the app's settings and models.

- The database URL comes from app.config.settings (the .env file), not from alembic.ini,
  so the app and the migrations always use the same database.
- target_metadata is the app's Base.metadata, with every model imported, so
  `alembic revision --autogenerate` can compare models to the real database.
"""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

from alembic import context
from app.config import settings
from app.db import models  # noqa: F401  (import all models so their tables are registered)
from app.db.setup import Base

config = context.config

# The URL from .env wins. '%' must be escaped for configparser (e.g. in passwords).
config.set_main_option("sqlalchemy.url", settings.database_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

_NOW_ALIASES = {"now", "current_timestamp"}


def compare_server_default(context, inspected_column, metadata_column,
                           inspected_default, metadata_default, rendered_metadata_default):
    """MariaDB reports now() as current_timestamp(). Treat them as equal so autogenerate
    doesn't create empty 'modify default' migrations. Return None = use Alembic's normal check."""
    def norm(value):
        return (value or "").lower().replace("'", "").replace("()", "").strip()

    if norm(inspected_default) in _NOW_ALIASES and norm(rendered_metadata_default) in _NOW_ALIASES:
        return False
    return None


def run_migrations_offline() -> None:
    """Generate SQL without a database connection: `alembic upgrade head --sql`."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against the live database."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,          # one short-lived connection; no pooling needed for migrations
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,            # detect column type changes (e.g. String(10) -> String(20))
            compare_server_default=compare_server_default,  # detect default changes (MariaDB-aware)
            transaction_per_migration=True,  # each migration file runs and commits on its own
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
