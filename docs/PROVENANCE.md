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
