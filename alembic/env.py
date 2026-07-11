import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# ── Load .env file explicitly ─────────────────────────────────────
# This ensures DATABASE_URL is available whether running via
# 'alembic upgrade head' or 'python -m alembic upgrade head' on Windows
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed — rely on environment variables

# Load app models so Alembic can detect them
from app.db.base import Base
from app.models import user, otp, audit_log, property, bill, payment, complaint, notice, setting  # noqa: F401

config = context.config

# Override sqlalchemy.url from environment
db_url = os.environ.get("DATABASE_URL", "")
if not db_url:
    raise ValueError(
        "DATABASE_URL is not set!\n"
        "Make sure your .env file exists and contains:\n"
        "  DATABASE_URL=postgresql://postgres:Admin@localhost:5432/as3_db\n"
        "Or set it manually in PowerShell:\n"
        '  $env:DATABASE_URL="postgresql://postgres:Admin@localhost:5432/as3_db"'
    )

config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
