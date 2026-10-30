from datetime import timedelta
from decimal import Decimal

import pytest
from activity_helpers import owner_subject
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from study_helpers import END, START, interval, migrate, running, session, validate

pytestmark = pytest.mark.integration


def test_backend_controls_pause_resume_finish_and_effective_duration(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        key = running(c, uid, sid)
        first_end = START + timedelta(minutes=10, microseconds=123456)
        c.execute(
            text("UPDATE study_session_intervals SET ended_at=:end"), {"end": first_end}
        )
        c.execute(
            text(
                "UPDATE study_sessions SET execution_state='paused',"
                "actual_duration=600.123456"
            )
        )
        validate(c)
        second_start = START + timedelta(minutes=20)
        interval(c, key, start=second_start)
        c.execute(text("UPDATE study_sessions SET execution_state='running'"))
        validate(c)
        c.execute(
            text(
                "UPDATE study_session_intervals SET ended_at=:end "
                "WHERE ended_at IS NULL"
            ),
            {"end": END},
        )
        c.execute(
            text(
                "UPDATE study_sessions SET execution_state='finished',status='partial',"
                "end_at=:end,actual_duration=(SELECT sum(extract(epoch FROM "
                "ended_at-started_at)) FROM study_session_intervals)"
            ),
            {"end": END},
        )
        validate(c)
        row = c.execute(text("SELECT * FROM study_sessions")).one()
        assert row.actual_duration == Decimal("1200.123456")
        assert row.actual_duration != Decimal(str((END - START).total_seconds()))
        assert row.start_at == START and row.end_at == END
        assert row.updated_at >= row.created_at
        assert c.scalar(text("SELECT count(*) FROM study_session_intervals")) == 2


@pytest.mark.parametrize(
    "state,status,start,end,duration",
    [
        ("running", None, START, None, 0),
        ("paused", None, START, None, 0),
        ("finished", "completed", START, END, 1800),
        ("finished", "partial", START, END, 1800),
    ],
)
def test_executed_state_without_interval_evidence_fails(
    pg_engine, state, status, start, end, duration
):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        with pytest.raises(IntegrityError), c.begin_nested():
            session(
                c,
                uid,
                sid,
                execution_state=state,
                status=status,
                start_at=start,
                end_at=end,
                actual_duration=duration,
            )
            validate(c)


@pytest.mark.parametrize(
    "start,end",
    [
        (None, None),
        ("infinity", None),
        (START, "-infinity"),
        (START, START),
        (END, START),
        (START, "infinity"),
    ],
)
def test_invalid_interval_timestamps(pg_engine, start, end):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        key = session(c, uid, sid)
        with pytest.raises(IntegrityError), c.begin_nested():
            interval(c, key, start=start, end=end)


def test_consistency_validated_at_commit_and_rejects_wrong_bounds(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        for state, start, end in [
            ("planned", START, END),
            ("running", START + timedelta(seconds=1), None),
            ("paused", START, None),
            ("finished", START, END + timedelta(seconds=1)),
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                extra = {} if state == "planned" else {"start_at": START}
                if state == "finished":
                    extra.update(end_at=END, actual_duration=1800, status="completed")
                key = session(c, uid, sid, execution_state=state, **extra)
                interval(c, key, start=start, end=end)
                validate(c)
    # A deferred failure on commit must roll back the whole attempted transaction.
    with pytest.raises(IntegrityError), engine.begin() as c:
        session(c, uid, sid, execution_state="running", start_at=START)
    with engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM study_sessions")) == 0


def test_interval_immutability_overlap_and_one_open(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        key = running(c, uid, sid)
        for sql in [
            "UPDATE study_sessions SET user_id=user_id+1",
            "UPDATE study_sessions SET id=id+1",
            "UPDATE study_sessions SET created_at=created_at+interval '1 day'",
            "UPDATE study_session_intervals SET id=id+1",
            "UPDATE study_session_intervals SET session_id=session_id+1",
            "UPDATE study_session_intervals SET started_at=started_at+interval '1s'",
            "UPDATE study_session_intervals SET created_at=now()",
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                c.execute(text(sql))
        with pytest.raises(IntegrityError), c.begin_nested():
            interval(c, key, start=END)  # second open interval
        c.execute(
            text("UPDATE study_session_intervals SET ended_at=:end"), {"end": END}
        )
        with pytest.raises(IntegrityError), c.begin_nested():
            interval(c, key, start=START + timedelta(seconds=1), end=END)
        interval(c, key, start=END)  # adjacent half-open ranges are allowed
        validate(c)
        for sql in [
            "UPDATE study_session_intervals SET ended_at=NULL "
            "WHERE ended_at IS NOT NULL",
            "UPDATE study_session_intervals SET ended_at=ended_at+interval '1s' "
            "WHERE ended_at IS NOT NULL",
        ]:
            with pytest.raises(IntegrityError), c.begin_nested():
                c.execute(text(sql))
        # Timer fields are not automatically updated by an interval write.
        assert c.scalar(text("SELECT actual_duration FROM study_sessions")) == 0
        assert c.scalar(text("SELECT execution_state FROM study_sessions")) == "running"


def test_transaction_rollback_preserves_previous_execution(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        running(c, uid, sid)
    with engine.connect() as c:
        before = c.execute(text("SELECT * FROM study_sessions")).all()
        intervals = c.execute(text("SELECT * FROM study_session_intervals")).all()
        c.rollback()
        tx = c.begin()
        c.execute(
            text("UPDATE study_session_intervals SET ended_at=:end"), {"end": END}
        )
        c.execute(
            text(
                "UPDATE study_sessions SET execution_state='finished',"
                "status='completed',end_at=:end,actual_duration=1800"
            ),
            {"end": END},
        )
        validate(c)
        tx.rollback()
        assert c.execute(text("SELECT * FROM study_sessions")).all() == before
        assert (
            c.execute(text("SELECT * FROM study_session_intervals")).all() == intervals
        )


def test_missing_session_and_distinct_sessions_do_not_share_intervals(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        with pytest.raises(IntegrityError), c.begin_nested():
            interval(c, -1)
        for suffix in ["one", "two"]:
            uid, sid = owner_subject(c, suffix)
            running(c, uid, sid)
        assert c.scalar(text("SELECT count(*) FROM study_session_intervals")) == 2
