from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest
from alembic import command
from sqlalchemy import inspect, text
from sqlalchemy.exc import DBAPIError, IntegrityError

from cognova_database.runner import main, migration_config

pytestmark = pytest.mark.integration
PREVIOUS = "0003_onboarding_questionnaire"
HEAD = "0004_subjects"


def migrate(connection, revision=HEAD, *, down=False):
    config = migration_config()
    config.attributes["connection"] = connection
    (command.downgrade if down else command.upgrade)(config, revision)


def user(connection, email="subject@test.io"):
    return connection.scalar(
        text(
            "INSERT INTO users (name,email,password_hash) "
            "VALUES ('Test',:email,'fixture-hash') RETURNING id"
        ),
        {"email": email},
    )


def subject(connection, uid, **overrides):
    values = dict(
        user_id=uid,
        name="Matemáticas",
        status="active",
        difficulty="medium",
        color_base="blue",
        color_shade=500,
        active_slot=1,
    )
    values.update(overrides)
    return connection.scalar(
        text(
            "INSERT INTO subjects "
            "(user_id,name,status,difficulty,color_base,color_shade,active_slot) "
            "VALUES (:user_id,:name,:status,:difficulty,:color_base,:color_shade,"
            ":active_slot) RETURNING id"
        ),
        values,
    )


@pytest.mark.parametrize("start", [None, PREVIOUS])
def test_upgrade_preserves_all_existing_rows_and_repeats(pg_engine, start):
    engine, schema = pg_engine
    with engine.begin() as c:
        if start:
            migrate(c, "0002_auth_sessions")
            uid = c.scalar(
                text(
                    "INSERT INTO users "
                    "(name,email,password_hash,degree_program,semester,academic_goal) "
                    "VALUES ('Test','old@test.io','hash','Degree',1,'Goal') "
                    "RETURNING id"
                )
            )
            migrate(c, start)
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
        tables = (
            []
            if not start
            else [t for t in inspect(c).get_table_names() if t != "alembic_version"]
        )
        before = {t: c.execute(text(f"SELECT * FROM {t}")).all() for t in tables}
        migrate(c)
        migrate(c)
        assert c.scalar(text("SELECT current_schema()")) == schema
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        for table, rows in before.items():
            assert c.execute(text(f"SELECT * FROM {table}")).all() == rows
        inspector = inspect(c)
        assert inspector.get_pk_constraint("subjects")["constrained_columns"] == ["id"]
        fk = inspector.get_foreign_keys("subjects")[0]
        assert fk["referred_table"] == "users"
        assert fk["options"]["ondelete"] == "RESTRICT"
        assert {x["name"] for x in inspector.get_check_constraints("subjects")} == {
            "ck_subjects_name",
            "ck_subjects_status",
            "ck_subjects_difficulty",
            "ck_subjects_color_base",
            "ck_subjects_color_shade",
            "ck_subjects_active_slot",
        }
        assert {x["name"] for x in inspector.get_indexes("subjects")} == {
            "uq_subjects_user_name_lower",
            "uq_subjects_active_slot",
            "ix_subjects_user_status",
        }


@pytest.mark.parametrize(
    "bad",
    [
        {"name": ""},
        {"name": " "},
        {"name": "\t"},
        {"name": " x"},
        {"name": "x "},
        {"name": "x" * 21},
        {"name": None},
        {"status": "Activa"},
        {"status": None},
        {"difficulty": "Fácil"},
        {"difficulty": None},
        {"color_base": ""},
        {"color_base": "Blue"},
        {"color_base": "a" * 33},
        {"color_base": None},
        {"color_shade": -1},
        {"color_shade": 1001},
        {"color_shade": None},
        {"active_slot": None},
        {"active_slot": 0},
        {"active_slot": 6},
        {"status": "archived"},
        {"user_id": -1},
        {"user_id": None},
    ],
)
def test_invalid_subject_rejected(pg_engine, bad):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid = user(c)
        with pytest.raises(IntegrityError), c.begin_nested():
            subject(c, uid, **bad)


def test_name_scope_archive_reactivate_and_five_limit(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid = user(c)
        other = user(c, "other@test.io")
        for slot in range(1, 6):
            subject(c, uid, name=f"Materia {slot}", active_slot=slot)
        for slot in range(1, 6):
            with pytest.raises(IntegrityError), c.begin_nested():
                subject(c, uid, name="Sexta", active_slot=slot)
        for i in range(8):
            subject(c, uid, name=f"Archivada {i}", status="archived", active_slot=None)
        subject(c, other, name="Materia 1", difficulty="easy", color_shade=0)
        with pytest.raises(IntegrityError), c.begin_nested():
            subject(c, uid, name="ARCHIVADA 0", status="archived", active_slot=None)
        archived = c.execute(
            text(
                "UPDATE subjects SET status='archived',active_slot=NULL "
                "WHERE user_id=:uid AND active_slot=1 RETURNING id,created_at"
            ),
            {"uid": uid},
        ).one()
        replacement = subject(
            c, uid, name="🚀" * 20, difficulty="hard", color_shade=1000
        )
        with pytest.raises(IntegrityError), c.begin_nested():
            c.execute(
                text("UPDATE subjects SET status='active',active_slot=1 WHERE id=:id"),
                {"id": archived.id},
            )
        c.execute(
            text("UPDATE subjects SET status='archived',active_slot=NULL WHERE id=:id"),
            {"id": replacement},
        )
        restored = c.execute(
            text(
                "UPDATE subjects SET status='active',active_slot=1 "
                "WHERE id=:id RETURNING id,created_at"
            ),
            {"id": archived.id},
        ).one()
        assert restored == archived
        with pytest.raises(IntegrityError), c.begin_nested():
            c.execute(text("DELETE FROM users WHERE id=:uid"), {"uid": uid})
        with pytest.raises(IntegrityError), c.begin_nested():
            c.execute(
                text("UPDATE subjects SET user_id=:uid WHERE user_id=:other"),
                {"uid": uid, "other": other},
            )


@pytest.mark.parametrize("status", ["active", "archived"])
def test_downgrade_refuses_data_atomically(pg_engine, status):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid = user(c)
        subject(c, uid, status=status, active_slot=1 if status == "active" else None)
    with pytest.raises(DBAPIError, match="Downgrade blocked"), engine.begin() as c:
        migrate(c, PREVIOUS, down=True)
    with engine.begin() as c:
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
        assert c.scalar(text("SELECT count(*) FROM subjects")) == 1


def test_empty_downgrade_reupgrade_and_rollback(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c, PREVIOUS)
        uid = user(c)
    with engine.connect() as c:
        tx = c.begin()
        migrate(c)
        tx.rollback()
        assert "subjects" not in inspect(c).get_table_names()
    with engine.begin() as c:
        migrate(c)
        migrate(c, PREVIOUS, down=True)
        assert "subjects" not in inspect(c).get_table_names()
        assert c.scalar(text("SELECT id FROM users")) == uid
        migrate(c)
        subject(c, uid)


@pytest.mark.parametrize("isolation", ["READ COMMITTED", "REPEATABLE READ"])
@pytest.mark.parametrize("reactivate", [False, True])
def test_concurrent_last_slot_cannot_exceed_limit(pg_engine, isolation, reactivate):
    engine, _ = pg_engine
    ids = []
    with engine.begin() as c:
        migrate(c)
        uid = user(c)
        for slot in range(1, 5):
            subject(c, uid, name=f"Existing {slot}", active_slot=slot)
        if reactivate:
            ids = [
                subject(
                    c, uid, name=f"Candidate {i}", status="archived", active_slot=None
                )
                for i in range(2)
            ]
    barrier = Barrier(2)

    def writer(i):
        try:
            with engine.connect().execution_options(isolation_level=isolation) as c:
                with c.begin():
                    c.execute(text("SET LOCAL statement_timeout='10s'"))
                    assert (
                        c.scalar(
                            text("SELECT count(*) FROM subjects WHERE status='active'")
                        )
                        == 4
                    )
                    barrier.wait(timeout=10)
                    if reactivate:
                        c.execute(
                            text(
                                "UPDATE subjects SET status='active',active_slot=5 "
                                "WHERE id=:id"
                            ),
                            {"id": ids[i]},
                        )
                    else:
                        subject(c, uid, name=f"Candidate {i}", active_slot=5)
            return "ok"
        except IntegrityError as exc:
            return exc.orig.sqlstate

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(writer, range(2))) == ["23505", "ok"]
    with engine.connect() as c:
        assert (
            c.scalar(text("SELECT count(*) FROM subjects WHERE status='active'")) == 5
        )


def test_cli_explicit_subjects_revision_is_repeatable(pg_engine, monkeypatch):
    engine, schema = pg_engine
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", engine.url.render_as_string(hide_password=False))
    assert main(["upgrade", HEAD]) == 0
    assert main(["upgrade", HEAD]) == 0
    with engine.connect() as c:
        assert c.scalar(text("SELECT current_schema()")) == schema
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD


def test_bulk_insert_limit_rolls_back_entire_statement(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        uid = user(c)
        with pytest.raises(IntegrityError), c.begin_nested():
            c.execute(
                text(
                    "INSERT INTO subjects "
                    "(user_id,name,status,difficulty,color_base,color_shade,"
                    "active_slot) "
                    "SELECT :uid,'Bulk '||i,'active','easy','blue',500, "
                    "((i-1) % 5)+1 FROM generate_series(1,6) i"
                ),
                {"uid": uid},
            )
        assert c.scalar(text("SELECT count(*) FROM subjects")) == 0


def test_downgrade_does_not_cascade_future_dependencies(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as c:
        migrate(c)
        # Test-only dependent table; no activity schema is added by the migration.
        c.execute(
            text(
                "CREATE TABLE future_reference (subject_id integer "
                "REFERENCES subjects(id) ON DELETE RESTRICT)"
            )
        )
    with pytest.raises(DBAPIError), engine.begin() as c:
        migrate(c, PREVIOUS, down=True)
    with engine.connect() as c:
        assert {"subjects", "future_reference"} <= set(inspect(c).get_table_names())
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == HEAD
