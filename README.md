# Cognova Database

Repositorio operativo del esquema PostgreSQL de Cognova. No es una API.
Historial vigente en código: `0001_create_users` → `0002_auth_sessions` →
`0003_onboarding_questionnaire` → `0004_subjects` → `0005_activities` →
`0006_study_sessions` → `0007_study_plans_and_challenges` →
`0008_ai_plan_proposal_snapshot` → `0009_academic_companion_chat` →
`0010_nullable_password_hash` ([modelo](docs/DATA_MODEL.md)).
Las revisiones 0001–0005 se conservan sin cambios. 0003 separa onboarding del registro y conserva
la percepción inicial y las revisiones del cuestionario.
Backend conserva ORM, conexiones, consultas, auth y lógica de negocio.

## Estado vigente del repositorio — 2026-11-20

`main` tiene como head `0010_nullable_password_hash`. La revisión 0009 fue aplicada
y validada en Docker local el 2026-11-16; al inspeccionar el volumen integrado el
2026-11-20, este aún reportaba 0009. La migración 0010 está en el repositorio, pero
no se confirmó aplicada a ese volumen ni a producción.

El pin que conserva Backend en `tools/database-ref.json` también apunta a 0009,
mientras que su código fuente actual exige 0010. Coordinar actualización del pin,
migración y verificación de Backend antes de declarar cerrada la integración. No
hay evidencia en este corte de un release de Database 0010 en producción.

- [Estado y trazabilidad](docs/PROJECT_STATE.md).
- [Operación y permisos vigentes](docs/OPERATIONS.md).
- [Evidencia productiva 0005](docs/evidence/0005-release-2026-10-24.json).
- [Backup verificado al aplicar 0005](docs/evidence/0005-backup-2026-10-24.json).
- [Release 0006 y grants](docs/evidence/0006-release-2026-11-02.json).
- [Backup verificado al aplicar 0006](docs/evidence/0006-backup-2026-11-02.json).
- [Modelo de Materias, Actividades y Sesiones](docs/DATA_MODEL.md).

Las evidencias de releases anteriores son capturas fechadas, no un inventario en
vivo. No reaplicar helpers históricos.

0006 agrega planificación de estudio, ciclo técnico, resultado y segmentos reales
de ejecución. Backend calcula segundos efectivos sin pausas; DB protege coherencia,
unicidad concurrente y conservación de historia mediante RESTRICT. No timer automático.
La revisión actual añade además snapshot IA, historial del Acompañamiento y permite
hash de contraseña nulo para la cuenta demo sin contraseña en el seed. Ver
[PROJECT_STATE](docs/PROJECT_STATE.md), [OPERATIONS](docs/OPERATIONS.md) y
[DATABASE_HANDOFF](docs/DATABASE_HANDOFF.md) para distinguir estado de código,
validación local y despliegue.

## Instalación y comandos

### Instalación inicial con datos de demostración

El contenedor `database-migrate` ejecuta `python -m cognova_database initialize`.
El inicializador identifica si `public` estaba vacío antes de migrar, aplica el
historial oficial hasta `head` y solo entonces carga
[`demo-academic.sql`](cognova_database/seed/demo-academic.sql). Un marcador
transaccional evita duplicados y permite reintentar si falla una restauración.
En bases existentes registra `skipped` y nunca importa ni reemplaza sus datos.
Recrear contenedores o reconstruir imágenes no vuelve a cargar el seed.

El seed conserva únicamente la cuenta ficticia `demo.software@example.com` y
sus registros académicos. No incluye hash de contraseña, sesiones, conversaciones,
límites de autenticación ni cuentas ajenas. La cuenta comienza sin contraseña:
desde el contenedor Backend, ejecuta el comando interactivo documentado en
[`docs/INITIAL_DEMO_BACKUP.md`](docs/INITIAL_DEMO_BACKUP.md) para definir o
recuperar una credencial; la contraseña se solicita sin eco y nunca se guarda en Git.

Para actualizar el seed, sigue el procedimiento privado de respaldo, sanitización
y revisión descrito en esa guía. Nunca copies un dump completo de producción o
desarrollo al repositorio.

Desde un checkout completo, con Python >=3.11 (validación local en 3.14.5):

```sh
python -m venv .venv
# Activar .venv según el shell.
python -m pip install --require-hashes -r requirements.lock
python -m pip install -e '.[dev]'
python -m cognova_database history
python -m cognova_database heads
python -m cognova_database upgrade head --sql
python -m pytest -q
```

El lock runtime deriva del backend; las herramientas dev se resuelven por separado.
Usar el checkout completo o archivo Git, no distribuir un wheel aislado sin migraciones.
La salida `--sql` es solo revisión DDL: no incluye el advisory lock del runner online.

Para una base **local desechable**, exportar `ENVIRONMENT=test` y `DATABASE_URL`
usando [los placeholders](.env.example), luego:

```sh
python -m cognova_database upgrade head
python -m cognova_database current
```

No se carga `.env` automáticamente. No se requiere JWT ni código del backend.
El estado vigente está en [OPERATIONS](docs/OPERATIONS.md).
[RELEASE_0003](docs/RELEASE_0003.md) es el registro histórico de ese release,
no la revisión productiva actual.

## Documentación

- [Arquitectura y ownership](docs/ARCHITECTURE.md)
- [Migraciones, configuración y pruebas](docs/MIGRATIONS.md)
- [Origen y preservación del historial](docs/PROVENANCE.md)
- [Estado verificable y DEPENDENCY BACKEND](docs/PROJECT_STATE.md)
- [Reglas para agentes](docs/AGENT_RULES.md)
- [Operación, permisos y recuperación](docs/OPERATIONS.md)
- [Contrato físico de onboarding y cuestionario](docs/SCHEMA_0003.md)
