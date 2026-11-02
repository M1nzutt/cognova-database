import json

import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from cognova_database.runner import migration_config
from scripts.release_0006 import CONTRACT, apply, snapshot, verify

pytestmark = pytest.mark.integration


def test_atomic_study_release_runtime_and_preservation(pg_engine):
    engine, _ = pg_engine
    with engine.connect() as c, c.begin() as transaction:
        assert inspect(c).get_table_names(schema="public") == []
        c.execute(text("SET LOCAL search_path=public"))
        config = migration_config()
        config.attributes["connection"] = c
        command.upgrade(config, "0005_activities")
        c.execute(text("CREATE ROLE cognova_runtime LOGIN"))
        c.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
        c.execute(text("GRANT USAGE ON SCHEMA public TO cognova_runtime"))
        c.execute(text("GRANT SELECT,UPDATE ON users TO cognova_runtime"))
        c.execute(
            text(
                "GRANT SELECT ON alembic_version,user_academic_goal_legacy "
                "TO cognova_runtime"
            )
        )
        c.execute(
            text("GRANT SELECT,INSERT ON questionnaire_responses TO cognova_runtime")
        )
        c.execute(
            text(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON subjects,activities "
                "TO cognova_runtime"
            )
        )
        c.execute(text("GRANT SELECT ON activity_deadline_events TO cognova_runtime"))
        c.execute(
            text(
                "GRANT USAGE,SELECT ON SEQUENCE subjects_id_seq,activities_id_seq "
                "TO cognova_runtime"
            )
        )
        uid = c.scalar(
            text(
                "INSERT INTO users(name,email,password_hash) VALUES "
                "('Test','release-study@test.io','synthetic') RETURNING id"
            )
        )
        sid = c.scalar(
            text(
                "INSERT INTO subjects(user_id,name,status,difficulty,color_base,"
                "color_shade,active_slot) VALUES "
                "(:uid,'Subject','active','easy','blue',100,1) RETURNING id"
            ),
            {"uid": uid},
        )
        aid = c.scalar(
            text(
                "INSERT INTO activities(user_id,subject_id,title,deadline,priority,"
                "status,estimated_duration) VALUES "
                "(:uid,:sid,'Activity','2030-01-01T00:00:00Z','medium','pending',30) "
                "RETURNING id"
            ),
            {"uid": uid, "sid": sid},
        )
        c.execute(text("UPDATE activities SET deadline=deadline+interval '1 day'"))
        before = snapshot(c)
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        report = apply(c, contract)
        assert snapshot(c) == before
        assert all(report["rows_preserved"].values())
        assert verify(c, contract)["catalog_matches_tested_contract"]
        c.execute(text("SET LOCAL ROLE cognova_runtime"))
        session_id = c.scalar(
            text(
                "INSERT INTO study_sessions(user_id,subject_id,activity_id,"
                "planned_start_at,planned_duration) VALUES "
                "(:uid,:sid,:aid,'2030-02-01T10:00:00Z',45) RETURNING id"
            ),
            {"uid": uid, "sid": sid, "aid": aid},
        )
        for sql in [
            "CREATE TABLE forbidden_ddl (id integer)",
            "TRUNCATE study_sessions",
            "UPDATE alembic_version SET version_num='fake'",
            "DELETE FROM activity_deadline_events",
        ]:
            with pytest.raises(DBAPIError) as error, c.begin_nested():
                c.execute(text(sql))
            assert error.value.orig.sqlstate == "42501"
        c.execute(text("DELETE FROM study_sessions WHERE id=:id"), {"id": session_id})
        c.execute(text("RESET ROLE"))
        transaction.rollback()


@pytest.mark.parametrize("failure", ["unexpected_revision", "bad_contract"])
def test_study_release_failure_is_atomic(pg_engine, failure):
    engine, _ = pg_engine
    with engine.connect() as c, c.begin() as transaction:
        c.execute(text("SET LOCAL search_path=public"))
        config = migration_config()
        config.attributes["connection"] = c
        command.upgrade(config, "0005_activities")
        c.execute(text("CREATE ROLE cognova_runtime LOGIN"))
        c.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
        c.execute(text("GRANT USAGE ON SCHEMA public TO cognova_runtime"))
        c.execute(text("GRANT SELECT,UPDATE ON users TO cognova_runtime"))
        c.execute(
            text(
                "GRANT SELECT ON alembic_version,user_academic_goal_legacy "
                "TO cognova_runtime"
            )
        )
        c.execute(
            text("GRANT SELECT,INSERT ON questionnaire_responses TO cognova_runtime")
        )
        c.execute(
            text(
                "GRANT SELECT,INSERT,UPDATE,DELETE ON subjects,activities "
                "TO cognova_runtime"
            )
        )
        c.execute(text("GRANT SELECT ON activity_deadline_events TO cognova_runtime"))
        if failure == "unexpected_revision":
            c.execute(text("UPDATE alembic_version SET version_num='wrong'"))
            with pytest.raises(RuntimeError, match="revision_before"):
                apply(c, json.loads(CONTRACT.read_text(encoding="utf-8")))
            assert c.scalar(text("SELECT version_num FROM alembic_version")) == "wrong"
        elif failure == "bad_contract":
            contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
            contract["functions"] = []
            savepoint = c.begin_nested()
            try:
                with pytest.raises(RuntimeError, match="installed_contract_differs"):
                    apply(c, contract)
            finally:
                savepoint.rollback()
            assert (
                c.scalar(text("SELECT version_num FROM alembic_version"))
                == "0005_activities"
            )
            assert "study_sessions" not in inspect(c).get_table_names(schema="public")
        transaction.rollback()
