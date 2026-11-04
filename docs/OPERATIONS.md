# Operación vigente, permisos y recuperación

## Preparación 0007 Planes y Retos — pendiente de release

La migración, comparador de catálogo y grants mínimos están en main mediante merge
`--no-ff` `2715a02759957f08697ee09a6155ba54afce135e`. Producción sigue en
`0006_study_sessions`; no se conectó a producción ni se ejecutó DDL o grants allí.
El código prepara la operación; la aplicación productiva queda pendiente.

El fix del último run de limpieza se publicó en 2a7cb932f1bcea61f01e4bb9e55d5a4fb8540352
y Database checks run 41745180653 pasó. La workflow de backup solo usa
workflow_dispatch; no se pudo iniciar desde esta ejecución porque no hay una
interfaz funcional de GitHub Actions dispatch disponible. No se produjo backup,
artifact ni rehearsal, así que el release se detuvo antes del preflight productivo.
Producción sigue en la última revisión documentada 0006_study_sessions; no ejecutar
el helper de apply sin completar y verificar el backup.

El workflow manual `backup-pre-0003.yml`, con `plans_challenges_release=true`, exige
exactamente 0006 antes y después, valida las once tablas existentes, cifra AES256,
verifica roundtrip/listado/decodificación y restaura el backup en PostgreSQL 18
aislado. Solo publica el ciphertext por siete días. Tras descargarlo, comparar el
SHA-256 ciphertext con el manifest, registrar `download_verification=passed` y
confirmar que el respaldo y su clave no expiren antes del corte. El helper requiere
que la verificación de descarga se agregue a la evidencia; no acepta un artifact
caducado, un dump incompleto o una revisión diferente.

`scripts/release_0007.py --apply` está protegido por pin exacto de código en main,
working tree limpio, host/base Render fijados, TLS, backup menor de 24 horas,
revisión origen exacta, advisory lock y ACCESS EXCLUSIVE locks. Dentro de una
transacción preserva filas/columnas, estructura, triggers, permisos, membresías y
secuencias anteriores; actualiza Alembic, aplica grants mínimos, y coteja checks,
FKs, índices y ACL contra el contrato probado. Después valida todo de nuevo con
conexión READ ONLY. Cualquier error antes del commit revierte DDL y grants. El
helper nunca ejecuta DML sintético productivo ni downgrade.

Grants de runtime que el release concedería: `study_plans` SELECT/INSERT/UPDATE/
DELETE; relaciones SELECT/INSERT/DELETE; decisiones SELECT/INSERT; Retos
SELECT/INSERT/UPDATE; secuencias nuevas USAGE/SELECT. Ningún TRUNCATE, UPDATE/
DELETE de evidencia de decisiones, DELETE de Retos, UPDATE de secuencias ni DDL.
El código preparado no autoriza el corte: requiere coordinación Backend que admita
0007 y autorización operativa productiva separada.

## Release 0006 aplicado — 2026-11-02

Producción está exactamente en 0006_study_sessions. Aplicación atómica con
runner oficial, pin de migración 96daa0b6f3b1f64c4ccdc00b0d2026aad9cabd30,
merge no-ff fbee151e03f56b97ec54e726abcae63fc786024c y SHA de código en main
usado para el release `20c6fdc21e2a48cd8f5fb37f46545460e9b9a161`. CI verde.
[Evidencia completa](evidence/0006-release-2026-11-02.json) y
[catálogo verificado de tablas, constraints, FKs, índices, triggers y funciones](evidence/0006-schema-contract.json).

Backup pre-0006 run 41537103226 / artifact 13183708284, verificado antes del DDL,
[manifiesto](evidence/0006-backup-2026-11-02.json). SHA-256 ciphertext
3ba26dbda223d71aef599dc264d0780a5cf1e97864b9142aba4aae66149ee84a;
cifrado AES256, listado/decodificación, roundtrip y restauración aislada aprobados.
Incluyó 9 tablas previas, incluidas activities e historial de deadlines.
Expira 2026-11-09; solo se conserva ciphertext y la clave existente sigue bajo
custodia del usuario.

Preflight READ ONLY exacto 0005_activities, TLS activo, cero transacciones
activas relevantes; 26 usuarios, 12 materias, 3 actividades y 8 eventos.
La aplicación bloqueó alembic_version y tablas previas, exigió revisión exacta,
verificó permisos runtime previos, capturó todas las filas/columnas y conservó
secuencias, estructura, triggers, permisos y memberships. Una primera transacción
revirtió antes de commit por la representación nueva de NOT NULL en el catálogo
PG18; el comparador se ajustó para excluir solo esas filas duplicadas y CI/local
pasaron antes del segundo intento exitoso. No hubo DML de comportamiento en prod.

Después del commit: revisión exacta 0006; estudio y sus dos tablas con catálogo
idéntico a referencia: 12 checks, 1 constraint de exclusión, 3 FKs RESTRICT,
2 PK, 8 índices válidos/listos, cinco triggers habilitados y tres funciones
verificadas. FKs RESTRICT e índices parciales/exclusión comprobados.
Se preservaron exactamente users=26, auth_sessions=36, rate_limit_buckets=1,
user_academic_goal_legacy=1, questionnaire_responses=33, subjects=12, activities=3
y activity_deadline_events=8. Tablas nuevas vacías.

Grants mínimos a cognova_runtime:

- study_sessions: SELECT, INSERT, UPDATE, DELETE.
- study_session_intervals: SELECT, INSERT, UPDATE; sin DELETE/TRUNCATE.
- study_sessions_id_seq y study_session_intervals_id_seq: USAGE, SELECT; sin UPDATE.
- Sin TRUNCATE, REFERENCES o TRIGGER en tablas nuevas; sin DDL persistente,
  ownership, memberships ni EXECUTE de funciones nuevas.
- Sin escritura de alembic_version/historia existente; privilegios anteriores
  y grants de otras tablas no cambiaron.

El permiso database TEMP sigue heredado de PUBLIC y ya existía antes de 0006;
no se concedió en el release ni se revocó por el efecto global que tendría retirar
TEMP a PUBLIC. No permite DDL persistente en el esquema. El catálogo y funciones
has_*_privilege se comprobaron después del commit en transacción READ ONLY.

No se ejecutaron probes productivos de INSERT/UPDATE: el comportamiento y el rol
runtime se probaron localmente con PostgreSQL desechable; post-release fue por catálogo.
No downgrade automático. Con datos de sesión, el downgrade falla preservando evidencia;
priorizar corrección hacia adelante.

## Histórico — Preparación 0006 Sesiones — 2026-10-29

La rama feat/0006-study-sessions implementa y ensaya0006 localmente. Producción
continúa documentada en0005; no se conectó ni operó producción en esta entrega.
En esa fase no se ejecutaron backups, grants ni DDL productivos. No hay datos demo.

Antes del release autorizado: fijar SHA probado, coordinar Backend que admita0006
en readiness y confirmar inventario exacto0005, TLS, locks y tamaño de activities.
Crear y verificar un backup fresco que incluya activities y activity_deadline_events
además de todas las tablas anteriores, cifrado, hash y restauración aislada.
Los helpers/workflows existentes solo cubren hasta pre-0005: NO certifican un
backup ni release0006 y requieren adaptación/revisión antes de operar0006.
Evaluar tiempo de lock al construir uq_activities_user_subject_id en activities.

Aplicación futura mediante runner oficial, destino explícito0006_study_sessions,
cuenta migradora y advisory lock1943187001; no usar runtime para DDL. Comparar
filas previas y catálogo antes/después, incluyendo constraints validados, índices
válidos y triggers habilitados. Probar grants mínimos con roles reales por catálogo.
Contrato ensayado localmente con rol temporal restringido:

- study_sessions: SELECT/INSERT/UPDATE/DELETE; DELETE solo sin intervalos.
- study_session_intervals: SELECT/INSERT/UPDATE; sin DELETE/TRUNCATE.
- study_sessions_id_seq y study_session_intervals_id_seq: USAGE/SELECT.
- USAGE de schema; sin CREATE/ownership/DDL ni escritura de alembic_version o
  historia existente. Sin EXECUTE directo de funciones de trigger.

Triggers SECURITY INVOKER usan esos permisos: la escritura de intervalo requiere
UPDATE de study_sessions para serializar solo metadata. El runtime Backend debe
cerrar el intervalo y actualizar acumulado/ciclo/resultado dentro de una transacción.
No existe cálculo automático de duración. Autorización del actor, transición y
retry acotado40001/40P01 pertenecen a Backend; errores pueden aparecer al commit.
PUBLIC no recibe acceso a tablas/secuencias/funciones0006; auditar default privileges
y membresías heredadas del rol real antes del release sin asumir el ensayo como grant.

No downgrade automático: con cualquier sesión/intervalo aborta; con esquema vacío
se ensayó reversión sin CASCADE y con preservación de0001–0005. Priorizar corrección
hacia adelante una vez exista evidencia. Esta preparación deja la migración lista
para revisión/release coordinado que se completó el 2026-11-02.

## Histórico — 0005 aplicado y permisos verificados — evidencia 2026-10-24

Revisión productiva en esa fecha: 0005_activities. Aplicación confirmada 19:38:45Z y
reconfirmada READ ONLY 19:38:54Z. [Evidencia](evidence/0005-release-2026-10-24.json).
No repetir --apply: exige exactamente0004. Para controles posteriores usar lectura
de revisión/catálogo/permisos; ante incidentes conservar datos y reparar hacia adelante.

Backup fresco verificado al aplicar: run40056632732 / artifact12544639694,
[manifest y hashes](evidence/0005-backup-2026-10-24.json), restauración aislada aprobada.
Expira 2026-10-31T03:02:29Z. El archivo descargado contiene solo ciphertext;
la clave de recuperación existente sigue custodiada por usuario.

Grants aplicados exclusivamente a cognova_runtime:

- activities: SELECT, INSERT, UPDATE, DELETE.
- activity_deadline_events: SELECT; ningún INSERT/UPDATE/DELETE/TRUNCATE.
- activities_id_seq: USAGE, SELECT; ningún UPDATE/setval.

El trigger SECURITY DEFINER registra eventos sin INSERT directo ni EXECUTE runtime.
Sin DDL persistente, ownership, privilegios elevados o membresías nuevas; sin cambios
de permisos anteriores, alembic_version o historia. TEMP heredado no se modificó.
Verificado por catálogo y funciones has_*_privilege en producción. DML real e
historial se ensayaron con rol restringido en PostgreSQL desechable, no en producción.
El login/runtime real y smoke HTTP pertenecen al release Backend, comunicado como
cerrado en esta sesión. Aquí se conserva la evidencia Database sin nuevas pruebas API.

Quince usuarios y siete materias, más sesiones/cuestionarios/datos previos, preservados
en todas sus filas/columnas dentro de locks. Catálogo nuevo coincide exactamente con
evidence/0005-schema-contract.json; constraints/índices válidos y triggers habilitados.
El backend productivo debe admitir 0005; no volver a una versión que exija 0004.
No hubo cambios de Backend/Frontend, de credenciales ni de configuración de hosting.
Los procedimientos siguientes conservan trazabilidad; no instruyen reaplicar el release.

## Archivo histórico de releases

Los apartados siguientes hasta el contrato vigente de roles describen fases
pasadas. Sus frases «pendiente», «producción conserva 0004» y grants iniciales
corresponden a esas fechas. Los comandos --apply no son mantenimiento actual.

## Histórico — Release 0005 autorizado — 2026-10-23

Usuario autoriza aplicar0005 y preparar runtime para Backend442f5b2. El workflow
backup-pre-0003.yml admite activities_release=true: exige0004, incluye subjects
y las seis tablas anteriores, restaura aisladamente y publica solo ciphertext
AES256 cognova-pre-0005.dump.gpg. No mezclar flags subjects/activities. Verificar
manifest, restauración, roundtrip y hash descargado antes de DDL.
Runtime: activities SELECT/INSERT/UPDATE/DELETE, events solo SELECT, secuencia
activities_id_seq USAGE/SELECT. Backend no requiere INSERT de historia: la escribe
el trigger SECURITY DEFINER. Verificar por catálogo sin cambiar membresías/secretos.
La ausencia de DDL se refiere a objetos persistentes; TEMP heredado se conserva.


### Procedimiento revisado 0005

Backup verificado: [manifest](evidence/0005-backup-2026-10-24.json),
run40056632732/artifact12544639694, siete tablas incluida subjects. Clave de cifrado
existente custodiada por usuario; no se imprime ni rota. Solo ciphertext descargado.

Aplicar con configuración explícita del migrador y ENVIRONMENT=production:
`python -m scripts.release_0005 --apply --backup-evidence
 docs/evidence/0005-backup-2026-10-24.json --evidence
 docs/evidence/0005-release-2026-10-24.json` (una línea).
El wrapper local ignorado carga exclusivamente DATABASE_URL existente sin imprimirla.
Se exige identidad del recurso, TLS, backup menor de24h/no expirado y revisión0004
bajo locks exclusivos; runner/migraciones deben ser idénticos al SHA fijado.
El runner aplica0005 y los grants específicos en una transacción. Compara todas las
filas/columnas previas en memoria, estructura salvo clave compuesta nueva, triggers,
secuencias, permisos runtime y membresías. No exporta datos ni hashes de filas.
Cualquier fallo anterior al commit revierte DDL/grants. No cambia membresías ni
contraseñas para probar runtime. El catálogo/has_table_privilege certifica permisos;
DML real y reglas se ensayan localmente con rol restringido, sin datos demo productivos.

La referencia evidence/0005-schema-contract.json contiene catálogo local comprobado:
columnas/checks/FK/índices y definiciones exactas de funciones/triggers. Verificar
igualdad productiva y validez de constraints/índices, también después del commit
mediante conexión READ ONLY. Si committed=true, o el fallo ocurre en
commit_in_progress, inspeccionar revisión/evidencia antes de decidir; nunca repetir
--apply a ciegas ni ejecutar downgrade automático. Backend anterior exige0004;
tras aplicar0005 debe seguir el deploy coordinado del Backend Actividades listo.

## Histórico — Preparación 0005 Actividades — 2026-10-21

Esta entrega implementa/prueba/publica código; **no aplica 0005 a producción**.
Producción conserva 0004. No ejecutar helpers históricos de release 0003/0004 para
esta migración ni asumir que su backup/grants certifican el siguiente release.
Contrato físico y separación DB/Backend en DATA_MODEL.
Código/pruebas fijados para handoff: `604e296e2670d154ba7e18d7afa3f010e66dd42d`.
Validación local PostgreSQL 17.11: 184 pruebas, incluidas 142 de integración,
sin skips; SQL offline, Ruff lint/formato y pip check aprobados. Esto no constituye
evidencia de aplicación ni de permisos productivos para 0005.

Antes de un release autorizado: fijar SHA de código, coordinar Backend que admita
0005 en readiness, inventario exacto 0004, respaldo fresco con subjects y datos
previos, restauración comprobada aislada, ventana y revisión de locks. Agregar la
clave compuesta en subjects requiere lock de DDL y construir índice; evaluar tamaño
y concurrencia. Mantener timeouts y advisory lock del runner, no stamp/create_all.
Aplicar mediante runner oficial con destino explícito 0005_activities, comprobar
preservación de filas, constraints/FK/índices y triggers antes/después del commit.
Ni runtime ni sus credenciales ejecutan migraciones.

Permisos mínimos a revisar y conceder en un release separado, al rol real verificado:
- activities: SELECT/INSERT/UPDATE; DELETE solo si Backend ofrece borrado explícito.
- activities_id_seq: USAGE/SELECT.
- activity_deadline_events: solo SELECT; nunca INSERT/UPDATE/DELETE/TRUNCATE.
- Funciones de trigger de 0005: ningún EXECUTE runtime/PUBLIC; tampoco ownership.
  El trigger SECURITY DEFINER escribe historia como propietario y respeta esquema
  explícito. No conceder capacidad de crear/alterar triggers o funciones persistentes.
- Conservar privilegios anteriores; no tocar subjects, alembic_version ni historia
  anterior. Sin grants masivos/default privileges que permitan falsificar eventos.

0005 revoca PUBLIC sobre sus tablas/funciones, sin grants a roles de nombre supuesto.
Auditar también privilegios heredados y ALTER DEFAULT PRIVILEGES del creador: grants
previos específicos a runtime podrían requerir remediación explícita antes de usarlo.
Probar con rol runtime real que UPDATE deadline genera historia sin INSERT/EXECUTE
directos y que escritura/truncado de historia, DDL y alteración de revisión fallan.
La prueba local usa un rol de ensayo temporalmente creado y después eliminado;
no acredita permisos productivos. TEMP preexistente no se revoca.

Rollback transaccional antes de commit no conserva tablas ni eventos parciales.
Downgrade deliberado con conexión inyectada hacia 0004 solo si activities e historia
están vacías; locks exclusivos y DROP sin CASCADE. Subjects con datos se conserva.
Si hay actividades/eventos, mantener schema y coordinar reparación hacia adelante;
no borrar datos ni historia para forzar un downgrade.

## Histórico — Permiso DELETE de subjects — 2026-10-20

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

## Histórico — Release autorizado de 0004 — 2026-10-19

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

## Histórico — Contrato operativo de 0004 Materias

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

## Contrato vigente de roles y grants

0004/0005 añaden los permisos específicos verificados arriba: DML completo en
subjects/activities, USAGE/SELECT de sus secuencias y solo SELECT de eventos.
El contrato base de auth/onboarding siguiente sigue aplicando.


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

## Backup y restauración: procedimiento general

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

Los ensayos aislados pre-0004 y pre-0005 sí están acreditados por sus manifests y
evidencias fechadas. Este procedimiento no acredita una restauración nueva ni la
disponibilidad actual de artifacts; verificar retención y acceso antes de usarlos.

## Backup manual en Actions — nombre histórico pre-0003

El workflow manual [backup-pre-0003.yml](../.github/workflows/backup-pre-0003.yml)
publica exclusivamente un .dump.gpg cifrado mediante BACKUP_ENCRYPTION_KEY. El repo
puede seguir público, pero la clave debe ser aleatoria, secreta, de al menos 32 bytes
y una línea. Guardar la clave de recuperación fuera de GitHub; rotar el secret no
debe eliminar la clave de backups aún retenidos. Retención: siete días.

El workflow ya está registrado en main. Para otro release autorizado, ejecutarlo
solo si sus precondiciones coinciden con la revisión origen requerida; verificar
status=completed/conclusion=success
y artifact no expirado. Comparar SHA-256 del .gpg descargado con el resumen del run;
descifrar en entorno protegido con GnuPG y la clave correspondiente, comparar SHA-256
del dump con el resumen y ejecutar pg_restore --list. No pasar la clave en argumentos
ni escribirla en logs. El digest ZIP de GitHub es distinto de los SHA-256 .gpg/.dump.
El workflow prueba el roundtrip antes del upload. subjects_release=true exige 0003
y ensaya restauración aislada pre-0004; activities_release=true exige 0004 y ensaya
restauración aislada pre-0005. Sin esos flags conserva el modo histórico pre-0003,
que exige 0002 y no realiza restauración aislada. No mezclar flags.
Ningún modo respalda el estado actual 0005: no dispararlo como backup genérico
post-0005 ni saltar sus gates. Otro release requiere preparación separada.
Revisar fecha y cambios posteriores antes de migrar; este workflow no aplica DDL.
