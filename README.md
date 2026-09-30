# SEMIMUS

Aplicación web para entrenar el oído musical con instrumentos andinos colombianos. El backend y las vistas usan **Flask 3, SQLAlchemy, PostgreSQL y Jinja**; Alpine.js añade interacciones en el navegador.

## Arquitectura

- `app/routes/`: autenticación, entrenamiento, administración y API.
- `app/models/`: entidades SQLAlchemy.
- `app/templates/`: páginas Jinja.
- `app/static/`: estilos compilados, JavaScript y recursos locales.
- `migrations/`: migraciones Alembic versionadas.
- `storage/audio/`: archivos de audio en el volumen persistente configurado.
- `docker-compose.yml`: servicio Flask para Coolify/producción.

## Desarrollo local

Requisitos: Python 3.12, Node.js 22+, Docker Compose y Git.

1. Copia `.env.example` a `.env`. Define un `SECRET_KEY` propio. Si necesitas el
   usuario inicial superadministrador, define también `SUPERADMIN_USERNAME`,
   `SUPERADMIN_EMAIL` y `SUPERADMIN_PASSWORD`.
2. Compila los recursos locales del frontend:

   ```bash
   npm ci
   npm run build
   ```

3. Inicia la aplicación y PostgreSQL de desarrollo:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

En otra terminal, carga los catálogos iniciales una sola vez:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml exec web python scripts/seed.py
```

La aplicación queda en `http://localhost:6000`; salud en `/api/health`. El
override de desarrollo crea un PostgreSQL aislado para la red local de Docker y
el servicio web aplica las migraciones antes de arrancar.

## Configuración de producción

Configura las variables en Coolify; no uses contraseñas de ejemplo:

| Variable | Uso |
|---|---|
| `FLASK_ENV=production` | Activa configuración de producción. |
| `SECRET_KEY` | Obligatoria; mínimo 32 caracteres aleatorios. |
| `DATABASE_URL` | Obligatoria; URL de conexión PostgreSQL. |
| `SUPERADMIN_USERNAME`, `SUPERADMIN_EMAIL`, `SUPERADMIN_PASSWORD` | Opcionales; se crea la cuenta solo si las tres existen y aún no hay superadministrador. Nunca se modifica una cuenta existente durante el arranque. |
| `AUDIO_STORAGE_PATH` | Volumen persistente de archivos de audio. |
| `AVATAR_STORAGE_PATH` | Volumen persistente de avatares. |
| `PROXY_FIX_X_FOR`, `PROXY_FIX_X_PROTO`, `PROXY_FIX_X_HOST` | Número de proxies de confianza por cabecera `X-Forwarded-*`; configura los saltos reales de tu instalación. |
| `RATELIMIT_STORAGE_URI` | `memory://` por defecto; usa una URL Redis para compartir límites entre workers. |
| `GUNICORN_WORKERS`, `GUNICORN_THREADS`, `GUNICORN_TIMEOUT` | Configuración del servidor (por defecto 2, 2 y 180 segundos). |
| `MAX_AUDIO_SIZE_MB`, `MAX_UPLOAD_MB` | Límites de audio por archivo y petición. |

La aplicación detiene el arranque en producción si falta `SECRET_KEY` o es un
valor de ejemplo. Los recursos Alpine.js 3.14.9, Chart.js 4.4.9 y TailwindCSS 3
se sirven desde el repositorio; no dependen de CDN en tiempo de ejecución.

## Migraciones

Las migraciones se crean y revisan durante el desarrollo, se guardan en el
repositorio y se aplican con:

```bash
flask db upgrade
```

El entrypoint ejecuta ese comando antes de iniciar Gunicorn. Para adoptar una
base de datos existente, realiza primero una copia de seguridad y verifica que
su esquema corresponde exactamente a la revisión que vas a marcar. En la
primera entrega, cuando la migración inicial era `head`, se usaba:

```bash
flask db stamp head
flask db upgrade
```

La revisión inicial de este repositorio es `b7d5683b9277`. Como ya existen
migraciones posteriores, una base antigua que solo coincide con el esquema
inicial debe marcar esa revisión explícitamente y después avanzar:

```bash
flask db stamp b7d5683b9277
flask db upgrade
```

`stamp` solo registra una revisión en `alembic_version`; no crea, altera ni
borra tablas. No marques `head` si el esquema no incluye todos los cambios hasta
esa revisión.

## Entrenamiento y audio

- Las preguntas quedan asociadas a la sesión y se restauran al refrescar.
- Para completar la sesión hay que responder todas las preguntas planificadas.
  Una sesión sin respuestas queda abandonada y no suma XP, monedas ni progreso;
  una sesión parcial permanece disponible para continuar.
- La carga de audio acepta WAV, AIFF/AIF, MP3, OGG, FLAC y WMA. WMA se convierte
  a WAV. Los archivos deben durar entre 3 y 12 segundos, tener al menos 44.1 kHz
  y respetar `MAX_AUDIO_SIZE_MB` (50 MB por defecto).
- Las cargas nuevas rechazan un segundo audio activo para el mismo
  instrumento/nota. Los audios ya existentes no se eliminan.

### Almacenamiento de audio: pendiente de aprobación

Actualmente el contenido se guarda tanto en `Audio.audio_data` (PostgreSQL)
como en `AUDIO_STORAGE_PATH`. Recomiendo guardar los archivos en un volumen
persistente o almacenamiento de objetos y mantener en PostgreSQL solo sus
metadatos y ubicación, para evitar duplicar almacenamiento y copias de
seguridad. **No cambié la estrategia actual**; la migración a una sola ubicación
requiere tu aprobación antes de mover datos o retirar los BLOB existentes.

## Comprobaciones

```bash
python -m pytest
ruff check --select F app tests scripts config.py run.py
python -m pip_audit -r requirements.txt
```

GitHub Actions aplica las migraciones guardadas en PostgreSQL, compila los
recursos web y ejecuta Ruff, pytest y pip-audit.
