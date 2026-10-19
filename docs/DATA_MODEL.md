# Modelo de datos

Contrato vigente: 0001 → 0002 → 0003_onboarding_questionnaire → **0004_subjects**.
0001–0003 son inmutables. El modelo anterior se detalla en
[MIGRATIONS](MIGRATIONS.md) y [SCHEMA_0003](SCHEMA_0003.md).

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
  de onboarding/cuestionario ni introduce CASCADE. No hay actividades nuevas.

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

DELETE será una operación destructiva explícita del Backend futuro, con permisos,
confirmación y política de retención. Esta migración no implementa ese flujo ni
una auditoría de cambios de materia. Futuras tablas relacionadas deberán referir
subjects.id con RESTRICT por defecto y preservar historial según su contrato;
no asumir que archivar autoriza eliminación o cascadas. El rol runtime ordinario
no debe recibir DELETE/TRUNCATE de subjects por esta entrega.

## Upgrade / downgrade

0004 solo agrega subjects, su secuencia, checks, FK e índices; no modifica filas
existentes. Compatible con conexión inyectada/search_path, SQL offline y bloqueo
transaccional compartido del runner. No incluye datos demo.

Downgrade a 0003 toma ACCESS EXCLUSIVE en subjects y aborta si existe cualquier
fila, activa o archivada. Tabla vacía: DROP sin CASCADE dentro de la transacción;
dependencias futuras impiden el DROP. No borra datos para permitir rollback.
Producción requiere inventario, respaldo y release coordinado según OPERATIONS.
