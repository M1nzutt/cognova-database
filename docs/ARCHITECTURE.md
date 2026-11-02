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

0003 permite registro mínimo y onboarding posterior. academic_goal permanece
nullable en users como compatibilidad transitoria; su copia histórica está en
user_academic_goal_legacy. El cuestionario completo vive en snapshots append-only
en questionnaire_responses: revisión 1 inicial, última revisión vigente. El goal
legacy es evidencia parcial anterior, no un cuestionario completo fabricado.
Ver [contrato físico](SCHEMA_0003.md). Backend posee opciones, cardinalidades y
validación semántica; database exige estructura, completitud e historial.

0006 separa planificación de estudio, ciclo técnico y resultado final en
study_sessions. study_session_intervals conserva los segmentos reales sin pausas.
Backend calcula actual_duration en segundos desde intervalos cerrados y escribe
ambas tablas en una transacción; DB no ejecuta el timer ni decide transiciones.
Los triggers diferidos validan evidencia al confirmar la transacción. Cada cambio
de intervalo actualiza metadata del padre para serializar validación concurrente.
FK compuestas conservan usuario/materia/actividad coherentes; RESTRICT protege
recursos referenciados e intervalos inmutables. Índices únicos parciales y exclusión
GiST impiden dos ejecuciones por usuario, dos intervalos abiertos y solapamientos.
No se instala extensión. Detalle y permisos en [DATA_MODEL](DATA_MODEL.md).
Producción documentada continúa en 0005; 0006 requiere un release separado.
