# Operación futura, permisos y recuperación

## Permiso DELETE de subjects — 2026-10-20

Aplicado y reconfirmado post-commit: únicamente
`GRANT DELETE ON TABLE public.subjects TO cognova_runtime`.
[Evidencia antes/después](evidence/subjects-delete-grant-2026-10-20.json).
Permisos actuales de subjects: SELECT/INSERT/UPDATE/DELETE; sin TRUNCATE.
La autorización explícita de borrado físico del usuario reemplaza la restricción
original de DELETE de la entrega 0004 descrita abajo y en DATA_MODEL.
No modifica la migración 0004 ni el contrato de integridad/ownership de Backend.

Verificación por catálogo/has_table_privilege con migrador: solo cambia ese bit
de autorización. DELETE sigue denegado en users, auth_sessions, alembic_version,
user_academic_goal_legacy y questionnaire_responses. El DELETE preexistente de
rate_limit_buckets se conserva. SELECT/INSERT/UPDATE previos no cambian.
Historia y alembic_version conservan la prohibición de modificaciones existente
(questionnaire_responses admite INSERT append-only). Sin ownership, CREATE
persistente ni privilegios elevados para runtime; TEMP heredado no se modifica.
No se ejecutaron DDL, DML de prueba, cambios de membresía ni de contraseñas.

Helper acotado, con configuración explícita del migrador y ENVIRONMENT=production:
`python -m scripts.grant_subjects_delete inspect --evidence <archivo.json>`.
Modo `apply` concede solo el permiso indicado, compara todas las autorizaciones
de tablas public y aborta si detecta cualquier diferencia adicional; tras commit
reconfirma en READ ONLY. No requiere volver a aplicar el release 0004.
Los secretos se inyectan localmente y no forman parte de la evidencia.

El repositorio no documenta la creación del rol ni contiene su contraseña
disponible; el release previo verificó SET ROLE, no autenticación runtime.
El usuario autorizó explícitamente verificar por catálogo ante esa ausencia.
Login runtime y ejecución real SELECT/INSERT/UPDATE/DELETE quedan pendientes
con el secreto ya desplegado en Backend. No rotarlo para estas comprobaciones.
Backend puede repetir ahora el smoke DELETE; esta entrega no certifica su API.

## Release autorizado de 0004 — 2026-10-19

**Aplicado y confirmado** 2026-10-19 17:34:03Z; reconfirmación READ ONLY
17:34:32Z. [Evidencia](evidence/0004-release-2026-10-19.json).
Revisión anterior 0003, actual 0004; datos, estructura y triggers previos intactos.
Backup fresco run 39294218069 / artifact 12206263488, recuperado en ensayo
aislado; [manifest y hashes](evidence/0004-backup-2026-10-19.json).
Expira 2026-10-26T17:27:44Z. Clave custodiada por el usuario; no rotada.
Grants subjects/secuencia ya aplicados a cognova_runtime, sin DELETE/TRUNCATE;
no repetir el helper de aplicación (exige 0003). Para operación posterior usar
inventario READ ONLY y readiness 0004. El siguiente procedimiento se conserva
como trazabilidad/reproducción controlada, no como instrucción de reaplicación.

El usuario autoriza aplicar 0004 y habilitar cognova_runtime para Backend Materias
06f6c4b1c94ddf6da4c78b518b2f7ccc0d2ad63c (database fijado c3394c3).
El workflow registrado backup-pre-0003.yml admite subjects_release=true para este
release: exige exactamente 0003 antes/después, verifica seis tablas, decodifica el
dump y ensaya pg_restore --exit-on-error en un contenedor PostgreSQL 18 aislado,
sin credenciales productivas. Omite ownership/ACL en el ensayo: los roles/grants
se verifican por separado. Publica solo cognova-pre-0004.dump.gpg, AES-256, con
roundtrip SHA-256 y retención de siete días. El nombre histórico del workflow y
del artifact se conserva; identificar alcance por el manifest y archivo interior.
Sin subjects_release conserva el procedimiento pre-0003. Verificar éxito, fecha,
SHA del ciphertext descargado y restauración antes de autorizar el helper DDL.

Aplicación autorizada con DATABASE_URL/ENVIRONMENT inyectados explícitamente:
`python scripts/release_0004.py --apply --backup-evidence
docs/evidence/0004-backup-2026-10-19.json --evidence
docs/evidence/0004-release-2026-10-19.json` (una línea).
Requiere backup verificado menor de 24 horas y revisión exacta 0003 bajo locks.
La API migration_config/conexión inyectada aplica exactamente 0004 y concede
SELECT/INSERT/UPDATE en subjects y USAGE/SELECT en subjects_id_seq. Verifica
preservación de todas las filas/columnas, estructura y triggers anteriores antes
del commit. Cualquier fallo aborta toda la transacción. Tras commit repite los
checks en READ ONLY; si reporta committed=true con fallo posterior, investigar
sin repetir --apply ni ejecutar downgrade.

El migrador tiene ADMIN, INHERIT=false y SET=false sobre cognova_runtime.
El helper habilita SET solo dentro de un savepoint para comprobar current_user,
SELECT y autorización INSERT/UPDATE mediante EXPLAIN sin ANALYZE; ensaya rechazo
42501 de DELETE, ALTER/CREATE y modificación de historia/alembic_version.
Rollback del savepoint revierte toda habilitación de membresía, sin cambio
permanente. DML real y reglas de capacidad se prueban solo en PostgreSQL local.
No se utiliza ni rota la contraseña runtime. TEMP heredado existente permite
objetos temporales propios; no hay DDL sobre objetos persistentes. Revocar TEMP
de PUBLIC afectaría otros roles y queda fuera de los grants de esta entrega.

## Contrato operativo de 0004 Materias

Contrato: [DATA_MODEL](DATA_MODEL.md). El código por sí solo no autoriza aplicar
DDL productivo; el release autorizado y aplicado figura arriba. Antes de releases, respaldo vigente,
inventario y Backend compatible con 0004 explícitamente admitida en readiness.
Runtime: SELECT/INSERT/UPDATE/DELETE en subjects y USAGE/SELECT en subjects_id_seq, además
de SELECT/UPDATE de users para el bloqueo de asignación. DELETE fue autorizado
posteriormente según la sección 2026-10-20. Siguen prohibidos TRUNCATE,
ownership y DDL persistente.
No se aplican grants a roles desconocidos en la migración.
Downgrade vía conexión inyectada hacia 0003 solo con subjects vacía; el bloqueo
exclusivo evita una carrera con escrituras. Nunca vaciarla para facilitar rollback.

El release operativo de 0003 está autorizado desde 2026-10-13. Su ejecución real
y bloqueos se registran en [RELEASE_0003](RELEASE_0003.md). No crear recursos nuevos,
datos demo ni una base sustituta. No asumir que autorización equivale a aplicación.

## Contrato de roles y grants

El rol migrador debe poseer el esquema/tablas y poder ejecutar DDL. El rol runtime
del backend requiere CONNECT a la base, USAGE del esquema, DML necesario sobre
users/auth_sessions/rate_limit_buckets, USAGE/SELECT de la secuencia users_id_seq,
y SELECT sobre alembic_version. No debe poseer tablas ni recibir CREATE/ALTER/DROP.

Para 0003 añadir SELECT/INSERT en questionnaire_responses, solo SELECT en
user_academic_goal_legacy y EXECUTE en cognova_valid_questionnaire_answers.
No conceder UPDATE/DELETE/TRUNCATE de historia ni capacidad de desactivar triggers.
No hay secuencias nuevas: PK user_id y (user_id,revision). Triggers SECURITY INVOKER,
search_path=pg_catalog; referencias internas mediante TG_TABLE_SCHEMA. El bloqueo
de users requiere SELECT/UPDATE, ya necesarios para onboarding. Revisar privilegios
de ejecución por defecto de funciones; runtime no debe ser propietario.

FK RESTRICT bloquea borrar usuarios con historia. La política explícita de
retención/eliminación de cuenta exige coordinación futura; no cambiar a CASCADE
silenciosamente. 0003 toma ACCESS EXCLUSIVE de users para DDL y backfill: evaluar
volumen/ventana. Mantiene lock_timeout=30s y statement_timeout=120s; ante timeout,
rollback y reprogramar. Inventariar nombres/emails legacy fuera de 30/50 con conteos,
remediar deliberadamente y después VALIDATE CONSTRAINT; no truncar ni loguear PII.

Antes del corte, inventariar roles, ownership y privilegios efectivos (incluidos
los heredados de PUBLIC). Con nombres reales revisados por operación, conceder
permisos explícitos sobre objetos actuales y configurar ALTER DEFAULT PRIVILEGES
FOR ROLE del creador real para objetos futuros. No otorgar DML indiscriminado
sobre alembic_version. Verificar con el rol runtime queries de auth y rechazo de
DDL. El rol migrador y su secreto no se entregan al runtime backend.

## Backup y restauración: runbook pendiente de ensayo

1. Operación confirma recursos Render existentes, responsable, versión PostgreSQL,
   retención, RPO/RTO y capacidad de backup del plan realmente contratado.
2. Registrar revisión efectiva y esquema; generar backup consistente con pg_dump
   en formato custom y cliente compatible. Inyectar credenciales por mecanismo
   seguro (servicio/archivo de passwords protegido), nunca en Git ni logs.
3. Cifrar el backup, restringir acceso, calcular digest y registrar fecha,
   versión/alcance y política de expiración. Los hashes/tokens de auth son sensibles.
4. Restaurar con pg_restore en un destino desechable aislado, con errores fatales;
   preparar roles/grants que pg_dump de una sola base no cubre por sí solo.
5. Verificar alembic_version, tablas, constraints, índices, conteos y pruebas de
   aplicación coordinadas. Registrar tiempo y evidencia del ensayo.
6. Solo tras demostrar recuperación, coordinar el corte. Un rollback de backend
   exige una revisión admitida; no ejecutar downgrade destructivo automáticamente.

Este runbook no acredita backup, restauración, retención o grants ya configurados.

## Backup pre-0003 en Actions

El workflow manual [backup-pre-0003.yml](../.github/workflows/backup-pre-0003.yml)
publica exclusivamente un .dump.gpg cifrado mediante BACKUP_ENCRYPTION_KEY. El repo
puede seguir público, pero la clave debe ser aleatoria, secreta, de al menos 32 bytes
y una línea. Guardar la clave de recuperación fuera de GitHub; rotar el secret no
debe eliminar la clave de backups aún retenidos. Retención: siete días.

Después de registrar el workflow en main, dispararlo
manualmente sobre un commit revisado, verificar status=completed/conclusion=success
y artifact no expirado. Comparar SHA-256 del .gpg descargado con el resumen del run;
descifrar en entorno protegido con GnuPG y la clave correspondiente, comparar SHA-256
del dump con el resumen y ejecutar pg_restore --list. No pasar la clave en argumentos
ni escribirla en logs. El digest ZIP de GitHub es distinto de los SHA-256 .gpg/.dump.
El workflow prueba este roundtrip antes del upload; no hace restauración a una base.
Revisar fecha y cambios posteriores antes de migrar. No ejecutar 0003 en este flujo.
