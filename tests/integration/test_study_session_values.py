import pytest
from activity_helpers import owner_subject
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from study_helpers import END, START, interval, migrate, session, validate

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("duration", [10, 180])
def test_planned_session_defaults_and_duration_boundaries(pg_engine, duration):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        session(c, uid, sid, planned_duration=duration)
        validate(c)
        row = c.execute(text("SELECT * FROM study_sessions")).one()
        assert row.execution_state == "planned"
        assert row.status is None and row.start_at is None and row.end_at is None
        assert row.activity_id is None and row.context is None
        assert row.actual_duration == 0
        assert row.created_at == row.updated_at


@pytest.mark.parametrize(
    "bad",
    [
        {"planned_duration": 9},
        {"planned_duration": 181},
        {"planned_duration": None},
        {"planned_start_at": None},
        {"planned_start_at": "infinity"},
        {"planned_start_at": "-infinity"},
        {"execution_state": "completed"},
        {"execution_state": None},
        {"status": "unknown"},
        {"actual_duration": -1},
        {"actual_duration": "NaN"},
        {"actual_duration": None},
        {"start_at": "infinity"},
        {"end_at": END},
        {"context": "unknown"},
        {"other_text": "unexpected"},
        {"status": "completed"},
        {"execution_state": "running"},
        {"context": "tired"},
        {"execution_state": "finished"},
        {"execution_state": "finished", "status": "completed"},
        {"execution_state": "finished", "status": "partial"},
        {
            "execution_state": "finished",
            "status": "completed",
            "start_at": START,
            "end_at": START,
            "actual_duration": 1,
        },
    ],
)
def test_invalid_scalar_values_rejected(pg_engine, bad):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        with pytest.raises(IntegrityError), c.begin_nested():
            session(c, uid, sid, **bad)
            validate(c)


@pytest.mark.parametrize("status", ["completed", "partial", "postponed", "cancelled"])
def test_finished_results_with_real_execution(pg_engine, status):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        key = session(
            c,
            uid,
            sid,
            execution_state="finished",
            status=status,
            start_at=START,
            end_at=END,
            actual_duration=1800,
        )
        interval(c, key, end=END)
        validate(c)
        assert c.scalar(text("SELECT status FROM study_sessions")) == status


@pytest.mark.parametrize("status", ["postponed", "cancelled"])
def test_unstarted_final_result_needs_no_execution(pg_engine, status):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        session(c, uid, sid, execution_state="finished", status=status)
        validate(c)
        assert c.scalar(text("SELECT count(*) FROM study_session_intervals")) == 0


@pytest.mark.parametrize(
    "context",
    [
        None,
        "finished_early",
        "distracted",
        "tired",
        "interrupted",
        "changed_activity",
        "other",
    ],
)
def test_final_context_tokens_and_unicode_limit(pg_engine, context):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        session(
            c,
            uid,
            sid,
            execution_state="finished",
            status="cancelled",
            context=context,
            other_text="🚀" * 200 if context == "other" else None,
        )
        validate(c)


@pytest.mark.parametrize(
    "context,other",
    [
        ("other", None),
        ("other", ""),
        ("other", " "),
        ("other", "\t"),
        ("other", " x"),
        ("other", "x "),
        ("other", "é" * 201),
        (None, "text"),
        ("tired", "text"),
    ],
)
def test_context_text_pair_is_strict(pg_engine, context, other):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        with pytest.raises(IntegrityError), c.begin_nested():
            session(
                c,
                uid,
                sid,
                execution_state="finished",
                status="cancelled",
                context=context,
                other_text=other,
            )
