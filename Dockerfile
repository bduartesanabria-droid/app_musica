# ── Build stage ────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Runtime stage ───────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

# System deps para soundfile / psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Copiar paquetes instalados
COPY --from=builder /install /usr/local

# Copiar código fuente
COPY . .

# Entrypoint ejecutable
RUN chmod +x /app/docker-entrypoint.sh

# Directorios necesarios
RUN mkdir -p /app/audio_storage

# Usuario no-root
RUN useradd -m -u 1001 semimus && chown -R semimus /app
USER semimus

EXPOSE 6000

ENTRYPOINT ["/app/docker-entrypoint.sh"]
