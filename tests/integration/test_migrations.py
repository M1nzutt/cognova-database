from uuid import uuid4

import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from cognova_database.runner import main, migration_config

pytestmark = pytest.mark.integration


def upgrade(connection, revision="head"):
    config = migration_config()
    config.attributes["connection"] = connection
    command.upgrade(config, revision)


def insert_user(connection, email="student@example.com", semester=2):
    return connection.scalar(
        text(
            "INSERT INTO users "
            "(name,email,password_hash,degree_program,semester,academic_goal) "
            "VALUES ('Test',:email,'test-hash','Engineering',:semester,'Unchanged') "
            "RETURNING id"
        ),
        {"email": email, "semester": semester},
    )


@pytest.mark.parametrize("outer_transaction", [True, False])
def test_empty_schema_head_and_physical_constraints(pg_engine, outer_transaction):
    engine, schema = pg_engine
    with engine.connect() as connection:
        if outer_transaction:
            connection.begin()
        upgrade(connection)
        if outer_transaction:
            assert connection.in_transaction()
            connection.commit()
        else:
            assert not connection.in_transaction()
        assert connection.scalar(text("SELECT current_schema()")) == schema
        assert connection.scalars(
            text("SELECT version_num FROM alembic_version")
        ).all() == ["0002_auth_sessions"]
        inspector = inspect(connection)
        assert set(inspector.get_table_names(schema=schema)) == {
            "users",
            "auth_sessions",
            "rate_limit_buckets",
            "alembic_version",
        }
        indexes = {
            item["name"]: item
            for table in ("users", "auth_sessions", "rate_limit_buckets")
            for item in inspector.get_indexes(table, schema=schema)
        }
        assert set(indexes) == {
            "uq_users_email_lower",
            "ix_auth_sessions_user_id",
            "ix_auth_sessions_expires_at",
            "ix_rate_limit_buckets_expires_at",
        }
        assert indexes["uq_users_email_lower"]["unique"]
        assert inspector.get_check_constraints("users", schema=schema)[0]["name"] == (
            "ck_users_semester_positive"
        )
        fk = inspector.get_foreign_keys("auth_sessions", schema=schema)[0]
        assert fk["referred_table"] == "users"
        assert fk["options"]["ondelete"] == "CASCADE"
        insert_user(connection)
        with pytest.raises(IntegrityError), connection.begin_nested():
            insert_user(connection, "STUDENT@example.com")
        with pytest.raises(IntegrityError), connection.begin_nested():
            insert_user(connection, "other@example.com", semester=0)
        with pytest.raises(IntegrityError), connection.begin_nested():
            insert_user(connection, email=None)


def test_upgrade_from_0001_and_repeat_preserves_data(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        upgrade(connection, "0001_create_users")
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0001_create_users"
        )
        user_id = insert_user(connection)
        before = dict(connection.execute(text("SELECT * FROM users")).mappings().one())
    with engine.begin() as connection:
        upgrade(connection)
        after = dict(connection.execute(text("SELECT * FROM users")).mappings().one())
        assert all(after[key] == value for key, value in before.items())
        assert after["updated_at"] is not None
        connection.execute(
            text(
                "INSERT INTO auth_sessions "
                "(id,user_id,refresh_token_hash,csrf_token_hash,"
                "expires_at,last_used_at) "
                "VALUES (:id,:user_id,:refresh,:csrf,now()+interval '1 day',now())"
            ),
            {"id": uuid4(), "user_id": user_id, "refresh": "a" * 64, "csrf": "b" * 64},
        )
        connection.execute(
            text(
                "INSERT INTO rate_limit_buckets "
                "VALUES ('test-key',2,now()+interval '1 hour')"
            )
        )
        tables = ("users", "auth_sessions", "rate_limit_buckets")
        snapshot = {
            t: connection.execute(text(f"SELECT * FROM {t}")).all() for t in tables
        }
    with engine.begin() as connection:
        upgrade(connection)
        upgrade(connection)
        for table in tables:
            assert (
                connection.execute(text(f"SELECT * FROM {table}")).all()
                == snapshot[table]
            )
        assert connection.scalars(
            text("SELECT version_num FROM alembic_version")
        ).all() == ["0002_auth_sessions"]
        connection.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})
        assert connection.scalar(text("SELECT count(*) FROM auth_sessions")) == 0


def test_injected_transaction_can_rollback_ddl(pg_engine):
    engine, schema = pg_engine
    with engine.connect() as connection:
        transaction = connection.begin()
        upgrade(connection)
        transaction.rollback()
    with engine.connect() as connection:
        assert inspect(connection).get_table_names(schema=schema) == []


def test_cli_own_connection_respects_search_path(pg_engine, monkeypatch):
    engine, schema = pg_engine
    with engine.connect() as connection:
        public_before = inspect(connection).get_table_names(schema="public")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", engine.url.render_as_string(hide_password=False))
    monkeypatch.delenv("JWT_SECRET", raising=False)
    assert main(["upgrade", "head"]) == 0
    assert main(["upgrade", "head"]) == 0
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT current_schema()")) == schema
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0002_auth_sessions"
        )
        assert inspect(connection).get_table_names(schema="public") == public_before
