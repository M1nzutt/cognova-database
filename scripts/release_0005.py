"""Atomic authorized 0005 release. No row probes or membership changes in production."""

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from alembic import command
from sqlalchemy import create_engine, text

from cognova_database.configuration import database_url
from cognova_database.runner import migration_config
from scripts.release_0004 import require, runtime_permissions, structure, triggers

PIN = "604e296e2670d154ba7e18d7afa3f010e66dd42d"
BEFORE = "0004_subjects"
TARGET = "0005_activities"
TABLES = (
    "users",
    "auth_sessions",
    "rate_limit_buckets",
    "user_academic_goal_legacy",
    "questionnaire_responses",
    "subjects",
)
NEW_TABLES = ("activities", "activity_deadline_events")
FUNCTIONS = (
    "cognova_prepare_activity",
    "cognova_record_activity_deadline",
    "cognova_preserve_activity_deadline",
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
CONTRACT = (
    Path(__file__).resolve().parents[1] / "docs/evidence/0005-schema-contract.json"
)


def snapshot(c):
    return {
        t: c.scalars(
            text(f"SELECT row_to_json(r)::text FROM public.{t} r ORDER BY 1")
        ).all()
        for t in TABLES
    }


def table_permissions(c, tables):
    return {
        t: {
            p: c.scalar(
                text("SELECT has_table_privilege('cognova_runtime',:t,:p)"),
                {"t": "public." + t, "p": p},
            )
            for p in PRIVILEGES
        }
        for t in tables
    }


def catalog_contract(c):
    functions = [
        dict(row)
        for row in c.execute(
            text(
                "SELECT "
                "proname,prosrc,prosecdef,proconfig,provolatile,prorettype::regtype::text"
                " AS return_type "
                "FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace "
                "WHERE n.nspname='public' AND proname IN "
                "('cognova_prepare_activity','cognova_record_activity_deadline','cognova_preserve_activity_deadline')"
                " "
                "ORDER BY proname"
            )
        ).mappings()
    ]
    return json.loads(
        json.dumps(
            {
                "tables": structure(c, NEW_TABLES),
                "triggers": [t for t in triggers(c) if t["relname"] in NEW_TABLES],
                "functions": functions,
            },
            default=str,
        )
    )


def verify(c, contract):
    require(
        c.scalars(text("SELECT version_num FROM public.alembic_version")).all()
        == [TARGET],
        "revision_after",
    )
    require(catalog_contract(c) == contract, "installed_contract_differs")
    require(
        c.scalar(
            text(
                "SELECT count(*) FROM pg_constraint WHERE "
                "conrelid='public.subjects'::regclass AND "
                "conname='uq_subjects_user_id_id' AND "
                "pg_get_constraintdef(oid)='UNIQUE (user_id, id)'"
            )
        )
        == 1,
        "subject_composite_key",
    )
    require(
        c.scalar(
            text(
                "SELECT count(*) FROM pg_index WHERE indrelid IN "
                "('public.activities'::regclass,'public.activity_deadline_events'::regclass,'public.subjects'::regclass)"
                " AND (NOT indisvalid OR NOT indisready)"
            )
        )
        == 0,
        "invalid_indexes",
    )
    require(
        c.scalar(
            text(
                "SELECT count(*) FROM pg_constraint WHERE conrelid IN "
                "('public.activities'::regclass,'public.activity_deadline_events'::regclass,'public.subjects'::regclass)"
                " AND NOT convalidated"
            )
        )
        == 0,
        "invalid_constraints",
    )
    safety = runtime_permissions(c, subjects=False)
    permissions = table_permissions(c, NEW_TABLES)
    for t, allowed in {
        "activities": {"SELECT", "INSERT", "UPDATE", "DELETE"},
        "activity_deadline_events": {"SELECT"},
    }.items():
        require(
            permissions[t] == {p: p in allowed for p in PRIVILEGES},
            "runtime_new_table_grants",
        )
    sequence = {
        p: c.scalar(
            text(
                "SELECT "
                "has_sequence_privilege('cognova_runtime','public.activities_id_seq',:p)"
            ),
            {"p": p},
        )
        for p in ("USAGE", "SELECT", "UPDATE")
    }
    require(
        sequence == {"USAGE": True, "SELECT": True, "UPDATE": False},
        "runtime_sequence_grants",
    )
    functions = {
        f: c.scalar(
            text("SELECT has_function_privilege('cognova_runtime',:f,'EXECUTE')"),
            {"f": "public." + f + "()"},
        )
        for f in FUNCTIONS
    }
    require(not any(functions.values()), "runtime_function_execute")
    return {
        "revision": TARGET,
        "catalog_matches_tested_contract": True,
        "runtime": safety,
        "table_privileges": permissions,
        "sequence_privileges": sequence,
        "function_execute": functions,
    }


def apply(c, contract):
    c.execute(text("SET LOCAL search_path=public"))
    c.execute(text("SET LOCAL lock_timeout='30s'"))
    c.execute(text("SET LOCAL statement_timeout='120s'"))
    c.execute(text("SELECT pg_advisory_xact_lock(1943187001)"))
    c.execute(
        text(
            "LOCK TABLE public.alembic_version,"
            + ",".join("public." + t for t in TABLES)
            + " IN ACCESS EXCLUSIVE MODE"
        )
    )
    require(
        c.scalars(text("SELECT version_num FROM public.alembic_version")).all()
        == [BEFORE],
        "revision_before",
    )
    runtime_permissions(c, subjects=False)
    before = snapshot(c)
    schema_before = structure(c, TABLES)
    triggers_before = triggers(c)
    permissions_before = table_permissions(c, (*TABLES, "alembic_version"))
    sequence_before = {
        t: c.execute(text(f"SELECT last_value,is_called FROM public.{t}_id_seq")).one()
        for t in ("users", "subjects")
    }
    memberships_before = c.execute(
        text("SELECT * FROM pg_auth_members ORDER BY roleid,member,grantor")
    ).all()
    config = migration_config()
    config.attributes["connection"] = c
    command.upgrade(config, TARGET)
    c.execute(
        text(
            "GRANT SELECT,INSERT,UPDATE,DELETE ON public.activities TO cognova_runtime"
        )
    )
    c.execute(
        text("GRANT SELECT ON public.activity_deadline_events TO cognova_runtime")
    )
    c.execute(
        text(
            "GRANT USAGE,SELECT ON SEQUENCE public.activities_id_seq TO cognova_runtime"
        )
    )
    require(snapshot(c) == before, "previous_rows_changed")
    schema_after = structure(c, TABLES)
    for kind in ("unique", "indexes"):
        schema_after["subjects"][kind] = [
            x
            for x in schema_after["subjects"][kind]
            if x["name"] != "uq_subjects_user_id_id"
        ]
    require(schema_after == schema_before, "previous_schema_changed")
    require(
        [t for t in triggers(c) if t["relname"] not in NEW_TABLES] == triggers_before,
        "previous_triggers_changed",
    )
    require(
        table_permissions(c, (*TABLES, "alembic_version")) == permissions_before,
        "previous_permissions_changed",
    )
    require(
        c.execute(
            text("SELECT * FROM pg_auth_members ORDER BY roleid,member,grantor")
        ).all()
        == memberships_before,
        "memberships_changed",
    )
    for t, values in sequence_before.items():
        require(
            c.execute(text(f"SELECT last_value,is_called FROM public.{t}_id_seq")).one()
            == values,
            "previous_sequence_changed",
        )
    report = verify(c, contract)
    report.update(
        revision_before=BEFORE,
        rows_preserved={t: True for t in TABLES},
        counts_before={t: len(rows) for t, rows in before.items()},
        previous_structure_preserved_except_subject_composite_key=True,
        previous_triggers_permissions_sequences_memberships_preserved=True,
        preservation_scope="all rows/columns under exclusive locks",
        production_behavior_checks=(
            "catalog identical to locally tested constraints/functions/triggers; "
            "no synthetic production writes"
        ),
    )
    return report


def backup_gate(backup):
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
        "backup_checks",
    )
    require(
        backup["revision_before"] == backup["revision_after"] == BEFORE,
        "backup_revision",
    )
    require(
        backup["encrypted_file"] == "cognova-pre-0005.dump.gpg"
        and "subjects" in backup["restored_counts"],
        "backup_scope",
    )
    age = datetime.now(timezone.utc) - datetime.fromisoformat(backup["verified_at_utc"])
    require(0 <= age.total_seconds() < 86400, "backup_freshness")
    require(
        datetime.fromisoformat(backup["expires_at"].replace("Z", "+00:00"))
        > datetime.now(timezone.utc),
        "backup_expired",
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", required=True)
    parser.add_argument("--backup-evidence", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    stage, committed = "backup_gate", False
    try:
        backup = json.loads(args.backup_evidence.read_text(encoding="utf-8"))
        backup_gate(backup)
        stage = "code_pin"
        check = subprocess.run(
            ["git", "diff", "--exit-code", PIN, "--", "cognova_database", "migrations"],
            capture_output=True,
            timeout=10,
        )
        require(check.returncode == 0, "code_differs_from_backend_pin")
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
        with engine.begin() as c:
            require(
                c.scalar(
                    text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
                ),
                "tls",
            )
            report = apply(c, contract)
            stage = "commit_in_progress"
        committed = True
        # Persist immediately; a failed read-only recheck must not invite replay.
        report.update(
            committed=True,
            backup_run=backup["run_id"],
            observed_at_utc=datetime.now(timezone.utc).isoformat(),
            code_pin=PIN,
        )
        args.evidence.write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        stage = "post_commit_read_only"
        with engine.connect() as c, c.begin():
            c.execute(text("SET TRANSACTION READ ONLY"))
            c.execute(text("SET LOCAL statement_timeout='15000ms'"))
            verify(c, contract)
            report["counts_after_commit"] = {
                t: c.scalar(text(f"SELECT count(*) FROM public.{t}"))
                for t in (*TABLES, *NEW_TABLES)
            }
        report["post_commit_checks"] = "passed"
        report["post_commit_at_utc"] = datetime.now(timezone.utc).isoformat()
        args.evidence.write_text(
            json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8"
        )
        engine.dispose()
        print(json.dumps({k: v for k, v in report.items() if k != "runtime"}))
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
