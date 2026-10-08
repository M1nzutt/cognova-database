"""Check the immutable history and SQL without a database or backend checkout."""

import hashlib
from io import StringIO

from alembic import command
from alembic.script import ScriptDirectory

from cognova_database.runner import ROOT, migration_config

BLOBS = {
    "0001_create_users.py": "847886004b17e4b57723029cd217a63dd063d381",
    "0002_auth_sessions.py": "ef8cd07f0a3482a272c5f62229f51a5390d74ec4",
}


def sql_for(revision):
    config = migration_config()
    config.output_buffer = StringIO()
    command.upgrade(config, revision, sql=True)
    return config.output_buffer.getvalue()


def test_original_blobs_and_single_linear_head():
    for filename, expected in BLOBS.items():
        # Git text normalization allows CRLF working trees on Windows.
        data = (ROOT / "migrations" / "versions" / filename).read_bytes()
        data = data.replace(b"\r\n", b"\n")
        blob = b"blob " + str(len(data)).encode() + b"\0" + data
        assert hashlib.sha1(blob).hexdigest() == expected
    script = ScriptDirectory.from_config(migration_config())
    assert script.get_heads() == ["0002_auth_sessions"]
    assert [(r.revision, r.down_revision) for r in script.walk_revisions()] == [
        ("0002_auth_sessions", "0001_create_users"),
        ("0001_create_users", None),
    ]


def test_complete_postgresql_ddl_without_environment(monkeypatch):
    for name in ("DATABASE_URL", "JWT_SECRET", "ENVIRONMENT"):
        monkeypatch.delenv(name, raising=False)
    sql = sql_for("head")
    for expected in (
        "CREATE TABLE users",
        "id SERIAL NOT NULL",
        "created_at TIMESTAMP WITH TIME ZONE DEFAULT now() NOT NULL",
        "CONSTRAINT ck_users_semester_positive CHECK (semester > 0)",
        "CREATE UNIQUE INDEX uq_users_email_lower ON users (lower(email))",
        "ALTER TABLE users ADD COLUMN updated_at",
        "CREATE TABLE auth_sessions",
        "id UUID NOT NULL",
        "FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE",
        "CREATE INDEX ix_auth_sessions_user_id",
        "CREATE INDEX ix_auth_sessions_expires_at",
        "CREATE TABLE rate_limit_buckets",
        "CREATE INDEX ix_rate_limit_buckets_expires_at",
        "UPDATE alembic_version SET version_num='0002_auth_sessions'",
    ):
        assert expected in sql


def test_upgrade_range_does_not_recreate_users():
    sql = sql_for("0001_create_users:0002_auth_sessions")
    assert "CREATE TABLE users" not in sql
    assert "ALTER TABLE users ADD COLUMN updated_at" in sql
    assert "CREATE TABLE auth_sessions" in sql


def test_same_head_offline_has_no_schema_operations():
    sql = sql_for("0002_auth_sessions:0002_auth_sessions")
    assert all(word not in sql for word in ("CREATE", "ALTER", "DROP", "INSERT"))


def test_paths_work_outside_repository(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    assert "CREATE TABLE users" in sql_for("head")
