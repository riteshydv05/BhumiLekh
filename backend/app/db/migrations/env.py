"""Alembic environment configuration for Land Record AI System.

Reads DATABASE_URL from app.core.config settings so we stay
consistent with the FastAPI / SQLAlchemy setup.
"""
from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---------------------------------------------------------------------------
# Alembic Config object — gives access to alembic.ini values
# ---------------------------------------------------------------------------
config = context.config

# Set up Python logging from the config file
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------------------------
# Import all models so Alembic can see them in MetaData
# ---------------------------------------------------------------------------
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from app.db.session import Base  # noqa: E402 — must be after sys.path
import app.models.document         # noqa: F401 — register Document
import app.models.document_result  # noqa: F401 — register DocumentResult
import app.models.document_page    # noqa: F401 — register DocumentPage (new)

target_metadata = Base.metadata

# ---------------------------------------------------------------------------
# Override sqlalchemy.url from app settings so we use the same creds
# ---------------------------------------------------------------------------
try:
    from app.core.config import settings
    config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
except Exception:
    pass  # Fall back to alembic.ini value


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL, no DB connection)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode (connect to DB and apply)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
