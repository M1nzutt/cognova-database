"""Full release rehearsal with runtime role; all changes rolled back locally."""

import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from cognova_database.runner import migration_config
from scripts.release_0004 import apply, snapshot

pytestmark = pytest.mark.integration


def test_atomic_release_and_runtime_contract(pg_engine):
    engine, _ = pg_engine
    with engine.connect() as c, c.begin() as transaction:
        # The helper deliberately targets public. Refuse any existing objects/role.
        assert inspect(c).get_table_names(schema="public") == []
        assert not c.scalar(
            text(
                "SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname='cognova_runtime')"
            )
        )
        c.execute(text("SET LOCAL search_path=public"))
        config = migration_config()
        config.attributes["connection"] = c
        command.upgrade(config, "0003_onboarding_questionnaire")
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
        uid = c.scalar(
            text(
                "INSERT INTO users(name,email,password_hash) "
                "VALUES ('Test','release@test.io','synthetic') RETURNING id"
            )
        )
        before = snapshot(c)
        report = apply(c)
        assert report["runtime_probes"]["denied_statements"] == 9
        assert snapshot(c) == before
        c.execute(text("SET LOCAL ROLE cognova_runtime"))
        insert = text(
            "INSERT INTO subjects(user_id,name,status,difficulty,color_base,"
            "color_shade,active_slot) VALUES (:uid,:name,:status,'easy','blue',"
            "100,:slot) RETURNING id"
        )
        for slot in range(1, 6):
            c.execute(
                insert,
                dict(uid=uid, name=f"Subject {slot}", status="active", slot=slot),
            )
        for name, slot, code in (
            ("Subject 6", 6, "23514"),
            ("Subject 6", 5, "23505"),
            ("subject 1", None, "23505"),
        ):
            with c.begin_nested() as savepoint:
                with pytest.raises(IntegrityError) as error:
                    c.execute(
                        insert,
                        dict(
                            uid=uid,
                            name=name,
                            status="archived" if slot is None else "active",
                            slot=slot,
                        ),
                    )
                assert error.value.orig.sqlstate == code
                savepoint.rollback()
        for n in range(7):
            c.execute(
                insert,
                dict(uid=uid, name=f"Archived {n}", status="archived", slot=None),
            )
        assert c.scalar(text("SELECT count(*) FROM subjects")) == 12
        c.execute(
            text(
                "UPDATE subjects SET status='archived',active_slot=NULL "
                "WHERE active_slot=1"
            )
        )
        c.execute(insert, dict(uid=uid, name="Replacement", status="active", slot=1))
        c.execute(text("RESET ROLE"))
        transaction.rollback()
