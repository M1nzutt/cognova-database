import pytest
from activity_helpers import activity
from plan_helpers import (
    END,
    HEAD,
    PREVIOUS,
    START,
    challenge,
    decision,
    migrate,
    owner_subject,
    plan,
    plan_activity,
    plan_session,
    plan_subject,
    study_session,
    subject,
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


def test_0007_indexes_cover_owners_dates_status_and_resource_joins(pg_engine):
    expected = {
        "study_plans": {
            "ix_study_plans_user_status_start": ["user_id", "status", "start_at", "id"],
            "ix_study_plans_user_end": ["user_id", "end_at", "id"],
        },
        "study_plan_subjects": {
            "ix_study_plan_subjects_user_subject_plan": [
                "user_id",
                "subject_id",
                "plan_id",
            ]
        },
        "study_plan_activities": {
            "ix_study_plan_activities_user_subject_activity": [
                "user_id",
                "subject_id",
                "activity_id",
            ]
        },
        "study_plan_sessions": {
            "ix_study_plan_sessions_user_subject_session": [
                "user_id",
                "subject_id",
                "study_session_id",
            ]
        },
        "study_plan_decisions": {
            "ix_study_plan_decisions_user_plan_created": [
                "user_id",
                "plan_id",
                "created_at",
                "id",
            ]
        },
        "study_challenges": {
            "ix_study_challenges_user_status_deadline": [
                "user_id",
                "status",
                "deadline",
                "id",
            ],
            "ix_study_challenges_user_plan_status_deadline": [
                "user_id",
                "plan_id",
                "status",
                "deadline",
                "id",
            ],
            "ix_study_challenges_plan_subject_activity": [
                "user_id",
                "plan_id",
                "subject_id",
                "activity_id",
            ],
            "ix_study_challenges_plan_subject_session": [
                "user_id",
                "plan_id",
                "subject_id",
                "study_session_id",
            ],
            "ix_study_challenges_user_subject_activity_session": [
                "user_id",
                "subject_id",
                "activity_id",
                "study_session_id",
            ],
        },
    }
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        for table, definitions in expected.items():
            actual = {
                index["name"]: index["column_names"]
                for index in inspect(connection).get_indexes(table)
            }
            assert {name: actual[name] for name in definitions} == definitions
        assert (
            connection.scalar(
                text(
                    "SELECT count(*) FROM pg_index i JOIN pg_class t "
                    "ON t.oid=i.indrelid "
                    "WHERE t.relnamespace=current_schema()::regnamespace "
                    "AND t.relname IN ('study_plans','study_plan_subjects',"
                    "'study_plan_activities','study_plan_sessions',"
                    "'study_plan_decisions','study_challenges') "
                    "AND (NOT i.indisvalid OR NOT i.indisready)"
                )
            )
            == 0
        )


def test_0007_revokes_public_on_new_tables_and_sequences(pg_engine):
    engine, _ = pg_engine
    tables = (
        "study_plans",
        "study_plan_subjects",
        "study_plan_activities",
        "study_plan_sessions",
        "study_plan_decisions",
        "study_challenges",
    )
    sequences = (
        "study_plans_id_seq",
        "study_plan_decisions_id_seq",
        "study_challenges_id_seq",
    )
    with engine.begin() as connection:
        migrate(connection)
        for relation in (*tables, *sequences):
            assert (
                connection.scalar(
                    text(
                        "SELECT count(*) FROM pg_class c "
                        "JOIN pg_namespace n ON n.oid=c.relnamespace "
                        "CROSS JOIN LATERAL aclexplode(c.relacl) acl "
                        "WHERE n.nspname=current_schema() AND c.relname=:name "
                        "AND acl.grantee=0"
                    ),
                    {"name": relation},
                )
                == 0
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


@pytest.mark.parametrize(
    ("status", "source"),
    [
        (status, source)
        for status in ("pending", "in_progress", "completed", "failed", "cancelled")
        for source in ("ai", "manual")
    ],
)
def test_challenge_status_source_tokens_and_optional_dates(pg_engine, status, source):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        user_id, subject_id = owner_subject(connection)
        plan_id = plan(connection, user_id)
        plan_subject(connection, user_id, plan_id, subject_id)
        challenge_id = challenge(
            connection, user_id, plan_id, status=status, source=source
        )
        assert challenge_id > 0
        assert connection.scalar(
            text(
                "SELECT start_at IS NULL AND deadline IS NULL "
                "FROM study_challenges WHERE id=:id"
            ),
            {"id": challenge_id},
        )


def test_challenge_target_types_and_target_boundaries(pg_engine):
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
        challenge(
            connection,
            user_id,
            plan_id,
            subject_id=subject_id,
            target_type="study_minutes",
            target_value={"minutes": 1},
        )
        challenge(
            connection,
            user_id,
            plan_id,
            subject_id=subject_id,
            target_type="study_minutes",
            target_value={"minutes": 1440},
        )
        challenge(
            connection,
            user_id,
            plan_id,
            subject_id=subject_id,
            activity_id=activity_id,
            target_type="activity_completion",
            target_value={"status": "completed"},
        )
        challenge(
            connection,
            user_id,
            plan_id,
            subject_id=subject_id,
            study_session_id=session_id,
            target_type="session_completion",
            target_value={"lifecycle": "finished"},
        )
        challenge(
            connection,
            user_id,
            plan_id,
            subject_id=subject_id,
            target_type="subject_mastery",
            target_value={"criterion": "Quadratic equations", "threshold": 75},
        )
        linked = challenge(
            connection,
            user_id,
            plan_id,
            subject_id=subject_id,
            activity_id=activity_id,
            study_session_id=session_id,
            target_type="custom",
        )
        challenge(
            connection,
            user_id,
            plan_id,
            start_at=END,
            deadline=END,
            target_type="custom",
        )
        challenge(
            connection,
            user_id,
            plan_id,
            deadline=END,
            generation_criteria={"strategy": "adapted", "reason": "missed topic"},
        )
        assert connection.scalar(
            text("SELECT target_value FROM study_challenges WHERE id=:id"),
            {"id": linked},
        ) == {"mode": "adaptive"}
        assert connection.scalar(text("SELECT count(*) FROM study_challenges")) == 8


@pytest.mark.parametrize(
    "overrides",
    [
        {"title": ""},
        {"title": "\t"},
        {"title": " padded"},
        {"title": "x" * 101},
        {"title": None},
        {"description": ""},
        {"description": " "},
        {"description": "x" * 2001},
        {"description": None},
        {"target_type": "generic"},
        {"target_type": "study_minutes", "subject_id": 1, "target_value": {}},
        {
            "target_type": "study_minutes",
            "subject_id": 1,
            "target_value": {"minutes": 0},
        },
        {
            "target_type": "study_minutes",
            "subject_id": 1,
            "target_value": {"minutes": 1441},
        },
        {
            "target_type": "study_minutes",
            "subject_id": 1,
            "target_value": {"minutes": "30"},
        },
        {
            "target_type": "study_minutes",
            "subject_id": 1,
            "target_value": {"minutes": 30, "unit": "minutes"},
        },
        {
            "target_type": "study_minutes",
            "subject_id": 1,
            "target_value": {"minutes": 30.5},
        },
        {"target_type": "activity_completion", "target_value": {"status": "done"}},
        {
            "target_type": "activity_completion",
            "subject_id": 1,
            "activity_id": 1,
            "target_value": {"status": "done"},
        },
        {"target_type": "session_completion", "target_value": {"lifecycle": "paused"}},
        {
            "target_type": "subject_mastery",
            "subject_id": 1,
            "target_value": {"criterion": "", "threshold": 80},
        },
        {
            "target_type": "subject_mastery",
            "subject_id": 1,
            "target_value": {"criterion": "Topic", "threshold": 101},
        },
        {
            "target_type": "subject_mastery",
            "subject_id": 1,
            "target_value": {"criterion": "Topic", "threshold": 70.5},
        },
        {"target_type": "custom", "target_value": {}},
        {"target_value": None},
        {"target_value": "not an object"},
        {"target_value": {"payload": "x" * 5000}},
        {"activity_id": 1},
        {"study_session_id": 1},
        {"start_at": "infinity"},
        {"deadline": "infinity"},
        {"start_at": END, "deadline": START},
        {"status": "open"},
        {"source": "gemini"},
        {"generation_criteria": None},
        {"generation_criteria": []},
        {"generation_criteria": {}},
        {"generation_criteria": {"reason": "x" * 16500}},
    ],
)
def test_invalid_challenge_values_are_rejected(pg_engine, overrides):
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
        resource_keys = {"subject_id", "activity_id", "study_session_id"}
        values = {
            key: value
            for key, value in overrides.items()
            if value != 1 or key not in resource_keys
        }
        for key in resource_keys:
            if overrides.get(key) == 1:
                values[key] = {
                    "subject_id": subject_id,
                    "activity_id": activity_id,
                    "study_session_id": session_id,
                }[key]
        with pytest.raises(IntegrityError), connection.begin_nested():
            challenge(connection, user_id, plan_id, **values)


def test_challenge_requires_owner_plan_resource_membership_and_consistency(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection)
        owner_id, owner_subject_id = owner_subject(connection, "owner@test.io")
        other_id, other_subject_id = owner_subject(connection, "other@test.io")
        second_subject_id = subject(connection, owner_id)
        owner_activity_id = activity(connection, owner_id, owner_subject_id)
        second_activity_id = activity(connection, owner_id, second_subject_id)
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
        plan_subject(connection, owner_id, owner_plan_id, second_subject_id)
        plan_subject(connection, other_id, other_plan_id, other_subject_id)
        plan_activity(
            connection, owner_id, owner_plan_id, owner_subject_id, owner_activity_id
        )
        plan_activity(
            connection, owner_id, owner_plan_id, second_subject_id, second_activity_id
        )
        plan_session(
            connection, owner_id, owner_plan_id, owner_subject_id, owner_session_id
        )

        with pytest.raises(IntegrityError), connection.begin_nested():
            challenge(connection, other_id, owner_plan_id)
        with pytest.raises(IntegrityError), connection.begin_nested():
            challenge(connection, owner_id, owner_plan_id, subject_id=other_subject_id)
        with pytest.raises(IntegrityError), connection.begin_nested():
            challenge(
                connection,
                owner_id,
                owner_plan_id,
                subject_id=owner_subject_id,
                activity_id=second_activity_id,
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            challenge(
                connection,
                owner_id,
                owner_plan_id,
                subject_id=owner_subject_id,
                study_session_id=other_session_id,
            )
        with pytest.raises(IntegrityError), connection.begin_nested():
            challenge(
                connection,
                owner_id,
                owner_plan_id,
                subject_id=owner_subject_id,
                activity_id=second_activity_id,
                study_session_id=owner_session_id,
            )

        challenge(
            connection,
            owner_id,
            owner_plan_id,
            subject_id=owner_subject_id,
            activity_id=owner_activity_id,
            study_session_id=owner_session_id,
        )
        for statement, params in (
            ("DELETE FROM study_plans WHERE id=:id", {"id": owner_plan_id}),
            ("DELETE FROM subjects WHERE id=:id", {"id": owner_subject_id}),
            ("DELETE FROM activities WHERE id=:id", {"id": owner_activity_id}),
            ("DELETE FROM study_sessions WHERE id=:id", {"id": owner_session_id}),
        ):
            with pytest.raises(IntegrityError), connection.begin_nested():
                connection.execute(text(statement), params)
