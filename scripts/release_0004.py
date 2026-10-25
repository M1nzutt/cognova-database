"""Authorized subjects release; secrets and row contents never enter evidence."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import DBAPIError

from cognova_database.configuration import database_url
from cognova_database.runner import migration_config

BEFORE = "0003_onboarding_questionnaire"
TARGET = "0004_subjects"
TABLES = (
    "users",
    "auth_sessions",
    "rate_limit_buckets",
    "user_academic_goal_legacy",
    "questionnaire_responses",
)
ROLE = "cognova_runtime"


def require(condition, label):
    if not condition:
        raise RuntimeError(label)


def snapshot(connection):
    return {
        table: connection.scalars(
            text(f"SELECT row_to_json(t)::text FROM public.{table} t ORDER BY 1")
        ).all()
        for table in TABLES
    }


def structure(connection, tables):
    inspector = inspect(connection)
    return {
        table: {
            "columns": [
                {**column, "type": str(column["type"])}
                for column in inspector.get_columns(table, schema="public")
            ],
            "checks": inspector.get_check_constraints(table, schema="public"),
            "indexes": inspector.get_indexes(table, schema="public"),
            "pk": inspector.get_pk_constraint(table, schema="public"),
            "fk": inspector.get_foreign_keys(table, schema="public"),
            "unique": inspector.get_unique_constraints(table, schema="public"),
        }
        for table in tables
    }


def triggers(connection):
    return [
        dict(row)
        for row in connection.execute(
            text(
                "SELECT c.relname,t.tgname,t.tgenabled,pg_get_triggerdef(t.oid) def "
                "FROM pg_trigger t JOIN pg_class c ON c.oid=t.tgrelid "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "WHERE n.nspname='public' AND NOT t.tgisinternal ORDER BY 1,2"
            )
        ).mappings()
    ]


def runtime_permissions(connection, subjects=True):
    role = dict(
        connection.execute(
            text(
                "SELECT rolname,rolsuper,rolcreaterole,rolcreatedb,rolcanlogin,"
                "rolreplication,rolbypassrls FROM pg_roles WHERE rolname=:role"
            ),
            {"role": ROLE},
        )
        .mappings()
        .one()
    )
    require(role["rolcanlogin"], "runtime_login")
    require(
        not any(v for k, v in role.items() if k not in ("rolname", "rolcanlogin")),
        "runtime_elevated",
    )
    memberships = connection.scalars(
        text(
            "SELECT rolname FROM pg_roles WHERE rolname<>:role "
            "AND pg_has_role(:role,oid,'MEMBER') ORDER BY rolname"
        ),
        {"role": ROLE},
    ).all()
    require(not memberships, "runtime_memberships")
    schema_create = connection.scalars(
        text(
            "SELECT nspname FROM pg_namespace WHERE "
            "has_schema_privilege(:role,oid,'CREATE')"
        ),
        {"role": ROLE},
    ).all()
    require(not schema_create, "runtime_schema_create")
    require(
        not connection.scalar(
            text("SELECT has_database_privilege(:role,current_database(),'CREATE')"),
            {"role": ROLE},
        ),
        "runtime_database_create",
    )
    owned = connection.scalars(
        text(
            "SELECT c.relname FROM pg_class c JOIN pg_roles r ON r.oid=c.relowner "
            "WHERE r.rolname=:role"
        ),
        {"role": ROLE},
    ).all()
    require(not owned, "runtime_ownership")
    require(
        connection.scalar(
            text(
                "SELECT count(*) FROM pg_proc p "
                "JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='public' AND p.prosecdef "
                "AND has_function_privilege(:role,p.oid,'EXECUTE')"
            ),
            {"role": ROLE},
        )
        == 0,
        "runtime_security_definer",
    )
    expected = {
        "alembic_version": {"SELECT"},
        "user_academic_goal_legacy": {"SELECT"},
        "questionnaire_responses": {"SELECT", "INSERT"},
    }
    if subjects:
        expected["subjects"] = {"SELECT", "INSERT", "UPDATE"}
    permissions = {}
    for table, allowed in expected.items():
        permissions[table] = {}
        for privilege in (
            "SELECT",
            "INSERT",
            "UPDATE",
            "DELETE",
            "TRUNCATE",
            "REFERENCES",
            "TRIGGER",
        ):
            value = connection.scalar(
                text("SELECT has_table_privilege(:role,:table,:privilege)"),
                {"role": ROLE, "table": "public." + table, "privilege": privilege},
            )
            require(value == (privilege in allowed), "runtime_table_privileges")
            permissions[table][privilege] = value
    for privilege in ("SELECT", "UPDATE"):
        require(
            connection.scalar(
                text("SELECT has_table_privilege(:role,'public.users',:privilege)"),
                {"role": ROLE, "privilege": privilege},
            ),
            "runtime_users_lock",
        )
    if subjects:
        for privilege in ("USAGE", "SELECT", "UPDATE"):
            require(
                connection.scalar(
                    text(
                        "SELECT has_sequence_privilege("
                        ":role,'public.subjects_id_seq',:p)"
                    ),
                    {"role": ROLE, "p": privilege},
                )
                == (privilege != "UPDATE"),
                "runtime_sequence",
            )
    temporary_ddl = connection.scalar(
        text("SELECT has_database_privilege(:role,current_database(),'TEMP')"),
        {"role": ROLE},
    )
    return {
        "role": role,
        "memberships": memberships,
        "owned_objects": owned,
        "schema_create": schema_create,
        "temporary_ddl_existing": temporary_ddl,
        "table_privileges": permissions,
    }


def verify(connection):
    require(
        connection.scalars(text("SELECT version_num FROM public.alembic_version")).all()
        == [TARGET],
        "revision_after",
    )
    subjects = structure(connection, ("subjects",))["subjects"]
    require(
        {c["name"] for c in subjects["checks"]}
        == {
            "ck_subjects_name",
            "ck_subjects_status",
            "ck_subjects_difficulty",
            "ck_subjects_color_base",
            "ck_subjects_color_shade",
            "ck_subjects_active_slot",
        },
        "subjects_checks",
    )
    require(subjects["pk"]["constrained_columns"] == ["id"], "subjects_pk")
    require(
        len(subjects["fk"]) == 1
        and subjects["fk"][0]["referred_table"] == "users"
        and subjects["fk"][0]["constrained_columns"] == ["user_id"]
        and subjects["fk"][0]["options"]["ondelete"] == "RESTRICT",
        "subjects_fk",
    )
    require(
        {i["name"] for i in subjects["indexes"]}
        == {
            "uq_subjects_user_name_lower",
            "uq_subjects_active_slot",
            "ix_subjects_user_status",
        },
        "subjects_indexes",
    )
    require(
        connection.scalar(
            text(
                "SELECT count(*) FROM pg_index "
                "WHERE indrelid='public.subjects'::regclass "
                "AND (NOT indisvalid OR NOT indisready)"
            )
        )
        == 0,
        "subjects_index_validity",
    )
    require(
        connection.scalar(
            text(
                "SELECT count(*) FROM pg_constraint "
                "WHERE conrelid='public.subjects'::regclass "
                "AND NOT convalidated"
            )
        )
        == 0,
        "subjects_constraints_validated",
    )
    return {
        "revision": TARGET,
        "subjects": subjects,
        "triggers": triggers(connection),
        "runtime": runtime_permissions(connection),
    }


def runtime_probes(connection):
    # Some managed migrators have ADMIN but deliberately not SET on runtime.
    # Enable SET only inside a savepoint and roll back the entire role grant.
    savepoint = connection.begin_nested()
    try:
        if not connection.scalar(
            text("SELECT pg_has_role(current_user,'cognova_runtime','SET')")
        ):
            migrator = connection.scalar(text("SELECT current_user"))
            quoted = connection.dialect.identifier_preparer.quote(migrator)
            connection.execute(
                text(f"GRANT cognova_runtime TO {quoted} WITH INHERIT FALSE, SET TRUE")
            )
        return _runtime_probes(connection)
    finally:
        savepoint.rollback()


def _runtime_probes(connection):
    # EXPLAIN without ANALYZE checks actual role authorization without writing rows
    # or advancing sequences. Behavioral/concurrency tests run only locally.
    connection.execute(text("SET LOCAL ROLE cognova_runtime"))
    require(connection.scalar(text("SELECT current_user")) == ROLE, "set_role")
    connection.execute(text("SELECT * FROM public.subjects LIMIT 0"))
    for sql in (
        "EXPLAIN INSERT INTO public.subjects "
        "(user_id,name,status,difficulty,color_base,color_shade,active_slot) "
        "VALUES (0,'permission probe','active','easy','blue',100,1)",
        "EXPLAIN UPDATE public.subjects SET name=name WHERE false",
        "EXPLAIN SELECT id FROM public.users WHERE false FOR UPDATE",
    ):
        connection.execute(text(sql))
    denied = (
        "DELETE FROM public.subjects WHERE false",
        "ALTER TABLE public.subjects ADD COLUMN runtime_probe integer",
        "CREATE TABLE public.cognova_runtime_probe (id integer)",
        "UPDATE public.alembic_version SET version_num=version_num WHERE false",
        "DELETE FROM public.alembic_version WHERE false",
        "UPDATE public.questionnaire_responses SET revision=revision WHERE false",
        "DELETE FROM public.questionnaire_responses WHERE false",
        "UPDATE public.user_academic_goal_legacy SET user_id=user_id WHERE false",
        "DELETE FROM public.user_academic_goal_legacy WHERE false",
    )
    for sql in denied:
        savepoint = connection.begin_nested()
        try:
            connection.execute(text(sql))
        except DBAPIError as error:
            require(
                getattr(error.orig, "sqlstate", None) == "42501",
                "runtime_expected_permission_denied",
            )
        else:
            raise RuntimeError("runtime_unexpected_permission")
        finally:
            savepoint.rollback()
    connection.execute(text("RESET ROLE"))
    return {
        "select": "passed",
        "insert_update": "EXPLAIN authorized, no writes",
        "denied_statements": len(denied),
        "ddl_history_delete": "42501",
    }


def apply(connection):
    connection.execute(text("SET LOCAL search_path=public"))
    connection.execute(text("SET LOCAL lock_timeout='30s'"))
    connection.execute(text("SET LOCAL statement_timeout='120s'"))
    connection.execute(text("SELECT pg_advisory_xact_lock(1943187001)"))
    connection.execute(
        text(
            "LOCK TABLE public.alembic_version,"
            + ",".join("public." + t for t in TABLES)
            + " IN ACCESS EXCLUSIVE MODE"
        )
    )
    require(
        connection.scalars(text("SELECT version_num FROM public.alembic_version")).all()
        == [BEFORE],
        "revision_before",
    )
    runtime_permissions(connection, subjects=False)
    before = snapshot(connection)
    old_structure = structure(connection, TABLES)
    old_triggers = triggers(connection)
    config = migration_config()
    config.attributes["connection"] = connection
    command.upgrade(config, TARGET)
    connection.execute(
        text("GRANT SELECT,INSERT,UPDATE ON public.subjects TO cognova_runtime")
    )
    connection.execute(
        text("GRANT USAGE,SELECT ON SEQUENCE public.subjects_id_seq TO cognova_runtime")
    )
    require(snapshot(connection) == before, "row_contents_changed")
    require(structure(connection, TABLES) == old_structure, "old_schema_changed")
    require(triggers(connection) == old_triggers, "old_triggers_changed")
    report = verify(connection)
    report["runtime_probes"] = runtime_probes(connection)
    report.update(
        revision_before=BEFORE,
        rows_preserved={t: True for t in TABLES},
        counts_before={t: len(rows) for t, rows in before.items()},
        old_schema_and_triggers_preserved=True,
        preservation_scope="all rows/columns under exclusive locks",
    )
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--backup-evidence", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    stage, committed = "backup_gate", False
    try:
        backup = json.loads(args.backup_evidence.read_text(encoding="utf-8"))
        require(
            all(
                backup.get(k) == "passed"
                for k in (
                    "restore_rehearsal",
                    "encryption_roundtrip",
                    "pg_restore_list",
                    "full_archive_decode",
                    "download_verification",
                )
            ),
            "backup_verification",
        )
        require(
            backup["revision_before"] == backup["revision_after"] == BEFORE,
            "backup_revision",
        )
        age = datetime.now(timezone.utc) - datetime.fromisoformat(
            backup["verified_at_utc"]
        )
        require(0 <= age.total_seconds() < 86400, "backup_freshness")
        stage = "target"
        url = database_url()
        require(
            url.host.split(".")[0] == "dpg-db2iojc9v7es7387i2ig-a"
            and url.host.endswith(".render.com")
            and url.database == "cognova",
            "production_target",
        )
        engine = create_engine(
            url, hide_parameters=True, connect_args={"connect_timeout": 10}
        )
        stage = "atomic_release"
        with engine.begin() as connection:
            require(
                connection.scalar(
                    text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
                ),
                "tls",
            )
            report = apply(connection)
        committed = True
        stage = "post_commit_read_only"
        with engine.connect() as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout='15000ms'"))
            verify(connection)
            report["counts_after_commit"] = {
                t: connection.scalar(text(f"SELECT count(*) FROM public.{t}"))
                for t in (*TABLES, "subjects")
            }
        engine.dispose()
        report.update(
            committed=True,
            post_commit_checks="passed",
            tls=True,
            backup_run=backup["run_id"],
            observed_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        args.evidence.write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        print(
            json.dumps(
                {
                    k: v
                    for k, v in report.items()
                    if k not in ("subjects", "triggers", "runtime")
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
