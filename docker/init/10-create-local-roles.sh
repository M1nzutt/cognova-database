#!/bin/sh
set -eu

: "${POSTGRES_USER:?POSTGRES_USER is required by the official PostgreSQL image}"
: "${POSTGRES_DB:?POSTGRES_DB is required by the official PostgreSQL image}"
: "${COGNOVA_RUNTIME_PASSWORD:?COGNOVA_RUNTIME_PASSWORD is required}"
: "${COGNOVA_MIGRATOR_PASSWORD:?COGNOVA_MIGRATOR_PASSWORD is required}"

psql --set=ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<'SQL'
\set ON_ERROR_STOP on
\getenv database_name POSTGRES_DB
\getenv runtime_password COGNOVA_RUNTIME_PASSWORD
\getenv migrator_password COGNOVA_MIGRATOR_PASSWORD

CREATE ROLE cognova_runtime
    WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    PASSWORD :'runtime_password';
CREATE ROLE cognova_migrator
    WITH LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOREPLICATION NOBYPASSRLS
    PASSWORD :'migrator_password';

GRANT CONNECT ON DATABASE :"database_name" TO cognova_runtime, cognova_migrator;
REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO cognova_runtime;
GRANT USAGE, CREATE ON SCHEMA public TO cognova_migrator;
SQL
