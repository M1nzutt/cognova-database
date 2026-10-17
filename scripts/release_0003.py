"""Authorized 0002 -> 0003 release with atomic preservation checks.

DATABASE_URL and ENVIRONMENT must already be injected; no secrets or row contents
are emitted. Uses the repository runner configuration and injected-connection API.
"""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect, text

from cognova_database.configuration import database_url
from cognova_database.runner import migration_config

TABLES = ("users", "auth_sessions", "rate_limit_buckets")
TARGET = "0003_onboarding_questionnaire"


def require(condition, label):
    if not condition:
        raise RuntimeError(label)


def snapshot(connection):
    # Kept only in process memory; never written to evidence or logs.
    return {
        table: connection.scalars(
            text(f"SELECT row_to_json(t)::text FROM public.{table} t ORDER BY 1")
        ).all()
        for table in TABLES
    }


def verify(connection):
    inspector = inspect(connection)
    require(
        connection.scalars(text("SELECT version_num FROM public.alembic_version")).all()
        == [TARGET],
        "revision",
    )
    columns = {c["name"]: c for c in inspector.get_columns("users", schema="public")}
    require(
        all(
            columns[c]["nullable"]
            for c in ("degree_program", "semester", "academic_goal")
        ),
        "nullable_onboarding",
    )
    require(
        all(not columns[c]["nullable"] for c in ("name", "email", "password_hash")),
        "required_registration",
    )
    constraints = (
        connection.execute(
            text(
                "SELECT c.conname,c.contype,c.convalidated,c.confdeltype,"
                "t.relname AS table_name,pg_get_constraintdef(c.oid) AS definition "
                "FROM pg_constraint c JOIN pg_class t ON t.oid=c.conrelid "
                "JOIN pg_namespace n ON n.oid=t.relnamespace WHERE n.nspname='public' "
                "ORDER BY t.relname,c.conname"
            )
        )
        .mappings()
        .all()
    )
    names = {c["conname"]: c for c in constraints}
    for name in ("ck_users_name_registration", "ck_users_email_registration"):
        require(
            name in names and not names[name]["convalidated"], "registration_checks"
        )
    for name in (
        "ck_questionnaire_revision_positive",
        "ck_questionnaire_version_positive",
        "ck_questionnaire_ten_answers",
        "ck_users_semester_positive",
    ):
        require(name in names and names[name]["convalidated"], "validated_checks")
    for table, pk in (
        ("user_academic_goal_legacy", ["user_id"]),
        ("questionnaire_responses", ["user_id", "revision"]),
    ):
        require(
            inspector.get_pk_constraint(table, schema="public")["constrained_columns"]
            == pk,
            "primary_key",
        )
        require(
            any(
                c["table_name"] == table
                and c["contype"] == "f"
                and c["confdeltype"] == "r"
                for c in constraints
            ),
            "restrict_fk",
        )
    indexes = (
        connection.execute(
            text(
                "SELECT tablename,indexname,indexdef FROM pg_indexes "
                "WHERE schemaname='public' ORDER BY indexname"
            )
        )
        .mappings()
        .all()
    )
    index_names = {i["indexname"] for i in indexes}
    require(
        {
            "uq_users_email_lower",
            "ix_auth_sessions_user_id",
            "ix_auth_sessions_expires_at",
            "ix_rate_limit_buckets_expires_at",
            "questionnaire_responses_pkey",
            "user_academic_goal_legacy_pkey",
        }
        <= index_names,
        "indexes",
    )
    triggers = (
        connection.execute(
            text(
                "SELECT c.relname,t.tgname,t.tgenabled,"
                "pg_get_triggerdef(t.oid) AS definition "
                "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='public' AND NOT t.tgisinternal "
                "ORDER BY c.relname,t.tgname"
            )
        )
        .mappings()
        .all()
    )
    require(
        {(t["relname"], t["tgname"]) for t in triggers if t["tgenabled"] == "O"}
        == {
            ("questionnaire_responses", "questionnaire_append"),
            ("questionnaire_responses", "preserve_history"),
            ("questionnaire_responses", "preserve_history_truncate"),
            ("user_academic_goal_legacy", "preserve_history"),
            ("user_academic_goal_legacy", "preserve_history_truncate"),
        },
        "triggers",
    )
    valid = json.dumps({f"q{i}": "operational-validation" for i in range(1, 11)})
    require(
        connection.scalar(
            text(
                "SELECT public.cognova_valid_questionnaire_answers("
                "CAST(:answers AS jsonb))"
            ),
            {"answers": valid},
        )
        is True,
        "validator_valid",
    )
    require(
        connection.scalar(
            text("SELECT public.cognova_valid_questionnaire_answers('{}'::jsonb)")
        )
        is False,
        "validator_invalid",
    )
    permissions = {}
    for table in (*TABLES, "user_academic_goal_legacy", "questionnaire_responses"):
        permissions[table] = dict(
            connection.execute(
                text(
                    "SELECT has_table_privilege(current_user,:table,'SELECT') "
                    "AS select, "
                    "has_table_privilege(current_user,:table,'INSERT') AS insert, "
                    "has_table_privilege(current_user,:table,'UPDATE') AS update, "
                    "has_table_privilege(current_user,:table,'DELETE') AS delete, "
                    "has_table_privilege(current_user,:table,'TRUNCATE') AS truncate"
                ),
                {"table": "public." + table},
            )
            .mappings()
            .one()
        )
        require(permissions[table]["select"], "migrator_select")
    require(
        connection.scalar(
            text(
                "SELECT has_function_privilege(current_user,"
                "'public.cognova_valid_questionnaire_answers(jsonb)','EXECUTE')"
            )
        ),
        "function_execute",
    )
    return {
        "revision": TARGET,
        "constraints": [dict(c) for c in constraints],
        "indexes": [dict(i) for i in indexes],
        "triggers": [dict(t) for t in triggers],
        "migrator_permissions": permissions,
        "validator_read_only_checks": "passed",
        "runtime_identity": "not_confirmed",
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    stage = "target"
    committed = False
    try:
        url = database_url()
        require(
            url.host.split(".")[0] == "dpg-db2iojc9v7es7387i2ig-a"
            and url.host.endswith(".render.com")
            and url.database == "cognova",
            "target",
        )
        engine = create_engine(
            url, hide_parameters=True, connect_args={"connect_timeout": 10}
        )
        with engine.begin() as connection:
            stage = "preflight_and_locks"
            connection.execute(text("SET LOCAL search_path=public"))
            connection.execute(text("SET LOCAL lock_timeout='30s'"))
            connection.execute(text("SET LOCAL statement_timeout='120s'"))
            connection.execute(text("SELECT pg_advisory_xact_lock(1943187001)"))
            connection.execute(
                text(
                    "LOCK TABLE public.users, public.auth_sessions, "
                    "public.rate_limit_buckets, "
                    "public.alembic_version IN ACCESS EXCLUSIVE MODE"
                )
            )
            require(
                connection.scalar(
                    text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
                )
                is True,
                "tls",
            )
            require(
                connection.scalars(
                    text("SELECT version_num FROM public.alembic_version")
                ).all()
                == ["0002_auth_sessions"],
                "before_revision",
            )
            before = snapshot(connection)
            stage = "official_runner_upgrade"
            config = migration_config()
            config.attributes["connection"] = connection
            command.upgrade(config, TARGET)
            stage = "atomic_preservation"
            require(before == snapshot(connection), "row_contents_changed")
            require(
                connection.scalar(
                    text(
                        "SELECT count(*) FROM public.users u FULL JOIN "
                        "public.user_academic_goal_legacy l ON l.user_id=u.id "
                        "WHERE u.id IS NULL OR l.user_id IS NULL "
                        "OR u.academic_goal IS DISTINCT FROM l.academic_goal"
                    )
                )
                == 0,
                "legacy_copy",
            )
            stage = "atomic_schema_verification"
            report = verify(connection)
            report.update(
                revision_before="0002_auth_sessions",
                counts_before={t: len(rows) for t, rows in before.items()},
                rows_preserved={t: True for t in TABLES},
                academic_goal_preserved=True,
                tls=True,
                preservation_scope="all rows/columns under exclusive transaction locks",
            )
        committed = True
        stage = "post_commit_read_only"
        with engine.connect() as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout='15000ms'"))
            verify(connection)
            report["counts_after_commit"] = {
                t: connection.scalar(text(f"SELECT count(*) FROM public.{t}"))
                for t in (
                    *TABLES,
                    "user_academic_goal_legacy",
                    "questionnaire_responses",
                )
            }
        engine.dispose()
        report["committed"] = True
        report["post_commit_checks"] = "passed"
        report["observed_at_utc"] = datetime.now(timezone.utc).isoformat()
        args.evidence.write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    k: v
                    for k, v in report.items()
                    if k
                    not in (
                        "constraints",
                        "indexes",
                        "triggers",
                        "migrator_permissions",
                    )
                }
            )
        )
        return 0
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "stage": stage,
                    "committed": committed,
                    "exception_type": type(error).__name__,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
