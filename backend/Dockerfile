FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    libsndfile1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/storage/audio

EXPOSE 5000

ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "run:app"]
