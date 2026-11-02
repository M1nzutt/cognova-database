import pytest
from sqlalchemy import text

from cognova_database.runner import main

pytestmark = pytest.mark.integration


def test_runner_explicit_studies_and_head(pg_engine, monkeypatch):
    engine, schema = pg_engine
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", engine.url.render_as_string(hide_password=False))
    assert main(["upgrade", "0005_activities"]) == 0
    assert main(["upgrade", "0006_study_sessions"]) == 0
    assert main(["upgrade", "head"]) == 0
    assert main(["current"]) == 0
    with engine.connect() as c:
        assert c.scalar(text("SELECT current_schema()")) == schema
        assert c.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0006_study_sessions"
        )
        assert c.scalar(text("SELECT count(*) FROM study_sessions")) == 0
