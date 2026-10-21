from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

import pytest
from activity_helpers import activity, migrate, owner_subject
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
def test_concurrent_deadlines_have_no_lost_events(pg_engine, isolation):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        activity(c, uid, sid)
    barrier = Barrier(2)

    def writer(_):
        try:
            with engine.connect().execution_options(isolation_level=isolation) as c:
                with c.begin():
                    c.execute(text("SET LOCAL statement_timeout='10s'"))
                    assert (
                        c.scalar(text("SELECT deadline_revision FROM activities")) == 0
                    )
                    barrier.wait(timeout=10)
                    c.execute(
                        text("UPDATE activities SET deadline=deadline+interval '1 day'")
                    )
            return "ok"
        except DBAPIError as exc:
            return exc.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = sorted(pool.map(writer, range(2)))
    assert results == (
        ["ok", "ok"] if isolation == "READ COMMITTED" else ["40001", "ok"]
    )
    with engine.begin() as c:
        events = c.execute(
            text("SELECT * FROM activity_deadline_events ORDER BY revision")
        ).all()
        row = c.execute(text("SELECT * FROM activities")).one()
        assert len(events) == row.deadline_revision == results.count("ok")
        assert events[0].previous_deadline == row.original_deadline
        assert events[-1].new_deadline == row.deadline
        for previous, current in zip(events, events[1:]):
            assert previous.new_deadline == current.previous_deadline
            assert previous.occurred_at <= current.occurred_at
        if isolation == "REPEATABLE READ":
            # Caller can retry the complete aborted transaction against fresh state.
            c.execute(text("UPDATE activities SET deadline=deadline+interval '1 day'"))
            assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 2


def test_runtime_updates_generate_history_without_history_write_privileges(pg_engine):
    engine, schema = pg_engine
    role = "activity_runtime_" + uuid4().hex
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        c.execute(text(f'CREATE ROLE "{role}" NOLOGIN'))
        c.execute(text(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"'))
        c.execute(text(f'GRANT SELECT,INSERT,UPDATE,DELETE ON activities TO "{role}"'))
        c.execute(text(f'GRANT USAGE,SELECT ON SEQUENCE activities_id_seq TO "{role}"'))
        c.execute(text(f'GRANT SELECT ON activity_deadline_events TO "{role}"'))
    try:
        with engine.begin() as c:
            c.execute(text(f'SET LOCAL ROLE "{role}"'))
            activity(c, uid, sid)
            c.execute(text("UPDATE activities SET deadline=deadline+interval '1 day'"))
            assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 1
            assert not c.scalar(
                text(
                    "SELECT has_function_privilege(current_user, "
                    "'cognova_record_activity_deadline()', 'EXECUTE')"
                )
            )
            for sql in [
                "INSERT INTO activity_deadline_events SELECT activity_id,revision+1,"
                "previous_deadline,new_deadline,event_type,occurred_at "
                "FROM activity_deadline_events",
                "UPDATE activity_deadline_events SET revision=revision+1",
                "DELETE FROM activity_deadline_events",
                "TRUNCATE activity_deadline_events",
                "ALTER TABLE activities ADD COLUMN surprise integer",
            ]:
                with pytest.raises(DBAPIError) as error, c.begin_nested():
                    c.execute(text(sql))
                assert error.value.orig.sqlstate == "42501"
            # A temporary trigger cannot be attached to the privileged function.
            c.execute(text("CREATE TEMP TABLE counterfeit (x integer)"))
            with pytest.raises(DBAPIError) as error, c.begin_nested():
                c.execute(
                    text(
                        "CREATE TRIGGER forge AFTER INSERT ON counterfeit "
                        "FOR EACH ROW EXECUTE FUNCTION "
                        "cognova_record_activity_deadline()"
                    )
                )
            assert error.value.orig.sqlstate == "42501"
            c.execute(text("DROP TABLE counterfeit"))
    finally:
        with engine.begin() as c:
            c.execute(text(f'DROP OWNED BY "{role}"'))
            c.execute(text(f'DROP ROLE "{role}"'))
