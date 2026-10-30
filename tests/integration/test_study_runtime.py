from uuid import uuid4

import pytest
from activity_helpers import owner_subject
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from study_helpers import END, migrate, running, session, validate

pytestmark = pytest.mark.integration


def test_least_privilege_runtime_and_deferred_validation(pg_engine):
    engine, schema = pg_engine
    role = "study_runtime_" + uuid4().hex
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        c.execute(text(f'CREATE ROLE "{role}" NOLOGIN'))
        c.execute(text(f'GRANT USAGE ON SCHEMA "{schema}" TO "{role}"'))
        c.execute(
            text(f'GRANT SELECT,INSERT,UPDATE,DELETE ON study_sessions TO "{role}"')
        )
        c.execute(
            text(f'GRANT SELECT,INSERT,UPDATE ON study_session_intervals TO "{role}"')
        )
        c.execute(
            text(
                "GRANT USAGE,SELECT ON SEQUENCE study_sessions_id_seq,"
                f'study_session_intervals_id_seq TO "{role}"'
            )
        )
    try:
        with engine.begin() as c:
            c.execute(text(f'SET LOCAL ROLE "{role}"'))
            disposable = session(c, uid, sid)
            c.execute(
                text("DELETE FROM study_sessions WHERE id=:key"), {"key": disposable}
            )
            running(c, uid, sid)
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
            assert not c.scalar(
                text(
                    "SELECT has_schema_privilege(current_user,"
                    "current_schema(),'CREATE')"
                )
            )
            for function in [
                "cognova_prepare_study_session",
                "cognova_prepare_study_interval",
                "cognova_validate_study_execution",
            ]:
                assert not c.scalar(
                    text("SELECT has_function_privilege(current_user,:fn,'EXECUTE')"),
                    {"fn": function + "()"},
                )
            assert c.scalar(
                text(
                    "SELECT has_table_privilege(current_user,'study_sessions',"
                    "'SELECT,INSERT,UPDATE,DELETE')"
                )
            )
            for sql in [
                "DELETE FROM study_session_intervals",
                "TRUNCATE study_session_intervals",
                "ALTER TABLE study_sessions ADD COLUMN surprise integer",
                "CREATE TABLE surprise (id integer)",
                "UPDATE alembic_version SET version_num='fake'",
                "DELETE FROM activity_deadline_events",
                "UPDATE user_academic_goal_legacy SET user_id=user_id",
            ]:
                with pytest.raises(DBAPIError) as error, c.begin_nested():
                    c.execute(text(sql))
                assert error.value.orig.sqlstate == "42501"
        with engine.connect() as c:
            assert c.scalar(text("SELECT count(*) FROM study_sessions")) == 1
            assert c.scalar(text("SELECT count(*) FROM study_session_intervals")) == 1
            assert c.scalar(text("SELECT actual_duration FROM study_sessions")) == 1800
            assert not c.scalar(
                text(
                    "SELECT EXISTS (SELECT 1 FROM pg_class c CROSS JOIN LATERAL "
                    "aclexplode(coalesce(c.relacl,acldefault('r',c.relowner))) a "
                    "WHERE c.relnamespace=current_schema()::regnamespace "
                    "AND c.relname IN ('study_sessions','study_session_intervals',"
                    "'study_sessions_id_seq','study_session_intervals_id_seq') "
                    "AND a.grantee=0)"
                )
            )
    finally:
        with engine.begin() as c:
            c.execute(text(f'DROP OWNED BY "{role}"'))
            c.execute(text(f'DROP ROLE "{role}"'))
