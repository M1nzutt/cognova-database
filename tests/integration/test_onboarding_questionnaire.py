import json
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from cognova_database.runner import main, migration_config

pytestmark = pytest.mark.integration
HEAD = "0003_onboarding_questionnaire"


def migrate(connection, revision="head", *, down=False):
    config = migration_config()
    config.attributes["connection"] = connection
    (command.downgrade if down else command.upgrade)(config, revision)


def old_user(connection, *, goal="Original goal", name="Student", email="old@test.io"):
    return connection.scalar(
        text(
            "INSERT INTO users "
            "(name,email,password_hash,degree_program,semester,academic_goal) "
            "VALUES (:name,:email,'preserved-hash','Engineering',3,:goal) RETURNING id"
        ),
        {"goal": goal, "name": name, "email": email},
    )


def new_user(connection):
    return connection.scalar(
        text(
            "INSERT INTO users (name,email,password_hash) "
            "VALUES ('New student','new@test.io','new-hash') RETURNING id"
        )
    )


def answers():
    # Storage fixtures are not invented product options or catalogues.
    return {f"q{i}": f"fixture-{i}" for i in range(1, 11)}


def respond(connection, user_id, revision=1, payload=None, version=1):
    connection.execute(
        text(
            "INSERT INTO questionnaire_responses "
            "(user_id,revision,questionnaire_version,answers) "
            "VALUES (:uid,:revision,:version,CAST(:answers AS jsonb))"
        ),
        {
            "uid": user_id,
            "revision": revision,
            "version": version,
            "answers": json.dumps(answers() if payload is None else payload),
        },
    )


@pytest.mark.parametrize(
    "goal", ["Original goal", "", "  keep whitespace  ", "Estudiar 🚀"]
)
def test_upgrade_preserves_legacy_and_repeats(pg_engine, goal):
    engine, schema = pg_engine
    with engine.begin() as connection:
        migrate(connection, "0002_auth_sessions")
        uid = old_user(connection, goal=goal)
        before = connection.execute(text("SELECT * FROM users")).one()
    with engine.begin() as connection:
        migrate(connection)
        assert connection.execute(text("SELECT * FROM users")).one() == before
        legacy = connection.execute(
            text("SELECT * FROM user_academic_goal_legacy")
        ).one()
        assert legacy.user_id == uid and legacy.academic_goal == goal
        assert (
            connection.scalar(text("SELECT count(*) FROM questionnaire_responses")) == 0
        )
        migrate(connection)
        assert (
            connection.execute(text("SELECT * FROM user_academic_goal_legacy")).one()
            == legacy
        )
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        )
        assert connection.scalar(text("SELECT current_schema()")) == schema


def test_long_legacy_values_are_not_truncated(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, "0002_auth_sessions")
        old_user(connection, name="n" * 31, email="e" * 51)
        migrate(connection)
        assert connection.execute(text("SELECT name,email FROM users")).one() == (
            "n" * 31,
            "e" * 51,
        )
        assert connection.execute(
            text(
                "SELECT convalidated FROM pg_constraint "
                "WHERE conrelid='users'::regclass AND conname LIKE '%registration'"
            )
        ).scalars().all() == [False, False]


def test_minimal_user_and_questionnaire_history(pg_engine):
    engine, schema = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        uid = new_user(connection)
        assert connection.execute(
            text("SELECT degree_program,semester,academic_goal FROM users")
        ).one() == (None, None, None)
        initial = answers()
        initial["q6"] = ["fixture-a", "fixture-b"]
        respond(connection, uid, payload=initial)
        updated = dict(initial, q1="Changed goal")
        respond(connection, uid, revision=2, payload=updated, version=2)
        rows = connection.execute(
            text(
                "SELECT revision,questionnaire_version,answers,recorded_at "
                "FROM questionnaire_responses ORDER BY revision"
            )
        ).all()
        assert [(r.revision, r.questionnaire_version, r.answers) for r in rows] == [
            (1, 1, initial),
            (2, 2, updated),
        ]
        assert rows[0].recorded_at <= rows[1].recorded_at
        inspector = inspect(connection)
        assert inspector.get_pk_constraint("questionnaire_responses", schema=schema)[
            "constrained_columns"
        ] == ["user_id", "revision"]
        assert inspector.get_pk_constraint("user_academic_goal_legacy", schema=schema)[
            "constrained_columns"
        ] == ["user_id"]
        assert (
            connection.scalar(
                text(
                    "SELECT count(*) FROM pg_indexes WHERE schemaname=current_schema() "
                    "AND indexname IN ('questionnaire_responses_pkey',"
                    "'user_academic_goal_legacy_pkey')"
                )
            )
            == 2
        )
        assert {i["name"] for i in inspector.get_indexes("users")} == {
            "uq_users_email_lower"
        }


@pytest.mark.parametrize(
    "column,value",
    [
        ("name", "n" * 31),
        ("name", ""),
        ("name", None),
        ("email", "e" * 51),
        ("email", ""),
        ("email", None),
        ("semester", 0),
        ("semester", -1),
        ("password_hash", None),
    ],
)
def test_user_constraints(pg_engine, column, value):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        uid = new_user(connection)
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                text(f"UPDATE users SET {column}=:value WHERE id=:id"),
                {"value": value, "id": uid},
            )
        connection.execute(
            text("UPDATE users SET name=:name,email=:email,semester=1"),
            {"name": "ñ" * 30, "email": "e" * 50},
        )


@pytest.mark.parametrize(
    "payload",
    [
        {},
        [],
        "text",
        {"q1": "only one"},
        dict(answers(), q11="extra"),
        dict(answers(), q1=None),
        dict(answers(), q1=""),
        dict(answers(), q1="   "),
        dict(answers(), q2=[]),
        dict(answers(), q2=[None]),
        dict(answers(), q2=["ok", ""]),
        dict(answers(), q2={"value": "x"}),
        dict(answers(), q2=42),
        dict(answers(), q2=True),
    ],
)
def test_incomplete_or_malformed_questionnaire_rejected(pg_engine, payload):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        uid = new_user(connection)
        with pytest.raises(IntegrityError), connection.begin_nested():
            respond(connection, uid, payload=payload)


@pytest.mark.parametrize("revision,version", [(0, 1), (2, 1), (1, 0), (1, -1)])
def test_revision_and_version_constraints(pg_engine, revision, version):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        uid = new_user(connection)
        with pytest.raises(IntegrityError), connection.begin_nested():
            respond(connection, uid, revision=revision, version=version)


@pytest.mark.parametrize(
    "table", ["user_academic_goal_legacy", "questionnaire_responses"]
)
@pytest.mark.parametrize("operation", ["UPDATE", "DELETE", "TRUNCATE"])
def test_history_is_immutable(pg_engine, table, operation):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, "0002_auth_sessions")
        uid = old_user(connection)
        migrate(connection)
        respond(connection, uid)
        statement = {
            "UPDATE": f"UPDATE {table} SET user_id=user_id",
            "DELETE": f"DELETE FROM {table}",
            "TRUNCATE": f"TRUNCATE {table}",
        }[operation]
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(text(statement))
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(text("DELETE FROM users WHERE id=:id"), {"id": uid})


def test_legacy_archive_cannot_be_forged_and_fk_is_enforced(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        uid = new_user(connection)
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                text(
                    "INSERT INTO user_academic_goal_legacy (user_id,academic_goal) "
                    "VALUES (:id,'fake')"
                ),
                {"id": uid},
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            respond(connection, uid + 1000)


@pytest.mark.parametrize("blocker", ["questionnaire", "nullable", "changed_goal"])
def test_downgrade_refuses_data_loss_atomically(pg_engine, blocker):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, "0002_auth_sessions")
        uid = old_user(connection)
        migrate(connection)
        if blocker == "questionnaire":
            respond(connection, uid)
        elif blocker == "nullable":
            new_user(connection)
        else:
            connection.execute(text("UPDATE users SET academic_goal='Changed'"))
    with pytest.raises(DBAPIError, match="Downgrade blocked"):
        with engine.begin() as connection:
            migrate(connection, "0002_auth_sessions", down=True)
    with engine.connect() as connection:
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        )
        assert (
            connection.scalar(
                text("SELECT academic_goal FROM user_academic_goal_legacy")
            )
            == "Original goal"
        )
        assert connection.scalar(
            text("SELECT count(*) FROM questionnaire_responses")
        ) == (1 if blocker == "questionnaire" else 0)


def test_safe_downgrade_and_reupgrade(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, "0002_auth_sessions")
        old_user(connection)
        before = connection.execute(text("SELECT * FROM users")).one()
        migrate(connection)
        migrate(connection, "0002_auth_sessions", down=True)
        assert connection.execute(text("SELECT * FROM users")).one() == before
        assert "questionnaire_responses" not in inspect(connection).get_table_names()
        assert all(not c["nullable"] for c in inspect(connection).get_columns("users"))
        migrate(connection)
        assert (
            connection.scalar(
                text("SELECT academic_goal FROM user_academic_goal_legacy")
            )
            == "Original goal"
        )


def test_cli_head_preserves_schema_and_is_repeatable(pg_engine, monkeypatch):
    engine, schema = pg_engine
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", engine.url.render_as_string(hide_password=False))
    assert main(["upgrade", "0002_auth_sessions"]) == 0
    assert main(["upgrade", HEAD]) == 0
    assert main(["upgrade", "head"]) == 0
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT current_schema()")) == schema
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        )


def test_concurrent_updates_cannot_replace_initial(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        uid = new_user(connection)
        respond(connection, uid)
    barrier = Barrier(2)

    def append():
        try:
            with engine.begin() as connection:
                connection.execute(text("SET LOCAL statement_timeout='10s'"))
                barrier.wait(timeout=10)
                respond(connection, uid, revision=2)
            return "inserted"
        except IntegrityError:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as executor:
        assert sorted(executor.map(lambda _: append(), range(2))) == [
            "conflict",
            "inserted",
        ]
    with engine.connect() as connection:
        assert connection.scalars(
            text("SELECT revision FROM questionnaire_responses ORDER BY revision")
        ).all() == [1, 2]
