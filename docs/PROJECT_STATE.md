# Estado de Cognova Database

Fecha: 2026-10-08. Fase: separación y estabilización; corte backend pendiente.

## Implementado

- Historial copiado desde backend y preservado: 0001_create_users → 0002_auth_sessions.
- Alembic independiente, sin ORM/backend/JWT; configuración por entorno.
- Conexión inyectada, search_path, transacciones y advisory lock compartido.
- CLI con errores sanitizados, dependencias runtime con pins/hashes y docs propias.
- Pruebas offline: 15 passed. Ruff lint y formato correctos (9 archivos Python);
  pip check sin incompatibilidades. El editor no descubrió tests: se usó pytest.

## Evidencia y límites

SHA-256 de las copias coincide con archivos originales. Backend estaba limpio en
5fa90a3; blobs idénticos a 06c3d2a. Python local 3.14.5 en venv propio; instalación
runtime con --require-hashes completada. No se ejecutó ninguna conexión PostgreSQL.
Alembic heads/history confirma una cadena lineal con único head 0002_auth_sessions.
Los tests verifican blobs originales y SQL completo, upgrade por rango y rango
head:head sin DDL; esto último no equivale a probar idempotencia online.
Revisión básica de secretos: sin archivos .env privados, dumps o claves versionados
ni coincidencias de patrones de claves privadas/tokens conocidos. No sustituye
una auditoría completa de seguridad.
No hay TEST_DATABASE_URL configurada, herramientas psql/pg_isready/docker en PATH
ni servicio PostgreSQL encontrado. Integración real, grants y recuperación no
validados. No se modifican backend, frontend ni producción.

## DEPENDENCY BACKEND

Después de que database publique una referencia fija y evidencia PostgreSQL real:

1. Fijar commit/artefacto y verificar digest; no consumir main/latest flotantes.
2. Adaptar CI y fixture de integración para usar esa versión con conexión inyectada
   y esquema test_<uuid>; conservar pruebas ORM/API/auth completas.
3. Retirar migrate() del launcher y verificar conectividad y compatibilidad antes
   de escuchar. Conservar readiness con conjunto exacto {0002_auth_sessions};
   revisión ausente, distinta o múltiples filas debe seguir rechazándose.
4. Tras coordinar el corte, retirar alembic.ini, migrations/, tests DDL ya
   transferidos y dependencia Alembic runtime; actualizar lock, CI y documentación.
   Las herramientas Alembic de fixtures pueden vivir en un entorno separado.
5. Reubicar alembic check junto al ORM en las pruebas de compatibilidad; database
   con metadata=None no puede sustituirlo. Adaptar tests de startup a disponibilidad
   y compatibilidad; conservar health/readiness/database y auth.
6. Coordinar recursos Render existentes, roles migrador/runtime, backup probado y
   eliminación de launchers antiguos capaces de migrar. No recrear base ni Blueprint.

## Siguiente paso

Completar checks offline, añadir integración aislada/CI y registrar resultados.
No declarar listo el corte operativo mientras falte PostgreSQL real y coordinación.
