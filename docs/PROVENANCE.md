# Procedencia del historial

Fuente: cognova-backend, commit `06c3d2a`; handoff documental inspeccionado en
`5fa90a3`. Las dos revisiones del HEAD inspeccionado conservan esos mismos blobs.
La copia inicial se verificó por SHA-256 contra los archivos originales.

| Archivo | revision | down_revision | Blob Git original |
| --- | --- | --- | --- |
| [0001](../migrations/versions/0001_create_users.py) | 0001_create_users | None | 847886004b17e4b57723029cd217a63dd063d381 |
| [0002](../migrations/versions/0002_auth_sessions.py) | 0002_auth_sessions | 0001_create_users | ef8cd07f0a3482a272c5f62229f51a5390d74ec4 |

Las pruebas verifican el blob tras normalizar CRLF a LF, como Git. No se modifica
ninguna instrucción de las revisiones, sus IDs, enlaces ni nombres físicos.
La plantilla se copia del backend. La configuración adapta únicamente el path
de importación a `%(here)s`; env.py sustituye el bootstrap acoplado al backend.
El lock conserva pins/hashes de las dependencias DB y transitivas del lock fuente.

No se importó todo el historial Git del backend: se conserva la trazabilidad de
origen y el historial Alembic completo que reconoce la base existente.

Al agregar 0004, también se protege el blob de 0003_onboarding_questionnaire.py:
`5e6e5c25d631efb6d0015fabce2b64ae9866fba1`, procedente de la entrega propia 0003.
Las pruebas offline verifican las tres revisiones inmutables, además del head
lineal 0004_subjects. No se renumeró ni modificó su SQL.

Al agregar 0005 se protege además el blob de 0004_subjects.py:
`6827c5d80d5591e2423eca6f971cde0273a5ce38`. Las cuatro revisiones históricas
permanecen idénticas; el nuevo head lineal es 0005_activities.
