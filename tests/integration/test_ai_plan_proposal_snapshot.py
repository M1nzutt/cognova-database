"""Exercise the additive AI snapshot migration on disposable PostgreSQL."""

import json

import pytest
from plan_helpers import migrate, owner_subject, plan
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

pytestmark = pytest.mark.integration

OLD = "0007_study_plans_and_challenges"
NEW = "0008_ai_plan_proposal_snapshot"


def _set_snapshot(connection, plan_id, value):
    connection.execute(
        text(
            "UPDATE study_plans SET ai_proposal_snapshot=CAST(:snapshot AS jsonb) "
            "WHERE id=:id"
        ),
        {"snapshot": json.dumps(value), "id": plan_id},
    )


def test_upgrade_preserves_existing_plan_and_earlier_data(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, OLD)
        user_id, subject_id = owner_subject(connection)
        plan_id = plan(connection, user_id, source="manual")
        before = {
            table: connection.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all()
            for table in inspect(connection).get_table_names()
            if table not in {"alembic_version", "study_plans"}
        }
        old_plan = connection.execute(
            text("SELECT id,user_id,name,objective,status,source FROM study_plans")
        ).one()
        assert "ai_proposal_snapshot" not in {
            column["name"] for column in inspect(connection).get_columns("study_plans")
        }

        migrate(connection, NEW)
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == NEW
        columns = {c["name"]: c for c in inspect(connection).get_columns("study_plans")}
        assert columns["ai_proposal_snapshot"]["nullable"]
        assert (
            connection.scalar(
                text("SELECT ai_proposal_snapshot FROM study_plans WHERE id=:id"),
                {"id": plan_id},
            )
            is None
        )
        assert (
            connection.execute(
                text("SELECT id,user_id,name,objective,status,source FROM study_plans")
            ).one()
            == old_plan
        )
        assert (
            connection.scalar(
                text("SELECT count(*) FROM subjects WHERE id=:id"), {"id": subject_id}
            )
            == 1
        )
        for table, rows in before.items():
            assert (
                connection.execute(text(f"SELECT * FROM {table} ORDER BY 1")).all()
                == rows
            )


def test_structured_snapshot_and_exact_utf8_size_limit(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, NEW)
        user_id, subject_id = owner_subject(connection)
        plan_id = plan(connection, user_id)
        proposal = {
            "schema_version": 1,
            "model": "gemini-model",
            "generated_at": "2030-01-01T12:00:00Z",
            "explanation": "Plan visible para preparar el examen",
            "reasoning_summary": "Se priorizan sesiones antes del examen",
            "plan": {
                "name": "Preparación",
                "objective": "Preparar el examen",
                "start_date": "2030-01-01",
                "end_date": "2030-01-08",
                "subject_ids": [subject_id],
                "activity_ids": [],
                "session_ids": [],
            },
            "challenges": [
                {
                    "title": "Repasar materia",
                    "objective": "Completar 30 minutos",
                    "explanation": "Ayuda con el examen",
                    "evidence": "Materia incluida en el plan",
                    "target_type": "study_minutes",
                    "target_id": subject_id,
                    "measurable_condition": {"minutes": 30},
                    "start_date": "2030-01-01",
                    "end_date": "2030-01-08",
                }
            ],
        }
        _set_snapshot(connection, plan_id, proposal)
        assert (
            connection.scalar(
                text("SELECT ai_proposal_snapshot FROM study_plans WHERE id=:id"),
                {"id": plan_id},
            )
            == proposal
        )
        _set_snapshot(connection, plan_id, {"text": "é" * 100})
        byte_count = connection.scalar(
            text("SELECT octet_length(ai_proposal_snapshot::text) FROM study_plans")
        )
        assert byte_count > 100

        for invalid in ([], "string", 7, True, None, {"text": "é" * 16385}):
            with pytest.raises(IntegrityError), connection.begin_nested():
                _set_snapshot(connection, plan_id, invalid)
        for length in (32768, 32769):
            # JSONB serializes this ASCII object as {"x": "..."}: eight bytes overhead.
            value = {"x": "a" * (length - 9)}
            serialized = json.dumps(value)
            assert len(serialized.encode()) == length
            if length == 32768:
                _set_snapshot(connection, plan_id, value)
            else:
                with pytest.raises(IntegrityError), connection.begin_nested():
                    _set_snapshot(connection, plan_id, value)


def test_downgrade_and_reupgrade_keep_0007_rows(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, OLD)
        user_id, _ = owner_subject(connection)
        plan_id = plan(connection, user_id, source="manual")
        migrate(connection, NEW)
        _set_snapshot(connection, plan_id, {"explanation": "Visible"})
        migrate(connection, OLD, down=True)
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == OLD
        assert "ai_proposal_snapshot" not in {
            c["name"] for c in inspect(connection).get_columns("study_plans")
        }
        assert connection.scalar(text("SELECT source FROM study_plans")) == "manual"
        migrate(connection, NEW)
        assert (
            connection.scalar(text("SELECT ai_proposal_snapshot FROM study_plans"))
            is None
        )
        assert connection.scalar(text("SELECT count(*) FROM users")) == 1


def test_snapshot_keeps_existing_ownership_and_permissions(pg_engine):
    engine, _ = pg_engine
    with engine.begin() as connection:
        migrate(connection, NEW)
        user_id, _ = owner_subject(connection)
        plan_id = plan(connection, user_id)
        _set_snapshot(connection, plan_id, {"explanation": "Visible"})
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM pg_constraint "
                    "WHERE conrelid='study_plans'::regclass "
                    "AND conname='fk_study_plans_user' AND confdeltype='r'"
                )
            )
            == 1
        )
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM pg_constraint "
                    "WHERE conrelid='study_plans'::regclass "
                    "AND conname='ck_study_plans_ai_proposal_snapshot' AND convalidated"
                )
            )
            == 1
        )
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM pg_class AS c CROSS JOIN LATERAL "
                    "aclexplode(COALESCE(c.relacl, "
                    "acldefault('r', c.relowner))) AS acl "
                    "WHERE c.oid='study_plans'::regclass AND acl.grantee=0"
                )
            )
            == 0
        )
        assert (
            connection.scalar(
                text(
                    "SELECT COUNT(*) FROM pg_class AS c CROSS JOIN LATERAL "
                    "aclexplode(COALESCE(c.relacl, "
                    "acldefault('r', c.relowner))) AS acl "
                    "WHERE c.oid='study_plans'::regclass AND acl.grantee<>c.relowner"
                )
            )
            == 0
        )
        with pytest.raises(IntegrityError), connection.begin_nested():
            connection.execute(text("DELETE FROM users WHERE id=:id"), {"id": user_id})
