# Database handoff — Planes y Retos 0007

## Estado

main contiene 0007_study_plans_and_challenges, integrada mediante el merge no-ff
2715a02759957f08697ee09a6155ba54afce135e. La indentación del último run del
workflow de backup se corrigió en 2a7cb932f1bcea61f01e4bb9e55d5a4fb8540352.
Database checks run 41745180653 pasó sobre ese commit.

Producción permanece en la última revisión documentada 0006_study_sessions. No se
aplicó 0007. La workflow manual backup-pre-0003.yml no se despachó con
plans_challenges_release=true; no existe artifact ni evidencia de restauración.

## Compatibilidad

0007 añade seis tablas de Planes, relaciones, decisiones y Retos. No cambia ni
elimina columnas de las tablas previas. El Backend que consume 0006 puede seguir
usando sus relaciones existentes por aditividad del esquema. La readiness
productiva posterior a 0007 no se ha comprobado porque la migración no se aplicó.

## Gate de release

Completar backup/restore exactamente en 0006, descargar y verificar SHA-256 del
artifact, confirmar TLS y conteos con preflight READ ONLY, y aplicar
scripts/release_0007.py --apply con el pin, host y locks descritos en OPERATIONS.
El entorno de esta ejecución no ofreció una interfaz funcional para dispatch de
GitHub Actions; por eso el procedimiento se detuvo antes del backup. No aplicar
0007 sin la evidencia requerida.
