# Release operativo 0003 — procedimiento y evidencia

Actualización: 2026-10-15. Objetivo actual: backup manual pre-0003, sin DDL.
Estado: **cifrado autorizado e implementado; ejecución y evidencia pendientes**.

## Adaptación a artifact cifrado

El usuario autorizó usar BACKUP_ENCRYPTION_KEY junto a DATABASE_URL como secrets.
La nueva versión elimina el requisito de repositorio privado y conserva únicamente
el archivo cognova-pre-0003.dump.gpg en el artifact. No sube dump plano, manifest,
TOC ni SHA256SUMS: tamaños, fechas y hashes se registran como metadata no sensible
en el resumen/log del run. La URL y clave no se imprimen.

GnuPG simétrico AES-256, S2K iterado con SHA-512 y count=65011712; clave aleatoria
de al menos 32 bytes y una línea, enviada por stdin (passphrase-fd=0), sin archivo
de clave ni argumento visible. BACKUP_ENCRYPTION_KEY no se propaga a procesos
PostgreSQL; la conexión no se propaga a GnuPG. Primero pg_restore --list y lectura
completa del dump, después cifrado y descifrado temporal con comparación SHA-256.
Se eliminan ambos archivos planos antes del upload; limpieza siempre al terminar.
El output de upload solo se habilita tras verificar el roundtrip completo.

El artifact cifrado puede ser descargable en el repo público: su confidencialidad
depende de la clave. Custodiar una copia de recuperación fuera de GitHub y conservar
la versión de clave correspondiente a cada backup, incluso si el secret se rota.
La verificación de descifrado no equivale a restauración ejecutada en una base.

Validación offline de la adaptación: 11 pruebas sintéticas cubren fallos de dump,
revisión, TOC, cifrado y roundtrip, ausencia/forma de clave y metadata sin secretos.
Registro inicial en main y dispatch manual autorizados como parte de ejecutar el
workflow; solo se registra ese YAML, sin migrar ni desplegar aplicaciones.

## Primera versión del workflow (histórica, sustituida por cifrado)

[backup-pre-0003.yml](../.github/workflows/backup-pre-0003.yml) usa solo
workflow_dispatch, sin push, cron ni triggers PR. Solo DATABASE_URL es un secret
de configuración; github.token es el token efímero de plataforma para comprobar
visibilidad, no una credencial PostgreSQL alternativa. No carga el .env local.

Instala postgresql-client-18 desde PGDG en ubuntu-24.04, utiliza sesiones de solo
lectura/TLS y rechaza un recurso diferente o una revisión distinta de 0002.
Genera pg_dump custom y verifica pg_restore --list, presencia de los datos de las
cuatro tablas y decodificación completa a /dev/null (sin ejecutar SQL). Calcula
SHA-256, tamaño, fecha UTC y versiones. Solo tras éxito publica dump, manifest.json
y SHA256SUMS, con retención de siete días. No publica errores nativos, TOC, filas,
credenciales ni datos en logs. Limpia archivos locales al finalizar. Ningún paso
aplica migraciones ni ejecuta DDL. Verificar el archivo no acredita un ensayo de
restauración, que debe registrarse separadamente.

### Bloqueo comprobado en GitHub

La API de GitHub confirmó visibility=public/private=false para
M1nzutt/cognova-database, con rama predeterminada main. GitHub no ofrece privacidad
individual por artifact: usuarios autenticados con lectura del repo pueden
descargarlos. No se puede llamar privado a un dump subido a este repositorio público.
El workflow verifica la privacidad antes de acceder al secret/base y nuevamente
antes del upload; aborta si el repositorio es público.

Se solicitó elegir entre repositorio privado o autorización de artifact cifrado
con clave de recuperación fuera de GitHub. No se cambió visibilidad ni se creó una
clave. La versión preparada exige repo privado; la alternativa cifrada requiere
adaptación explícita. Hasta resolverlo no se ejecuta el backup ni se suben datos.

Además, workflow_dispatch exige registrar el workflow en la rama predeterminada
para activarlo por primera vez. El archivo se prepara/publica en la rama de trabajo;
su registro en main y dispatch quedan pendientes junto con la decisión de privacidad.

Evidencia real de esta fase: workflow escrito y validado offline; **sin run de
backup ni artifact, tamaño, digest o versión cliente ejecutada que certificar**.
Seis pruebas sintéticas cubren fallos de dump/revisión/TOC, destino distinto/secret
ausente y manifest sin filtraciones. No constituyen un backup de producción.

Fuentes oficiales:
- [Acceso a artifacts](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/download-workflow-artifacts).
- [Requisito de rama predeterminada](https://docs.github.com/en/actions/how-tos/manage-workflow-runs/manually-run-a-workflow).
- [Cliente PostgreSQL en Ubuntu](https://www.postgresql.org/download/linux/ubuntu/).

Esta fase parte de 8 commits. El commit de workflow, pruebas y documentación deja
9 commits en esta rama (492 faltantes hasta 501), sin commits vacíos ni squash.

## Inventario productivo confirmado — 2026-10-14

El .env se cargó explícitamente en memoria, sin mostrar su contenido. SQLAlchemy
2.1.3 está instalado sin extensiones nativas; importación y pip check correctos.
No cambió el lock, runner ni las migraciones fijadas por backend. El inventario
revisado solo ejecutó transacciones READ ONLY, con timeout de sentencia de 15s.

- Etiqueta de recurso derivada del host Render: dpg-db2iojc9v7es7387i2ig-a.
- Base cognova, esquema public, PostgreSQL 18.6, TLS confirmado por pg_stat_ssl.
- Rol conectado cognova_user; recurso fijado por fingerprint sin credenciales.
- alembic_version: exactamente una fila 0002_auth_sessions en ambas lecturas.
- Conteos: users=1, auth_sessions=3, rate_limit_buckets=2 en ambas lecturas.
- Cero anomalías detectadas para name/email vacíos o fuera de máximos 30/50.
- Solo existen las cuatro tablas de 0002; las dos tablas nuevas aún no existen.
- users conserva NOT NULL en degree_program/semester/academic_goal.
- uq_users_email_lower UNIQUE sobre lower(email), ck_users_semester_positive,
  índices ix_auth_sessions_user_id/ix_auth_sessions_expires_at/
  ix_rate_limit_buckets_expires_at y FK de sesiones ON DELETE CASCADE presentes.

Evidencia sin datos de usuarios ni credenciales:
[inventario JSON](evidence/0003-preflight-2026-10-14.json).
Última observación: 2026-10-15T02:59:10Z (2026-10-14 en America/Bogota).
La igualdad de conteos no se presenta como prueba de igualdad de contenido.

### Permisos observados

cognova_user es propietario de las cuatro tablas y tiene USAGE/CREATE en public;
no es superusuario, pero tiene CREATEROLE/CREATEDB y privilegios DML/TRUNCATE/TRIGGER
sobre las tablas. El acceso es apto para administración del esquema, no evidencia
de un rol runtime separado de mínimo privilegio. No se conoce la identidad efectiva
del rol usado por el backend desplegado. Si usa cognova_user, conserva capacidad
DDL/ownership y requiere separación coordinada. No se cambiaron roles ni grants.
Los permisos de objetos nuevos no pueden certificarse porque todavía no existen.

### Respaldo: bloqueo real antes de DDL

El cliente local anterior era PostgreSQL 17, incompatible para pg_dump de un
servidor 18. Se descargó el paquete oficial EDB PostgreSQL 18.6 y se extrajeron
únicamente clientes en artifacts/postgres18-client (ignorado por Git). No se creó
otra base, servidor ni servicio. Windows Application Control bloqueó pg_dump.exe
al ejecutar --version, antes de cualquier conexión de respaldo. pg_restore sí
reportó versión 18.6, pero no hay archivo de backup que validar/restaurar.

No se deshabilitó ni evadió la política de Windows. Tampoco existe acceso al panel/API
Render para verificar plan, snapshot/PITR, fecha, estado o procedimiento recuperable.
No se afirma que el servicio carezca de backups: su disponibilidad no se pudo
comprobar. No se generó un dump ni se ejecutó un ensayo de restauración.

**Decisión: detenerse antes de migrar.** Sin backup/mecanismo recuperable verificado,
no se cumple el prerrequisito del usuario. Se solicitó un backup reciente verificable,
acceso al respaldo Render o ejecución de pg_dump 18 en un entorno autorizado.
La base sigue en 0002. No se realizaron upgrade, downgrade, stamp ni escrituras.

## Identidad y código comprobado

- Repo cognova-database; rama feat/0003-onboarding-questionnaire.
- SHA fijado por backend: 232c43130c0fb3eddd32e1dd3707368ba0d87d4c, disponible localmente.
- Revisión 0003_onboarding_questionnaire, padre 0002_auth_sessions.
- Blob de 0003: 5e6e5c25d631efb6d0015fabce2b64ae9866fba1.
- Runner/migraciones actuales sin diff respecto al SHA fijado.
- Inicio: 5 commits, árbol limpio en 28fa023abeb13c687417e18282710891ac188e29.
- git ls-remote confirmó ese mismo SHA en la rama publicada. Las revisiones y
  tooling coinciden con 232c431; la diferencia hasta 28fa023 es documental.

## Historial del bloqueo de acceso (superado)

No están configuradas DATABASE_URL, RENDER_API_KEY, RENDER_API_TOKEN ni variables
PGHOST/PGDATABASE/PGUSER/PGPASSWORD/PGSERVICE en el proceso disponible. No hay .env
local ni CLI Render en PATH. No se encontraron herramientas Render dedicadas en
el catálogo disponible. Inventario de navegadores vacío; abrir Render falló porque
el navegador integrado no está disponible. No se buscaron ni imprimieron secretos.

Se solicitó habilitar acceso por entorno seguro y nombre/ID del recurso, o una
sesión Render accesible. No enviar contraseñas por chat ni incluirlas en Git.
No se puede identificar el recurso real a partir de un nombre de Blueprint antiguo.

### Reintento tras aviso de DATABASE_URL configurada

El usuario indicó que configuró DATABASE_URL. Se comprobó nuevamente su presencia
sin imprimir el valor: no aparece en el proceso sandbox ni, fuera del sandbox, en
los ámbitos Windows Process, User o Machine. No existe .env local ni otro archivo
.env de conexión en la raíz (solo .env.example). .env y .env.local están ignorados.
Esto no demuestra que falte en una terminal independiente: una variable definida
solo en esa terminal no se hereda por los procesos ya abiertos del agente.

Se solicitó la ubicación o cargarla mediante el .env ignorado, sin enviar el secreto
por chat. No se intentó conectar a un host alternativo, ni se ejecutaron consultas,
backup o migración. El bloqueo sigue siendo acceso a la configuración efectiva,
no un fallo PostgreSQL ni un riesgo de pérdida de datos observado.

## Secuencia operativa preparada (pendiente de ejecutar)

1. Correlacionar el PostgreSQL Render real (ID/nombre/estado/región/versión/plan)
   con la conexión efectiva del backend. Registrar base/esquema y roles, sin URL
   completa, contraseña o tokens. Confirmar que no es la instancia de pruebas.
2. Inventario en transacción de solo lectura: current_database/current_schema,
   current_user, server_version, search_path, todas las filas alembic_version,
   conteos users/auth_sessions/rate_limit_buckets, columnas/nulabilidad/defaults,
   pg_constraint, pg_indexes, ownership y privilegios efectivos runtime/migrador.
   Registrar anomalías de name/email fuera de 30/50 mediante conteos sin PII.
3. Respaldo antes de DDL: inspeccionar capacidad efectiva del servicio. Usar snapshot
   recuperable identificado por ID/fecha/estado, o pg_dump custom con cliente
   compatible, salida completa y código 0. Verificar archivo con pg_restore --list
   y digest; esa inspección no sustituye ensayo de restauración. Probar recuperación
   en entorno aislado cuando sea posible y documentar alcance/limitaciones.
   Proteger/cifrar backup fuera de Git. Nunca documentar un backup no observado.
4. Si el plan no proporciona backup verificable, intentar respaldo lógico con
   permisos disponibles. Si tampoco es posible, registrar la limitación concreta
   y no marcar cumplido el prerrequisito de recuperación ni ejecutar DDL a ciegas.
5. Acordar ventana sin escrituras competidoras; no alterar servicios externos desde
   este repo. Comparar contenido previo/posterior sin persistir datos personales
   en evidencia pública. Conteos iguales por sí solos no prueban preservación.
   Usar comparación temporal por claves/digests del contenido en almacenamiento
   protegido; distinguir cambios concurrentes legítimos de cambios de la migración.
6. Exigir revisión previa conocida. Con 0002, aplicar destino explícito usando el
   tooling fijado: `python -m cognova_database upgrade 0003_onboarding_questionnaire`.
   Inyectar ENVIRONMENT=production y DATABASE_URL por entorno seguro (TLS).
   Con 0003 ya aplicada, verificar estado antes de decidir si hace falta una
   operación idempotente. Ante head ausente/desconocido/múltiple, diagnosticar;
   nunca stamp, create_all, downgrade automático ni recrear base.
7. Verificar exactamente una fila alembic_version=0003_onboarding_questionnaire,
   columnas nullable, checks NOT VALID, tablas/funciones/triggers/PK/FK e índices.
   Comparar usuarios/sesiones existentes y objetivos del snapshot previo con
   user_academic_goal_legacy. No ejecutar suite de integración contra producción.
8. Revisar permisos según OPERATIONS: runtime SELECT/INSERT de responses, SELECT
   legacy, funciones necesarias y acceso de bloqueo users; sin ownership/DDL ni
   capacidad de borrar historia. Registrar diferencias y no inventar nombres de
   roles ni otorgar permisos amplios para ocultar problemas.
9. Queries operativas de solo lectura sobre tablas anteriores/nuevas. Coordinar
   comprobación backend que espera exactamente 0003. Frontend queda sin desplegar
   hasta compatibilidad backend+database demostrada. No cambiar código externo.
10. Registrar resultados reales, commits/push y limitaciones. Nunca convertir
    pruebas locales de 2026-10-12 en evidencia de producción.

## Resultados de esta ejecución

| Control | Resultado |
| --- | --- |
| Identidad del PostgreSQL Render efectivo | dpg-db2iojc9v7es7387i2ig-a, cognova/public, TLS |
| Revisión/conteos/constraints/índices previos | 0002; 1 usuario, 3 sesiones, 2 buckets; JSON adjunto |
| Plan y mecanismo de respaldo del servicio | No consultados |
| Backup o restauración verificados | No; pg_dump 18 bloqueado por Windows y backup Render no verificable |
| Aplicación 0003 | No ejecutada |
| Preservación posterior y queries operativas | No verificadas |
| Roles/grants runtime y migrador | cognova_user propietario; separación runtime pendiente de confirmar |
| Producción/frontend/backend modificados | No |

## DEPENDENCY BACKEND

No hay evidencia de 0003 en producción. El backend que exige exactamente 0003
permanece bloqueado para su compatibilidad operativa hasta verificar este release.
No desplegar frontend por asumir que el push del esquema aplicó la migración.
La lectura productiva ahora confirma expresamente 0002_auth_sessions. No hay tablas
de 0003 ni evidencia de compatibilidad con el backend nuevo que exige 0003.
Resolver primero el respaldo verificable y confirmar el rol runtime efectivo;
después repetir el inventario sobre el mismo fingerprint y ejecutar el release.

## Política Git

Conteo inicial: 5. Meta global: 501, no obligación de crear commits vacíos en esta
fase. Separar cambios documentales/operativos reales, sin squash ni historial
artificial. Registrar conteo final y diferencia 501 menos total al cerrar.
Este bloque de preparación/evidencia añade un commit documental: total 6,
faltantes hasta 501: 495. No se usa esta cifra para afirmar que el release se aplicó.
El reintento posterior parte de 6 y añade un commit de evidencia: total 7,
faltantes hasta 501: 494. Ninguna revisión Alembic fue modificada.
Este intento con conexión funcional parte de 7 y añade un commit de inventario,
permisos y bloqueo de respaldo: total 8, faltantes hasta 501: 493.

Checks de esta fase: enlaces Markdown locales y git diff --check correctos;
revisión del diff y patrones básicos de secretos sin hallazgos. No se repitieron
tests Python/PostgreSQL en los intentos iniciales: solo cambió documentación y no
hubo conexión productiva entonces. En el intento actual: pip check, import/version
de SQLAlchemy 2.1.3 sin extensiones, dos inventarios productivos READ ONLY,
validación del JSON, enlaces locales y diff. No se ejecutó la suite contra producción.
