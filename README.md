# Cognova Database

Repositorio operativo del esquema PostgreSQL existente de Cognova. No es una API.
Historial: `0001_create_users` → `0002_auth_sessions` → `0003_onboarding_questionnaire`
→ `0004_subjects` → `0005_activities` → `0006_study_sessions`
([contrato](docs/DATA_MODEL.md)).
Las revisiones 0001–0005 se conservan sin cambios. 0003 separa onboarding del registro y conserva
la percepción inicial y las revisiones del cuestionario.
Backend conserva ORM, conexiones, consultas, auth y lógica de negocio.

## Estado vigente — 2026-10-29

**La rama feat/0006-study-sessions prepara Sesiones; producción sigue en0005.**
Main representa el esquema productivo 0005_activities e integra sin squash
feat/0005-activities, incluidos scripts, pruebas y evidencias de los releases.
Producción sí fue operada: 0003 se aplicó el 2026-10-17, 0004 el 2026-10-19 y
0005 el 2026-10-24. El historial no termina en 0002.

- [Estado y trazabilidad](docs/PROJECT_STATE.md).
- [Operación y permisos vigentes](docs/OPERATIONS.md).
- [Evidencia productiva 0005](docs/evidence/0005-release-2026-10-24.json).
- [Backup verificado al aplicar 0005](docs/evidence/0005-backup-2026-10-24.json).
- [Modelo de Materias, Actividades y Sesiones](docs/DATA_MODEL.md).

El SHA de esquema fijado por Backend sigue siendo
604e296e2670d154ba7e18d7afa3f010e66dd42d; integrar main no cambia ese pin.
La preparación0006 no ejecuta migraciones, grants ni backups productivos. Las evidencias contienen
capturas fechadas del release, no un inventario nuevo. No reaplicar helpers históricos.

0006 agrega planificación de estudio, ciclo técnico, resultado y segmentos reales
de ejecución. Backend calcula segundos efectivos sin pausas; DB protege coherencia,
unicidad concurrente y conservación de historia mediante RESTRICT. No timer automático.
Validación local:278 pruebas (225 PostgreSQL), sin omisiones; Ruff/formato y pip check
verdes. Producción requiere un release separado con backup fresco adaptado a0006,
compatibilidad de Backend y permisos mínimos; ver OPERATIONS.

## Instalación y comandos

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
