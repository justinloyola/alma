from logging.config import fileConfig

# Standard library imports
from typing import Optional

from sqlalchemy import create_engine

# This must be imported first to set up the Python path
import _path_setup  # noqa: F401

# Third-party imports
from alembic import context

# Local application imports
from app.core.config import settings
from app.db.base import Base

# Get the database URL from settings
database_url: Optional[str] = settings.SQLALCHEMY_DATABASE_URI

# Ensure we have a valid database URL
if not database_url:
    raise ValueError(
        "No database URL configured. Set DATABASE_URL environment variable."
    )

# Convert to string if it's a SQLAlchemy URL object
if hasattr(database_url, "render_as_string"):
    SQLALCHEMY_DATABASE_URI = database_url.render_as_string(hide_password=False)
else:
    SQLALCHEMY_DATABASE_URI = str(database_url)

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Get the metadata from the base class
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    context.configure(
        url=SQLALCHEMY_DATABASE_URI,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=True,  # Enable batch mode for SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = create_engine(SQLALCHEMY_DATABASE_URI)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
            render_as_batch=True,  # Enable batch mode for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
