"""Apply the disposable Docker stack's least-privilege runtime ACLs."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping

from sqlalchemy import Connection, create_engine, text

from cognova_database.configuration import database_url

EXPECTED_REVISION = "0009_academic_companion_chat"
MIGRATOR_ROLE = "cognova_migrator"
RUNTIME_ROLE = "cognova_runtime"
TABLE_PRIVILEGES: Mapping[str, frozenset[str]] = {
    "alembic_version": frozenset({"SELECT"}),
    "users": frozenset({"SELECT", "INSERT", "UPDATE"}),
    "auth_sessions": frozenset({"SELECT", "INSERT", "UPDATE"}),
    "rate_limit_buckets": frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"}),
    "user_academic_goal_legacy": frozenset({"SELECT"}),
    "questionnaire_responses": frozenset({"SELECT", "INSERT"}),
    "subjects": frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"}),
    "activities": frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"}),
    "activity_deadline_events": frozenset({"SELECT"}),
    "study_sessions": frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"}),
    "study_session_intervals": frozenset({"SELECT", "INSERT", "UPDATE"}),
    "study_plans": frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"}),
    "study_plan_subjects": frozenset({"SELECT", "INSERT", "DELETE"}),
    "study_plan_activities": frozenset({"SELECT", "INSERT", "DELETE"}),
    "study_plan_sessions": frozenset({"SELECT", "INSERT", "DELETE"}),
    "study_plan_decisions": frozenset({"SELECT", "INSERT"}),
    "study_challenges": frozenset({"SELECT", "INSERT", "UPDATE"}),
    "academic_conversations": frozenset({"SELECT", "INSERT", "UPDATE", "DELETE"}),
    "academic_messages": frozenset({"SELECT", "INSERT"}),
}
SEQUENCES = (
    "users_id_seq",
    "subjects_id_seq",
    "activities_id_seq",
    "study_sessions_id_seq",
    "study_session_intervals_id_seq",
    "study_plans_id_seq",
    "study_plan_decisions_id_seq",
    "study_challenges_id_seq",
    "academic_conversations_id_seq",
    "academic_messages_id_seq",
)
TABLE_PRIVILEGE_CHECKS = (
    "SELECT",
    "INSERT",
    "UPDATE",
    "DELETE",
    "TRUNCATE",
    "REFERENCES",
    "TRIGGER",
)


def validate_local_target(environment: str | None, host: str | None, user: str) -> None:
    """Refuse production and refuse to run outside the compose migrator service."""
    if environment != "development":
        raise ValueError("local_environment_required")
    if host != "postgres":
        raise ValueError("compose_database_host_required")
    if user != MIGRATOR_ROLE:
        raise ValueError("migration_role_required")


def apply_runtime_grants(connection: Connection) -> None:
    """Grant only application DML; Alembic remains owned by Database/migrator."""
    current_user = connection.scalar(text("SELECT current_user"))
    if current_user != MIGRATOR_ROLE:
        raise ValueError("migration_role_required")

    revision = connection.scalars(
        text("SELECT version_num FROM public.alembic_version")
    ).all()
    if revision != [EXPECTED_REVISION]:
        raise ValueError("database_revision_mismatch")

    runtime = (
        connection.execute(
            text(
                "SELECT rolcanlogin, rolsuper, rolcreatedb, rolcreaterole, "
                "rolreplication, rolbypassrls FROM pg_roles WHERE rolname=:role"
            ),
            {"role": RUNTIME_ROLE},
        )
        .mappings()
        .one_or_none()
    )
    if runtime is None or runtime["rolcanlogin"] is not True:
        raise ValueError("runtime_role_missing")
    if any(
        runtime[key]
        for key in (
            "rolsuper",
            "rolcreatedb",
            "rolcreaterole",
            "rolreplication",
            "rolbypassrls",
        )
    ):
        raise ValueError("runtime_role_elevated")

    membership_count = connection.scalar(
        text(
            "SELECT count(*) FROM pg_auth_members m "
            "JOIN pg_roles granted ON granted.oid=m.roleid "
            "JOIN pg_roles member ON member.oid=m.member "
            "WHERE granted.rolname=:role OR member.rolname=:role"
        ),
        {"role": RUNTIME_ROLE},
    )
    if membership_count:
        raise ValueError("runtime_role_membership_present")

    owner_count = connection.scalar(
        text(
            "SELECT count(*) FROM pg_shdepend "
            "WHERE refclassid='pg_authid'::regclass "
            "AND refobjid=(SELECT oid FROM pg_roles WHERE rolname=:role) "
            "AND deptype='o'"
        ),
        {"role": RUNTIME_ROLE},
    )
    if owner_count:
        raise ValueError("runtime_role_owns_objects")

    if connection.scalar(
        text("SELECT has_schema_privilege(:role,'public','CREATE')"),
        {"role": RUNTIME_ROLE},
    ):
        raise ValueError("runtime_schema_create_present")

    for table in TABLE_PRIVILEGES:
        connection.execute(text(f"REVOKE ALL ON TABLE public.{table} FROM PUBLIC"))
        connection.execute(
            text(f"REVOKE ALL ON TABLE public.{table} FROM {RUNTIME_ROLE}")
        )
    for table, privileges in TABLE_PRIVILEGES.items():
        connection.execute(
            text(
                f"GRANT {','.join(sorted(privileges))} "
                f"ON TABLE public.{table} TO {RUNTIME_ROLE}"
            )
        )

    for sequence in SEQUENCES:
        connection.execute(
            text(
                f"REVOKE ALL ON SEQUENCE public.{sequence} FROM PUBLIC, {RUNTIME_ROLE}"
            )
        )
        connection.execute(
            text(f"GRANT USAGE,SELECT ON SEQUENCE public.{sequence} TO {RUNTIME_ROLE}")
        )

    for table, allowed in TABLE_PRIVILEGES.items():
        observed = {
            privilege
            for privilege in TABLE_PRIVILEGE_CHECKS
            if connection.scalar(
                text("SELECT has_table_privilege(:role,:table,:privilege)"),
                {
                    "role": RUNTIME_ROLE,
                    "table": f"public.{table}",
                    "privilege": privilege,
                },
            )
        }
        if observed != set(allowed):
            raise ValueError("runtime_table_privileges_mismatch")

    public_privileges = connection.scalar(
        text(
            "SELECT count(*) FROM pg_class c "
            "JOIN pg_namespace n ON n.oid=c.relnamespace "
            "CROSS JOIN LATERAL aclexplode(c.relacl) acl "
            "WHERE n.nspname='public' AND c.relname = ANY(CAST(:objects AS text[])) "
            "AND acl.grantee=0"
        ),
        {"objects": [*TABLE_PRIVILEGES, *SEQUENCES]},
    )
    if public_privileges:
        raise ValueError("public_object_privileges_present")

    for sequence in SEQUENCES:
        if connection.scalar(
            text("SELECT has_sequence_privilege(:role,:sequence,'UPDATE')"),
            {"role": RUNTIME_ROLE, "sequence": f"public.{sequence}"},
        ):
            raise ValueError("runtime_sequence_update_present")
        for privilege in ("USAGE", "SELECT"):
            if not connection.scalar(
                text("SELECT has_sequence_privilege(:role,:sequence,:privilege)"),
                {
                    "role": RUNTIME_ROLE,
                    "sequence": f"public.{sequence}",
                    "privilege": privilege,
                },
            ):
                raise ValueError("runtime_sequence_privileges_missing")


def main() -> int:
    engine = None
    try:
        url = database_url()
        validate_local_target(
            os.environ.get("ENVIRONMENT"), url.host, url.username or ""
        )
        engine = create_engine(url, hide_parameters=True, pool_pre_ping=True)
        with engine.begin() as connection:
            apply_runtime_grants(connection)
        print(
            "local_runtime_grants=applied "
            f"revision={EXPECTED_REVISION} tables={len(TABLE_PRIVILEGES)}"
        )
        return 0
    except Exception as exc:
        print(
            f"local_runtime_grants_failed exception_type={type(exc).__name__}",
            file=sys.stderr,
        )
        return 1
    finally:
        if engine is not None:
            engine.dispose()


if __name__ == "__main__":
    raise SystemExit(main())
