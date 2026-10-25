"""Release rehearsal confined to the opted-in disposable PostgreSQL fixture."""

import json

import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError

from cognova_database.runner import migration_config
from scripts.release_0005 import CONTRACT, apply, snapshot, verify

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("reject_contract", [False, True])
def test_atomic_activities_release_and_permissions(pg_engine, reject_contract):
    engine, _ = pg_engine
    with engine.connect() as c, c.begin() as transaction:
        assert inspect(c).get_table_names(schema="public") == []
        assert not c.scalar(
            text(
                "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='cognova_runtime')"
            )
        )
        c.execute(text("SET LOCAL search_path=public"))
        config = migration_config()
        config.attributes["connection"] = c
        command.upgrade(config, "0004_subjects")
        c.execute(text("CREATE ROLE cognova_runtime LOGIN"))
        c.execute(text("REVOKE CREATE ON SCHEMA public FROM PUBLIC"))
        c.execute(text("GRANT USAGE ON SCHEMA public TO cognova_runtime"))
        c.execute(text("GRANT SELECT,UPDATE ON users TO cognova_runtime"))
        c.execute(
            text(
                "GRANT SELECT ON alembic_version,user_academic_goal_legacy TO "
                "cognova_runtime"
            )
        )
        c.execute(
            text("GRANT SELECT,INSERT ON questionnaire_responses TO cognova_runtime")
        )
        c.execute(
            text("GRANT SELECT,INSERT,UPDATE,DELETE ON subjects TO cognova_runtime")
        )
        c.execute(
            text("GRANT USAGE,SELECT ON SEQUENCE subjects_id_seq TO cognova_runtime")
        )
        uid = c.scalar(
            text(
                "INSERT INTO users(name,email,password_hash) VALUES "
                "('Test','activity-release@test.io','synthetic') RETURNING id"
            )
        )
        sid = c.scalar(
            text(
                "INSERT INTO "
                "subjects(user_id,name,status,difficulty,color_base,color_shade,active_slot)"
                " VALUES (:uid,'Subject','active','easy','blue',100,1) RETURNING "
                "id"
            ),
            {"uid": uid},
        )
        before = snapshot(c)
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        if reject_contract:
            bad = json.loads(json.dumps(contract))
            bad["functions"] = []
            with c.begin_nested() as savepoint:
                with pytest.raises(RuntimeError, match="installed_contract_differs"):
                    apply(c, bad)
                savepoint.rollback()
            assert (
                c.scalar(text("SELECT version_num FROM alembic_version"))
                == "0004_subjects"
            )
            assert "activities" not in inspect(c).get_table_names(schema="public")
            assert snapshot(c) == before
        report = apply(c, contract)
        assert snapshot(c) == before
        assert all(report["rows_preserved"].values())
        assert verify(c, contract)["catalog_matches_tested_contract"]
        with c.begin_nested() as savepoint:
            with pytest.raises(RuntimeError, match="revision_before"):
                apply(c, contract)
            savepoint.rollback()
        c.execute(text("SET LOCAL ROLE cognova_runtime"))
        insert = text(
            "INSERT INTO "
            "activities(user_id,subject_id,title,deadline,priority,status,estimated_duration)"
            " VALUES "
            "(:uid,:sid,'Activity','2030-01-01T00:00:00Z','medium','pending',30)"
            " RETURNING id"
        )
        aid = c.scalar(insert, {"uid": uid, "sid": sid})
        for date in (
            "2030-01-03T00:00:00Z",
            "2030-01-02T00:00:00Z",
            "2030-01-04T00:00:00Z",
        ):
            c.execute(
                text("UPDATE activities SET deadline=:d WHERE id=:id"),
                {"d": date, "id": aid},
            )
        assert c.scalars(
            text("SELECT event_type FROM activity_deadline_events ORDER BY revision")
        ).all() == ["postponed", "rescheduled", "postponed"]
        assert c.scalar(
            text(
                "SELECT original_deadline=TIMESTAMPTZ '2030-01-01T00:00:00Z' FROM "
                "activities WHERE id=:id"
            ),
            {"id": aid},
        )
        for sql, code in (
            ("UPDATE activities SET original_deadline=deadline", "23514"),
            ("DELETE FROM subjects", "23503"),
            ("DELETE FROM activities", "23503"),
            (
                "INSERT INTO activity_deadline_events "
                "SELECT * FROM activity_deadline_events",
                "42501",
            ),
            ("UPDATE activity_deadline_events SET revision=1", "42501"),
            ("DELETE FROM activity_deadline_events", "42501"),
            ("UPDATE alembic_version SET version_num='bad'", "42501"),
            ("ALTER TABLE activities ADD COLUMN bad int", "42501"),
            ("CREATE TABLE public.bad(id int)", "42501"),
            ("SELECT cognova_record_activity_deadline()", "42501"),
        ):
            with c.begin_nested() as savepoint:
                with pytest.raises(DBAPIError) as error:
                    c.execute(text(sql))
                assert error.value.orig.sqlstate == code
                savepoint.rollback()
        c.execute(text("UPDATE subjects SET status='archived',active_slot=NULL"))
        assert c.scalar(text("SELECT count(*) FROM activities")) == 1
        fresh = c.scalar(insert, {"uid": uid, "sid": sid})
        c.execute(text("DELETE FROM activities WHERE id=:id"), {"id": fresh})
        c.execute(text("RESET ROLE"))
        transaction.rollback()
