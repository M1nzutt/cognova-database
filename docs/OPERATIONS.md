# Operación futura, permisos y recuperación

No se ha consultado ni modificado producción. No existen seeds o scripts de backup
originales que trasladar. No crear datos demo o una base sustituta en esta fase.

## Roles y grants pendientes de aplicar

El rol migrador debe poseer el esquema/tablas y poder ejecutar DDL. El rol runtime
del backend requiere CONNECT a la base, USAGE del esquema, DML necesario sobre
users/auth_sessions/rate_limit_buckets, USAGE/SELECT de la secuencia users_id_seq,
y SELECT sobre alembic_version. No debe poseer tablas ni recibir CREATE/ALTER/DROP.

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
