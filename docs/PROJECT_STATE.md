# Estado de Cognova Database

Fecha: 2026-10-12. Rama: feat/0003-onboarding-questionnaire.

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

Incluye upgrade limpio 0002→0003 y desde base vacía, objetivos legacy normales/
vacíos/espacios/Unicode, nombres/emails largos sin truncado, usuarios sin onboarding,
diez respuestas y nuevas revisiones, constraints/índices, inmutabilidad/FK,
concurrencia, downgrade seguro y rechazo atómico de tres causas de pérdida,
repetición y search_path. Las pruebas ORM/API/auth backend no se ejecutaron.
Ruff lint y formato pasan (15 archivos Python), pip check sin incompatibilidades,
editor sin diagnósticos y git diff --check correcto. Se verifican los blobs
históricos mediante tests; 0001/0002 no tienen diff. No se ejecutó CI remota aún.

## Riesgos y límites

- Faltan opciones/cardinalidades definitivas de las diez preguntas en el contrato
  documental: backend debe fijarlas; no se inventaron valores de producto.
- Filas antiguas fuera de 30/50 requieren remediación antes de actualizarse.
  NOT VALID no certifica conformidad histórica global.
- Backfill con bloqueo exclusivo: evaluar volumen/ventana antes de producción.
- FK RESTRICT bloquea borrar usuarios con historia: retención/eliminación de cuenta
  requieren coordinación explícita; no se borran datos para facilitar ese flujo.
- Producción, grants reales, backups/restauración y despliegue coordinado no se
  verificaron ni ejecutaron. Nuevo head requiere release backend compatible.

## DEPENDENCY BACKEND

1. Fijar SHA de código database publicado en esta fase; se registra tras cerrar
   validaciones. No consumir main/latest ni el ZIP del handoff anterior.
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

Cerrar Ruff/checks, revisar diff/secretos, commits coherentes y publicar rama.
Backend integra la referencia y prepara pruebas y despliegue coordinados;
no ejecutar migración de producción sin esa preparación operativa.
