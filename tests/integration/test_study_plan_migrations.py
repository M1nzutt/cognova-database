import pytest
from activity_helpers import activity
from plan_helpers import (
    END,
    HEAD,
    PREVIOUS,
    decision,
    migrate,
    owner_subject,
    plan,
    plan_activity,
    plan_session,
    plan_subject,
    study_session,
)
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
            pytest.raises(DBAPIError, match="study plan data exists"),
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
        connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
        session_before = connection.execute(
            text("SELECT * FROM study_sessions WHERE id=:id"), {"id": session_id}
        ).one()
        activity_before = connection.execute(
            text("SELECT * FROM activities WHERE id=:id"), {"id": activity_id}
        ).one()
        migrate(connection)
        plan_id = plan(connection, user_id)
        with (
            pytest.raises(DBAPIError, match="study plan data exists"),
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


def test_plan_subject_activity_session_links_and_duplicates(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        user_id, subject_id = owner_subject(connection)
        activity_id = activity(connection, user_id, subject_id)
        session_id = study_session(connection, user_id, subject_id, activity_id)
        plan_id = plan(connection, user_id)
        plan_subject(connection, user_id, plan_id, subject_id)
        plan_activity(connection, user_id, plan_id, subject_id, activity_id)
        plan_session(connection, user_id, plan_id, subject_id, session_id)

        for statement, params in (
            (
                "INSERT INTO study_plan_subjects VALUES (:uid,:plan,:subject)",
                {"uid": user_id, "plan": plan_id, "subject": subject_id},
            ),
            (
                "INSERT INTO study_plan_activities VALUES "
                "(:uid,:plan,:subject,:activity)",
                {
                    "uid": user_id,
                    "plan": plan_id,
                    "subject": subject_id,
                    "activity": activity_id,
                },
            ),
            (
                "INSERT INTO study_plan_sessions VALUES (:uid,:plan,:subject,:session)",
                {
                    "uid": user_id,
                    "plan": plan_id,
                    "subject": subject_id,
                    "session": session_id,
                },
            ),
        ):
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(text(statement), params)

        assert {
            table: [column["name"] for column in inspect(connection).get_columns(table)]
            for table in (
                "study_plan_subjects",
                "study_plan_activities",
                "study_plan_sessions",
            )
        } == {
            "study_plan_subjects": ["user_id", "plan_id", "subject_id"],
            "study_plan_activities": [
                "user_id",
                "plan_id",
                "subject_id",
                "activity_id",
            ],
            "study_plan_sessions": [
                "user_id",
                "plan_id",
                "subject_id",
                "study_session_id",
            ],
        }

        for statement, params in (
            ("DELETE FROM study_plans WHERE id=:id", {"id": plan_id}),
            ("DELETE FROM subjects WHERE id=:id", {"id": subject_id}),
            ("DELETE FROM activities WHERE id=:id", {"id": activity_id}),
            ("DELETE FROM study_sessions WHERE id=:id", {"id": session_id}),
        ):
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(text(statement), params)


def test_resource_links_enforce_owner_plan_and_subject_consistency(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        owner_id, owner_subject_id = owner_subject(connection, "owner@test.io")
        other_id, other_subject_id = owner_subject(connection, "other@test.io")
        owner_activity_id = activity(connection, owner_id, owner_subject_id)
        other_activity_id = activity(connection, other_id, other_subject_id)
        owner_session_id = study_session(
            connection, owner_id, owner_subject_id, owner_activity_id
        )
        other_session_id = study_session(
            connection, other_id, other_subject_id, other_activity_id
        )
        owner_plan_id = plan(connection, owner_id)
        other_plan_id = plan(connection, other_id)
        plan_subject(connection, owner_id, owner_plan_id, owner_subject_id)
        plan_subject(connection, other_id, other_plan_id, other_subject_id)

        with pytest.raises(IntegrityError), connection.begin_nested():
            plan_subject(connection, other_id, owner_plan_id, other_subject_id)
        with pytest.raises(IntegrityError), connection.begin_nested():
            plan_subject(connection, owner_id, owner_plan_id, other_subject_id)
        with pytest.raises(IntegrityError), connection.begin_nested():
            plan_activity(
                connection,
                owner_id,
                owner_plan_id,
                owner_subject_id,
                other_activity_id,
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            plan_activity(
                connection,
                owner_id,
                owner_plan_id,
                other_subject_id,
                other_activity_id,
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            plan_session(
                connection,
                owner_id,
                owner_plan_id,
                owner_subject_id,
                other_session_id,
            )

        with pytest.raises(IntegrityError), connection.begin_nested():
            study_session(connection, owner_id, owner_subject_id, other_activity_id)
        plan_activity(
            connection, owner_id, owner_plan_id, owner_subject_id, owner_activity_id
        )
        plan_session(
            connection, owner_id, owner_plan_id, owner_subject_id, owner_session_id
        )


def test_plan_decisions_preserve_ai_user_choices_without_applying_them(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        user_id, _ = owner_subject(connection)
        plan_id = plan(connection, user_id)
        proposal = {"name": "AI plan", "objective": "Review algebra"}
        cases = (
            ("accepted", None, proposal, proposal),
            ("edited", "/objective", proposal, {"objective": "Review geometry"}),
            ("rejected", None, proposal, None),
            ("regenerated", None, proposal, None),
        )
        for action, field_path, proposed, chosen in cases:
            decision(
                connection,
                user_id,
                plan_id,
                action,
                field_path=field_path,
                proposed_value=proposed,
                chosen_value=chosen,
            )

        rows = connection.execute(
            text(
                "SELECT action,field_path,proposed_value,chosen_value,created_at "
                "FROM study_plan_decisions ORDER BY id"
            )
        ).all()
        assert [(row.action, row.field_path) for row in rows] == [
            (action, path) for action, path, _, _ in cases
        ]
        assert [row.proposed_value for row in rows] == [item[2] for item in cases]
        assert [row.chosen_value for row in rows] == [item[3] for item in cases]
        assert all(row.created_at is not None for row in rows)
        assert connection.execute(
            text("SELECT status,name,objective FROM study_plans WHERE id=:id"),
            {"id": plan_id},
        ).one() == ("draft", "Exam preparation", "Prepare for the final exam")


@pytest.mark.parametrize(
    "overrides",
    [
        {"action": "ignored"},
        {"action": "accepted", "proposed_value": None},
        {"action": "accepted", "chosen_value": None},
        {"action": "edited", "field_path": None},
        {"action": "edited", "field_path": " ", "chosen_value": {"x": 1}},
        {
            "action": "edited",
            "field_path": "/objective",
            "proposed_value": {"x": 1},
            "chosen_value": {"x": 1},
        },
        {"action": "edited", "field_path": "/" + "x" * 200},
        {"action": "rejected", "proposed_value": None},
        {"action": "rejected", "chosen_value": {"status": "draft"}},
        {"action": "regenerated", "chosen_value": {"status": "draft"}},
        {"action": "accepted", "proposed_value": {"value": "x" * 66000}},
    ],
)
def test_invalid_plan_decisions_are_rejected(pg_engine, overrides):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        user_id, _ = owner_subject(connection)
        plan_id = plan(connection, user_id)
        action = overrides["action"]
        values = {key: value for key, value in overrides.items() if key != "action"}
        with pytest.raises(IntegrityError), connection.begin_nested():
            decision(connection, user_id, plan_id, action, **values)


def test_plan_decisions_require_plan_ownership_and_restrict_deletion(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        owner_id, _ = owner_subject(connection, "owner@test.io")
        other_id, _ = owner_subject(connection, "other@test.io")
        plan_id = plan(connection, owner_id)
        with pytest.raises(IntegrityError), connection.begin_nested():
            decision(connection, other_id, plan_id, "rejected")
        decision(connection, owner_id, plan_id, "rejected")
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(
                text("DELETE FROM study_plans WHERE id=:id"), {"id": plan_id}
            )
