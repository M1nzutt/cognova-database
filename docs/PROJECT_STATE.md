# Estado de Cognova Database

## Materias — 2026-10-18

Implementada 0004_subjects después de 0003, sin modificar 0001–0003. Contrato:
[DATA_MODEL](DATA_MODEL.md). Cinco posiciones activas únicas por usuario garantizan
el límite concurrente; archivadas no consumen posiciones. Downgrade rechaza toda
tabla con datos. DATA_MODEL no existía al iniciar esta tarea y se crea aquí.
Validación local: 129 pruebas pasan, 0 omitidas (41 offline y 88 PostgreSQL;
37 casos nuevos de Materias). PostgreSQL 17.11 local desechable en 127.0.0.1:55433.
Upgrade desde vacío y 0003 con comparación de filas de las cinco tablas previas;
repetición, constraints/FK/índices, Unicode, archivo/reactivación, límite concurrente
en READ COMMITTED y REPEATABLE READ, inserción masiva atómica, rollback DDL,
downgrade vacío y rechazo con activas, archivadas o dependencias futuras.
JUnit local: artifacts/test-results-0004.xml; validador sin omisiones, Ruff lint/
formato, pip check, SQL offline, blobs históricos y diff verificados. Primer intento
de integración falló por usar rol postgres inexistente; repetición con el rol local
cognova_test comprobado. No se cargó .env ni se conectó a producción.
Inicio de esta tarea: 24 commits. Entrega/push y SHA Backend pendientes de cierre.
No se aplicó 0004 a producción; la evidencia operativa previa sigue siendo 0003.
Las secciones siguientes son historial de la entrega 0003, no el head de código.

Fecha de actualización: 2026-10-17. Rama: feat/0003-onboarding-questionnaire.

## Fase actual: aplicación operativa de 0003

**0003_onboarding_questionnaire aplicada y commit confirmado** el 2026-10-17,
verificación a las 16:13:38Z, reconfirmada a las 16:13:59Z. Antes: 0002 exactamente.
Mismo PostgreSQL, TLS. users=1, auth_sessions=3, rate_limit_buckets=2 preservados:
comparación de todas las filas/columnas dentro de bloqueos exclusivos, no solo
conteos. Legacy=1 con academic_goal idéntico; questionnaire_responses=0.
Ver [evidencia](evidence/0003-release-2026-10-17.json) y [release](RELEASE_0003.md).
Nullable onboarding/goal, checks, PK/FK, índices y cinco triggers comprobados.
Función validadora acepta diez respuestas sintéticas y rechaza objeto vacío por
SELECT sin insertar datos. Verificación READ ONLY tras commit e inventario pasan.
Artifact 12106388644 sigue vigente; no se repitió backup ni se ensayó restauración.
API oficial de conexión inyectada con migration_config del runner y Alembic;
runner/migraciones no difieren del SHA backend. No downgrade ni pérdida de datos.
41 pruebas offline, Ruff/formato/diff pasan; no suite DDL ni pruebas API en producción.
Migrador cognova_user propietario de las seis tablas, con permisos amplios y
EXECUTE del validador. No se modificaron grants. Identidad/permisos runtime reales
siguen pendientes: si backend usa otro rol, debe comprobarlos antes de desplegar.
Inicio 22 commits; preparación y evidencia dejan 24 (477 faltantes hasta 501).

### Backup previo verificado

Corrección libpq implementada: PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD se
derivan de la URI en memoria, decodificando credenciales; PGDATABASE solo contiene
el nombre de base. TLS require por defecto (preserva opciones más estrictas),
timeouts y read-only conservados. 41 pruebas offline pasan; Ruff/diff correctos.
Validate-only 39047961450 y backup real 39048024551: success, commit 05d234b.
Revisión 0002 antes/después y TLS confirmados. pg_dump/pg_restore 18.6, lista y
decodificación completa aprobadas, GnuPG 2.4.4 AES-256 y roundtrip SHA-256 aprobado.
Artifact 12106388644 descargado y comprobado: solo cognova-pre-0003.dump.gpg,
10199 bytes; dump original 10107 bytes. Hashes/fechas en RELEASE_0003.
Respaldo verificado; vence 2026-10-24T16:07:43Z. Clave custodiada por usuario.
No se ensayó restauración en base aislada ni se aplicó 0003. Antes de migrar,
revisar vigencia del backup, ventana y controles operativos pendientes; no declarar
compatibilidad backend/0003 por este éxito. 20 commits iniciales; cierre 22, faltan 479.

### Historial anterior al backup exitoso

Diagnóstico de conexión preparado con input diagnose_connection: solo SELECT de
revisión y retorno antes de pg_dump. Clasifica en memoria DNS, TCP/puerto,
autenticación, TLS, base inexistente u otro psql; nunca muestra errores nativos.
Incluye indicación constante si psql intenta un socket local. No cambia backup,
cifrado ni 0003. 40 pruebas offline pasan; Ruff/formato/diff correctos.
Run 39047675514 completado: `OTHER_PSQL: default_local_socket`. psql intenta un
socket Unix del runner: el helper entrega la URI completa en PGDATABASE pero no
establece PGHOST. El destino remoto no fue alcanzado; no demuestra fallo de
secret, red/Render, autenticación ni TLS. Corrección pendiente en el adaptador
de conexión: pasar los componentes libpq explícitamente, sin secretos en argv/logs,
conservando destino y TLS. Se detiene aquí según instrucción. Sin backup, artifacts,
escrituras ni 0003. Dos commits de diagnóstico/evidencia: 18 iniciales, 20 finales.

Diagnóstico por operación implementado: las once llamadas del helper reciben
etiquetas literales. Fallos de salida, timeout o arranque solo muestran la etiqueta,
sin stdout/stderr nativos ni traceback. 33 pruebas offline pasan, 51 integration
deselected; Ruff y diff correctos. Validate-only 39047262512: success. Run real
39047309888: failure, `Backup stopped at: psql_revision`. Ambos ejecutaron
945e123d31906ec2376a23d7f9cdda882b0c5590. Falla el comando inicial que consulta
alembic_version, antes de pg_dump; no es un rechazo por revisión distinta.
No se imprimen errores nativos, por lo que no se determina la causa subyacente.
Upload skipped, cero artifacts, limpieza success. No hay dump/hashes/cifrado que
verificar. Reintentos detenidos según instrucción; 0003 no se ejecuta.
Próximo paso de aquel intento: diagnóstico seguro limitado a psql_revision; no repetir inventario
ni asumir un problema de secrets, red o permisos sin evidencia. Backend bloqueado
por ausencia de respaldo. Conteo inicial 16; dos commits útiles dejan 18 (483 a 501).

Actualización: el usuario autorizó el artifact cifrado usando el secret
BACKUP_ENCRYPTION_KEY. El workflow genera/verifica el dump, cifra con GnuPG AES-256,
verifica descifrado por SHA-256 y publica únicamente .dump.gpg; nunca dump plano.
La clave se pasa por stdin y no se guarda ni imprime. El workflow está registrado
en main y publicado en la rama de trabajo. Todavía no existe backup verificable.
No se aplica 0003. Ver [RELEASE_0003](RELEASE_0003.md).
Primer dispatch real: run 38766220897 terminó failure con ValueError en validación
previa; instalación cliente 18.6/GnuPG correcta, upload omitido y cero artifacts.
Se añade validación manual sin conexión para diagnosticar sin repetir el backup,
con errores constantes que no imprimen secretos.

Validate-only anterior: run 38766608404, commit f996b936bf834bd10539e14295d983bbbbe3ab48,
completed/failure. Falló la condición de BACKUP_ENCRYPTION_KEY: mínimo 32 bytes
UTF-8 y ausencia de CR/LF/NUL. El error conjunto no permite distinguir cuál de
esas condiciones falló; tampoco acredita ausencia del secret. No se evaluó la
URL ni se conectó a PostgreSQL. Upload skipped y cero artifacts confirmados.
El usuario confirmó actualización del secret y custodia de la clave. Nuevo
validate-only 39046801431: success; configuración aceptada sin conexión ni backup.
Run real posterior 39046879415: failure con RuntimeError; upload skipped y cero
artifacts. Ambos ejecutaron f996b936bf834bd10539e14295d983bbbbe3ab48.
El wrapper oculta errores nativos y no identifica la operación que falló; no se
pueden certificar pg_dump, pg_restore, cifrado ni hashes. No inferir credenciales
incorrectas ni fallo de red sin evidencia. Se detuvieron los reintentos.
El diagnóstico por etapa solicitado después queda registrado arriba.
No se aplicó 0003. Backend continúa bloqueado.
Validación local: 30 tests offline passed, 51 integration deselected; Ruff y
git diff --check correctos. No se ejecutaron tests contra producción.
Esta continuación parte de 15 commits; cierre documental: 16, faltantes a 501: 485.

### Historial: versión anterior con bloqueo de privacidad

Creado [backup-pre-0003.yml](../.github/workflows/backup-pre-0003.yml): únicamente
workflow_dispatch, secret DATABASE_URL, cliente PostgreSQL 18 en runner Ubuntu,
dump custom, pg_restore --list/decodificación, tamaño/fecha/versiones/SHA-256 y
artifact con retención de siete días. Sin DDL ni migraciones. Seis pruebas offline
con datos sintéticos pasan; todavía no existe evidencia de un backup real.

**Bloqueo nuevo confirmado:** GitHub indica que el repositorio es público. Los
artifacts heredan acceso de lectura y no pueden marcarse privados individualmente.
Se solicitó decisión entre repo privado y artifact cifrado; no se cambió visibilidad.
El workflow aborta antes de conectar y antes de subir si no es privado. Ejecución,
registro inicial del workflow en main, artifact y evidencia productiva pendientes;
no se reporta run success. Detalles en [RELEASE_0003](RELEASE_0003.md).
Inicio: 8 commits; cierre documental y workflow: 9, faltantes hasta 501: 492.

## Release operativo actual

Conectividad confirmada con carga explícita del .env. Recurso Render
dpg-db2iojc9v7es7387i2ig-a, cognova/public, PostgreSQL 18.6, TLS. Estado productivo
verificado: **0002_auth_sessions; 0003 todavía no aplicado**. Dos inventarios
READ ONLY confirman 1 usuario, 3 sesiones y 2 buckets. SQLAlchemy 2.1.3 sin
extensiones nativas y pip check correctos; código fijado sin cambios.
Ver [evidencia productiva](evidence/0003-preflight-2026-10-14.json) y
[release](RELEASE_0003.md). Rol conectado cognova_user propietario; identidad y
separación del runtime real no confirmadas. No se modificaron roles ni datos.
**Bloqueo vigente: respaldo recuperable no verificado.** pg_dump 18.6 fue bloqueado
por Windows Application Control antes de ejecutarse; pg_restore 18.6 funciona pero
no hay dump. El plan/snapshots/PITR de Render no son accesibles para verificarlos.
Se detuvo el release antes del DDL; backend que exige 0003 sigue bloqueado y no se
desplegaron backend/frontend. Se necesita backup verificable o un cliente pg_dump
18 autorizado, conservando el mismo destino. No eludir protecciones de Windows.
Inicio de este intento: 7 commits, Git limpio. Evidencia/estado agrupados en un
commit útil: total 8 al cerrar, 493 faltantes hasta 501. Validaciones actuales:
pip check, import/version de SQLAlchemy, inventarios READ ONLY, JSON, enlaces y
git diff --check; no hay pruebas de upgrade productivo ni respaldo exitoso.

### Historial de intentos previos

En los intentos anteriores, el release estaba autorizado pero no aplicado:
falta acceso efectivo a Render/PostgreSQL. No se configuró DATABASE_URL ni acceso
API/UI utilizable; no se consultaron inventario, plan, backups ni permisos reales.
Se solicitó acceso seguro. Procedimiento y evidencia: [RELEASE_0003](RELEASE_0003.md).
El backend nuevo espera exactamente 0003 según confirmación del usuario; no se
declara compatible producción ni se despliega frontend hasta verificar el release.
Inicio de esta fase: 5 commits y Git limpio. El SHA fijado existe y runner/migraciones
no difieren de él. No se crean commits artificiales para alcanzar la meta 501.
Preparación/evidencia agrupadas en un commit documental: total 6 al cerrar,
faltantes hasta 501: 495. Verificación de enlaces/diff y revisión básica de secretos;
sin nueva ejecución de tests ni de operaciones productivas.

Reintento tras aviso del usuario: DATABASE_URL continúa ausente en los procesos
disponibles, incluso fuera del sandbox y consultando Process/User/Machine. Tampoco
hay .env local. Se solicitó ubicación/carga segura; no se imprimió ningún secreto
ni se intentó otro recurso. No hubo conectividad, inventario, backup o DDL que
certificar. Este reintento parte de 6 commits y añade evidencia documental:
total 7, faltantes hasta 501: 494. Sigue pendiente habilitar la configuración
efectiva del mismo PostgreSQL existente; detalles en RELEASE_0003.

## Entrega publicada

Commit de código que backend debe fijar:
`232c43130c0fb3eddd32e1dd3707368ba0d87d4c`.
Incluye migración, tooling, pruebas y contrato físico; publicado en
origin/feat/0003-onboarding-questionnaire. El commit documental posterior solo
registra esta referencia y el cierre de validaciones; no cambia el esquema.

## Estado reconstruido

Inicio limpio en main/origin/main, 3 commits: 7158cb4, f7b6fa5 y 325e7ea.
La fase anterior validó offline (18 passed, 5 skipped) y no aplicó DDL en producción.
La validación real se ejecutó en esta fase. El ZIP anterior corresponde a f7b6fa5
y ya no representa el head nuevo; no reutilizarlo para esta entrega.

## Decisión y revisión

0003_onboarding_questionnaire, down_revision=0002_auth_sessions.
0001/0002 y sus blobs originales intactos: [PROVENANCE](PROVENANCE.md).

- Registro mínimo con name/email no vacíos y máximos 30/50 mediante checks NOT
  VALID: conservan anomalías antiguas, restringen nuevas escrituras.
- degree_program, semester y academic_goal nullable; password_hash sin cambios.
- user_academic_goal_legacy conserva literalmente el objetivo anterior por usuario;
  no fabrica las otras nueve respuestas.
- questionnaire_responses: diez respuestas JSONB completas por snapshot, versión
  de catálogo y revisiones contiguas por usuario. Primera inicial, última vigente;
  historia append-only con triggers/FK RESTRICT.
- Downgrade condicionado a no perder respuestas/goals ni tener que rellenar NULL;
  aborta antes del DDL dentro de la transacción cuando no es seguro.

Contrato físico/justificación JSONB: [SCHEMA_0003](SCHEMA_0003.md).

## Pruebas reales

PostgreSQL 17.11 x64 Windows, instancia desechable propia en 127.0.0.1:55433,
base cognova_test, sin servicio del sistema ni producción. Binarios EDB en
artifacts ignorado por Git; cada caso crea/elimina un esquema test_<uuid>.

TEST_DATABASE_ALLOW_DDL=yes y REQUIRE_POSTGRES_TESTS=1:
**69 passed, 0 skipped; 51 casos PostgreSQL**. JUnit local:
artifacts/test-results-0003.xml. El validador CI acepta el reporte sin omisiones.
Al finalizar quedaron cero esquemas test_<uuid> y la instancia local se detuvo.

Incluye upgrade limpio 0002→0003 y desde base vacía, objetivos legacy normales/
vacíos/espacios/Unicode, nombres/emails largos sin truncado, usuarios sin onboarding,
diez respuestas y nuevas revisiones, constraints/índices, inmutabilidad/FK,
concurrencia, downgrade seguro y rechazo atómico de tres causas de pérdida,
repetición y search_path. Las pruebas ORM/API/auth backend no se ejecutaron.
Ruff lint y formato pasan (15 archivos Python), pip check sin incompatibilidades,
editor sin diagnósticos y git diff --check correcto. Se verifican los blobs
históricos mediante tests; 0001/0002 no tienen diff. La ejecución de CI remota
tras el push no está certificada aquí; los resultados son locales reproducibles.
Revisión básica de secretos sin coincidencias de tokens/claves privadas ni .env,
dumps o binarios versionados. Enlaces Markdown locales correctos. No se afirma
auditoría exhaustiva de vulnerabilidades ni pruebas contra otros motores/versiones.

## Riesgos y límites

- Faltan opciones/cardinalidades definitivas de las diez preguntas en el contrato
  documental: backend debe fijarlas; no se inventaron valores de producto.
- Filas antiguas fuera de 30/50 requieren remediación antes de actualizarse.
  NOT VALID no certifica conformidad histórica global.
- Backfill con bloqueo exclusivo: evaluar volumen/ventana antes de producción.
- FK RESTRICT bloquea borrar usuarios con historia: retención/eliminación de cuenta
  requieren coordinación explícita; no se borran datos para facilitar ese flujo.
- Producción ya está en 0003 y el respaldo está verificado. Runtime real,
  ensayo aislado de restauración y pruebas backend continúan pendientes.

## DEPENDENCY BACKEND

El bloqueo de revisión de base está resuelto: producción está en 0003. Antes de
desplegar, confirmar rol efectivo y permisos de OPERATIONS y ejecutar readiness/
smoke tests del backend compatible. No se certifica ese despliegue desde database.

1. Fijar 232c43130c0fb3eddd32e1dd3707368ba0d87d4c. No consumir main/latest ni
   el ZIP del handoff anterior. Esta referencia contiene 0003 y sus pruebas reales.
2. Actualizar ORM/DTOs/validación: name <=30, email <=50, password→hash; onboarding
   nullable y academic_goal legacy opcional. No rehacer autenticación.
3. Leer evidencia previa del archivo, inicial completa revision=1 y actual de la
   última revisión. Insertar snapshots completos; aprobar catálogo versionado,
   validar opciones/cardinalidades/ownership y manejar concurrencia.
4. Admitir explícitamente 0003 en readiness/startup con release compatible antes
   del DDL. Seguir rechazando heads ausentes/desconocidos/múltiples.
5. Consumir database fijo en fixtures/CI y verificar ORM/API/auth reales. Si aún
   existe Alembic local/startup DDL, coordinar su retiro; no asumir que ya ocurrió.
6. Configurar permisos de tablas/funciones y decidir retención/borrado de cuenta,
   más remediación de anomalías legacy. Detalles en SCHEMA_0003 y OPERATIONS.

## Próximo paso

Backend confirma su rol/permisos, integra la referencia y realiza readiness/smoke
tests de su release compatible. No volver a aplicar ni revertir 0003 para ese paso.
