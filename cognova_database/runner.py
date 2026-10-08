"""Repository-based CLI. Keep the repository and migrations together."""

import argparse
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

ROOT = Path(__file__).resolve().parents[1]


def migration_config() -> Config:
    return Config(str(ROOT / "alembic.ini"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Cognova PostgreSQL migrations")
    commands = parser.add_subparsers(dest="action", required=True)
    upgrade = commands.add_parser("upgrade")
    upgrade.add_argument("revision", choices=["0001_create_users", "head"])
    upgrade.add_argument("--sql", action="store_true", help="Offline SQL only")
    for name in ("heads", "history", "current"):
        commands.add_parser(name)
    args = parser.parse_args(argv)
    try:
        config = migration_config()
        if args.action == "upgrade":
            command.upgrade(config, args.revision, sql=args.sql)
        else:
            getattr(command, args.action)(config)
    except Exception as exc:
        # DB errors can contain URLs, passwords or SQL values. Never print them.
        print(f"migration_failed exception_type={type(exc).__name__}", file=sys.stderr)
        return 1
    return 0
