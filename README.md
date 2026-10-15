#  Cognova Database

Repositorio operativo del esquema PostgreSQL existente de Cognova. No es una API.
Historial: `0001_create_users` → `0002_auth_sessions` → `0003_onboarding_questionnaire`.
0001 y 0002 permanecen intactas. 0003 separa onboarding del registro y conserva
la percepción inicial y las revisiones del cuestionario.
Backend conserva ORM, conexiones, consultas, auth y lógica de negocio.

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
El release operativo autorizado de 0003 y su evidencia se registran en
[RELEASE_0003](docs/RELEASE_0003.md); consultar el estado antes de operar producción.

## Documentación

- [Arquitectura y ownership](docs/ARCHITECTURE.md)
- [Migraciones, configuración y pruebas](docs/MIGRATIONS.md)
- [Origen y preservación del historial](docs/PROVENANCE.md)
- [Estado verificable y DEPENDENCY BACKEND](docs/PROJECT_STATE.md)
- [Reglas para agentes](docs/AGENT_RULES.md)
- [Operación, permisos y recuperación](docs/OPERATIONS.md)
- [Contrato físico de onboarding y cuestionario](docs/SCHEMA_0003.md)
