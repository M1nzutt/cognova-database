# Modelo de datos

Head de código: 0001 → 0002 → 0003_onboarding_questionnaire → 0004_subjects
→ **0005_activities**. Producción permanece en 0004; 0005 requiere release separado.
0001–0004 son inmutables. El modelo anterior se detalla en
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
