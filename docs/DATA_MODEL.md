# Modelo de datos

Head de código de esta rama: **0006_study_sessions**. Producción documentada:
**0005_activities**. Revisiones 0001–0005 inmutables; esta entrega no opera producción.

## Sesiones de estudio — contrato 0006 confirmado 2026-10-29

Nueva revisión 0006_study_sessions después de 0005; desarrollo local, NO aplicada
a producción. 0001–0005 permanecen inmutables. No datos demo ni lógica de timer.

### study_sessions
- id INTEGER SERIAL PK; user_id y subject_id INTEGER NOT NULL.
- activity_id INTEGER nullable. FK (user_id,subject_id) a subjects(user_id,id).
  FK (user_id,subject_id,activity_id) a activities(user_id,subject_id,id), MATCH
  SIMPLE permite activity_id NULL. Ambas UPDATE/DELETE RESTRICT.
  0006 añade uq_activities_user_subject_id, sin cambiar filas ni revisión0005.
- planned_start_at TIMESTAMPTZ NOT NULL finito; fecha que usará Calendario futuro.
- planned_duration SMALLINT NOT NULL, 10–180 minutos inclusivos.
- execution_state TEXT NOT NULL default planned: planned/running/paused/finished.
- status TEXT nullable: completed/partial/postponed/cancelled, resultado final.
- start_at/end_at TIMESTAMPTZ nullable, finitos. start_at es primer inicio real;
  end_at cierre definitivo, nunca duración acumulada. end_at exige start_at y >.
- actual_duration NUMERIC(20,6) NOT NULL default0: segundos efectivos acumulados,
  no negativos y finitos. Backend calcula SUM de segundos de intervalos cerrados
  y actualiza este campo en la misma transacción. DB NO suma ni corrige duración.
  No se limita por duración planificada: la ejecución puede exceder el plan.
- context TEXT nullable: finished_early/distracted/tired/interrupted/changed_activity/other.
- other_text TEXT nullable: requerido con other, trim ASCII, no solo blancos,
  1–200 caracteres PostgreSQL; NULL para cualquier otro contexto.
- created_at/updated_at TIMESTAMPTZ NOT NULL; metadata de DB, creación inmutable,
  actualización monotónica. id/user_id también inmutables.

Coherencia física: planned sin ejecución/resultado/contexto y duración0.
running/paused requieren start_at, no end_at ni resultado/contexto.
finished exige resultado; completed/partial exigen inicio/cierre e intervalos reales.
postponed/cancelled antes de iniciar: sin start/end, duración0, sin intervalos.
Si hubo ejecución, todo resultado finished exige cierre definitivo.
Contexto opcional solo con finished. No se deduce resultado por duración.

UNIQUE parcial user_id WHERE execution_state IN ('running','paused') garantiza
como máximo una sesión activa/pausada por usuario, incluso con concurrencia.
Índices (user_id,planned_start_at,id) para calendario/listado y
(user_id,subject_id,activity_id) para FKs/dependencias. Sin índices redundantes.

### study_session_intervals
id INTEGER SERIAL PK; session_id INTEGER NOT NULL FK a study_sessions.id,
UPDATE/DELETE RESTRICT. started_at TIMESTAMPTZ NOT NULL finito;
ended_at TIMESTAMPTZ nullable finito; si existe, estrictamente > started_at.
Metadata created_at/updated_at como la sesión.
UNIQUE parcial session_id WHERE ended_at IS NULL: un intervalo abierto.
EXCLUDE GiST sobre int8range(session_id,session_id,'[]') y
tstzrange(started_at,ended_at,'[)') impide solapamientos de una sesión, incluso
con concurrencia; rangos incorporados PostgreSQL, sin extensión btree_gist.
Índice (session_id,started_at,id) para historia ordenada.

Intervalos append-only: identidad/inicio inmutables; un intervalo abierto puede
cerrarse una vez, nunca reabrirse; no DELETE/TRUNCATE. No borrar historia para
forzar downgrade. Una sesión con intervalos no puede borrarse por FK; una sesión
sin intervalos puede borrarse explícitamente si Backend lo autoriza.

Triggers de integridad diferidos comprueban el estado final de la transacción:
primer intervalo coincide con start_at, intervalos dentro del rango de ejecución;
running tiene un intervalo abierto, paused solo cerrados y al menos uno,
finished ejecutada tiene intervalos cerrados y ningún abierto. No ordenan acciones
de timer ni generan intervalos. Backend decide transiciones y envía ambas tablas.
Escribir un intervalo toca solo updated_at del padre para serializar su validación
con cambios concurrentes; REPEATABLE READ puede abortar con40001.
Ningún trigger calcula actual_duration ni altera planificación/ciclo/resultado.

### Responsabilidades, permisos y reversión
DB: integridad física, ownership referencial (no autorización del actor),
unicidad concurrente, no solapamiento, evidencia y conservación de intervalos.
Backend: auth/onboarding/ownership en cada request; transiciones, permisos de
edición, inicio/pausa/reanudación/finalización, cálculo de duración desde intervalos,
precondiciones y retry transaccional acotado40001/40P01; mensajes seguros.
La FK también impide reasignar una actividad a otra materia si tiene sesiones.

Sin grants a runtime productivo en esta entrega. Contrato futuro mínimo:
sesiones SELECT/INSERT/UPDATE/DELETE, intervalos SELECT/INSERT/UPDATE;
USAGE/SELECT de ambas secuencias, sin DDL/TRUNCATE/escritura de alembic_version,
sin EXECUTE directo de funciones de trigger. Revisar roles/default privileges
reales en release separado. PUBLIC revocado en nuevos objetos.

Downgrade toma locks exclusivos y aborta si existe cualquier sesión o intervalo.
Vacío elimina solo objetos0006 y clave compuesta añadida a activities; sin CASCADE.
Dependencias futuras provocan rollback atómico. Datos0001–0005 preservados.
Upgrade mantiene search_path, conexión inyectada, transacción y advisory lock1943187001.


## Modelo previo vigente en producción

Cadena productiva: 0001 → 0002 → 0003_onboarding_questionnaire → 0004_subjects
→ **0005_activities**, aplicada el 2026-10-24 según OPERATIONS.
El modelo anterior se detalla en
[MIGRATIONS](MIGRATIONS.md) y [SCHEMA_0003](SCHEMA_0003.md).

## Actividades — contrato 0005 confirmado 2026-10-21

El usuario confirmó deadline obligatorio TIMESTAMPTZ, prioridades
low/medium/high/urgent y registro automático de **todo** cambio de deadline:
postponed al moverlo hacia adelante, rescheduled al adelantarlo. El tipo de
evento no cambia automáticamente el estado: sus transiciones pertenecen a Backend.

### activities

| Columna | Tipo / regla |
| --- | --- |
| id | INTEGER SERIAL, PK |
| user_id, subject_id | INTEGER NOT NULL; FK compuesta a subjects(user_id,id), UPDATE/DELETE RESTRICT |
| title | TEXT NOT NULL, 1–50 caracteres PostgreSQL, sin espacios ASCII extremos ni solo blancos |
| deadline | TIMESTAMPTZ NOT NULL finito, instante vigente; no se exige que sea futuro |
| original_deadline | TIMESTAMPTZ NOT NULL finito; trigger copia deadline al crear y lo conserva inmutable |
| deadline_revision | INTEGER NOT NULL, inicial 0; DB incrementa solo cuando cambia el instante |
| priority | TEXT NOT NULL: low, medium, high, urgent |
| status | TEXT NOT NULL: pending, in_progress, completed, postponed, cancelled |
| estimated_duration | SMALLINT NOT NULL, 10–300 minutos inclusivos |
| notes | TEXT nullable, máximo 200 caracteres; vacío permitido |
| created_at, updated_at | TIMESTAMPTZ NOT NULL, generados por trigger; created_at inmutable, updated_at no decrece |

Etiquetas de estado: Pendiente → pending; En progreso → in_progress;
Completada → completed; Postergada → postponed; Cancelada → cancelled.
Sin unicidad de título ni defaults de producto inventados; Backend envía priority/status.
No se añaden type, calendario, sesiones ni datos demo en este contrato.

La FK compuesta impide asociar una materia ajena incluso con SQL directo. Añade
uq_subjects_user_id_id en 0005 (sin editar 0004) como clave referenciada. La FK de
subjects a users garantiza indirectamente la existencia de user_id. Sin RLS:
Backend sigue autenticando y autorizando cada acceso; la FK no autoriza al actor.

Índices: ix_activities_user_subject cubre FK/listados por materia;
ix_activities_user_status_deadline (user_id,status,deadline,id) cubre listas por
estado y vencimiento estable. No se impone orden lexicográfico de prioridad.
Nueve checks ck_activities_* validan título, deadlines finitos, revisión, prioridad,
estado, duración, notas y coherencia temporal. FK/NOT NULL completan la integridad.

### activity_deadline_events

PK (activity_id,revision), revisión positiva, FK activity_id → activities.id
con UPDATE/DELETE RESTRICT. Campos NOT NULL: previous_deadline, new_deadline,
event_type y occurred_at. Los tres timestamps son TIMESTAMPTZ finitos.
ck_deadline_events_direction exige postponed con fecha nueva mayor, o rescheduled
con fecha nueva menor. Misma fecha/instante (incluso otro offset): no genera evento.
La PK cubre la consulta de historia por actividad en orden de revisión; sin índice
redundante ni secuencia de eventos. La fecha inicial reside siempre en activities.

Cada UPDATE de deadline incrementa la revisión y agrega un evento en **la misma
transacción**. Antes/después quedan ligados a la fila bloqueada por PostgreSQL;
no se usa max(revision) susceptible a carreras. Un error del INSERT de historia
revierte también la actividad. Rollback revierte ambos. Múltiples cambios en una
transacción generan múltiples eventos, aun si al final vuelve a la fecha original.

Triggers: activity_prepare protege identidad, user_id, created_at, fecha inicial
y contador; mantiene timestamps. activity_record_deadline registra la diferencia.
deadline_events_immutable y deadline_events_no_truncate rechazan UPDATE/DELETE/
TRUNCATE de historia. El runtime no debe tener INSERT de historia.

El escritor automático es SECURITY DEFINER, search_path fijo pg_catalog y SQL
interno calificado con TG_TABLE_SCHEMA; no depende del search_path del cliente.
EXECUTE revocado a PUBLIC en las tres funciones de 0005; no concederlo a runtime.
El trigger existente funciona sin ese permiso, evitando que runtime pueda adjuntar
la función privilegiada a triggers temporales propios. Propietarios/superusuarios
siguen siendo administradores confiables capaces de alterar protecciones.

Archivar materia solo cambia subjects: conserva actividades e historia. Borrar una
materia con cualquier actividad falla por FK. Una actividad sin historia puede
eliminarse con autorización explícita; si tiene eventos, RESTRICT impide perderlos.
Retención o purga futura requiere decisión separada, nunca CASCADE silencioso.

### DB frente a Backend

DB: límites físicos, enum de tokens, relación de mismo dueño, identidad/fecha
inicial inmutables, timestamps coherentes, historial automático y append-only,
restricciones de borrado, atomicidad y serialización de UPDATE sobre la misma fila.
Backend: autorización, DTOs, normalización Unicode, zona de presentación, reglas
de fechas de producto, estados/transiciones, política sobre materias archivadas,
confirmación destructiva y mapeo de errores. Puede cambiar subject_id a otra materia
del mismo usuario; user_id no puede cambiar. No enviar metadata histórica en PUT.
Si necesita evitar sobreescrituras de un cliente desactualizado, usar bloqueo de fila
y/o una precondición explícita; el historial conserva todos los cambios confirmados
pero no decide intención de usuario. READ COMMITTED serializa y registra ambos;
REPEATABLE READ puede abortar con 40001. Reintentar la transacción completa de forma
acotada ante 40001/40P01; manejar 23503/23514/23505 sin filtrar SQL interno.

### Upgrade / downgrade de 0005

Upgrade agrega dos tablas, una secuencia, una clave única en subjects, dos índices
y las funciones/triggers. No modifica filas de tablas previas ni 0001–0004.
Downgrade bloquea subjects/activities/history en ACCESS EXCLUSIVE y rechaza cualquier
actividad o evento, incluso completado/cancelado. Solo vacío elimina los objetos
nuevos y uq_subjects_user_id_id; nunca CASCADE ni vaciado previo automático.
Dependencias futuras impiden DROP y revierten todo. Conexión inyectada/search_path,
SQL offline, transacción y advisory lock del runner permanecen iguales.

## Materias: subjects

| Columna | Tipo / regla |
| --- | --- |
| id | INTEGER SERIAL, PK subjects_pkey |
| user_id | INTEGER NOT NULL, FK fk_subjects_user_id_users → users.id, DELETE RESTRICT |
| name | TEXT NOT NULL, 1–20 caracteres PostgreSQL, sin espacios ASCII extremos ni solo blancos |
| status | TEXT NOT NULL: active (Activa), archived (Archivada) |
| difficulty | TEXT NOT NULL: easy (Fácil), medium (Media), hard (Difícil) |
| color_base | TEXT NOT NULL, token ASCII minúsculo de 1–32 caracteres: letra inicial, luego letras/dígitos/_/- |
| color_shade | SMALLINT NOT NULL, 0–1000 |
| active_slot | SMALLINT: 1–5 para activas, NULL para archivadas |
| created_at, updated_at | TIMESTAMPTZ NOT NULL, default now(); Backend mantiene updated_at |

No hay defaults de producto: el llamador debe indicar estado, dificultad y color.
Base y shade son componentes de un token de paleta, no un hexadecimal ni una
intensidad porcentual. El intervalo técnico 0–1000 permite shades numéricos;
Backend define y valida el catálogo real y las combinaciones soportadas.

## Integridad impuesta por DB

- Checks: ck_subjects_name, ck_subjects_status, ck_subjects_difficulty,
  ck_subjects_color_base, ck_subjects_color_shade, ck_subjects_active_slot.
- uq_subjects_user_name_lower: UNIQUE (user_id, lower(name)), incluyendo archivadas.
  Un nombre queda reservado al archivar; otro usuario puede usarlo. La comparación
  ignora mayúsculas según la collation PostgreSQL, conserva acentos y no garantiza
  equivalencia entre diferentes normalizaciones Unicode.
- uq_subjects_active_slot: UNIQUE (user_id, active_slot), NULL distintos. Junto al
  check de estado/slot garantiza máximo cinco activas incluso con concurrencia,
  SQL directo, inserciones masivas y aislamiento REPEATABLE READ. No depende de
  un SELECT count(*) susceptible de carreras. Archivadas no consumen posiciones.
- ix_subjects_user_status: listado por usuario/estado; los índices anteriores
  cubren nombre y posiciones por usuario. No se agrega índice redundante user_id.
- FK RESTRICT evita pérdida implícita al borrar un usuario. No cambia historia
  de onboarding/cuestionario ni introduce CASCADE. 0005 agrega las actividades
  descritas arriba y restringe el borrado de materias con dependencias.

## Responsabilidad Backend (DEPENDENCY BACKEND)

Autenticar/autorizar ownership en cada lectura/escritura; DB no implementa RLS.
Mantener id/user_id/created_at estables y updated_at en modificaciones; validar
catálogo de color, normalización Unicode y mensajes de producto. Mapear las
etiquetas españolas a los tokens persistidos anteriores.

Crear/reactivar: en una transacción, bloquear la fila users con SELECT FOR UPDATE,
buscar una posición libre 1–5 e insertar/actualizar status='active', active_slot=N.
Si no hay ninguna, rechazar por límite. Todos los flujos del usuario deben seguir
el mismo protocolo; la restricción UNIQUE sigue siendo la garantía final aun si
un escritor no lo sigue. Manejar 23505, 23514, 23503 y reintentar transacciones
abortadas por serialización/deadlock (40001/40P01) de forma acotada. Un choque de
slot no demuestra que haya cinco materias: releer antes de mostrar el mensaje.

Archivar: UPDATE de la misma fila, status='archived', active_slot=NULL, updated_at
actualizado, conservando id y demás atributos. Reactivar reutiliza esa misma fila
y puede fallar por capacidad; jamás borrar/reinsertar para simular el archivado.
No se impone una posición visual ni un ranking mediante active_slot.

DELETE requiere confirmación explícita en Backend. El permiso DELETE de subjects
fue autorizado el 2026-10-20 (ver OPERATIONS); TRUNCATE sigue prohibido.
0005 no cambia esos permisos: su FK impide borrar materias con actividades.
Archivar no autoriza eliminación ni cascadas. No se añade auditoría de cambios
de materia en esta migración.

## Upgrade / downgrade

0004 solo agrega subjects, su secuencia, checks, FK e índices; no modifica filas
existentes. Compatible con conexión inyectada/search_path, SQL offline y bloqueo
transaccional compartido del runner. No incluye datos demo.

Downgrade a 0003 toma ACCESS EXCLUSIVE en subjects y aborta si existe cualquier
fila, activa o archivada. Tabla vacía: DROP sin CASCADE dentro de la transacción;
dependencias futuras impiden el DROP. No borra datos para permitir rollback.
Producción requiere inventario, respaldo y release coordinado según OPERATIONS.
