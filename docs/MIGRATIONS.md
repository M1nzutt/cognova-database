# Migraciones, configuración y validación

## Configuración

`ENVIRONMENT` debe ser development, test o production para conexión propia.
`DATABASE_URL` debe contener host y base PostgreSQL; postgres/postgresql se
normalizan a postgresql+psycopg. Se preservan opciones de conexión como search_path.
Producción exige TLS (require por defecto; acepta verify-ca y verify-full).
Los secretos se inyectan por entorno y no se imprimen en errores del CLI soportado.
`--sql`, heads e history no necesitan URL ni JWT. No hay carga implícita de .env.

Preferir `python -m cognova_database` al CLI Alembic directo: maneja errores sin
imprimir sus mensajes, que podrían incluir credenciales. El CLI no ofrece stamp,
downgrade ni generación de revisiones; el historial original conserva downgrade
para trazabilidad, no como mecanismo automático de rollback.

## Conexión inyectada

```python
from alembic import command
from cognova_database.runner import migration_config

config = migration_config()
with engine.begin() as connection:  # PostgreSQL local desechable configurado aparte
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
```

La conexión evita leer ENVIRONMENT/DATABASE_URL. El llamador selecciona un único
esquema existente mediante search_path antes de migrar. No se fuerza public ni se
crea un esquema automáticamente. Con transacción abierta, el llamador conserva
commit/rollback; sin ella, env.py abre una transacción y la confirma al terminar.
Los errores de la API inyectada se propagan: su consumidor debe sanitizar logs.

Cada ejecución online usa lock_timeout=30s, statement_timeout=120s y advisory lock
transaccional 1943187001. Una transacción inyectada debe terminar pronto: retiene
lock y ajustes SET LOCAL hasta commit/rollback. No usar autocommit.

## Esquema actual

- users: id SERIAL PK; name/email/password_hash/degree_program/academic_goal TEXT
  NOT NULL; semester INTEGER NOT NULL con ck_users_semester_positive (`> 0`);
  created_at y updated_at timestamptz NOT NULL con default now().
- uq_users_email_lower: índice UNIQUE sobre lower(email), reconocido por auth.
- auth_sessions: id UUID PK; user_id INTEGER NOT NULL con FK users.id ON DELETE
  CASCADE; refresh_token_hash y csrf_token_hash VARCHAR(64) NOT NULL; created_at
  timestamptz NOT NULL default now(); expires_at y last_used_at timestamptz NOT NULL;
  revoked_at timestamptz nullable. Índices ix_auth_sessions_user_id y
  ix_auth_sessions_expires_at.
- rate_limit_buckets: key_hash VARCHAR(64) PK, hits INTEGER NOT NULL y expires_at
  timestamptz NOT NULL; índice ix_rate_limit_buckets_expires_at.
- alembic_version: una fila `0002_auth_sessions` al completar el upgrade.

UUID de sesión y onupdate de users.updated_at son comportamientos del ORM, no
defaults/triggers nuevos que database deba añadir.

## Pruebas

`python -m pytest -q -m 'not integration'` comprueba blobs, cadena, SQL PostgreSQL,
configuración y manejo seguro de errores sin conexión. SQL offline no demuestra
idempotencia real, constraints aplicados ni conservación de datos.

Las pruebas integration requieren TEST_DATABASE_URL local desechable y
TEST_DATABASE_ALLOW_DDL=yes. Sin URL se omiten; en CI deben ser obligatorias.
El detalle de lo realmente ejecutado está en [PROJECT_STATE](PROJECT_STATE.md).

La URL de integración admite solo localhost/127.0.0.1/::1, driver
postgresql+psycopg y ninguna opción de URL; esto evita redirigir el host mediante
opciones. El operador sigue siendo responsable de que el destino local sea
desechable y no un túnel a producción. Cada caso crea un esquema test_<uuid>,
establece search_path únicamente a ese esquema y elimina exclusivamente ese
esquema al terminar. No usar credenciales o conexiones de producción.

```sh
# Exportar TEST_DATABASE_URL y TEST_DATABASE_ALLOW_DDL=yes explícitamente.
python -m pytest -q --junitxml=artifacts/test-results.xml
python scripts/check_test_results.py artifacts/test-results.xml
```

El segundo comando rechaza tests omitidos, fallidos o ausencia de integración.
El workflow usa PostgreSQL 17 desechable, REQUIRE_POSTGRES_TESTS=1 y conserva el
JUnit y SQL offline como evidencia. Tener el workflow escrito no significa que
se haya ejecutado. La suite cubre base/esquema vacío, upgrade desde 0001 con datos,
repetición con hashes/sesiones, constraints/índices, cascada, rollback DDL y
search_path con conexión propia e inyectada. Los tests con mocks verifican solo
el contrato de manejo de conexión, nunca comportamiento real del motor.
