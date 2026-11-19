"""Repository-based CLI. Keep the repository and migrations together."""

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

ROOT = Path(__file__).resolve().parents[1]
SEED_FILE = ROOT / "cognova_database" / "seed" / "demo-academic.sql"
INITIALIZATION_LOCK = 1943187001


def migration_config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


def initialize() -> None:
    """Migrate first, then seed only a database identified as empty beforehand."""
    from cognova_database.configuration import database_url

    engine = create_engine(
        database_url(),
        poolclass=NullPool,
        hide_parameters=True,
        connect_args={"connect_timeout": 10},
    )
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT pg_advisory_lock(:lock_id)"),
                {"lock_id": INITIALIZATION_LOCK},
            )
            connection.commit()
            try:
                with connection.begin():
                    marker_exists = connection.scalar(
                        text(
                            "SELECT to_regclass('public.cognova_initialization') "
                            "IS NOT NULL"
                        )
                    )
                    if not marker_exists:
                        existing_relations = connection.scalar(
                            text(
                                "SELECT count(*) FROM pg_catalog.pg_class c "
                                "JOIN pg_catalog.pg_namespace n "
                                "ON n.oid = c.relnamespace "
                                "WHERE n.nspname = 'public' "
                                "AND c.relkind IN ('r','p','v','m','S','f')"
                            )
                        )
                        connection.execute(
                            text(
                                "CREATE TABLE public.cognova_initialization ("
                                "id text PRIMARY KEY, status text NOT NULL "
                                "CHECK (status IN ('pending', 'complete', 'skipped')))"
                            )
                        )
                        connection.execute(
                            text(
                                "INSERT INTO public.cognova_initialization "
                                "(id, status) VALUES ('demo-academic-seed', :status)"
                            ),
                            {
                                "status": "pending"
                                if existing_relations == 0
                                else "skipped"
                            },
                        )

                config = migration_config()
                config.attributes["connection"] = connection
                command.upgrade(config, "head")

                with connection.begin():
                    status = connection.scalar(
                        text(
                            "SELECT status FROM public.cognova_initialization "
                            "WHERE id = 'demo-academic-seed' FOR UPDATE"
                        )
                    )
                    if status == "pending":
                        if not SEED_FILE.is_file():
                            raise FileNotFoundError("Academic seed file is missing")
                        connection.exec_driver_sql(
                            SEED_FILE.read_text(encoding="utf-8"),
                            execution_options={"no_parameters": True},
                        )
                        connection.execute(
                            text(
                                "UPDATE public.cognova_initialization "
                                "SET status = 'complete' "
                                "WHERE id = 'demo-academic-seed'"
                            )
                        )
            finally:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": INITIALIZATION_LOCK},
                )
                connection.commit()
    finally:
        engine.dispose()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cognova PostgreSQL migrations")
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("initialize")
    upgrade = commands.add_parser("upgrade")
    upgrade.add_argument(
        "revision",
        choices=[
            "0001_create_users",
            "0002_auth_sessions",
            "0003_onboarding_questionnaire",
            "0004_subjects",
            "0005_activities",
            "0006_study_sessions",
            "0007_study_plans_and_challenges",
            "0008_ai_plan_proposal_snapshot",
            "0009_academic_companion_chat",
            "0010_nullable_password_hash",
            "head",
        ],
    )
    upgrade.add_argument("--sql", action="store_true", help="Offline SQL only")
    for name in ("heads", "history", "current"):
        commands.add_parser(name)
    args = parser.parse_args(argv)
    try:
        config = migration_config()
        if args.action == "initialize":
            initialize()
        elif args.action == "upgrade":
            command.upgrade(config, args.revision, sql=args.sql)
        else:
            getattr(command, args.action)(config)
    except Exception as exc:
        # DB errors can contain URLs, passwords or SQL values. Never print them.
        print(f"migration_failed exception_type={type(exc).__name__}", file=sys.stderr)
        return 1
    return 0
