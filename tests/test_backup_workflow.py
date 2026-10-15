"""Exercise workflow error handling without a database, dump binary or secret."""

import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/backup-pre-0003.yml"
PLAINTEXT = b"PGDMP-synthetic-fixture-not-a-real-backup"
KEY = "synthetic-encryption-passphrase-123456789"


@pytest.fixture
def backup_code(monkeypatch, tmp_path):
    source = WORKFLOW.read_text(encoding="utf-8")
    script = source.split("python3 - <<'PY'\n", 1)[1].split("          PY\n", 1)[0]
    script = "\n".join(line[10:] for line in script.splitlines())
    tree = ast.parse(script)
    # Load imports/functions only; never invoke the workflow's entrypoint.
    tree.body = [node for node in tree.body if not isinstance(node, ast.Try)]
    namespace = {}
    exec(compile(tree, str(WORKFLOW), "exec"), namespace)
    for name, value in {
        "RUNNER_TEMP": str(tmp_path),
        "GITHUB_OUTPUT": str(tmp_path / "outputs"),
        "GITHUB_STEP_SUMMARY": str(tmp_path / "summary"),
        "GITHUB_RUN_ID": "123",
        "GITHUB_RUN_ATTEMPT": "1",
        "GITHUB_SHA": "test-commit",
    }.items():
        monkeypatch.setenv(name, value)
    # Synthetic credential; never use the local .env in workflow tests.
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://test:synthetic-password@"
        "dpg-db2iojc9v7es7387i2ig-a.oregon-postgres.render.com/cognova",
    )
    monkeypatch.setenv("BACKUP_ENCRYPTION_KEY", KEY)
    return namespace


def fake_commands(monkeypatch, namespace, failure=None):
    calls = []

    def execute(args, **kwargs):
        calls.append(args)
        assert all("synthetic-password" not in arg for arg in args)
        assert all(KEY not in arg for arg in args)
        assert "BACKUP_ENCRYPTION_KEY" not in kwargs["env"]
        binary = Path(args[0]).name
        if binary != "gpg":
            assert kwargs["env"]["PGSSLMODE"] == "require"
        else:
            assert not any(k.startswith("PG") for k in kwargs["env"])
        if failure == "dump" and binary == "pg_dump" and "--version" not in args:
            return SimpleNamespace(returncode=1, stdout=b"", stderr=b"secret error")
        if "--version" in args:
            output = f"{binary} (PostgreSQL) 18.6".encode()
        elif binary == "psql":
            output = b"t" if "pg_stat_ssl" in args[-1] else b"0002_auth_sessions"
            if failure == "revision" and "alembic_version" in args[-1]:
                output = b"0003_onboarding_questionnaire"
        elif binary == "pg_dump":
            Path(args[-1]).write_bytes(PLAINTEXT)
            output = b""
        elif binary == "gpg":
            assert kwargs["input"] == KEY.encode() + b"\n"
            if failure == "encryption":
                return SimpleNamespace(returncode=1, stdout=b"", stderr=KEY.encode())
            data = b"encrypted-test-fixture" if "--symmetric" in args else PLAINTEXT
            if failure == "roundtrip" and "--decrypt" in args:
                data = b"corrupt"
            Path(args[args.index("--output") + 1]).write_bytes(data)
            output = b""
        elif "--list" in args:
            output = b"\n".join(
                f"TABLE DATA public {table} test_owner".encode()
                for table in (
                    "users",
                    "auth_sessions",
                    "rate_limit_buckets",
                    "alembic_version",
                )
            )
            if failure == "toc":
                output = b""
        else:
            output = b""
        return SimpleNamespace(returncode=0, stdout=output, stderr=b"")

    monkeypatch.setattr(namespace["subprocess"], "run", execute)
    return calls


@pytest.mark.parametrize(
    "failure", ["dump", "revision", "toc", "encryption", "roundtrip"]
)
def test_failures_never_mark_backup_ready(backup_code, monkeypatch, tmp_path, failure):
    fake_commands(monkeypatch, backup_code, failure)
    with pytest.raises((RuntimeError, ValueError)):
        backup_code["backup"]()
    assert not (tmp_path / "outputs").exists()
    assert not (tmp_path / "summary").exists()


@pytest.mark.parametrize("url", ["", "postgresql://test:password@localhost/cognova"])
def test_missing_or_different_target_never_connects(backup_code, monkeypatch, url):
    calls = fake_commands(monkeypatch, backup_code)
    monkeypatch.setenv("DATABASE_URL", url)
    with pytest.raises(ValueError):
        backup_code["backup"]()
    assert not calls


def test_verified_manifest_has_correct_digest_and_no_secret(
    backup_code, monkeypatch, tmp_path, capsys
):
    fake_commands(monkeypatch, backup_code)
    backup_code["backup"]()
    directory = tmp_path / "cognova-pre-0003"
    output = capsys.readouterr().out
    manifest = json.loads(output)
    assert not (directory / "cognova-pre-0003.dump").exists()
    assert not (directory / "roundtrip.dump").exists()
    assert manifest["size_bytes"] == len(PLAINTEXT)
    assert manifest["sha256"] == hashlib.sha256(PLAINTEXT).hexdigest()
    encrypted = (directory / "cognova-pre-0003.dump.gpg").read_bytes()
    assert manifest["encrypted_sha256"] == hashlib.sha256(encrypted).hexdigest()
    assert manifest["encrypted_size_bytes"] == len(encrypted)
    assert manifest["encryption_roundtrip"] == "passed"
    assert manifest["pg_restore_list"] == "passed"
    assert manifest["restore_rehearsal"] == "not_performed"
    assert "synthetic-password" not in output
    assert KEY not in output
    assert "synthetic-password" not in (tmp_path / "summary").read_text()
    assert KEY not in (tmp_path / "summary").read_text()


@pytest.mark.parametrize("key", ["", "too-short", "x" * 32 + "\n"])
def test_invalid_encryption_key_never_connects(backup_code, monkeypatch, key):
    calls = fake_commands(monkeypatch, backup_code)
    monkeypatch.setenv("BACKUP_ENCRYPTION_KEY", key)
    with pytest.raises(ValueError):
        backup_code["backup"]()
    assert not calls
