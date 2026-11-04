# Reglas para agentes

## Estado vigente — 0007 aplicada en producción — 2026-11-03

- `main` integra `0007_study_plans_and_challenges` mediante merge --no-ff
  `2715a02759957f08697ee09a6155ba54afce135e`. Código fijado para el release:
  `e750754507545efa6bc2a80515a89db07768a665`.
- Producción quedó verificada en `0007_study_plans_and_challenges`. Backup previo,
  preflight TLS/read-only, aplicación y catálogo posterior tienen evidencia en
  `docs/evidence/0007-*.json`.
- Trabajar solo en cognova-database. Backend/Frontend se consultan solo en lectura.
  No cambiar revisiones 0001–0006 ni otros repositorios.
- El Backend productivo aún comprueba readiness contra `0006_study_sessions`;
  no afirmar readiness posterior a 0007. La compatibilidad de Backend queda para
  un cambio separado en su repositorio, fuera de este alcance.
- Grants runtime de 0007 son mínimos; sin PUBLIC, TRUNCATE, DDL persistente,
  ownership ni privilegios elevados. TEMP heredado vía PUBLIC preexistía.

## Histórico — desarrollo 2026-10-29

- Implementar 0006_study_sessions en rama feat/0006-study-sessions según el
  contrato confirmado en DATA_MODEL: planificación, ejecución e intervalos.
- Preservar 0001–0005. Probar únicamente en PostgreSQL local desechable.
- No operar producción ni cambiar Backend/Frontend. No timer automático ni demos.
- Commits atómicos reales y push de la rama; sin squash ni merge a main solicitado.
- Producción permanece en 0005; preparar código no equivale a autorizar su release.

## Histórico — alineación documental 2026-10-25

- Alinear main/documentación con producción 0005; preservar commits sin squash.
- No modificar migraciones, lógica, scripts ni evidencias existentes.
- No operar producción ni modificar otros repositorios.
- Las autorizaciones fechadas siguientes describen fases anteriores, no órdenes
  de repetir releases. Estado vigente en PROJECT_STATE y OPERATIONS.


- Release Actividades autorizado el 2026-10-23: preflight, backup fresco con
  restauración aislada, aplicación 0005 y grants mínimos al runtime identificado.
  Esta autorización sustituye la exclusión productiva de la fase de desarrollo;
  no permite cambios de otros repos ni de 0001–0004. Ver OPERATIONS.

- La fase Actividades autorizada el 2026-10-21 agrega 0005_activities después de
  0004, sin editar 0001–0004. Sustituye las exclusiones históricas de actividades
  de fases anteriores. Alcance: esquema, historial de fechas, pruebas locales,
  documentación y push; no autoriza DDL/grants productivos ni cambios en otros repos.

- Leer README, PROJECT_STATE, ARCHITECTURE, MIGRATIONS y PROVENANCE antes de editar.
- Modificar solo cognova-database. Backend/frontend se consultan solo en lectura.
- No alterar las revisiones históricas; no squash, renumeración, stamp ni create_all.
- No copiar ORM, auth o settings del backend. Respetar el alcance explícito vigente;
  las limitaciones de producto de fases anteriores son históricas.
- 0003 autoriza academic_goal nullable con copia histórica inmutable; leer
  SCHEMA_0003. No eliminar valores ni fabricar respuestas faltantes.
- La fase Materias autorizada el 2026-10-18 agrega 0004_subjects; leer DATA_MODEL.
  Preservar 0001–0003, probar en PostgreSQL desechable y no implementar Backend,
  frontend, IA ni actividades. Desarrollo y push no implican despliegue productivo.
- La fase operativa autorizada el 2026-10-13 permite inventario, respaldo,
  aplicación de 0003 y verificación en el PostgreSQL Render existente. Identificar
  el recurso y verificar respaldo antes de DDL; no recrear recursos ni borrar datos.
  No exponer ni versionar credenciales. No modificar backend/frontend.
- Probar solo con PostgreSQL local desechable y opt-in explícito; nunca SQLite.
- Mantener conexión inyectada, search_path, transacciones y bloqueo compartido.
- No retirar migraciones del backend: documentar DEPENDENCY BACKEND.
- Antes de cada commit: pruebas/checks, diff, revisión básica de secretos,
  documentación y PROJECT_STATE. Commits pequeños; no afirmar pruebas no ejecutadas.
