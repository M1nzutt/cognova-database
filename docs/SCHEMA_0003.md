# Contrato físico: 0003_onboarding_questionnaire

Fecha: 2026-10-12. Padre: 0002_auth_sessions. 0001 y 0002 no cambian.

## Users y registro mínimo

| Columna | Cambio |
| --- | --- |
| name | TEXT NOT NULL; check no vacío y char_length <=30 |
| email | TEXT NOT NULL; check no vacío y char_length <=50 |
| password_hash | Sin cambio; nunca se almacena password plano |
| degree_program | TEXT nullable, sin default artificial |
| semester | INTEGER nullable; conserva check positivo original |
| academic_goal | TEXT nullable, compatibilidad legacy |

ck_users_name_registration y ck_users_email_registration se crean NOT VALID:
el esquema anterior permitía textos largos y no debemos truncar ni impedir el
upgrade de usuarios existentes. Todas las nuevas inserciones/actualizaciones deben
cumplir los checks. Una fila legacy no conforme puede fallar incluso al actualizar
otra columna: backend debe remediarla con decisión explícita. No se normaliza ni
completa información inventada. NULL permite onboarding pendiente; degree_program
vacío no acredita completitud. Backend valida completitud y semántica.

## Copia histórica de academic_goal

user_academic_goal_legacy contiene user_id INTEGER PK/FK users.id ON DELETE RESTRICT,
academic_goal TEXT nullable y captured_at TIMESTAMPTZ NOT NULL DEFAULT now().
Se copia literalmente una fila por usuario existente, incluidos blancos, vacío y
NULL inesperado si la fuente ya tenía ese drift. captured_at es fecha de captura
en migración, no una fecha inventada de respuesta original.

La columna original permanece. Después del backfill, triggers prohíben INSERT,
UPDATE, DELETE y TRUNCATE del archivo. Usuarios nuevos no reciben archivo ficticio.
Cambiar users.academic_goal no altera el dato previo; backend debe dejar de usar
esa columna como fuente actual. El archivo es evidencia parcial histórica de q1,
no una respuesta certificada del catálogo nuevo ni un cuestionario completo.

## Snapshots completos e historial

| Campo de questionnaire_responses | Tipo/regla |
| --- | --- |
| user_id | INTEGER NOT NULL, FK users.id ON DELETE RESTRICT |
| revision | INTEGER >0, secuencia contigua por usuario empezando en 1 |
| questionnaire_version | INTEGER >0, contrato/catálogo backend |
| answers | JSONB NOT NULL, exactamente claves q1…q10 |
| recorded_at | TIMESTAMPTZ NOT NULL; trigger fija clock_timestamp() |

PK (user_id,revision) evita duplicados e indexa inicial y última respuesta (recorrido
inverso). La PK legacy indexa su lectura por usuario. No hay índice JSONB sin una
consulta justificada. Índices de users/auth/rate limiting se conservan.

JSONB representa las diez respuestas como un snapshot completo atómico, sin diez
columnas cuyos tipos/opciones todavía no están congelados ni filas históricas
mutables. La función IMMUTABLE cognova_valid_questionnaire_answers exige un objeto
con exactamente q1…q10; valores string no vacío o array no vacío de strings no
vacíos. Rechaza null JSON, números, booleanos, objetos, extras y preguntas faltantes.
No se guardan borradores incompletos en esta tabla.

La documentación de producto consultada contiene diez preguntas pero **faltan
opciones y cardinalidades definitivas**. No se inventan catálogos: backend debe
aprobar/versionar opciones, single/multi, unicidad de selecciones y versiones
admitidas antes de aceptar respuestas reales. El formato descrito es de
persistencia; puede traducirse desde DTOs del backend.

- revision=1: percepción inicial completa e inmutable.
- Última revision del usuario: percepción vigente; intermedias conservan historia.
- Cambiar questionnaire_version no reinicia revision ni sobrescribe el inicio.
- Para usuarios antiguos, el archivo legacy conserva también su evidencia parcial
  anterior al primer cuestionario completo.

El trigger de INSERT bloquea users, exige la siguiente revisión y fija fecha.
Una colisión concurrente falla: backend reconsulta y resuelve/reintenta, nunca
sobrescribe. Usar una transacción por usuario. Triggers prohíben UPDATE/DELETE/
TRUNCATE y FK RESTRICT impide pérdida por borrado de usuarios. Un propietario que
desactive triggers/elimine tablas queda fuera de esta garantía de integridad.

## Upgrade y downgrade

Upgrade bloquea users, cambia nulabilidad, agrega checks NOT VALID, copia legacy
y crea tabla/funciones/triggers. No fabrica nueve respuestas faltantes. Repetir
upgrade head no vuelve a copiar ni modifica historia. No usa ORM ni create_all.

Downgrade bloquea las tres tablas y verifica antes del DDL:

1. questionnaire_responses está vacía.
2. Ningún usuario tiene NULL en degree_program/semester/academic_goal.
3. Cada goal archivado sigue idéntico en users.

Si falla algo, aborta íntegramente. Si pasa, elimina objetos nuevos y restaura NOT
NULL; los valores originales permanecen en users. Se descarta metadata de captura
de la migración, no respuestas. Re-upgrade recaptura con nueva fecha y no pretende
reconstruir una fecha original de percepción.

## DEPENDENCY BACKEND

- Fijar commit database con 0003, preparar release compatible 0002/0003 antes del
  DDL y habilitar funcionalidades nuevas tras comprobar 0003. Readiness debe seguir
  rechazando revisión ausente/desconocida o múltiples heads.
- ORM nullable para onboarding/academic_goal; registro name/email/password con
  máximos 30/50 y hash existente. Manejar anomalías legacy sin truncado silencioso.
- Mapear tablas nuevas sin DDL automático. Leer legacy por user_id, inicial por
  revision=1, actual por ORDER BY revision DESC LIMIT 1. Autorizar ownership.
- Congelar catálogo versionado de q1…q10; validar opciones/cardinalidades; INSERT
  completo con siguiente revisión y manejo de conflictos, nunca UPDATE/DELETE.
- Añadir pruebas ORM/API/auth, configurar permisos y definir retención/borrado
  de cuenta. No se realizaron cambios en otros repositorios.
