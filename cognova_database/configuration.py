"""Read only database configuration, without loading application secrets."""

import os

from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ArgumentError


def database_url() -> URL:
    environment = os.environ.get("ENVIRONMENT")
    if environment not in {"development", "test", "production"}:
        raise ValueError("ENVIRONMENT must be development, test or production")
    try:
        url = make_url(os.environ["DATABASE_URL"])
    except (KeyError, ValueError, ArgumentError):
        raise ValueError("DATABASE_URL must be a valid PostgreSQL URL") from None
    if url.drivername in {"postgres", "postgresql"}:
        url = url.set(drivername="postgresql+psycopg")
    if url.drivername != "postgresql+psycopg" or not url.host or not url.database:
        raise ValueError("PostgreSQL with psycopg, host and database are required")
    if environment == "production":
        if url.query.get("sslmode", "require") not in {
            "require",
            "verify-ca",
            "verify-full",
        }:
            raise ValueError("Production PostgreSQL requires TLS")
        if "sslmode" not in url.query:
            url = url.update_query_dict({"sslmode": "require"})
    return url
