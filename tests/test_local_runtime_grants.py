import pytest

from scripts.prepare_local_runtime import (
    EXPECTED_REVISION,
    RUNTIME_ROLE,
    SEQUENCES,
    TABLE_PRIVILEGES,
    validate_local_target,
)


def test_compose_runtime_grants_are_limited_to_application_dml():
    assert EXPECTED_REVISION == "0009_academic_companion_chat"
    assert TABLE_PRIVILEGES["study_plans"] == frozenset(
        {"SELECT", "INSERT", "UPDATE", "DELETE"}
    )
    assert TABLE_PRIVILEGES["study_plan_decisions"] == frozenset({"SELECT", "INSERT"})
    assert TABLE_PRIVILEGES["study_challenges"] == frozenset(
        {"SELECT", "INSERT", "UPDATE"}
    )
    assert TABLE_PRIVILEGES["academic_conversations"] == frozenset(
        {"SELECT", "INSERT", "UPDATE", "DELETE"}
    )
    assert TABLE_PRIVILEGES["academic_messages"] == frozenset({"SELECT", "INSERT"})
    assert all(
        "TRUNCATE" not in privileges
        and "REFERENCES" not in privileges
        and "TRIGGER" not in privileges
        for privileges in TABLE_PRIVILEGES.values()
    )


def test_interval_sequence_is_granted_for_timer_inserts():
    assert "study_session_intervals_id_seq" in SEQUENCES
    assert "academic_messages_id_seq" in SEQUENCES


def test_runtime_grant_tool_is_confined_to_the_compose_migrator():
    validate_local_target("development", "postgres", "cognova_migrator")


@pytest.mark.parametrize(
    ("environment", "host", "user"),
    [
        ("production", "postgres", "cognova_migrator"),
        ("test", "postgres", "cognova_migrator"),
        ("development", "localhost", "cognova_migrator"),
        ("development", "postgres", RUNTIME_ROLE),
    ],
)
def test_runtime_grant_tool_rejects_non_local_targets(environment, host, user):
    with pytest.raises(ValueError):
        validate_local_target(environment, host, user)
