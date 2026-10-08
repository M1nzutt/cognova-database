"""Offline resource-lifecycle checks, not substitutes for PostgreSQL tests."""

import runpy
from contextlib import nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from alembic import context

from cognova_database.runner import ROOT


def run_env(monkeypatch, connection, *, failure=None):
    config = SimpleNamespace(attributes={"connection": connection})
    monkeypatch.setattr(context, "config", config, raising=False)
    monkeypatch.setattr(context, "is_offline_mode", lambda: False)
    configure = MagicMock()
    monkeypatch.setattr(context, "configure", configure)
    monkeypatch.setattr(context, "begin_transaction", nullcontext)
    monkeypatch.setattr(context, "run_migrations", MagicMock(side_effect=failure))
    engine = MagicMock(side_effect=AssertionError("Must use injected connection"))
    monkeypatch.setattr("sqlalchemy.create_engine", engine)
    runpy.run_path(str(ROOT / "migrations" / "env.py"))
    return configure


@pytest.mark.parametrize("in_transaction", [True, False])
def test_injected_connection_keeps_owner_and_search_path(monkeypatch, in_transaction):
    connection = MagicMock()
    connection.dialect.name = "postgresql"
    connection.in_transaction.return_value = in_transaction
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    configure = run_env(monkeypatch, connection)
    configure.assert_called_once_with(connection=connection, target_metadata=None)
    statements = [str(call.args[0]) for call in connection.execute.call_args_list]
    assert statements == [
        "SET LOCAL lock_timeout = '30s'",
        "SET LOCAL statement_timeout = '120s'",
        "SELECT pg_advisory_xact_lock(1943187001)",
    ]
    assert connection.begin.call_count == (0 if in_transaction else 1)
    connection.close.assert_not_called()
    connection.commit.assert_not_called()
    connection.rollback.assert_not_called()


def test_injected_failure_reaches_transaction_owner(monkeypatch):
    connection = MagicMock()
    connection.dialect.name = "postgresql"
    connection.in_transaction.return_value = True
    with pytest.raises(RuntimeError, match="ddl failed"):
        run_env(monkeypatch, connection, failure=RuntimeError("ddl failed"))
    connection.commit.assert_not_called()
    connection.close.assert_not_called()
