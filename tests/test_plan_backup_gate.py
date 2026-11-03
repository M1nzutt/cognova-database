from copy import deepcopy
from datetime import datetime, timedelta, timezone

import pytest

from scripts.release_0007 import TABLES, backup_gate


@pytest.fixture
def manifest():
    now = datetime.now(timezone.utc)
    return {
        "restore_rehearsal": "passed",
        "encryption_roundtrip": "passed",
        "pg_restore_list": "passed",
        "full_archive_decode": "passed",
        "download_verification": "passed",
        "revision_before": "0006_study_sessions",
        "revision_after": "0006_study_sessions",
        "encrypted_file": "cognova-pre-0007.dump.gpg",
        "restored_counts": {**dict.fromkeys(TABLES, 0), "alembic_version": 1},
        "verified_at_utc": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }


def test_pre_0007_backup_gate_requires_fresh_complete_restorable_manifest(manifest):
    backup_gate(manifest)


@pytest.mark.parametrize(
    ("key", "value", "label"),
    [
        ("revision_after", "0007_study_plans_and_challenges", "backup_revision"),
        ("encrypted_file", "other.dump.gpg", "backup_scope"),
        ("expires_at", "2020-01-01T00:00:00Z", "backup_expired"),
        ("restore_rehearsal", "failed", "backup_checks"),
    ],
)
def test_pre_0007_backup_gate_rejects_unusable_manifest(manifest, key, value, label):
    invalid = deepcopy(manifest)
    invalid[key] = value
    with pytest.raises(RuntimeError, match=label):
        backup_gate(invalid)


def test_pre_0007_backup_gate_requires_all_0006_data_tables(manifest):
    del manifest["restored_counts"]["study_session_intervals"]
    with pytest.raises(RuntimeError, match="backup_scope"):
        backup_gate(manifest)
