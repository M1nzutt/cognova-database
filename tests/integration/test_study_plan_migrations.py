import pytest
from activity_helpers import activity
from plan_helpers import END, HEAD, PREVIOUS, migrate, owner_subject, plan
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

pytestmark = pytest.mark.integration


def test_upgrade_from_0006_creates_plans_and_preserves_existing_rows(pg_engine):
    engine, schema = pg_engine
    with engine.begin() as connection:
        migrate(connection, PREVIOUS)
        user_id, subject_id = owner_subject(connection)
        activity(connection, user_id, subject_id)
        before = {
            table: connection.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all()
            for table in inspect(connection).get_table_names()
            if table != "alembic_version"
        }

        migrate(connection)
        migrate(connection)

        assert connection.scalar(text("SELECT current_schema()")) == schema
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            HEAD
        )
        for table, rows in before.items():
            assert (
                connection.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all()
                == rows
            )
        assert connection.scalar(text("SELECT count(*) FROM study_plans")) == 0
        plan_id = plan(connection, user_id)
        created_at, updated_at = connection.execute(
            text("SELECT created_at,updated_at FROM study_plans WHERE id=:id"),
            {"id": plan_id},
        ).one()
        assert created_at is not None
        assert updated_at >= created_at


@pytest.mark.parametrize(
    "bad",
    [
        {"name": ""},
        {"name": " "},
        {"name": "\t"},
        {"name": " padded"},
        {"name": "padded "},
        {"name": "x" * 101},
        {"name": None},
        {"objective": ""},
        {"objective": " "},
        {"objective": "x" * 2001},
        {"objective": None},
        {"start_at": "infinity"},
        {"end_at": "infinity"},
        {"start_at": END, "end_at": END},
        {"start_at": END, "end_at": "2030-01-01T00:00:00Z"},
        {"status": "invalid"},
        {"status": None},
        {"source": "gemini"},
        {"source": None},
    ],
)
def test_invalid_plan_values_are_rejected(pg_engine, bad):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        user_id, _ = owner_subject(connection)
        with pytest.raises(IntegrityError), connection.begin_nested():
            plan(connection, user_id, **bad)


@pytest.mark.parametrize("status", ["draft", "active", "completed", "abandoned"])
@pytest.mark.parametrize("source", ["ai", "manual"])
def test_plan_state_and_source_tokens(pg_engine, status, source):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        user_id, _ = owner_subject(connection)
        assert plan(connection, user_id, status=status, source=source) > 0


def test_plan_user_fk_and_restrict_delete(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        user_id, _ = owner_subject(connection)
        plan(connection, user_id)
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})


def test_0001_to_0007_and_0007_to_0006_to_0007(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, "0001_create_users")
        connection.execute(
            text(
                "INSERT INTO users (name,email,password_hash,degree_program,"
                "semester,academic_goal) VALUES ('Legacy','legacy@test.io','fixture',"
                "'Engineering',2,'Keep this goal')"
            )
        )
        migrate(connection)
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        )
        assert (
            connection.scalar(
                text("SELECT academic_goal FROM users WHERE email='legacy@test.io'")
            )
            == "Keep this goal"
        )
        user_id = connection.scalar(text("SELECT id FROM users"))
        plan_id = plan(connection, user_id)
        with (
            pytest.raises(DBAPIError, match="study plans exist"),
            connection.begin_nested(),
        ):
            migrate(connection, PREVIOUS, down=True)
        connection.execute(
            text("DELETE FROM study_plans WHERE id=:id"), {"id": plan_id}
        )
        migrate(connection, PREVIOUS, down=True)
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            PREVIOUS
        )
        assert "study_plans" not in inspect(connection).get_table_names()
        migrate(connection)
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        )
        assert (
            connection.scalar(
                text("SELECT academic_goal FROM users WHERE email='legacy@test.io'")
            )
            == "Keep this goal"
        )


def test_0007_downgrade_preserves_0006_and_blocks_future_dependencies(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, PREVIOUS)
        user_id, subject_id = owner_subject(connection)
        activity_id = activity(connection, user_id, subject_id)
        session_id = connection.scalar(
            text(
                "INSERT INTO study_sessions (user_id,subject_id,activity_id,"
                "planned_start_at,planned_duration) VALUES (:uid,:sid,:aid,"
                "'2030-01-01T12:00:00Z',30) RETURNING id"
            ),
            {"uid": user_id, "sid": subject_id, "aid": activity_id},
        )
        session_before = connection.execute(
            text("SELECT * FROM study_sessions WHERE id=:id"), {"id": session_id}
        ).one()
        activity_before = connection.execute(
            text("SELECT * FROM activities WHERE id=:id"), {"id": activity_id}
        ).one()
        migrate(connection)
        plan_id = plan(connection, user_id)
        with (
            pytest.raises(DBAPIError, match="study plans exist"),
            connection.begin_nested(),
        ):
            migrate(connection, PREVIOUS, down=True)
        connection.execute(
            text("DELETE FROM study_plans WHERE id=:id"), {"id": plan_id}
        )
        connection.execute(
            text("CREATE VIEW future_plan_dependency AS SELECT * FROM study_plans")
        )
        with pytest.raises(DBAPIError), connection.begin_nested():
            migrate(connection, PREVIOUS, down=True)
        assert (
            connection.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        )
        connection.execute(text("DROP VIEW future_plan_dependency"))
        migrate(connection, PREVIOUS, down=True)
        assert (
            connection.execute(
                text("SELECT * FROM study_sessions WHERE id=:id"), {"id": session_id}
            ).one()
            == session_before
        )
        assert (
            connection.execute(
                text("SELECT * FROM activities WHERE id=:id"), {"id": activity_id}
            ).one()
            == activity_before
        )
