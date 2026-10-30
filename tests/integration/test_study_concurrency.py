from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from activity_helpers import owner_subject
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from study_helpers import END, START, interval, migrate, session

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
@pytest.mark.parametrize("case", ["active_session", "open_interval", "overlap"])
def test_concurrent_execution_integrity(pg_engine, isolation, case):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        if case == "active_session":
            keys = [session(c, uid, sid), session(c, uid, sid)]
        else:
            key = session(
                c,
                uid,
                sid,
                execution_state="paused",
                start_at=START,
                actual_duration=300,
            )
            interval(c, key, end=START + timedelta(minutes=5))
            keys = [key, key]
    barrier = Barrier(2)

    def writer(index):
        try:
            with engine.connect().execution_options(isolation_level=isolation) as c:
                with c.begin():
                    c.execute(text("SET LOCAL statement_timeout='10s'"))
                    c.execute(text("SELECT * FROM study_sessions")).all()
                    barrier.wait(timeout=10)
                    key = keys[index]
                    if case != "overlap":
                        c.execute(
                            text(
                                "UPDATE study_sessions SET execution_state='running',"
                                "start_at=:start WHERE id=:key"
                            ),
                            {"key": key, "start": START},
                        )
                    interval(
                        c,
                        key,
                        start=START if case == "active_session" else END,
                        end=END + timedelta(minutes=5) if case == "overlap" else None,
                    )
            return "ok"
        except DBAPIError as exc:
            return exc.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(writer, range(2)))
    assert results.count("ok") == 1, results
    assert set(results) <= {"ok", "23505", "23P01", "40001"}, results
    if isolation == "REPEATABLE READ" and case != "active_session":
        assert "40001" in results
    with engine.connect() as c:
        assert c.scalar(text("SELECT count(*) FROM study_session_intervals")) == (
            1 if case == "active_session" else 2
        )
        assert c.scalar(
            text("SELECT count(*) FROM study_session_intervals WHERE ended_at IS NULL")
        ) == (0 if case == "overlap" else 1)
        # Neither metadata serialization nor validation computes timer duration.
        assert c.scalar(text("SELECT sum(actual_duration) FROM study_sessions")) == (
            0 if case == "active_session" else 300
        )
