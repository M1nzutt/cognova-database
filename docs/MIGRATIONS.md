# Migraciones, configuración y validación

## Historial de código y producción

Único head de feat/0006-study-sessions: **0006_study_sessions**, aún no aplicado
a producción. Main y producción documentada conservan **0005_activities**.
Cadena de código: 0001_create_users → 0002_auth_sessions →
0003_onboarding_questionnaire → 0004_subjects → 0005_activities → 0006_study_sessions.
Ver [evidencia](evidence/0005-release-2026-10-24.json) y [OPERATIONS](OPERATIONS.md).
La descripción 0002 inferior es histórica. Integrar la rama no ejecuta migraciones.

## 0006 — ejecución de estudio, sin temporizador automático

Dos tablas: study_sessions y study_session_intervals; contrato en DATA_MODEL.
Upgrade crea checks, claves compuestas RESTRICT, índices parciales y exclusión
GiST nativa. Añade una clave única referenciada a activities, sin alterar sus datos.
No modifica 0001–0005 ni requiere extensión, ORM, autogenerate o nuevos servicios.
El runner oficial acepta `upgrade 0006_study_sessions` y `upgrade head --sql`.
Solo se ha ensayado en PostgreSQL desechable: no ejecutar esos comandos online
contra producción sin el release separado indicado en OPERATIONS.

Downgrade 0006→0005 solo en entorno controlado: toma locks ACCESS EXCLUSIVE,
rechaza cualquier sesión/intervalo y elimina únicamente objetos añadidos por0006
sin CASCADE. Si hay una dependencia futura, toda la reversión falla atómicamente.
No borrar evidencia para habilitarlo; con datos, corregir hacia adelante.
Se probó upgrade desde vacío y0005, repetición, rollback DDL, downgrade vacío y
reupgrade, preservación completa de tablas previas y rechazo de pérdida de datos.

La validación diferida de ejecución observa el estado final transaccional, no el
orden de sentencias. Backend debe escribir padre/intervalos/acumulado en la misma
transacción y manejar errores también al commit. Para comprobar antes del commit
puede usar SET CONSTRAINTS ALL IMMEDIATE. La API inyectada propaga errores; el
consumidor conserva la responsabilidad de no registrar parámetros sensibles.

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

## Esquema histórico de partida (0002)

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

El head de código de la rama es0006; producción documentada es0005 (OPERATIONS).
Ver [DATA_MODEL](DATA_MODEL.md).
Para onboarding ver [SCHEMA_0003](SCHEMA_0003.md).
Estas definiciones describen el punto de partida, no la nulabilidad actual.

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

## Runner vigente y referencia histórica de downgrade 0003

El runner acepta destinos explícitos 0001_create_users, 0002_auth_sessions,
0003_onboarding_questionnaire, 0004_subjects, 0005_activities,
0006_study_sessions y head.
Backend debe fijar la revisión admitida;
no inferir compatibilidad por orden numérico de IDs.

El ejemplo siguiente corresponde exclusivamente al downgrade histórico 0003→0002,
no al estado productivo 0005. Ver DATA_MODEL para restricciones de 0004/0005/0006 y
OPERATIONS para recuperación; nunca vaciar datos para forzar un downgrade.

Downgrade deliberado vía API Alembic: con conexión inyectada, llamar
`command.downgrade(config, "0002_auth_sessions")`. Usa locks exclusivos y aborta
si hay respuestas, onboarding NULL o un goal que difiera del archivo histórico.
No completar datos ficticios, forzar stamp ni usarlo como rollback automático.
La suite real de PostgreSQL está registrada en [PROJECT_STATE](PROJECT_STATE.md).
