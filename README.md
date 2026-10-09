#  Cognova Database

Repositorio operativo del esquema PostgreSQL existente de Cognova. No es una API.
El historial original permanece `0001_create_users` → `0002_auth_sessions`.
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
No se ha autorizado ni ejecutado operación contra producción en esta separación.

## Documentación

- [Arquitectura y ownership](docs/ARCHITECTURE.md)
- [Migraciones, configuración y pruebas](docs/MIGRATIONS.md)
- [Origen y preservación del historial](docs/PROVENANCE.md)
- [Estado verificable y DEPENDENCY BACKEND](docs/PROJECT_STATE.md)
- [Reglas para agentes](docs/AGENT_RULES.md)
- [Operación, permisos y recuperación](docs/OPERATIONS.md)
