# Estado de Cognova Database

Fecha: 2026-10-08. Fase: separación y estabilización; corte backend pendiente.

## Implementado

- Historial copiado desde backend y preservado: 0001_create_users → 0002_auth_sessions.
- Alembic independiente, sin ORM/backend/JWT; configuración por entorno.
- Conexión inyectada, search_path, transacciones y advisory lock compartido.
- CLI con errores sanitizados, dependencias runtime con pins/hashes y docs propias.
- Primer bloque: 15 pruebas offline aprobadas, Ruff y pip check correctos;
  commit 7158cb4. El editor no descubrió tests: se usó pytest.
- Segundo bloque: integración PostgreSQL aislada y workflow CI preparados;
  contrato de conexiones inyectadas verificado también offline.

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

Resultado de suite ampliada: **18 passed, 5 skipped**. Las 5 omisiones corresponden
a PostgreSQL real (dos variantes de transacción sobre esquema vacío, upgrade con
datos/repetición, rollback DDL y CLI/search_path). El control de resultados CI
rechazó correctamente el JUnit local por esas omisiones. No se ha ejecutado CI
remota. No presentar esos cinco escenarios como validados ni retirar aún la copia
backend. Las pruebas SQL y mocks no certifican constraints o transacciones reales.
Ruff lint y formato pasan (13 archivos Python); pip check e instalación editable
sin dependencias adicionales pasan. Paquetes usados: Alembic 1.20.0, SQLAlchemy
2.1.3, psycopg 3.3.6, pytest 9.1.1 y Ruff 0.16.10. Otras versiones de Python no
se han probado localmente. No se ha ejecutado auditoría de vulnerabilidades.
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

Ejecutar la suite completa en PostgreSQL 17 local desechable o CI y adjuntar
evidencia sin omisiones. Coordinar luego pruebas ORM/auth backend, permisos y
restauración. No declarar listo el corte operativo mientras falten esos controles.
