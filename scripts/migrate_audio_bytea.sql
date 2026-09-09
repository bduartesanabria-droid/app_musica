-- Agrega almacenamiento binario para los audios existentes.
-- Ejecutar en DBeaver conectado a la base de datos que usa la aplicacion.

BEGIN;

ALTER TABLE audios
    ADD COLUMN IF NOT EXISTS audio_data BYTEA;

COMMIT;
