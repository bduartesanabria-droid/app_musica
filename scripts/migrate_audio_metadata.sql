-- Ejecutar una sola vez en la base de datos actual de SEMIMUS.
-- Agrega los metadatos usados por la carga masiva por instrumento.

BEGIN;

ALTER TABLE audios ADD COLUMN IF NOT EXISTS technique VARCHAR(50);
ALTER TABLE audios ADD COLUMN IF NOT EXISTS rhythm VARCHAR(50);
ALTER TABLE audios ADD COLUMN IF NOT EXISTS octave INTEGER;
ALTER TABLE audios ADD COLUMN IF NOT EXISTS audio_data BYTEA;

COMMIT;
