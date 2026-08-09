import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool, create_engine
from alembic import context

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

config = context.config

# Get DATABASE_URL from environment
db_url = os.environ.get("DATABASE_URL", "")
if not db_url:
    raise ValueError("DATABASE_URL is not set!")

# Railway gives postgres:// but SQLAlchemy needs postgresql://
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Set URL BEFORE importing app models to avoid config.py reading .env
config.set_main_option("sqlalchemy.url", db_url)
os.environ["DATABASE_URL"] = db_url  # ensure app/db/base.py also gets correct URL

# Load app models AFTER setting URL
from app.db.base import Base
from app.models import user, otp, audit_log, property, bill, payment, complaint, notice, setting  # noqa: F401

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(db_url, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
