"""Independent Alembic environment; the historical revisions are authoritative."""

from alembic import context
from sqlalchemy import create_engine, pool, text

from cognova_database.configuration import database_url

config = context.config
target_metadata = None


def run_migrations_offline() -> None:
    # SQL generation needs a dialect, not credentials or an application import.
    context.configure(
        dialect_name="postgresql",
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def migrate(connection) -> None:
    if connection.dialect.name != "postgresql":
        raise ValueError("Only PostgreSQL is supported")
    # The caller owns injected connections and any surrounding transaction.
    # Do not change search_path: both DDL and alembic_version use that scope.
    connection.execute(text("SET LOCAL lock_timeout = '30s'"))
    connection.execute(text("SET LOCAL statement_timeout = '120s'"))
    connection.execute(text("SELECT pg_advisory_xact_lock(1943187001)"))
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is not None:
        if connection.in_transaction():
            migrate(connection)
        else:
            with connection.begin():
                migrate(connection)
        return
    engine = create_engine(
        database_url(),
        poolclass=pool.NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 10},
    )
    try:
        with engine.begin() as connection:
            migrate(connection)
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
