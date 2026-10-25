"""Narrow production ACL change; no schema migrations or row modifications."""

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, text

from cognova_database.configuration import database_url
from scripts.release_0004 import ROLE, TARGET, require, runtime_permissions

PRIVILEGES = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "TRUNCATE",
    "REFERENCES",
    "TRIGGER",
)


def inventory(connection):
    require(
        connection.scalar(text("SELECT current_database()")) == "cognova",
        "database",
    )
    require(
        connection.scalar(
            text("SELECT ssl FROM pg_stat_ssl WHERE pid=pg_backend_pid()")
        ),
        "tls",
    )
    require(
        connection.scalars(text("SELECT version_num FROM public.alembic_version")).all()
        == [TARGET],
        "revision",
    )
    safety = runtime_permissions(connection, subjects=False)
    tables = connection.scalars(
        text(
            "SELECT c.relname FROM pg_class c JOIN pg_namespace n "
            "ON n.oid=c.relnamespace WHERE n.nspname='public' "
            "AND c.relkind IN ('r','p') ORDER BY 1"
        )
    ).all()
    privileges = {
        table: {
            privilege: connection.scalar(
                text("SELECT has_table_privilege(:role,:table,:privilege)"),
                {"role": ROLE, "table": "public." + table, "privilege": privilege},
            )
            for privilege in PRIVILEGES
        }
        for table in tables
    }
    require("subjects" in privileges, "subjects_missing")
    require(not privileges["subjects"]["TRUNCATE"], "subjects_truncate")
    return {"revision": TARGET, "safety": safety, "table_privileges": privileges}


def grant(connection):
    connection.execute(text("SET LOCAL lock_timeout='10s'"))
    connection.execute(text("SET LOCAL statement_timeout='30s'"))
    connection.execute(text("SELECT pg_advisory_xact_lock(1943187001)"))
    before = inventory(connection)
    connection.execute(text("GRANT DELETE ON TABLE public.subjects TO cognova_runtime"))
    after = inventory(connection)
    expected = json.loads(json.dumps(before))
    expected["table_privileges"]["subjects"]["DELETE"] = True
    require(after == expected, "unexpected_permission_change")
    return {"before": before, "after": after}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("inspect", "apply"))
    parser.add_argument("--evidence", required=True, type=Path)
    args = parser.parse_args()
    committed = False
    try:
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
        with engine.connect() as connection:
            with connection.begin():
                connection.execute(text("SET LOCAL statement_timeout='30s'"))
                if args.mode == "inspect":
                    connection.execute(text("SET TRANSACTION READ ONLY"))
                    report = inventory(connection)
                else:
                    report = grant(connection)
            committed = args.mode == "apply"
            if committed:
                with connection.begin():
                    connection.execute(text("SET TRANSACTION READ ONLY"))
                    require(inventory(connection) == report["after"], "post_commit")
                report["post_commit_checks"] = "passed"
        engine.dispose()
        report.update(
            mode=args.mode,
            committed=committed,
            observed_at_utc=datetime.now(timezone.utc).isoformat(),
        )
        args.evidence.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report))
        return 0
    except Exception as error:
        print(
            json.dumps(
                {
                    "status": "failed",
                    "committed": committed,
                    "exception_type": type(error).__name__,
                    "sqlstate": getattr(getattr(error, "orig", None), "sqlstate", None),
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
