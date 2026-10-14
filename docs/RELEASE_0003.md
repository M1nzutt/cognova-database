# Release operativo 0003 — procedimiento y evidencia

Fecha: 2026-10-13. Objetivo: migrar exclusivamente el PostgreSQL Render existente.
Estado: **bloqueado por acceso; no aplicado**.

## Identidad y código comprobado

- Repo cognova-database; rama feat/0003-onboarding-questionnaire.
- SHA fijado por backend: 232c43130c0fb3eddd32e1dd3707368ba0d87d4c, disponible localmente.
- Revisión 0003_onboarding_questionnaire, padre 0002_auth_sessions.
- Blob de 0003: 5e6e5c25d631efb6d0015fabce2b64ae9866fba1.
- Runner/migraciones actuales sin diff respecto al SHA fijado.
- Inicio: 5 commits, árbol limpio en 28fa023abeb13c687417e18282710891ac188e29.
- git ls-remote confirmó ese mismo SHA en la rama publicada. Las revisiones y
  tooling coinciden con 232c431; la diferencia hasta 28fa023 es documental.

## Acceso comprobado

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
| Identidad del PostgreSQL Render efectivo | No accesible; no confirmado |
| Revisión/conteos/constraints/índices previos | No consultados |
| Plan y mecanismo de respaldo del servicio | No consultados |
| Backup o restauración verificados | No ejecutados; falta conexión/acceso |
| Aplicación 0003 | No ejecutada |
| Preservación posterior y queries operativas | No verificadas |
| Roles/grants runtime y migrador | No consultados |
| Producción/frontend/backend modificados | No |

## DEPENDENCY BACKEND

No hay evidencia de 0003 en producción. El backend que exige exactamente 0003
permanece bloqueado para su compatibilidad operativa hasta verificar este release.
No desplegar frontend por asumir que el push del esquema aplicó la migración.

## Política Git

Conteo inicial: 5. Meta global: 501, no obligación de crear commits vacíos en esta
fase. Separar cambios documentales/operativos reales, sin squash ni historial
artificial. Registrar conteo final y diferencia 501 menos total al cerrar.
Este bloque de preparación/evidencia añade un commit documental: total 6,
faltantes hasta 501: 495. No se usa esta cifra para afirmar que el release se aplicó.
El reintento posterior parte de 6 y añade un commit de evidencia: total 7,
faltantes hasta 501: 494. Ninguna revisión Alembic fue modificada.

Checks de esta fase: enlaces Markdown locales y git diff --check correctos;
revisión del diff y patrones básicos de secretos sin hallazgos. No se repitieron
tests Python/PostgreSQL: solo cambió documentación y no hubo conexión productiva.
