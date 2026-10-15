# Operación futura, permisos y recuperación

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
exige repositorio privado. Un artifact no tiene ACL privada independiente en un
repo público: no subir dumps sin resolver la confidencialidad. Retención: siete
días; planificar custodia restringida y expiración antes del release. No publicar
el repositorio mientras conserve artifacts con datos sensibles.

Después de habilitar privacidad y registrar el workflow en main, dispararlo
manualmente sobre un commit revisado, verificar status=completed/conclusion=success
y artifact no expirado. Contrastar manifest con SHA256SUMS y digest del dump al
descargarlo. El digest ZIP de GitHub es distinto del SHA-256 del archivo .dump.
Revisar fecha y cambios posteriores antes de migrar. No ejecutar 0003 en este flujo.
