# 🎵 SEMIMUS — Sistema de Entrenamiento Melódico Musical

> Plataforma PWA para el entrenamiento del oído musical con instrumentos andinos colombianos: **Tiple**, **Requinto** y **Bandola**.

![Stack](https://img.shields.io/badge/Backend-Flask%203.0%20%2B%20PostgreSQL-blue)
![Stack](https://img.shields.io/badge/Frontend-React%2018%20%2B%20Vite%20%2B%20TailwindCSS-cyan)
![Stack](https://img.shields.io/badge/Deploy-Docker%20%2B%20Coolify-purple)
![License](https://img.shields.io/badge/License-MIT-green)

---

## 🏗️ Arquitectura

```
semimus/
├── backend/               # Flask API REST
│   ├── app/
│   │   ├── models/        # SQLAlchemy models (Users, Audio, Sessions...)
│   │   ├── api/           # Blueprints de la API REST
│   │   └── utils/         # Generador de preguntas, procesamiento de audio
│   ├── storage/audio/     # Archivos WAV/MP3 (volumen Docker)
│   └── Dockerfile
├── frontend/              # React + Vite PWA
│   ├── src/
│   │   ├── pages/         # Login, Dashboard, Training, Admin...
│   │   ├── components/    # Layout, Audio Player, UI components
│   │   ├── store/         # Zustand (auth, theme)
│   │   └── services/      # Axios API client
│   └── Dockerfile
├── nginx/                 # Reverse proxy
├── .github/workflows/     # CI/CD GitHub Actions
└── docker-compose.yml
```

---

## 🚀 Inicio Rápido

### Requisitos
- Docker Desktop
- Git

### 1. Clonar y configurar

```bash
git clone <repo-url> semimus
cd semimus
cp .env.example .env
# Edita .env con tus valores
```

### 2. Levantar con Docker

```bash
docker-compose up -d
```

### 3. Inicializar base de datos

```bash
docker exec semimus_backend flask db upgrade
docker exec semimus_backend python scripts/seed.py
```

### 4. Acceder

| Servicio | URL |
|----------|-----|
| Frontend | http://localhost |
| API | http://localhost/api |
| Health | http://localhost/api/health |

**Credenciales por defecto:**
- Email: `admin@semimus.app`
- Contraseña: `Admin123!`

---

## 💻 Desarrollo Local

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt

# Configura PostgreSQL local y crea .env
cp ../.env.example .env

# Migraciones
flask db init
flask db migrate -m "initial"
flask db upgrade

# Seed
python scripts/seed.py

# Servidor
python run.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
# → http://localhost:5173
```

---

## 🎯 Modos de Entrenamiento

| Modo | Descripción |
|------|-------------|
| **Notas** | Identificación de notas DO, RE, MI, FA, SOL, LA, SI |
| **Intervalos** | Reconocimiento de 2das, 3ras, 4tas, 5tas, octavas |
| **Escalas** | Mayor, menor, pentatónica, armónica |
| **Dictado Melódico** | Transcripción de frases musicales |
| **Patrones Andinos** | Ritmos y motivos de la música andina colombiana |
| **Guabina** | Entrenamiento con ritmo de guabina |
| **Tiple** | Específico para el Tiple colombiano |
| **Requinto** | Específico para el Requinto |
| **Bandola** | Específico para la Bandola |

---

## 🔊 Banco Sonoro

Los archivos de audio deben seguir el formato:
```
{Instrumento}_{Nota}{Octava}.wav
Ejemplos:
  Tiple_DO4.wav
  Requinto_LA3.wav
  Bandola_SOL5.wav
```

**Especificaciones técnicas:**
- Formato: WAV (recomendado), MP3, OGG, FLAC
- Bit depth: 24 bits
- Sample rate: 44.1 kHz
- Normalización: -1 dB
- Duración: 3-5 segundos

---

## 🎮 Sistema de Gamificación

| Elemento | Descripción |
|----------|-------------|
| **XP** | 10 XP/pregunta correcta + bonos por precisión |
| **Monedas** | 5 por sesión + 15 si precisión ≥ 80% |
| **Niveles** | Principiante → Aprendiz → Estudiante → Músico → Intérprete → Maestro → Virtuoso → Gran Maestro |
| **Insignias** | Primera Nota, Racha 7 días, Oído Perfecto... |
| **Rankings** | Global, semanal, mensual, por precisión |
| **Desafíos** | Reto diario con XP/monedas extras |

---

## 📡 API REST

```
POST   /api/auth/register          Registro de usuario
POST   /api/auth/login             Login + JWT
POST   /api/auth/refresh           Renovar access token
GET    /api/auth/me                Datos del usuario autenticado

GET    /api/instruments/           Listar instrumentos
GET    /api/instruments/notes      Listar notas
GET    /api/instruments/intervals  Listar intervalos

GET    /api/audio/                 Listar audios (paginado)
POST   /api/audio/upload           Subir audio (admin/instructor)
GET    /api/audio/stream/{file}    Streaming de audio

POST   /api/questions/generate     Generar preguntas estocásticas
POST   /api/sessions/              Crear sesión de entrenamiento
POST   /api/sessions/{id}/answer   Enviar respuesta
POST   /api/sessions/{id}/complete Completar sesión + gamificación

GET    /api/progress/me            Progreso personal
GET    /api/statistics/me          Estadísticas detalladas
GET    /api/rankings/global        Ranking global/semanal/mensual
```

---

## 🔐 Roles y Permisos

| Rol | Permisos |
|-----|----------|
| **Aprendiz** | Entrenar, ver sus estadísticas y rankings |
| **Instructor** | + Subir/gestionar audios, ver estadísticas de aprendices |
| **Admin** | + Gestionar usuarios, roles, configuraciones |

---

## 🐳 Despliegue en Coolify

1. Conecta tu repositorio GitHub en Coolify
2. Configura las variables de entorno del `.env.example`
3. Selecciona `docker-compose.yml` como archivo de despliegue
4. El webhook de GitHub Actions dispara el redespliegue automático

**Variables de entorno requeridas en producción:**
```
SECRET_KEY=<cadena aleatoria de 64 caracteres>
JWT_SECRET_KEY=<cadena aleatoria de 64 caracteres>
DATABASE_URL=postgresql://user:pass@host:5432/semimus
POSTGRES_PASSWORD=<contraseña segura>
FRONTEND_URL=https://tu-dominio.com
CORS_ORIGINS=https://tu-dominio.com
```

---

## 📊 Diagrama ER (Simplificado)

```
users ──────────── progress (1:1)
  │              ├── user_gamification (1:1)
  │              └── user_statistics (1:1)
  │
  └── training_sessions ─── answers ─── questions
                                            │
                                         audios
                                            │
                                    instruments ── notes
```

---

## 🛠️ Tecnologías

**Backend:**
- Python 3.12 + Flask 3.0
- PostgreSQL 16 + SQLAlchemy + Flask-Migrate
- JWT (Flask-JWT-Extended)
- Redis (rate limiting)
- Gunicorn (producción)
- librosa + soundfile (análisis de audio)

**Frontend:**
- React 18 + Vite 5
- TailwindCSS 3
- React Query (caché de datos)
- Zustand (estado global)
- Framer Motion (animaciones)
- Recharts (gráficas)
- WaveSurfer.js (visualización de audio)
- PWA (Service Workers, offline, instalable)

**DevOps:**
- Docker + Docker Compose
- Nginx (reverse proxy)
- GitHub Actions (CI/CD)
- Coolify (deployment)
- Let's Encrypt (SSL)

---

## 📄 Licencia

MIT License — Desarrollado con ❤️ para la música andina colombiana.
