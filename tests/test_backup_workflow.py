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
        "VALIDATE_ONLY": "false",
        "DIAGNOSE_CONNECTION": "false",
        "SUBJECTS_RELEASE": "false",
        "ACTIVITIES_RELEASE": "false",
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
        local = kwargs["env"].get("PGHOST") == "127.0.0.1"
        if binary == "docker" or local:
            assert "PGPASSWORD" not in kwargs["env"]
        elif binary != "gpg":
            assert kwargs["env"]["PGSSLMODE"] == "require"
            assert kwargs["env"]["PGDATABASE"] == "cognova"
            assert kwargs["env"]["PGHOST"].startswith("dpg-db2iojc9v7es7387i2ig-a.")
            assert kwargs["env"]["PGPORT"] == "5432"
            assert kwargs["env"]["PGUSER"] == "test"
            assert kwargs["env"]["PGPASSWORD"] == "synthetic-password"
        else:
            assert not any(k.startswith("PG") for k in kwargs["env"])
        if failure == "dump" and binary == "pg_dump" and "--version" not in args:
            return SimpleNamespace(returncode=1, stdout=b"", stderr=b"secret error")
        if "--version" in args:
            output = f"{binary} (PostgreSQL) 18.6".encode()
        elif binary == "psql":
            output = b"t" if "pg_stat_ssl" in args[-1] else b"0002_auth_sessions"
            if namespace["os"].environ.get("SUBJECTS_RELEASE") == "true":
                output = (
                    b"t"
                    if "pg_stat_ssl" in args[-1]
                    else b"0003_onboarding_questionnaire"
                )
            if namespace["os"].environ.get("ACTIVITIES_RELEASE") == "true":
                output = b"t" if "pg_stat_ssl" in args[-1] else b"0004_subjects"
            if "count(*)" in args[-1]:
                output = b"0"
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
                    "user_academic_goal_legacy",
                    "questionnaire_responses",
                    "subjects",
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


def test_preflight_only_never_connects_or_creates_artifact(
    backup_code, monkeypatch, tmp_path
):
    calls = fake_commands(monkeypatch, backup_code)
    monkeypatch.setenv("VALIDATE_ONLY", "true")
    backup_code["backup"]()
    assert not calls
    assert not (tmp_path / "outputs").exists()
    assert not (tmp_path / "cognova-pre-0003").exists()


def test_libpq_parameters_decode_credentials_and_preserve_options(
    backup_code, monkeypatch, capsys
):
    monkeypatch.setenv(
        "DATABASE_URL",
        (
            "postgresql://test%40user:p%40ss%3Aword@"
            "dpg-db2iojc9v7es7387i2ig-a.oregon-postgres.render.com:5433/cognova"
            "?sslmode=verify-full&channel_binding=require&connect_timeout=12"
        ),
    )
    monkeypatch.setenv("PGHOST", "unwanted-host")
    monkeypatch.setenv("PGSERVICE", "unwanted-service")
    monkeypatch.setenv("DIAGNOSE_CONNECTION", "true")

    def execute(args, **kwargs):
        env = kwargs["env"]
        assert env["PGDATABASE"] == "cognova"
        assert env["PGPORT"] == "5433"
        assert env["PGUSER"] == "test@user"
        assert env["PGPASSWORD"] == "p@ss:word"
        assert env["PGSSLMODE"] == "verify-full"
        assert env["PGCHANNELBINDING"] == "require"
        assert env["PGCONNECT_TIMEOUT"] == "12"
        assert "PGSERVICE" not in env
        assert "DATABASE_URL" not in env
        assert not any("p@ss:word" in arg or "postgresql://" in arg for arg in args)
        return SimpleNamespace(returncode=0, stdout=b"0002_auth_sessions", stderr=b"")

    monkeypatch.setattr(backup_code["subprocess"], "run", execute)
    backup_code["backup"]()
    assert capsys.readouterr().out == "Connection diagnostic: SUCCESS\n"


@pytest.mark.parametrize("failure", ["exit", "timeout", "spawn"])
def test_operation_errors_print_only_constant_label(
    backup_code, monkeypatch, capsys, failure
):
    source = WORKFLOW.read_text(encoding="utf-8")
    script = source.split("python3 - <<'PY'\n", 1)[1].split("          PY\n", 1)[0]
    tree = ast.parse("\n".join(line[10:] for line in script.splitlines()))
    calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "run"
    ]
    assert len(calls) == 16
    labels = []
    for call in calls:
        assert isinstance(call.args[0], ast.Constant)
        labels.append(call.args[0].value)
    assert len(set(labels)) == len(labels)
    native = "native-error synthetic-password " + KEY

    def fail(args, **kwargs):
        if failure == "timeout":
            raise backup_code["subprocess"].TimeoutExpired(
                args, 600, output=native.encode(), stderr=native.encode()
            )
        if failure == "spawn":
            raise OSError(native)
        return SimpleNamespace(
            returncode=1, stdout=native.encode(), stderr=native.encode()
        )

    monkeypatch.setattr(backup_code["subprocess"], "run", fail)
    entry = ast.Module(body=[tree.body[-1]], type_ignores=[])
    for label in labels:
        backup_code["backup"] = lambda label=label: backup_code["run"](
            label, [native], {}, KEY.encode()
        )
        with pytest.raises(SystemExit) as stopped:
            exec(compile(entry, str(WORKFLOW), "exec"), backup_code)
        assert stopped.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == f"::error::Backup stopped at: {label}\n"
        assert captured.err == ""


@pytest.mark.parametrize(
    ("native", "category"),
    [
        ('could not translate host name "sensitive-host"', "DNS"),
        ("connection refused", "TCP_PORT"),
        ("password authentication failed", "AUTHENTICATION"),
        ("SSL error: certificate verify failed", "TLS"),
        ('FATAL:  database "sensitive-db" does not exist', "DATABASE_NOT_FOUND"),
        (
            "connection to server on socket sensitive-path failed",
            "OTHER_PSQL: default_local_socket",
        ),
        ("unrecognized native failure", "OTHER_PSQL"),
    ],
)
def test_connection_diagnostic_is_read_only_and_never_leaks(
    backup_code, monkeypatch, tmp_path, capsys, native, category
):
    monkeypatch.setenv("DIAGNOSE_CONNECTION", "true")
    calls = []

    def execute(args, **kwargs):
        calls.append(args)
        assert Path(args[0]).name == "psql"
        assert args[-1] == (
            "SELECT version_num FROM public.alembic_version ORDER BY version_num"
        )
        assert "default_transaction_read_only=on" in kwargs["env"]["PGOPTIONS"]
        assert kwargs["env"]["LC_ALL"] == "C"
        assert kwargs["capture_output"]
        return SimpleNamespace(
            returncode=2,
            stdout=KEY.encode(),
            stderr=(native + " synthetic-password " + KEY).encode(),
        )

    monkeypatch.setattr(backup_code["subprocess"], "run", execute)
    backup_code["backup"]()
    assert len(calls) == 1
    captured = capsys.readouterr()
    assert captured.out == f"Connection diagnostic: {category}\n"
    assert captured.err == ""
    assert not (tmp_path / "outputs").exists()
    assert not (tmp_path / "cognova-pre-0003").exists()


def test_subjects_backup_restores_isolated_before_publishing(
    backup_code, monkeypatch, tmp_path, capsys
):
    monkeypatch.setenv("SUBJECTS_RELEASE", "true")
    calls = fake_commands(monkeypatch, backup_code)
    backup_code["backup"]()
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["revision_before"] == "0003_onboarding_questionnaire"
    assert manifest["restore_rehearsal"] == "passed"
    assert len(manifest["restored_counts"]) == 6
    assert manifest["encrypted_file"] == "cognova-pre-0004.dump.gpg"
    assert any("--exit-on-error" in call for call in calls)
    assert not (tmp_path / "cognova-pre-0004/roundtrip.dump").exists()


def test_activities_backup_includes_subjects_and_restore(
    backup_code, monkeypatch, capsys
):
    monkeypatch.setenv("ACTIVITIES_RELEASE", "true")
    calls = fake_commands(monkeypatch, backup_code)
    backup_code["backup"]()
    manifest = json.loads(capsys.readouterr().out)
    assert manifest["revision_before"] == manifest["revision_after"] == "0004_subjects"
    assert manifest["restore_rehearsal"] == "passed"
    assert len(manifest["restored_counts"]) == 7
    assert "subjects" in manifest["restored_counts"]
    assert manifest["encrypted_file"] == "cognova-pre-0005.dump.gpg"
    assert any("--exit-on-error" in call for call in calls)


def test_conflicting_release_flags_never_connect(backup_code, monkeypatch):
    monkeypatch.setenv("ACTIVITIES_RELEASE", "true")
    monkeypatch.setenv("SUBJECTS_RELEASE", "true")
    calls = fake_commands(monkeypatch, backup_code)
    with pytest.raises(ValueError):
        backup_code["backup"]()
    assert not calls
