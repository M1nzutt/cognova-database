import pytest
from activity_helpers import activity, owner_subject
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from study_helpers import migrate, running, session, validate

pytestmark = pytest.mark.integration


def test_same_owner_and_same_subject_are_required_even_for_direct_sql(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        other, foreign_sid = owner_subject(c, "other")
        aid = activity(c, uid, sid)
        foreign_aid = activity(c, other, foreign_sid)
        same_owner_sid = c.scalar(
            text(
                "INSERT INTO subjects(user_id,name,status,difficulty,color_base,"
                "color_shade) VALUES (:uid,'Second','archived','easy','blue',100) "
                "RETURNING id"
            ),
            {"uid": uid},
        )
        other_subject_aid = activity(c, uid, same_owner_sid)
        for owner, subject, activity_id in [
            (uid, foreign_sid, None),
            (uid, sid, foreign_aid),
            (uid, sid, other_subject_aid),
            (other, sid, aid),
            (uid, sid, -1),
            (-1, sid, None),
            (uid, -1, None),
            (None, sid, None),
            (uid, None, None),
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                session(c, owner, subject, activity_id=activity_id)
        session(c, uid, sid, activity_id=aid)
        session(c, uid, same_owner_sid)
        validate(c)
        assert c.scalar(text("SELECT count(*) FROM study_sessions")) == 2


def test_restrict_updates_deletes_and_archive_preserve_sessions(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        aid = activity(c, uid, sid)
        key = session(c, uid, sid, activity_id=aid)
        validate(c)
        original = c.execute(text("SELECT * FROM study_sessions")).all()
        c.execute(text("UPDATE subjects SET status='archived',active_slot=NULL"))
        assert c.execute(text("SELECT * FROM study_sessions")).all() == original
        sid2 = c.scalar(
            text(
                "INSERT INTO subjects(user_id,name,status,difficulty,color_base,"
                "color_shade) VALUES (:uid,'Second','archived','easy','blue',100) "
                "RETURNING id"
            ),
            {"uid": uid},
        )
        for sql in [
            "DELETE FROM users",
            "DELETE FROM subjects WHERE id=" + str(sid),
            "DELETE FROM activities",
            "UPDATE activities SET subject_id=" + str(sid2),
            "UPDATE study_sessions SET subject_id=" + str(sid2),
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                c.execute(text(sql))
        c.execute(text("DELETE FROM study_sessions WHERE id=:id"), {"id": key})
        c.execute(text("DELETE FROM activities"))
        c.execute(text("DELETE FROM subjects"))


def test_interval_evidence_cannot_be_deleted_or_cascaded(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        running(c, uid, sid)
        for sql in [
            "DELETE FROM study_sessions",
            "DELETE FROM study_session_intervals",
            "TRUNCATE study_session_intervals",
            "TRUNCATE study_sessions CASCADE",
            "DELETE FROM subjects",
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                c.execute(text(sql))
        assert c.scalar(text("SELECT count(*) FROM study_session_intervals")) == 1


def test_catalog_foreign_keys_and_indexes(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        inspector = inspect(c)
        keys = inspector.get_foreign_keys("study_sessions")
        assert {tuple(k["constrained_columns"]) for k in keys} == {
            ("user_id", "subject_id"),
            ("user_id", "subject_id", "activity_id"),
        }
        for table in ["study_sessions", "study_session_intervals"]:
            for key in inspector.get_foreign_keys(table):
                assert key["options"] == {
                    "ondelete": "RESTRICT",
                    "onupdate": "RESTRICT",
                }
        assert "uq_activities_user_subject_id" in {
            k["name"] for k in inspector.get_unique_constraints("activities")
        }
        names = set(
            c.scalars(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE schemaname=current_schema() "
                    "AND tablename IN ('study_sessions','study_session_intervals')"
                )
            )
        )
        assert names == {
            "study_sessions_pkey",
            "study_session_intervals_pkey",
            "ix_study_sessions_user_planned",
            "ix_study_sessions_owner_activity",
            "uq_study_sessions_user_executing",
            "ix_study_intervals_session_started",
            "uq_study_intervals_open",
            "ex_study_intervals_overlap",
        }
        assert c.scalar(
            text(
                "SELECT bool_and(i.indisvalid AND i.indisready) FROM pg_index i "
                "JOIN pg_class t ON t.oid=i.indrelid "
                "WHERE t.relnamespace=current_schema()::regnamespace"
            )
        )
