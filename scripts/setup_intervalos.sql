-- SEMIMUS - Base de datos para entrenamiento de intervalos (y notas/escalas)
-- Solo PostgreSQL. Ejecutar como superusuario:
--   psql -U postgres -f scripts/setup_intervalos.sql
-- Re-ejecutable: reinicia el esquema public en cada ejecucion.
-- La base coincide con el default de DevelopmentConfig: semimus_dev.

\set dbname semimus_dev

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'semimus') THEN
        CREATE ROLE semimus WITH LOGIN PASSWORD 'semimus123';
    END IF;
END
$$;

SELECT 'CREATE DATABASE ' || :'dbname' || ' OWNER semimus'
WHERE NOT EXISTS (
    SELECT FROM pg_database WHERE datname = :'dbname'
)
\gexec

\connect :dbname

DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO semimus;
GRANT ALL ON SCHEMA public TO public;

BEGIN;

-- Usuarios y autenticacion
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(120) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(80) NOT NULL,
    last_name VARCHAR(80) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'aprendiz',
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    avatar_url VARCHAR(255),
    bio TEXT,
    reset_token VARCHAR(255),
    reset_token_expires TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);
CREATE INDEX ix_users_email ON users (email);
CREATE INDEX ix_users_username ON users (username);

-- Catalogos necesarios para encontrar pares de notas
CREATE TABLE instruments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    type VARCHAR(30),
    emoji VARCHAR(10),
    description TEXT,
    image_url VARCHAR(255),
    tuning VARCHAR(100),
    range_low VARCHAR(10),
    range_high VARCHAR(10),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE notes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(10) NOT NULL,
    octave INTEGER NOT NULL,
    frequency DOUBLE PRECISION,
    midi_number INTEGER,
    scientific_name VARCHAR(15),
    CONSTRAINT uq_note_octave UNIQUE (name, octave)
);

CREATE TABLE intervals (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    semitones INTEGER NOT NULL,
    abbreviation VARCHAR(10),
    consonance VARCHAR(20),
    description TEXT
);
CREATE INDEX ix_intervals_semitones ON intervals (semitones);

-- Escalas disponibles para el modelo Scale.
CREATE TABLE scales (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    type VARCHAR(30),
    intervals_pattern VARCHAR(100) NOT NULL,
    description TEXT
);

-- Audios usados para formar los pares del ejercicio
CREATE TABLE audios (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    audio_data BYTEA,
    instrument_id INTEGER REFERENCES instruments(id),
    note_id INTEGER REFERENCES notes(id),
    duration DOUBLE PRECISION,
    sample_rate INTEGER,
    bit_depth INTEGER,
    channels INTEGER,
    peak_amplitude DOUBLE PRECISION,
    file_size INTEGER,
    difficulty VARCHAR(20) NOT NULL DEFAULT 'intermedio',
    is_active BOOLEAN DEFAULT TRUE,
    waveform_data TEXT,
    tags VARCHAR(255),
    description TEXT,
    uploaded_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_audios_instrument_id ON audios (instrument_id);
CREATE INDEX ix_audios_note_id ON audios (note_id);

-- Preguntas y resultados del entrenamiento
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    mode VARCHAR(30) NOT NULL DEFAULT 'intervalos',
    type VARCHAR(30) NOT NULL DEFAULT 'identificar_intervalo',
    audio_id INTEGER REFERENCES audios(id),
    correct_answer VARCHAR(255) NOT NULL,
    options_json TEXT,
    difficulty INTEGER NOT NULL DEFAULT 1,
    instrument_id INTEGER REFERENCES instruments(id),
    hint TEXT,
    explanation TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    times_answered INTEGER DEFAULT 0,
    times_correct INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_questions_mode ON questions (mode);

CREATE TABLE training_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    mode VARCHAR(30) NOT NULL DEFAULT 'intervalos',
    instrument_id INTEGER REFERENCES instruments(id),
    difficulty_level INTEGER DEFAULT 1,
    total_questions INTEGER DEFAULT 0,
    correct_answers INTEGER DEFAULT 0,
    total_time_secs DOUBLE PRECISION DEFAULT 0,
    avg_response_time DOUBLE PRECISION DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    coins_earned INTEGER DEFAULT 0,
    is_completed BOOLEAN DEFAULT FALSE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);
CREATE INDEX ix_training_sessions_user_id ON training_sessions (user_id);

CREATE TABLE answers (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES training_sessions(id),
    question_id INTEGER REFERENCES questions(id),
    user_answer VARCHAR(255) NOT NULL,
    is_correct BOOLEAN NOT NULL,
    response_time DOUBLE PRECISION,
    answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX ix_answers_session_id ON answers (session_id);
CREATE INDEX ix_answers_question_id ON answers (question_id);

-- Progreso, estadisticas y recompensas usados por el cierre de una sesion
CREATE TABLE progress (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    total_sessions INTEGER DEFAULT 0,
    total_questions_answered INTEGER DEFAULT 0,
    total_correct INTEGER DEFAULT 0,
    total_time_minutes DOUBLE PRECISION DEFAULT 0,
    current_streak_days INTEGER DEFAULT 0,
    longest_streak_days INTEGER DEFAULT 0,
    last_activity_date DATE,
    weakest_notes_json TEXT,
    weakest_intervals_json TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_statistics (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    accuracy_by_mode_json TEXT,
    accuracy_by_instr_json TEXT,
    weekly_sessions_json TEXT,
    avg_response_time DOUBLE PRECISION DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_gamification (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
    total_xp INTEGER DEFAULT 0,
    current_level INTEGER DEFAULT 1,
    coins INTEGER DEFAULT 0,
    total_coins_earned INTEGER DEFAULT 0,
    weekly_xp INTEGER DEFAULT 0,
    monthly_xp INTEGER DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE badges (
    id SERIAL PRIMARY KEY,
    name VARCHAR(80) NOT NULL UNIQUE,
    description TEXT,
    icon VARCHAR(10),
    category VARCHAR(30),
    requirement_type VARCHAR(30),
    requirement_value INTEGER,
    xp_reward INTEGER DEFAULT 0,
    coin_reward INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE user_badges (
    id SERIAL PRIMARY KEY,
    user_gamification_id INTEGER NOT NULL REFERENCES user_gamification(id),
    badge_id INTEGER NOT NULL REFERENCES badges(id),
    earned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Instrumentos disponibles para cargar sus notas
INSERT INTO instruments (name, type, emoji, description) VALUES
    ('Tiple', 'cuerdas', '🎸', 'Instrumento de cuerdas de la musica andina colombiana.'),
    ('Requinto', 'cuerdas', '🎻', 'Instrumento de cuerdas de registro agudo.'),
    ('Bandola', 'cuerdas', '🪕', 'Instrumento de cuerdas pulsadas de la musica andina.'),
    ('Guitarra', 'cuerdas', '🎸', 'Instrumento usado como referencia armonica.');

-- Notas DO2 a SI6. El MIDI permite encontrar la segunda nota del intervalo.
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name)
SELECT n.name,
       o.octave,
       440.0 * power(2.0, ((o.octave - 4) * 12 + n.semitone - 9) / 12.0),
       (o.octave + 1) * 12 + n.semitone,
       n.name || o.octave
FROM (VALUES
    ('DO', 0), ('DO#', 1), ('RE', 2), ('RE#', 3), ('MI', 4), ('FA', 5),
    ('FA#', 6), ('SOL', 7), ('SOL#', 8), ('LA', 9), ('LA#', 10), ('SI', 11)
) AS n(name, semitone)
CROSS JOIN generate_series(2, 6) AS o(octave);

INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES
    ('Unisono', 0, 'U', 'perfecto'),
    ('Segunda menor', 1, '2m', 'disonante'),
    ('Segunda mayor', 2, '2M', 'disonante'),
    ('Tercera menor', 3, '3m', 'consonante'),
    ('Tercera mayor', 4, '3M', 'consonante'),
    ('Cuarta justa', 5, '4J', 'perfecto'),
    ('Cuarta aumentada', 6, '4A', 'disonante'),
    ('Quinta justa', 7, '5J', 'perfecto'),
    ('Sexta menor', 8, '6m', 'consonante'),
    ('Sexta mayor', 9, '6M', 'consonante'),
    ('Septima menor', 10, '7m', 'disonante'),
    ('Septima mayor', 11, '7M', 'disonante'),
    ('Octava', 12, '8J', 'perfecto');

-- El codigo actual consulta estos cuatro intervalos en la primera version.
-- Se cargan todos arriba para que el catalogo quede completo.

INSERT INTO scales (name, type, intervals_pattern, description) VALUES
    ('Mayor', 'diatonica', '2,2,1,2,2,2,1', 'Escala mayor natural.'),
    ('Menor natural', 'diatonica', '2,1,2,2,1,2,2', 'Escala menor natural.');

INSERT INTO badges (name, description, requirement_type, requirement_value, xp_reward, coin_reward) VALUES
    ('Primera sesion', 'Completa tu primera sesion de intervalos.', 'sessions', 1, 10, 5),
    ('Decena', 'Completa 10 sesiones de intervalos.', 'sessions', 10, 50, 20),
    ('Precision', 'Alcanza 80 por ciento de aciertos.', 'accuracy', 80, 25, 10),
    ('Racha', 'Mantiene una racha de 7 dias.', 'streak', 7, 100, 40);

-- Usuario inicial: admin / Semimus2026!
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified)
VALUES ('admin', 'admin@semimus.app',
        '$2b$12$LYkYBg4Y7kIGp2umpzUavexlGAOLDO2Vd9wTgBUXaVzp9AIb5VoMm',
        'Admin', 'SEMIMUS', 'admin', TRUE, TRUE);

INSERT INTO progress (user_id) SELECT id FROM users WHERE username = 'admin';
INSERT INTO user_statistics (user_id) SELECT id FROM users WHERE username = 'admin';
INSERT INTO user_gamification (user_id) SELECT id FROM users WHERE username = 'admin';

COMMIT;

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO semimus;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO semimus;
GRANT USAGE ON SCHEMA public TO semimus;
