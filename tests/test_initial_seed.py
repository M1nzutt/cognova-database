import re
from pathlib import Path

import pytest

from scripts.prepare_demo_seed import prepare

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "cognova_database" / "seed" / "demo-academic.sql"


def test_versioned_seed_contains_only_passwordless_demo_identity():
    sql = SEED.read_text(encoding="utf-8")

    assert len(re.findall(r"INSERT INTO public\.users \(", sql)) == 1
    assert "VALUES (36, 'Lucia Torres Demo', 'demo.software@example.com', NULL," in sql
    assert set(
        re.findall(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", sql, re.IGNORECASE)
    ) == {"demo.software@example.com"}
    assert not re.search(r"\$argon2(?:id|i|d)\$", sql)
    assert not re.search(r"(?im)^\\(?:restrict|unrestrict)", sql)
    for table in ("auth_sessions", "academic_conversations", "academic_messages"):
        assert f"INSERT INTO public.{table} " not in sql


def test_private_snapshot_sanitizer_is_guarded_to_disposable_database():
    sql = (ROOT / "scripts" / "sanitize_demo_snapshot.sql").read_text(encoding="utf-8")
    assert "current_database() <> 'cognova_seed_scratch'" in sql
    assert "scratch_sanitization_requires_superuser" in sql
    assert "UPDATE public.users SET password_hash = NULL" in sql
    assert "unexpected_non_demo_data" in sql
    assert "'public.users_id_seq'" in sql
    assert "public.academic_conversations_id_seq', 1, false" in sql


def test_seed_preparation_adds_trigger_window_and_strips_psql_meta(tmp_path):
    source = tmp_path / "dump.sql"
    destination = tmp_path / "seed.sql"
    source.write_text(
        "\\restrict random-token\n"
        "INSERT INTO public.users (id, name, email, password_hash, degree_program) "
        "VALUES (36, 'Lucia Torres Demo', 'demo.software@example.com', NULL, 'Demo');\n"
        "INSERT INTO public.subjects (id, user_id) VALUES (25, 36);\n"
        "INSERT INTO public.activities (id, user_id, original_deadline) "
        "VALUES (1, 36, NULL);\n"
        "\\unrestrict random-token\n",
        encoding="utf-8",
    )

    prepare(source, destination)
    result = destination.read_text(encoding="utf-8")
    assert "\\restrict" not in result
    assert result.index("DISABLE TRIGGER activity_prepare") < result.index(
        "INSERT INTO public.activities"
    )
    assert result.index("ENABLE TRIGGER activity_prepare") > result.index(
        "INSERT INTO public.activities"
    )
    assert result.endswith("\n") and not result.endswith("\n\n")


def test_seed_preparation_rejects_non_demo_identity_and_credentials(tmp_path):
    source = tmp_path / "dump.sql"
    destination = tmp_path / "seed.sql"
    source.write_text(
        "INSERT INTO public.users (id, name, email, password_hash) "
        "VALUES (36, 'Other', 'other@example.com', NULL);\n"
        "INSERT INTO public.activities (id, user_id) VALUES (1, 36);\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="demo_identity_or_null_password_missing"):
        prepare(source, destination)
