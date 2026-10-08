"""DDL is allowed only on an explicitly opted-in local disposable database."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.schema import CreateSchema, DropSchema


@pytest.fixture
def pg_engine():
    raw_url = os.environ.get("TEST_DATABASE_URL")
    if not raw_url:
        if os.environ.get("REQUIRE_POSTGRES_TESTS") == "1":
            pytest.fail("CI requires TEST_DATABASE_URL")
        pytest.skip("No disposable PostgreSQL: TEST_DATABASE_URL is unset")
    if os.environ.get("TEST_DATABASE_ALLOW_DDL") != "yes":
        pytest.fail("Set TEST_DATABASE_ALLOW_DDL=yes only for a disposable local DB")
    try:
        url = make_url(raw_url)
    except Exception:
        pytest.fail("Invalid test URL", pytrace=False)
    if (
        url.drivername != "postgresql+psycopg"
        or url.host not in {"localhost", "127.0.0.1", "::1"}
        or not url.database
        or url.query
    ):
        pytest.fail(
            "Tests require local PostgreSQL+psycopg, database and no URL options"
        )
    schema = "test_" + uuid4().hex
    admin = create_engine(
        url, hide_parameters=True, connect_args={"connect_timeout": 5}
    )
    scoped = None
    created = False
    try:
        with admin.begin() as connection:
            connection.execute(CreateSchema(schema))
        created = True
        scoped_url = url.update_query_dict({"options": f"-csearch_path={schema}"})
        scoped = create_engine(
            scoped_url, hide_parameters=True, connect_args={"connect_timeout": 5}
        )
        yield scoped, schema
    finally:
        if scoped is not None:
            scoped.dispose()
        if created:
            with admin.begin() as connection:
                connection.execute(DropSchema(schema, cascade=True))
        admin.dispose()
