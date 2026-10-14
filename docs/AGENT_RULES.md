# Reglas para agentes

- Leer README, PROJECT_STATE, ARCHITECTURE, MIGRATIONS y PROVENANCE antes de editar.
- Modificar solo cognova-database. Backend/frontend se consultan solo en lectura.
- No alterar las revisiones históricas; no squash, renumeración, stamp ni create_all.
- No copiar ORM, auth o settings del backend. Limitar esta fase al registro mínimo,
  onboarding y percepción/cuestionario autorizados por el usuario.
- 0003 autoriza academic_goal nullable con copia histórica inmutable; leer
  SCHEMA_0003. No eliminar valores ni fabricar respuestas faltantes.
- La fase operativa autorizada el 2026-10-13 permite inventario, respaldo,
  aplicación de 0003 y verificación en el PostgreSQL Render existente. Identificar
  el recurso y verificar respaldo antes de DDL; no recrear recursos ni borrar datos.
  No exponer ni versionar credenciales. No modificar backend/frontend.
- Probar solo con PostgreSQL local desechable y opt-in explícito; nunca SQLite.
- Mantener conexión inyectada, search_path, transacciones y bloqueo compartido.
- No retirar migraciones del backend: documentar DEPENDENCY BACKEND.
- Antes de cada commit: pruebas/checks, diff, revisión básica de secretos,
  documentación y PROJECT_STATE. Commits pequeños; no afirmar pruebas no ejecutadas.
