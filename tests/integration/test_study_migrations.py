import pytest
from activity_helpers import activity, owner_subject
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError
from study_helpers import HEAD, PREVIOUS, migrate, running, session

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("existing", [False, True])
def test_upgrade_empty_or_from_0005_preserves_every_prior_table(pg_engine, existing):
    engine, schema = pg_engine
    with engine.begin() as c:
        before = {}
        if existing:
            migrate(c, "0002_auth_sessions")
            c.execute(
                text(
                    "INSERT INTO users (name,email,password_hash,degree_program,"
                    "semester,academic_goal) VALUES "
                    "('Legacy','legacy@test.io','fixture','Degree',2,'Preserved goal')"
                )
            )
            migrate(c, PREVIOUS)
            uid, sid = owner_subject(c)
            activity(c, uid, sid)
            c.execute(text("UPDATE activities SET deadline=deadline+interval '1 day'"))
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
                    "('00000000-0000-0000-0000-000000000001',:uid,'fixture','fixture',"
                    "now(),now()+interval '1 day',now(),NULL)"
                ),
                {"uid": uid},
            )
            c.execute(text("INSERT INTO rate_limit_buckets VALUES ('fixture',1,now())"))
            before = {
                t: c.execute(text(f"SELECT * FROM {t} ORDER BY 1")).all()
                for t in inspect(c).get_table_names()
                if t != "alembic_version"
            }
            constraints = inspect(c).get_check_constraints("activities")
        migrate(c)
        migrate(c)
        assert c.scalar(text("SELECT current_schema()")) == schema
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        for table, rows in before.items():
            assert c.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all() == rows
        if existing:
            assert inspect(c).get_check_constraints("activities") == constraints
            # Existing activity trigger remains functional.
            c.execute(text("UPDATE activities SET deadline=deadline-interval '2 days'"))
            assert c.scalar(text("SELECT count(*) FROM activity_deadline_events")) == 2
        assert c.scalar(text("SELECT count(*) FROM study_sessions")) == 0
        assert c.scalar(text("SELECT count(*) FROM study_session_intervals")) == 0


@pytest.mark.parametrize("state", ["planned", "running", "cancelled"])
def test_downgrade_refuses_all_session_data(pg_engine, state):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid, sid = owner_subject(c)
        if state == "running":
            running(c, uid, sid)
        else:
            session(
                c,
                uid,
                sid,
                **(
                    {"execution_state": "finished", "status": state}
                    if state == "cancelled"
                    else {}
                ),
            )
        before = c.execute(text("SELECT * FROM study_sessions")).all()
        evidence = c.execute(text("SELECT * FROM study_session_intervals")).all()
    with pytest.raises(DBAPIError, match="Downgrade blocked"), engine.begin() as c:
        migrate(c, PREVIOUS, down=True)
    with engine.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        assert c.execute(text("SELECT * FROM study_sessions")).all() == before
        assert (
            c.execute(text("SELECT * FROM study_session_intervals")).all() == evidence
        )


def test_empty_downgrade_and_reupgrade_preserve_activities(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c, PREVIOUS)
        uid, sid = owner_subject(c)
        activity(c, uid, sid)
        before = c.execute(text("SELECT * FROM activities")).all()
        migrate(c)
        migrate(c, PREVIOUS, down=True)
        assert c.execute(text("SELECT * FROM activities")).all() == before
        assert "study_sessions" not in inspect(c).get_table_names()
        assert "study_session_intervals" not in inspect(c).get_table_names()
        assert "uq_activities_user_subject_id" not in {
            item["name"] for item in inspect(c).get_unique_constraints("activities")
        }
        assert (
            c.scalar(
                text(
                    "SELECT count(*) FROM pg_proc WHERE pronamespace="
                    "current_schema()::regnamespace AND proname LIKE 'cognova_%study%'"
                )
            )
            == 0
        )
        migrate(c)
        session(c, uid, sid, activity_id=c.scalar(text("SELECT id FROM activities")))


def test_upgrade_ddl_rolls_back_and_future_dependencies_block_downgrade(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c, PREVIOUS)
        uid, sid = owner_subject(c)
        activity(c, uid, sid)
    with engine.connect() as c:
        tx = c.begin()
        migrate(c)
        tx.rollback()
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == PREVIOUS
        assert "study_sessions" not in inspect(c).get_table_names()
        assert "uq_activities_user_subject_id" not in {
            item["name"] for item in inspect(c).get_unique_constraints("activities")
        }
    with engine.begin() as c:
        migrate(c)
        c.execute(
            text("CREATE VIEW future_study_dependency AS SELECT * FROM study_sessions")
        )
    with pytest.raises(DBAPIError), engine.begin() as c:
        migrate(c, PREVIOUS, down=True)
    with engine.connect() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        assert "study_session_intervals" in inspect(c).get_table_names()
        assert c.scalar(text("SELECT count(*) FROM activities")) == 1
