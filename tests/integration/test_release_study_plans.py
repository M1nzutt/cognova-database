"""Release rehearsal for 0007 using only the opted-in disposable database."""

import json

import pytest
from activity_helpers import activity
from alembic import command
from plan_helpers import study_session
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from cognova_database.runner import migration_config
from scripts.release_0007 import (
    ALLOWED,
    CONTRACT,
    TABLES,
    TARGET,
    apply,
    snapshot,
    verify,
)

pytestmark = pytest.mark.integration


def _prepare(connection):
    assert inspect(connection).get_table_names(schema="public") == []
    assert not connection.scalar(
        text("SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='cognova_runtime')")
    )
    connection.execute(text("SET LOCAL search_path=public"))
    config = migration_config()
    config.attributes["connection"] = connection
    command.upgrade(config, "0006_study_sessions")
    connection.execute(text("CREATE ROLE cognova_runtime LOGIN"))
    connection.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
    connection.execute(text("GRANT USAGE ON SCHEMA public TO cognova_runtime"))
    connection.execute(text("GRANT SELECT,UPDATE ON users TO cognova_runtime"))
    connection.execute(
        text(
            "GRANT SELECT ON alembic_version,user_academic_goal_legacy "
            "TO cognova_runtime"
        )
    )
    connection.execute(
        text("GRANT SELECT,INSERT ON questionnaire_responses TO cognova_runtime")
    )
    connection.execute(
        text("GRANT SELECT,INSERT,UPDATE,DELETE ON subjects TO cognova_runtime")
    )
    connection.execute(
        text("GRANT USAGE,SELECT ON SEQUENCE subjects_id_seq TO cognova_runtime")
    )
    connection.execute(
        text("GRANT SELECT,INSERT,UPDATE,DELETE ON activities TO cognova_runtime")
    )
    connection.execute(
        text("GRANT SELECT ON activity_deadline_events TO cognova_runtime")
    )
    connection.execute(
        text("GRANT USAGE,SELECT ON SEQUENCE activities_id_seq TO cognova_runtime")
    )
    connection.execute(
        text("GRANT SELECT,INSERT,UPDATE,DELETE ON study_sessions TO cognova_runtime")
    )
    connection.execute(
        text("GRANT SELECT,INSERT,UPDATE ON study_session_intervals TO cognova_runtime")
    )
    connection.execute(
        text(
            "GRANT USAGE,SELECT ON SEQUENCE study_sessions_id_seq,"
            "study_session_intervals_id_seq TO cognova_runtime"
        )
    )
    user_id = connection.scalar(
        text(
            "INSERT INTO users(name,email,password_hash) VALUES "
            "('Release','plan-release@test.io','synthetic') RETURNING id"
        )
    )
    subject_id = connection.scalar(
        text(
            "INSERT INTO subjects(user_id,name,status,difficulty,color_base,"
            "color_shade,active_slot) VALUES "
            "(:uid,'Physics','active','easy','blue',100,1) RETURNING id"
        ),
        {"uid": user_id},
    )
    activity_id = activity(connection, user_id, subject_id)
    session_id = study_session(connection, user_id, subject_id, activity_id)
    connection.execute(text("SET CONSTRAINTS ALL IMMEDIATE"))
    return user_id, subject_id, activity_id, session_id


def test_atomic_plan_release_preserves_0006_and_runtime_is_least_privilege(pg_engine):
    engine, _ = pg_engine
    with engine.connect() as connection, connection.begin() as transaction:
        user_id, subject_id, activity_id, session_id = _prepare(connection)
        before = snapshot(connection)
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        report = apply(connection, contract)

        assert snapshot(connection) == before
        assert set(before) == set(TABLES)
        assert all(report["rows_preserved"].values())
        assert verify(connection, contract)["catalog_matches_tested_contract"]
        assert report["revision_before"] == "0006_study_sessions"
        assert report["revision"] == TARGET

        connection.execute(text("SET LOCAL ROLE cognova_runtime"))
        plan_id = connection.scalar(
            text(
                "INSERT INTO study_plans(user_id,name,objective,start_at,end_at,"
                "status,source) VALUES (:uid,'Exam plan','Prepare for final',"
                "'2030-01-01T00:00:00Z','2030-01-08T00:00:00Z','draft','ai') "
                "RETURNING id"
            ),
            {"uid": user_id},
        )
        connection.execute(
            text(
                "INSERT INTO study_plan_subjects(user_id,plan_id,subject_id) "
                "VALUES (:uid,:plan,:subject)"
            ),
            {"uid": user_id, "plan": plan_id, "subject": subject_id},
        )
        connection.execute(
            text(
                "INSERT INTO study_plan_activities"
                "(user_id,plan_id,subject_id,activity_id) "
                "VALUES (:uid,:plan,:subject,:activity)"
            ),
            {
                "uid": user_id,
                "plan": plan_id,
                "subject": subject_id,
                "activity": activity_id,
            },
        )
        connection.execute(
            text(
                "INSERT INTO study_plan_sessions"
                "(user_id,plan_id,subject_id,study_session_id) "
                "VALUES (:uid,:plan,:subject,:session)"
            ),
            {
                "uid": user_id,
                "plan": plan_id,
                "subject": subject_id,
                "session": session_id,
            },
        )
        connection.execute(
            text(
                "INSERT INTO study_plan_decisions"
                "(user_id,plan_id,action,proposed_value,chosen_value) "
                "VALUES (:uid,:plan,'accepted','{\"status\":\"draft\"}'::jsonb,"
                '\'{"status":"active"}\'::jsonb)'
            ),
            {"uid": user_id, "plan": plan_id},
        )
        challenge_id = connection.scalar(
            text(
                "INSERT INTO study_challenges"
                "(user_id,plan_id,subject_id,activity_id,study_session_id,title,"
                "description,target_type,target_value,status,source,"
                "generation_criteria) "
                "VALUES (:uid,:plan,:subject,:activity,:session,'Review topic',"
                "'Review and adapt next topic','custom',"
                '\'{"mode":"adaptive"}\'::jsonb,'
                "'pending','ai','{\"strategy\":\"contextual\"}'::jsonb) "
                "RETURNING id"
            ),
            {
                "uid": user_id,
                "plan": plan_id,
                "subject": subject_id,
                "activity": activity_id,
                "session": session_id,
            },
        )
        connection.execute(
            text("UPDATE study_plans SET status='active' WHERE id=:id"),
            {"id": plan_id},
        )
        connection.execute(
            text("UPDATE study_challenges SET status='in_progress' WHERE id=:id"),
            {"id": challenge_id},
        )

        for statement in (
            "UPDATE study_plan_decisions SET action='rejected'",
            "DELETE FROM study_plan_decisions",
            "DELETE FROM study_challenges",
            "TRUNCATE study_plans",
            "UPDATE alembic_version SET version_num='fake'",
            "CREATE TABLE forbidden_release_ddl(id integer)",
        ):
            with pytest.raises(DBAPIError) as error, connection.begin_nested():
                connection.execute(text(statement))
            assert error.value.orig.sqlstate == "42501"

        for table, allowed in ALLOWED.items():
            privileges = {
                privilege
                for privilege in (
                    "SELECT",
                    "INSERT",
                    "UPDATE",
                    "DELETE",
                    "TRUNCATE",
                    "REFERENCES",
                    "TRIGGER",
                )
                if connection.scalar(
                    text("SELECT has_table_privilege(current_user,:table,:p)"),
                    {"table": "public." + table, "p": privilege},
                )
            }
            assert privileges == allowed

        connection.execute(text("RESET ROLE"))
        transaction.rollback()


@pytest.mark.parametrize("failure", ["wrong_revision", "bad_contract"])
def test_plan_release_failure_leaves_0006_untouched(pg_engine, failure):
    engine, _ = pg_engine
    with engine.connect() as connection, connection.begin() as transaction:
        _prepare(connection)
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        if failure == "wrong_revision":
            connection.execute(text("UPDATE alembic_version SET version_num='wrong'"))
            with pytest.raises(RuntimeError, match="revision_before"):
                apply(connection, contract)
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "wrong"
            )
        else:
            contract["bad_contract_marker"] = True
            savepoint = connection.begin_nested()
            try:
                with pytest.raises(RuntimeError, match="installed_contract_differs"):
                    apply(connection, contract)
            finally:
                savepoint.rollback()
            assert (
                connection.scalar(text("SELECT version_num FROM alembic_version"))
                == "0006_study_sessions"
            )
            assert "study_plans" not in inspect(connection).get_table_names(
                schema="public"
            )
        transaction.rollback()
