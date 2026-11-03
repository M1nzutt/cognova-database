"""Atomic 0007 release runner. Production use requires a separate authorization."""

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, text

from cognova_database.configuration import database_url
from cognova_database.runner import migration_config
from scripts.release_0004 import require, runtime_permissions, structure, triggers

BEFORE = "0006_study_sessions"
TARGET = "0007_study_plans_and_challenges"
ROLE = "cognova_runtime"
TABLES = (
    "users",
    "auth_sessions",
    "rate_limit_buckets",
    "user_academic_goal_legacy",
    "questionnaire_responses",
    "subjects",
    "activities",
    "activity_deadline_events",
    "study_sessions",
    "study_session_intervals",
)
NEW_TABLES = (
    "study_plans",
    "study_plan_subjects",
    "study_plan_activities",
    "study_plan_sessions",
    "study_plan_decisions",
    "study_challenges",
)
NEW_SEQUENCES = (
    "study_plans_id_seq",
    "study_plan_decisions_id_seq",
    "study_challenges_id_seq",
)
ADDED_SESSION_KEYS = (
    "uq_study_sessions_user_subject_id",
    "uq_study_sessions_user_subject_activity_id",
)
PRIVILEGES = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "TRUNCATE",
    "REFERENCES",
    "TRIGGER",
)
ALLOWED = {
    "study_plans": {"SELECT", "INSERT", "UPDATE", "DELETE"},
    "study_plan_subjects": {"SELECT", "INSERT", "DELETE"},
    "study_plan_activities": {"SELECT", "INSERT", "DELETE"},
    "study_plan_sessions": {"SELECT", "INSERT", "DELETE"},
    "study_plan_decisions": {"SELECT", "INSERT"},
    "study_challenges": {"SELECT", "INSERT", "UPDATE"},
}
CONTRACT = (
    Path(__file__).resolve().parents[1] / "docs/evidence/0007-schema-contract.json"
)


def snapshot(connection):
    return {
        table: connection.scalars(
            text(f"SELECT row_to_json(r)::text FROM public.{table} r ORDER BY 1")
        ).all()
        for table in TABLES
    }


def table_permissions(connection, tables):
    return {
        table: {
            privilege: connection.scalar(
                text("SELECT has_table_privilege(:role,:table,:privilege)"),
                {
                    "role": ROLE,
                    "table": "public." + table,
                    "privilege": privilege,
                },
            )
            for privilege in PRIVILEGES
        }
        for table in tables
    }


def public_acl(connection, relations):
    return {
        relation: connection.scalars(
            text(
                "SELECT acl.privilege_type FROM pg_class c "
                "JOIN pg_namespace n ON n.oid=c.relnamespace "
                "CROSS JOIN LATERAL aclexplode(c.relacl) acl "
                "WHERE n.nspname='public' AND c.relname=:relation "
                "AND acl.grantee=0 ORDER BY acl.privilege_type"
            ),
            {"relation": relation},
        ).all()
        for relation in relations
    }


def catalog_contract(connection):
    return json.loads(
        json.dumps(
            {
                "tables": structure(connection, NEW_TABLES),
                "session_keys": [
                    dict(row)
                    for row in connection.execute(
                        text(
                            "SELECT conname,pg_get_constraintdef(oid) AS definition "
                            "FROM pg_constraint WHERE "
                            "conrelid='public.study_sessions'::regclass "
                            "AND conname IN (:first,:second) ORDER BY conname"
                        ),
                        {
                            "first": ADDED_SESSION_KEYS[0],
                            "second": ADDED_SESSION_KEYS[1],
                        },
                    ).mappings()
                ],
                "constraints": [
                    dict(row)
                    for row in connection.execute(
                        text(
                            "SELECT c.relname,p.conname,p.contype,p.convalidated,"
                            "pg_get_constraintdef(p.oid) AS definition "
                            "FROM pg_constraint p JOIN pg_class c ON c.oid=p.conrelid "
                            "WHERE c.relnamespace='public'::regnamespace "
                            "AND p.contype <> 'n' AND c.relname = ANY(:tables) "
                            "ORDER BY 1,2"
                        ),
                        {"tables": list(NEW_TABLES)},
                    ).mappings()
                ],
                "all_indexes": [
                    dict(row)
                    for row in connection.execute(
                        text(
                            "SELECT c.relname,i.relname AS index_name,"
                            "p.indisvalid,p.indisready,"
                            "pg_get_indexdef(i.oid) AS definition "
                            "FROM pg_index p JOIN pg_class c ON c.oid=p.indrelid "
                            "JOIN pg_class i ON i.oid=p.indexrelid "
                            "WHERE c.relnamespace='public'::regnamespace "
                            "AND c.relname = ANY(:tables) ORDER BY 1,2"
                        ),
                        {"tables": list(NEW_TABLES)},
                    ).mappings()
                ],
                "public_acl": public_acl(connection, (*NEW_TABLES, *NEW_SEQUENCES)),
            },
            default=str,
        )
    )


def verify(connection, contract):
    require(
        connection.scalars(text("SELECT version_num FROM public.alembic_version")).all()
        == [TARGET],
        "revision_after",
    )
    require(catalog_contract(connection) == contract, "installed_contract_differs")
    require(
        connection.scalars(
            text(
                "SELECT conname FROM pg_constraint "
                "WHERE conrelid='public.study_sessions'::regclass "
                "AND conname = ANY(:names) ORDER BY conname"
            ),
            {"names": list(ADDED_SESSION_KEYS)},
        ).all()
        == sorted(ADDED_SESSION_KEYS),
        "session_composite_keys",
    )
    require(
        connection.scalar(
            text(
                "SELECT count(*) FROM pg_index WHERE indrelid IN ("
                + ",".join(f"'public.{table}'::regclass" for table in NEW_TABLES)
                + ", 'public.study_sessions'::regclass) "
                "AND (NOT indisvalid OR NOT indisready)"
            )
        )
        == 0,
        "invalid_indexes",
    )
    require(
        connection.scalar(
            text(
                "SELECT count(*) FROM pg_constraint WHERE conrelid IN ("
                + ",".join(f"'public.{table}'::regclass" for table in NEW_TABLES)
                + ", 'public.study_sessions'::regclass) AND NOT convalidated"
            )
        )
        == 0,
        "invalid_constraints",
    )
    acl = public_acl(connection, (*NEW_TABLES, *NEW_SEQUENCES))
    require(not any(acl.values()), "public_privileges")
    safety = runtime_permissions(connection, subjects=False)
    permissions = table_permissions(connection, NEW_TABLES)
    for table, allowed in ALLOWED.items():
        require(
            permissions[table] == {p: p in allowed for p in PRIVILEGES},
            "runtime_new_table_grants",
        )
    sequences = {
        sequence: {
            privilege: connection.scalar(
                text("SELECT has_sequence_privilege(:role,:sequence,:privilege)"),
                {
                    "role": ROLE,
                    "sequence": "public." + sequence,
                    "privilege": privilege,
                },
            )
            for privilege in ("USAGE", "SELECT", "UPDATE")
        }
        for sequence in NEW_SEQUENCES
    }
    require(
        all(
            values == {"USAGE": True, "SELECT": True, "UPDATE": False}
            for values in sequences.values()
        ),
        "runtime_sequence_grants",
    )
    require(
        connection.scalar(
            text("SELECT has_schema_privilege(:role,'public','USAGE')"),
            {"role": ROLE},
        ),
        "runtime_schema_usage",
    )
    return {
        "revision": TARGET,
        "catalog_matches_tested_contract": True,
        "runtime": safety,
        "table_privileges": permissions,
        "sequence_privileges": sequences,
        "public_acl": acl,
    }


def apply(connection, contract):
    connection.execute(text("SET LOCAL search_path=public"))
    connection.execute(text("SET LOCAL lock_timeout='30s'"))
    connection.execute(text("SET LOCAL statement_timeout='120s'"))
    connection.execute(text("SELECT pg_advisory_xact_lock(1943187001)"))
    connection.execute(
        text(
            "LOCK TABLE public.alembic_version,"
            + ",".join("public." + table for table in TABLES)
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
    schema_before = structure(connection, TABLES)
    triggers_before = triggers(connection)
    permissions_before = table_permissions(connection, (*TABLES, "alembic_version"))
    sequences_before = {
        sequence: connection.execute(
            text(f"SELECT last_value,is_called FROM public.{sequence}")
        ).one()
        for sequence in (
            "users_id_seq",
            "subjects_id_seq",
            "activities_id_seq",
            "study_sessions_id_seq",
            "study_session_intervals_id_seq",
        )
    }
    memberships_before = connection.execute(
        text("SELECT * FROM pg_auth_members ORDER BY roleid,member,grantor")
    ).all()

    config = migration_config()
    config.attributes["connection"] = connection
    command.upgrade(config, TARGET)
    connection.execute(
        text(
            "GRANT SELECT,INSERT,UPDATE,DELETE ON public.study_plans TO cognova_runtime"
        )
    )
    for table in (
        "study_plan_subjects",
        "study_plan_activities",
        "study_plan_sessions",
    ):
        connection.execute(
            text(f"GRANT SELECT,INSERT,DELETE ON public.{table} TO cognova_runtime")
        )
    connection.execute(
        text("GRANT SELECT,INSERT ON public.study_plan_decisions TO cognova_runtime")
    )
    connection.execute(
        text("GRANT SELECT,INSERT,UPDATE ON public.study_challenges TO cognova_runtime")
    )
    connection.execute(
        text(
            "GRANT USAGE,SELECT ON SEQUENCE "
            + ",".join("public." + sequence for sequence in NEW_SEQUENCES)
            + " TO cognova_runtime"
        )
    )

    require(snapshot(connection) == before, "previous_rows_changed")
    schema_after = structure(connection, TABLES)
    for kind in ("unique", "indexes"):
        schema_after["study_sessions"][kind] = [
            item
            for item in schema_after["study_sessions"][kind]
            if item["name"] not in ADDED_SESSION_KEYS
        ]
    require(schema_after == schema_before, "previous_schema_changed")
    require(triggers(connection) == triggers_before, "previous_triggers_changed")
    require(
        table_permissions(connection, (*TABLES, "alembic_version"))
        == permissions_before,
        "previous_permissions_changed",
    )
    require(
        connection.execute(
            text("SELECT * FROM pg_auth_members ORDER BY roleid,member,grantor")
        ).all()
        == memberships_before,
        "memberships_changed",
    )
    for sequence, values in sequences_before.items():
        require(
            connection.execute(
                text(f"SELECT last_value,is_called FROM public.{sequence}")
            ).one()
            == values,
            "previous_sequence_changed",
        )
    report = verify(connection, contract)
    report.update(
        revision_before=BEFORE,
        rows_preserved={table: True for table in TABLES},
        counts_before={table: len(rows) for table, rows in before.items()},
        previous_schema_preserved_except_session_composite_keys=True,
        previous_triggers_permissions_sequences_memberships_preserved=True,
        preservation_scope="all rows/columns under exclusive locks",
        production_behavior_checks=(
            "catalog matches local contract; no synthetic production writes"
        ),
    )
    return report


def backup_gate(backup):
    require(
        all(
            backup.get(key) == "passed"
            for key in (
                "restore_rehearsal",
                "encryption_roundtrip",
                "pg_restore_list",
                "full_archive_decode",
                "download_verification",
            )
        ),
        "backup_checks",
    )
    require(
        backup.get("revision_before") == backup.get("revision_after") == BEFORE,
        "backup_revision",
    )
    require(
        backup.get("encrypted_file") == "cognova-pre-0007.dump.gpg"
        and set(backup.get("restored_counts") or ()) == {*TABLES, "alembic_version"},
        "backup_scope",
    )
    verified = datetime.fromisoformat(backup["verified_at_utc"])
    if verified.tzinfo is None:
        verified = verified.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - verified.astimezone(timezone.utc)
    require(0 <= age.total_seconds() < 86400, "backup_freshness")
    expires = datetime.fromisoformat(backup["expires_at"].replace("Z", "+00:00"))
    require(expires > datetime.now(timezone.utc), "backup_expired")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--backup-evidence", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--code-pin", required=True)
    args = parser.parse_args()
    stage, committed = "backup_gate", False
    try:
        backup = json.loads(args.backup_evidence.read_text(encoding="utf-8"))
        backup_gate(backup)
        encrypted = Path("artifacts") / backup["encrypted_file"]
        require(encrypted.is_file(), "downloaded_ciphertext_missing")
        require(
            hashlib.sha256(encrypted.read_bytes()).hexdigest()
            == backup["encrypted_sha256"],
            "downloaded_ciphertext_hash",
        )
        stage = "code_pin"
        current = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, timeout=10
        )
        require(current.returncode == 0, "git_head")
        require(current.stdout.decode().strip() == args.code_pin, "code_pin")
        branch = subprocess.run(
            ["git", "branch", "--show-current"], capture_output=True, timeout=10
        )
        require(
            branch.returncode == 0 and branch.stdout.decode().strip() == "main",
            "main_branch",
        )
        status = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, timeout=10
        )
        require(status.returncode == 0 and not status.stdout.strip(), "clean_worktree")
        stage = "tested_catalog_contract"
        contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
        stage = "production_target"
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
            report = apply(connection, contract)
            stage = "commit_in_progress"
        committed = True
        report.update(
            committed=True,
            backup_run=backup.get("run_id"),
            observed_at_utc=datetime.now(timezone.utc).isoformat(),
            code_pin=args.code_pin,
        )
        args.evidence.write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        stage = "post_commit_read_only"
        with engine.connect() as connection, connection.begin():
            connection.execute(text("SET TRANSACTION READ ONLY"))
            connection.execute(text("SET LOCAL statement_timeout='15000ms'"))
            verify(connection, contract)
            report["counts_after_commit"] = {
                table: connection.scalar(text(f"SELECT count(*) FROM public.{table}"))
                for table in (*TABLES, *NEW_TABLES)
            }
        report["post_commit_checks"] = "passed"
        report["post_commit_at_utc"] = datetime.now(timezone.utc).isoformat()
        args.evidence.write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        engine.dispose()
        print(
            json.dumps(
                {key: value for key, value in report.items() if key != "runtime"}
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
                    "check": str(error) if type(error) is RuntimeError else None,
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
