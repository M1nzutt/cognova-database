# Database handoff — Planes y Retos 0007

## Handoff 0008 pendiente de release

La rama 0008 prepara `study_plans.ai_proposal_snapshot JSONB NULL`, objeto JSON
de máximo 32768 bytes de `jsonb::text`. Backend podrá conservar y devolver tras
refresh la explicación visible y propuesta estructurada vigentes. Los planes
manuales/existentes usan NULL. En regenerate, Backend debe copiar la versión
anterior a `study_plan_decisions.proposed_value` (límite 65536 bytes) y verificar
el tamaño del valor final con sus metadatos antes de escribir. No se guardan
razonamiento interno, prompts, respuesta cruda ni secretos. La migración no otorga
permisos: `cognova_runtime` conserva el DML previo sobre `study_plans`; PUBLIC
sigue revocado y no se conceden DDL, TRUNCATE ni ownership. Producción sigue en
0007 y requiere backup/release 0008 separados antes de desplegar Gemini.

La rama se validó en [CI 42164531703](https://github.com/M1nzutt/cognova-database/actions/runs/42164531703):
400 pruebas aprobadas (332 PostgreSQL real), sin omisiones, más Ruff,
formato, Gitleaks y SQL Alembic offline. Este resultado prepara el backup y
release; no acredita aplicación productiva de 0008.

## Estado productivo

Producción está exactamente en `0007_study_plans_and_challenges`. Se aplicó con el
runner oficial, con pin de código `e750754507545efa6bc2a80515a89db07768a665`,
después del backup previo verificado en GitHub Actions run `41754539310`. El backup
y artifact, preflight y verificación posterior están en [evidencia](evidence/0007-release-2026-11-03.json).

La migración creó seis tablas vacías: `study_plans`, `study_plan_subjects`,
`study_plan_activities`, `study_plan_sessions`, `study_plan_decisions` y
`study_challenges`. Catálogo coincide con el contrato PG18: 43 constraints,
13 FKs compuestas RESTRICT, 21 CHECK, once índices explícitos (20 físicos con
índices PK/UNIQUE) y tres secuencias. Las tablas/secuencias nuevas no tienen ACL
para PUBLIC. `cognova_runtime` tiene solo los grants mínimos acordados; no tiene
TRUNCATE, DDL, ownership ni privilegios elevados.

Conteos preservados de 0001–0006: users=39, auth_sessions=49,
rate_limit_buckets=1, user_academic_goal_legacy=1, questionnaire_responses=46,
subjects=21, activities=10, activity_deadline_events=8, study_sessions=20,
study_session_intervals=21. La verificación posterior fue READ ONLY y no hizo
escrituras de comportamiento en producción.

## Compatibilidad Backend

La migración es aditiva y mantiene las tablas/columnas consumidas por el Backend.
Sin embargo, el Backend productivo en SHA
`4735a697aed69f66f3055c902a00507b66a556e0` todavía valida que la revisión sea
exactamente `0006_study_sessions` en `/ready`. No se puede confirmar readiness
tras 0007 hasta publicar una versión Backend compatible. Las solicitudes a health
y ready expiraron desde el entorno de verificación. No se modificó Backend por el
límite de alcance.

## Evidencia

- [Backup pre-0007](evidence/0007-backup-2026-11-03.json): PostgreSQL 18.6,
  custom dump, decode, restore rehearsal, AES256 roundtrip y digest verificados.
- [Preflight READ ONLY](evidence/0007-preflight-2026-11-03.json): revisión 0006,
  TLSv1.3, inventario y cero transacciones peligrosas.
- [Verificación post-release READ ONLY](evidence/0007-postrelease-readonly-2026-11-03.json):
  revisión 0007, catálogo, grants, secuencias y conteos.
- [Release](evidence/0007-release-2026-11-03.json): commit/rollback, conteos antes
  y después, pin y comprobaciones post-commit.

CI Database checks run `41758908150` pasó sobre el cierre documental SHA
`d2e99723078eb67163bd2ad2ebb147a2a7a790bb`: 395 pruebas, incluidas 328 PostgreSQL
17, Ruff, formato, pip check, checker JUnit, heads, upgrade offline y Gitleaks.
El backup/restore rehearsal fue con PostgreSQL 18.6. La repetición local posterior
no se pudo ejecutar en el entorno Windows aislado: la sandbox denegó el arranque
por `pg_ctl` y el Python del entorno virtual apunta a una instalación base
inaccesible. El smoke productivo tras el release fue estrictamente read-only.
