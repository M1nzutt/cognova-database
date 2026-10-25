from datetime import datetime, timedelta, timezone

import pytest

from scripts.release_0005 import backup_gate


def manifest():
    now = datetime.now(timezone.utc)
    return {
        **{
            k: "passed"
            for k in (
                "restore_rehearsal",
                "encryption_roundtrip",
                "pg_restore_list",
                "full_archive_decode",
                "download_verification",
            )
        },
        "revision_before": "0004_subjects",
        "revision_after": "0004_subjects",
        "encrypted_file": "cognova-pre-0005.dump.gpg",
        "restored_counts": {"subjects": 7},
        "verified_at_utc": now.isoformat(),
        "expires_at": (now + timedelta(days=7)).isoformat(),
    }


def test_valid_fresh_backup():
    backup_gate(manifest())


@pytest.mark.parametrize(
    "key,value",
    [
        ("restore_rehearsal", "not_performed"),
        ("revision_before", "0003_onboarding_questionnaire"),
        ("verified_at_utc", "2020-01-01T00:00:00Z"),
        ("expires_at", "2020-01-01T00:00:00Z"),
        ("restored_counts", {}),
        ("download_verification", "failed"),
    ],
)
def test_release_refuses_invalid_backup(key, value):
    data = manifest()
    data[key] = value
    with pytest.raises(RuntimeError):
        backup_gate(data)
