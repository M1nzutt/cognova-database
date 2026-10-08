# Arquitectura

Frontend → REST → Backend → SQLAlchemy/psycopg → PostgreSQL.
Database administra el esquema sobre el PostgreSQL existente mediante Alembic;
no agrega un servicio HTTP ni una base sustituta.

Database posee revisiones, DDL, constraints, índices, seeds físicos futuros y
backup/restauración. Backend conserva ORM, queries, transacciones, autorización y
auth. Frontend nunca recibe credenciales PostgreSQL.

Las revisiones son autocontenidas. [env.py](../migrations/env.py) usa
`target_metadata=None`: no importa `app`, no copia modelos ni comparte settings
JWT. No usar autogenerate ni presentar `alembic check` como detector de drift sin
metadata. La compatibilidad ORM se comprobará en backend contra una versión fija
de database y con sus pruebas reales de auth. Una futura política de generación
requerirá una decisión explícita; no crear ahora una segunda definición de tablas.

Se conserva conexión inyectada y su search_path. Los jobs online usan el mismo
advisory lock transaccional `1943187001` que el launcher transitorio del backend.
Las revisiones se ejecutan dentro de una transacción; el propietario de una
conexión inyectada con transacción abierta conserva commit/rollback y cierre.

`academic_goal` permanece en users. No hay cambios de producto ni nuevas tablas.
