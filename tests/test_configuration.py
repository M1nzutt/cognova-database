import pytest

from cognova_database.configuration import database_url
from cognova_database.runner import main


@pytest.mark.parametrize("scheme", ["postgres", "postgresql", "postgresql+psycopg"])
def test_database_configuration_needs_no_jwt(monkeypatch, scheme):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", f"{scheme}://user:placeholder@localhost/test")
    monkeypatch.delenv("JWT_SECRET", raising=False)
    assert database_url().drivername == "postgresql+psycopg"


@pytest.mark.parametrize("value", ["invalid", "sqlite:///test", "postgresql:///test"])
def test_invalid_urls_do_not_echo_input(monkeypatch, value):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", value)
    with pytest.raises(ValueError) as error:
        database_url()
    assert value not in str(error.value)


def test_environment_is_explicit(monkeypatch):
    monkeypatch.delenv("ENVIRONMENT", raising=False)
    with pytest.raises(ValueError, match="ENVIRONMENT"):
        database_url()


def test_missing_url_is_rejected(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(ValueError, match="DATABASE_URL"):
        database_url()


def test_tls_and_search_path_are_preserved(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://user:placeholder@localhost/test?options=-csearch_path%3Dtest_1",
    )
    url = database_url()
    assert url.query["sslmode"] == "require"
    assert url.query["options"] == "-csearch_path=test_1"
    monkeypatch.setenv("DATABASE_URL", str(url) + "&sslmode=disable")
    with pytest.raises(ValueError, match="TLS"):
        database_url()


def test_runner_returns_failure_without_logging_secret(monkeypatch, capsys):
    def fail(*args, **kwargs):
        raise RuntimeError("private-db-secret")

    monkeypatch.setattr("cognova_database.runner.command.upgrade", fail)
    assert main(["upgrade", "head"]) == 1
    result = capsys.readouterr()
    assert "private-db-secret" not in result.out + result.err
    assert "migration_failed exception_type=RuntimeError" in result.err
