# Operación futura, permisos y recuperación

## Release autorizado de 0004 — 2026-10-19

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

## Preparación de 0004 Materias

Contrato: [DATA_MODEL](DATA_MODEL.md). Esta entrega implementa y prueba la migración;
no autoriza por sí sola aplicar DDL productivo. Antes del release, respaldo vigente,
inventario y Backend compatible con 0004 explícitamente admitida en readiness.
Runtime: SELECT/INSERT/UPDATE en subjects y USAGE/SELECT en subjects_id_seq, además
de SELECT/UPDATE de users para el bloqueo de asignación. Sin DELETE/TRUNCATE de
subjects, ownership ni DDL. El flujo destructivo futuro requiere política y grants
revisados aparte. No se aplican grants a roles desconocidos en la migración.
Downgrade vía conexión inyectada hacia 0003 solo con subjects vacía; el bloqueo
exclusivo evita una carrera con escrituras. Nunca vaciarla para facilitar rollback.

El release operativo de 0003 está autorizado desde 2026-10-13. Su ejecución real
y bloqueos se registran en [RELEASE_0003](RELEASE_0003.md). No crear recursos nuevos,
datos demo ni una base sustituta. No asumir que autorización equivale a aplicación.

## Roles y grants pendientes de aplicar

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
