from datetime import timedelta

import pytest
from activity_helpers import DEADLINE, HEAD, PREVIOUS, activity, migrate, owner_subject
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from cognova_database.runner import main

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("existing", [False, True])
def test_upgrade_preserves_prior_data_and_schema(pg_engine, existing):
    engine, schema = pg_engine
    with engine.begin() as c:
        before = {}
        if existing:
            migrate(c, "0002_auth_sessions")
            c.execute(
                text(
                    "INSERT INTO users (name,email,password_hash,degree_program,"
                    "semester,academic_goal) VALUES "
                    "('Old','old@test.io','hash','Degree',2,'Original goal')"
                )
            )
            migrate(c, PREVIOUS)
            uid, sid = owner_subject(c)
            c.execute(
                text(
                    "INSERT INTO questionnaire_responses VALUES "
                    "(:uid,1,1,(SELECT jsonb_object_agg('q'||i,'fixture'::text) "
                    "FROM generate_series(1,10) i),now())"
                ),
                {"uid": uid},
            )
            c.execute(
                text(
                    "INSERT INTO auth_sessions VALUES "
                    "('00000000-0000-0000-0000-000000000001',:uid,'hash','csrf',"
                    "now(),now()+interval '1 day',now(),NULL)"
                ),
                {"uid": uid},
            )
            c.execute(text("INSERT INTO rate_limit_buckets VALUES ('fixture',1,now())"))
            tables = set(inspect(c).get_table_names()) - {"alembic_version"}
            before = {
                t: c.execute(text(f"SELECT * FROM {t} ORDER BY 1")).all()
                for t in tables
            }
            subject_checks = inspect(c).get_check_constraints("subjects")
        migrate(c)
        migrate(c)
        assert c.scalar(text("SELECT current_schema()")) == schema
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        for table, rows in before.items():
            assert c.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all() == rows
        if existing:
            assert inspect(c).get_check_constraints("subjects") == subject_checks
            activity(c, uid, sid)
        assert {t for t in inspect(c).get_table_names() if t.startswith("activit")} == {
            "activities",
            "activity_deadline_events",
        }
        fk = inspect(c).get_foreign_keys("activities")[0]
        assert fk["constrained_columns"] == ["user_id", "subject_id"]
        assert fk["referred_columns"] == ["user_id", "id"]
        assert fk["options"] == {"ondelete": "RESTRICT", "onupdate": "RESTRICT"}
        assert {i["name"] for i in inspect(c).get_indexes("activities")} == {
            "ix_activities_user_subject",
            "ix_activities_user_status_deadline",
        }
        assert inspect(c).get_pk_constraint("activity_deadline_events")[
            "constrained_columns"
        ] == ["activity_id", "revision"]
        assert "uq_subjects_user_id_id" in {
            x["name"] for x in inspect(c).get_unique_constraints("subjects")
        }


@pytest.mark.parametrize(
    "bad",
    [
        {"title": ""},
        {"title": " "},
        {"title": "\t"},
        {"title": " x"},
        {"title": "x "},
        {"title": "x" * 51},
        {"title": None},
        {"deadline": None},
        {"deadline": "infinity"},
        {"deadline": "-infinity"},
        {"priority": None},
        {"priority": "highest"},
        {"status": None},
        {"status": "Pendiente"},
        {"estimated_duration": 9},
        {"estimated_duration": 301},
        {"estimated_duration": None},
        {"notes": "x" * 201},
        {"subject_id": None},
        {"subject_id": -1},
        {"user_id": None},
        {"user_id": -1},
        {"original_deadline": DEADLINE + timedelta(days=1)},
        {"deadline_revision": 1},
    ],
)
def test_invalid_activity_is_rejected(pg_engine, bad):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        with pytest.raises(IntegrityError), c.begin_nested():
            activity(c, uid, sid, **bad)


@pytest.mark.parametrize(
    "status", ["pending", "in_progress", "completed", "postponed", "cancelled"]
)
@pytest.mark.parametrize("duration", [10, 300])
def test_boundaries_and_status_tokens(pg_engine, status, duration):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        aid = activity(
            c,
            uid,
            sid,
            title="🚀" * 50,
            notes="é" * 200,
            estimated_duration=duration,
            status=status,
        )
        row = c.execute(
            text("SELECT * FROM activities WHERE id=:id"), {"id": aid}
        ).one()
        assert row.original_deadline == DEADLINE == row.deadline
        assert row.deadline_revision == 0
        assert row.created_at == row.updated_at
        assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 0


def test_same_owner_fk_archive_and_restrict_deletes(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        other, other_sid = owner_subject(c, "other")
        with pytest.raises(IntegrityError), c.begin_nested():
            activity(c, uid, other_sid)
        aid = activity(c, uid, sid)
        before = c.execute(text("SELECT * FROM activities")).all()
        c.execute(
            text("UPDATE subjects SET status='archived',active_slot=NULL WHERE id=:id"),
            {"id": sid},
        )
        assert c.execute(text("SELECT * FROM activities")).all() == before
        for sql, values in [
            ("DELETE FROM subjects WHERE id=:id", {"id": sid}),
            ("DELETE FROM users WHERE id=:id", {"id": uid}),
            ("UPDATE activities SET subject_id=:id", {"id": other_sid}),
            (
                "UPDATE subjects SET user_id=:id WHERE id=:sid",
                {"id": other, "sid": sid},
            ),
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                c.execute(text(sql), values)
        # An activity without deadline history can be explicitly deleted.
        c.execute(text("DELETE FROM activities WHERE id=:id"), {"id": aid})
        c.execute(text("DELETE FROM subjects WHERE id=:id"), {"id": sid})


def test_multiple_postponements_reschedule_and_timestamps(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        aid = activity(c, uid, sid)
        created = c.scalar(text("SELECT created_at FROM activities"))
        previous = DEADLINE
        for revision, delta in enumerate([2, 5, 1, 7], 1):
            deadline = DEADLINE + timedelta(days=delta)
            c.execute(
                text("UPDATE activities SET deadline=:d WHERE id=:id"),
                {"d": deadline, "id": aid},
            )
            row = c.execute(text("SELECT * FROM activities")).one()
            event = c.execute(
                text("SELECT * FROM activity_deadline_events WHERE revision=:r"),
                {"r": revision},
            ).one()
            assert row.created_at == created <= row.updated_at
            assert row.original_deadline == DEADLINE
            assert row.status == "pending"  # Backend owns state transitions.
            assert row.deadline_revision == revision
            assert event.previous_deadline == previous
            assert event.new_deadline == deadline
            assert event.occurred_at == row.updated_at
            assert event.event_type == (
                "postponed" if deadline > previous else "rescheduled"
            )
            previous = deadline
        c.execute(
            text(
                "UPDATE activities SET deadline=deadline,status='completed',"
                "notes='Changed',updated_at='1999-01-01'"
            )
        )
        assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 4
        assert c.scalar(text("SELECT updated_at >= created_at FROM activities"))
        for sql in [
            "UPDATE activities SET original_deadline=deadline",
            "UPDATE activities SET deadline_revision=0",
            "UPDATE activities SET id=id+100",
            "UPDATE activities SET user_id=user_id+1",
            "UPDATE activities SET created_at=now() + interval '1 day'",
            "UPDATE activity_deadline_events SET new_deadline=previous_deadline",
            "DELETE FROM activity_deadline_events",
            "TRUNCATE activity_deadline_events",
            "DELETE FROM activities",
            "TRUNCATE activities CASCADE",
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                c.execute(text(sql))


def test_deadline_offset_represents_same_instant_without_event(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        activity(c, uid, sid)
        c.execute(text("UPDATE activities SET deadline='2030-01-01 07:00:00-05'"))
        assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 0
        assert c.scalar(text("SELECT deadline FROM activities")) == DEADLINE


def test_transaction_and_bulk_failure_roll_back_history(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        activity(c, uid, sid)
        activity(c, uid, sid)
    with engine.connect() as c:
        tx = c.begin()
        c.execute(text("UPDATE activities SET deadline=deadline+interval '1 day'"))
        assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 2
        tx.rollback()
        assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 0
        c.rollback()
        with pytest.raises(IntegrityError), c.begin():
            c.execute(
                text(
                    "UPDATE activities SET deadline=deadline+interval '1 day',"
                    "estimated_duration=CASE WHEN id=(SELECT max(id) FROM activities) "
                    "THEN 301 ELSE 30 END"
                )
            )
        assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 0
        assert c.scalar(text("SELECT bool_and(deadline_revision=0) FROM activities"))


@pytest.mark.parametrize("status", ["pending", "completed", "cancelled"])
def test_downgrade_refuses_any_activity(pg_engine, status):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        activity(c, uid, sid, status=status)
    with pytest.raises(DBAPIError, match="Downgrade blocked"), engine.begin() as c:
        migrate(c, PREVIOUS, down=True)
    with engine.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        assert c.scalar(text("SELECT count(*) FROM activities")) == 1


def test_empty_downgrade_reupgrade_and_transactional_ddl(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c, PREVIOUS)
        owner_subject(c)
        before = c.execute(text("SELECT * FROM subjects")).all()
    with engine.connect() as c:
        tx = c.begin()
        migrate(c)
        tx.rollback()
        assert "activities" not in inspect(c).get_table_names()
        assert "uq_subjects_user_id_id" not in {
            x["name"] for x in inspect(c).get_unique_constraints("subjects")
        }
    with engine.begin() as c:
        migrate(c)
        migrate(c, PREVIOUS, down=True)
        assert c.execute(text("SELECT * FROM subjects")).all() == before
        assert "activities" not in inspect(c).get_table_names()
        assert (
            c.scalar(
                text(
                    "SELECT count(*) FROM pg_proc p JOIN pg_namespace n "
                    "ON p.pronamespace=n.oid WHERE n.nspname=current_schema() "
                    "AND p.proname LIKE 'cognova_%activity%'"
                )
            )
            == 0
        )
        migrate(c)
        c.execute(
            text("CREATE VIEW future_activity_dependency AS SELECT * FROM activities")
        )
    with pytest.raises(DBAPIError), engine.begin() as c:
        migrate(c, PREVIOUS, down=True)
    with engine.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        assert "activity_deadline_events" in inspect(c).get_table_names()


@pytest.mark.parametrize("priority", ["low", "medium", "high", "urgent"])
def test_all_priorities_and_empty_notes(pg_engine, priority):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        activity(c, uid, sid, priority=priority, notes="")
        assert c.scalar(text("SELECT priority FROM activities")) == priority


def test_history_insert_failure_is_atomic(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        activity(c, uid, sid)
        c.execute(
            text(
                "ALTER TABLE activity_deadline_events ADD CONSTRAINT "
                "test_reject_event CHECK (revision < 0) NOT VALID"
            )
        )
    with pytest.raises(IntegrityError), engine.begin() as c:
        c.execute(text("UPDATE activities SET deadline=deadline+interval '1 day'"))
    with engine.connect() as c:
        assert c.scalar(text("SELECT deadline FROM activities")) == DEADLINE
        assert c.scalar(text("SELECT deadline_revision FROM activities")) == 0
        assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 0


def test_cli_explicit_activities_and_head(pg_engine, monkeypatch):
    engine, schema = pg_engine
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", engine.url.render_as_string(hide_password=False))
    assert main(["upgrade", HEAD]) == 0
    assert main(["upgrade", "head"]) == 0
    with engine.connect() as c:
        assert c.scalar(text("SELECT current_schema()")) == schema
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
