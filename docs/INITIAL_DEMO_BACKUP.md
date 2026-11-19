# Respaldo inicial y despliegue de Cognova

## Qué se incluye en Git

`cognova_database/seed/demo-academic.sql` contiene una única cuenta ficticia
(`demo.software@example.com`) y sus datos académicos. No incluye hash de
contraseña, sesiones/tokens, conversaciones, límites de autenticación ni otras
cuentas. Las propuestas de IA ya generadas se conservan como snapshots asociados
a sus planes. El usuario debe establecer una contraseña localmente antes de iniciar
sesión.

El dump completo que se usa para preparar o recuperar el respaldo es privado:
no se copia al repositorio, a un issue ni a un servicio externo.

## Crear un respaldo privado de PostgreSQL

Desde la raíz del checkout local, identifica el contenedor y comprueba que el
volumen activo es el esperado. Usa un directorio privado fuera del repositorio:

```powershell
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backup = "$env:LOCALAPPDATA\Temp\opencode\cognova-private-$stamp"
New-Item -ItemType Directory -Path $backup | Out-Null
$dbDump = "cognova-full-$stamp.dump"
$globals = "cognova-globals-$stamp.sql"
docker exec cognova-postgres-1 pg_dump -U cognova_admin -d cognova -Fc -f "/tmp/$dbDump"
docker exec cognova-postgres-1 pg_dumpall -U cognova_admin --globals-only -f "/tmp/$globals"
docker cp "cognova-postgres-1:/tmp/$dbDump" "$backup\$dbDump"
docker cp "cognova-postgres-1:/tmp/$globals" "$backup\$globals"
docker exec cognova-postgres-1 pg_restore --list "/tmp/$dbDump"
Get-FileHash "$backup\$dbDump" -Algorithm SHA256
```

Guarda el hash y verifica que `pg_restore --list` termina correctamente. En
Windows, elimina herencia y concede acceso solo a la cuenta operadora, SYSTEM y
Administrators; confirma la ACL con `icacls`. Protege también los globals: incluyen
configuración de roles. No restaures sobre el volumen original para probar.

## Actualizar el seed versionable

1. Crea otro volumen/instancia PostgreSQL desechable, con una base llamada
   `cognova_seed_scratch`; nunca uses el contenedor ni volumen de origen.
2. Copia el dump privado a esa instancia y restáuralo allí:

   ```sh
   pg_restore --exit-on-error --no-owner --no-privileges \
     --dbname=cognova_seed_scratch cognova-full.dump
   ```

3. Desde la sesión superusuario de esa instancia, ejecuta
   `scripts/sanitize_demo_snapshot.sql`. El script comprueba el nombre de base y
   exige superusuario; elimina las demás cuentas y sus datos, sesiones, chat y
   límites de autenticación, y pone el hash demo en `NULL`.
4. Comprueba los recuentos y las relaciones antes de exportar. En la instantánea
   validada: 1 cuenta, 5 materias, 30 actividades, 37 sesiones, 7 intervalos,
   6 planes (4 con propuesta de IA), 17 retos, 4 decisiones, 3 eventos de fecha
   límite y 1 cuestionario.
5. Exporta solo los datos; excluye la versión de Alembic y no exportes esquema ni
   roles:

   ```sh
   pg_dump -U seedadmin -d cognova_seed_scratch --data-only --column-inserts \
     --no-owner --no-privileges \
     --exclude-table-data=public.alembic_version -f demo-academic-raw.sql
   python scripts/prepare_demo_seed.py demo-academic-raw.sql \
     cognova_database/seed/demo-academic.sql
   ```

   El preparador elimina las líneas meta `\restrict`/`\unrestrict`, exige la única
   identidad ficticia con hash nulo y sin sesiones/chat/tokens, y agrega una ventana
   acotada para deshabilitar el trigger que normalmente impide insertar historial
   importado. La transacción del inicializador garantiza que el trigger se vuelva a
   habilitar o se revierta la importación completa. Revisa que no haya emails
   externos, secretos o tokens; ejecuta `test_initial_seed.py` y una restauración
   limpia antes de actualizar el seed en Git.
6. Elimina únicamente la instancia y volumen desechables al concluir; conserva el
   dump privado conforme a la política de respaldo.

No ejecutes `sanitize_demo_snapshot.sql` en una base productiva, de desarrollo
compartida ni en la original. No uses `--clean` ni vuelques un dump completo en el
repositorio.

## Primer despliegue y actualizaciones

1. Obtén localmente los tres repositorios (`cognova-backend`,
   `cognova-database` y `cognova-frontend`) con las rutas relativas que espera
   `cognova-backend/compose.yaml`.
2. Copia `cognova-backend/.env.example` a `.env` y configura contraseñas de
   PostgreSQL, runtime, migrador y JWT localmente. No las incluyas en Git. Añade
   `GEMINI_API_KEY` si se desea generar nuevas propuestas; las propuestas ya
   almacenadas no necesitan una clave para mostrarse.
3. Desde `cognova-backend`, construye e inicia:

   ```sh
   docker compose up --build -d
   docker compose ps
   ```

   `database-migrate` ejecuta `python -m cognova_database initialize`: identifica
   si `public` estaba vacío, aplica todas las migraciones oficiales hasta 0010 y,
   únicamente en ese caso, carga el seed en una transacción. Un marcador durable
   (`cognova_initialization`) diferencia `pending`, `complete` y `skipped`.
   Si la carga falla, se revierte completa y se puede reintentar; una base ya
   inicializada queda marcada `skipped`. Reiniciar o reconstruir los contenedores
   no duplica ni sobrescribe datos.
4. El runtime recibe permisos mínimos después de migrar. La API debe quedar
   saludable (`http://localhost:8000/api/v1/ready`) y el frontend en
   `http://localhost:8080`.
5. Define o recupera la credencial demo de forma interactiva (no aparece en el
   historial de comandos ni se guarda en el repositorio):

   ```sh
   docker compose exec backend python -m app.cli set-demo-password
   ```

   La solicitud permite 8–12 caracteres, solicita confirmación, genera Argon2 y
   actualiza solamente `demo.software@example.com`. Después inicia sesión desde
   el frontend con la contraseña que acabas de elegir.

En una instalación existente, ejecuta las migraciones como de costumbre. El
inicializador registra que la base ya tenía tablas y no importa el seed. No borres
el volumen para forzar la carga: un despliegue no debe destruir datos.

## Restaurar una copia operativa

Para recuperación, crea una base y volumen nuevos, restaura el dump privado
verificado con los roles y permisos necesarios, y valida integridad antes de
conectar Backend. No restaures el seed académico sobre una instalación existente:
ese archivo está reservado exclusivamente para bootstrap vacío.

## Pruebas de aceptación

En el volumen desechable confirma:

- Alembic llega a `0010_nullable_password_hash`.
- La clave foránea de cada entidad académica refiere al usuario demo 36 y sus
  materias, actividades, sesiones, intervalos y planes relacionados.
- Los recuentos del procedimiento de exportación coinciden con la sección anterior.
- `password_hash IS NULL`, `auth_sessions` está vacío y el login falla hasta que se
  configura la contraseña; después el login y la sesión autenticada funcionan.
- Repetir `initialize` y reconstruir imágenes no cambia recuentos ni importa de
  nuevo; una base preexistente recibe el marcador `skipped`.
- Backend queda saludable y Frontend carga el flujo de login y los datos académicos.
