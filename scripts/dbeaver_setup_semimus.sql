-- ===============================================================
-- SEMIMUS - Script Completo para DBeaver (PostgreSQL)
-- Copia y pega este contenido en el Editor SQL de DBeaver estando
-- conectado a la base de datos "semimus" (o "semimus_dev").
-- Ejecuta usando el botón "Ejecutar Script SQL" (Alt + X o Ctrl + Shift + E).
-- ===============================================================

BEGIN;

-- 1. Eliminar tablas existentes (si las hay) para evitar conflictos
DROP TABLE IF EXISTS user_badges CASCADE;
DROP TABLE IF EXISTS user_gamification CASCADE;
DROP TABLE IF EXISTS user_statistics CASCADE;
DROP TABLE IF EXISTS progress CASCADE;
DROP TABLE IF EXISTS answers CASCADE;
DROP TABLE IF EXISTS training_sessions CASCADE;
DROP TABLE IF EXISTS questions CASCADE;
DROP TABLE IF EXISTS audios CASCADE;
DROP TABLE IF EXISTS notes CASCADE;
DROP TABLE IF EXISTS instruments CASCADE;
DROP TABLE IF EXISTS users CASCADE;
DROP TABLE IF EXISTS badges CASCADE;
DROP TABLE IF EXISTS intervals CASCADE;
DROP TABLE IF EXISTS scales CASCADE;

-- 2. Habilitar extensión pgcrypto (si no existe)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 3. Crear esquema de tablas

-- Tabla: instruments
CREATE TABLE instruments (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	type VARCHAR(30), 
	emoji VARCHAR(10), 
	description TEXT, 
	image_url VARCHAR(255), 
	tuning VARCHAR(100), 
	range_low VARCHAR(10), 
	range_high VARCHAR(10), 
	is_active BOOLEAN DEFAULT TRUE, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

-- Tabla: users
CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	first_name VARCHAR(80) NOT NULL, 
	last_name VARCHAR(80) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	is_active BOOLEAN DEFAULT TRUE, 
	is_verified BOOLEAN DEFAULT FALSE, 
	avatar_url VARCHAR(255), 
	bio TEXT, 
	reset_token VARCHAR(255), 
	reset_token_expires TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	last_login TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);
CREATE UNIQUE INDEX ix_users_username ON users (username);

-- Tabla: notes
CREATE TABLE notes (
	id SERIAL NOT NULL, 
	name VARCHAR(10) NOT NULL, 
	octave INTEGER NOT NULL, 
	frequency FLOAT, 
	midi_number INTEGER, 
	scientific_name VARCHAR(15), 
	PRIMARY KEY (id), 
	CONSTRAINT uq_note_octave UNIQUE (name, octave)
);

-- Tabla: audios
CREATE TABLE audios (
	id SERIAL NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	original_filename VARCHAR(255) NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	instrument_id INTEGER, 
	note_id INTEGER, 
	duration FLOAT, 
	sample_rate INTEGER, 
	bit_depth INTEGER, 
	channels INTEGER, 
	peak_amplitude FLOAT, 
	file_size INTEGER, 
	difficulty VARCHAR(20) NOT NULL, 
	is_active BOOLEAN DEFAULT TRUE, 
	waveform_data TEXT, 
	tags VARCHAR(255), 
	description TEXT, 
	uploaded_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instrument_id) REFERENCES instruments (id) ON DELETE SET NULL, 
	FOREIGN KEY(note_id) REFERENCES notes (id) ON DELETE SET NULL, 
	FOREIGN KEY(uploaded_by) REFERENCES users (id) ON DELETE SET NULL
);

CREATE INDEX ix_audios_instrument_id ON audios (instrument_id);
CREATE INDEX ix_audios_note_id ON audios (note_id);

-- Tabla: questions
CREATE TABLE questions (
	id SERIAL NOT NULL, 
	mode VARCHAR(30) NOT NULL, 
	type VARCHAR(30) NOT NULL, 
	audio_id INTEGER, 
	correct_answer VARCHAR(255) NOT NULL, 
	options_json TEXT, 
	difficulty INTEGER NOT NULL, 
	instrument_id INTEGER, 
	hint TEXT, 
	explanation TEXT, 
	is_active BOOLEAN DEFAULT TRUE, 
	times_answered INTEGER DEFAULT 0, 
	times_correct INTEGER DEFAULT 0, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(audio_id) REFERENCES audios (id) ON DELETE CASCADE, 
	FOREIGN KEY(instrument_id) REFERENCES instruments (id) ON DELETE SET NULL
);

CREATE INDEX ix_questions_mode ON questions (mode);

-- Tabla: training_sessions
CREATE TABLE training_sessions (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	mode VARCHAR(30) NOT NULL, 
	instrument_id INTEGER, 
	difficulty_level INTEGER, 
	total_questions INTEGER DEFAULT 0, 
	correct_answers INTEGER DEFAULT 0, 
	total_time_secs FLOAT, 
	avg_response_time FLOAT, 
	xp_earned INTEGER DEFAULT 0, 
	coins_earned INTEGER DEFAULT 0, 
	is_completed BOOLEAN DEFAULT FALSE, 
	started_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE, 
	FOREIGN KEY(instrument_id) REFERENCES instruments (id) ON DELETE SET NULL
);

CREATE INDEX ix_training_sessions_user_id ON training_sessions (user_id);

-- Tabla: answers
CREATE TABLE answers (
	id SERIAL NOT NULL, 
	session_id INTEGER NOT NULL, 
	question_id INTEGER, 
	user_answer VARCHAR(255) NOT NULL, 
	is_correct BOOLEAN NOT NULL, 
	response_time FLOAT, 
	answered_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES training_sessions (id) ON DELETE CASCADE, 
	FOREIGN KEY(question_id) REFERENCES questions (id) ON DELETE SET NULL
);

CREATE INDEX ix_answers_question_id ON answers (question_id);
CREATE INDEX ix_answers_session_id ON answers (session_id);

-- Tabla: badges
CREATE TABLE badges (
	id SERIAL NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	description TEXT, 
	icon VARCHAR(10), 
	category VARCHAR(30), 
	requirement_type VARCHAR(30), 
	requirement_value INTEGER, 
	xp_reward INTEGER DEFAULT 0, 
	coin_reward INTEGER DEFAULT 0, 
	is_active BOOLEAN DEFAULT TRUE, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

-- Tabla: intervals
CREATE TABLE intervals (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	semitones INTEGER NOT NULL, 
	abbreviation VARCHAR(10), 
	consonance VARCHAR(20), 
	description TEXT, 
	PRIMARY KEY (id)
);

-- Tabla: progress
CREATE TABLE progress (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	total_sessions INTEGER DEFAULT 0, 
	total_questions_answered INTEGER DEFAULT 0, 
	total_correct INTEGER DEFAULT 0, 
	total_time_minutes FLOAT DEFAULT 0.0, 
	current_streak_days INTEGER DEFAULT 0, 
	longest_streak_days INTEGER DEFAULT 0, 
	last_activity_date DATE, 
	weakest_notes_json TEXT, 
	weakest_intervals_json TEXT, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Tabla: scales
CREATE TABLE scales (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	type VARCHAR(30), 
	intervals_pattern VARCHAR(100) NOT NULL, 
	description TEXT, 
	PRIMARY KEY (id)
);

-- Tabla: user_gamification
CREATE TABLE user_gamification (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	total_xp INTEGER DEFAULT 0, 
	current_level INTEGER DEFAULT 1, 
	coins INTEGER DEFAULT 0, 
	total_coins_earned INTEGER DEFAULT 0, 
	weekly_xp INTEGER DEFAULT 0, 
	monthly_xp INTEGER DEFAULT 0, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);

-- Tabla: user_badges
CREATE TABLE user_badges (
	id SERIAL NOT NULL, 
	user_gamification_id INTEGER NOT NULL, 
	badge_id INTEGER NOT NULL, 
	earned_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_gamification_id) REFERENCES user_gamification (id) ON DELETE CASCADE, 
	FOREIGN KEY(badge_id) REFERENCES badges (id) ON DELETE CASCADE
);

-- Tabla: user_statistics
CREATE TABLE user_statistics (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	accuracy_by_mode_json TEXT, 
	accuracy_by_instr_json TEXT, 
	weekly_sessions_json TEXT, 
	avg_response_time FLOAT DEFAULT 0.0, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE
);


-- 4. Insertar datos iniciales (Seeds)

-- Instrumentos
INSERT INTO instruments (name, description, emoji, is_active) VALUES 
('Tiple', E'Instrumento de cuerdas tipico de la musica andina colombiana, con 12 cuerdas agrupadas en cuatro ordenes.', '🎸', TRUE),
('Requinto', E'Guitarra pequena de cuerdas de nylon, usada en duetos y trios colombianos.', '🎻', TRUE),
('Bandola', E'Instrumento de cuerdas pulsadas del folclore andino colombiano, similar al laud.', '🪕', TRUE),
('Guitarra', E'Guitarra clasica usada como base armonica en la musica andina.', '🎸', TRUE);

-- Notas (Octavas 2 a 5)
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES 
('DO', 2, 65.41, 36, 'DO2'), ('DO#', 2, 69.3, 37, 'DO#2'), ('RE', 2, 73.42, 38, 'RE2'), ('RE#', 2, 77.78, 39, 'RE#2'),
('MI', 2, 82.41, 40, 'MI2'), ('FA', 2, 87.31, 41, 'FA2'), ('FA#', 2, 92.5, 42, 'FA#2'), ('SOL', 2, 98.0, 43, 'SOL2'),
('SOL#', 2, 103.83, 44, 'SOL#2'), ('LA', 2, 110.0, 45, 'LA2'), ('LA#', 2, 116.54, 46, 'LA#2'), ('SI', 2, 123.47, 47, 'SI2'),
('DO', 3, 130.81, 48, 'DO3'), ('DO#', 3, 138.59, 49, 'DO#3'), ('RE', 3, 146.83, 50, 'RE3'), ('RE#', 3, 155.56, 51, 'RE#3'),
('MI', 3, 164.81, 52, 'MI3'), ('FA', 3, 174.62, 53, 'FA3'), ('FA#', 3, 185.0, 54, 'FA#3'), ('SOL', 3, 196.0, 55, 'SOL3'),
('SOL#', 3, 207.65, 56, 'SOL#3'), ('LA', 3, 220.0, 57, 'LA3'), ('LA#', 3, 233.08, 58, 'LA#3'), ('SI', 3, 246.94, 59, 'SI3'),
('DO', 4, 261.63, 60, 'DO4'), ('DO#', 4, 277.18, 61, 'DO#4'), ('RE', 4, 293.66, 62, 'RE4'), ('RE#', 4, 311.13, 63, 'RE#4'),
('MI', 4, 329.63, 64, 'MI4'), ('FA', 4, 349.23, 65, 'FA4'), ('FA#', 4, 369.99, 66, 'FA#4'), ('SOL', 4, 392.0, 67, 'SOL4'),
('SOL#', 4, 415.3, 68, 'SOL#4'), ('LA', 4, 440.0, 69, 'LA4'), ('LA#', 4, 466.16, 70, 'LA#4'), ('SI', 4, 493.88, 71, 'SI4'),
('DO', 5, 523.26, 72, 'DO5'), ('DO#', 5, 554.36, 73, 'DO#5'), ('RE', 5, 587.32, 74, 'RE5'), ('RE#', 5, 622.26, 75, 'RE#5'),
('MI', 5, 659.26, 76, 'MI5'), ('FA', 5, 698.46, 77, 'FA5'), ('FA#', 5, 739.98, 78, 'FA#5'), ('SOL', 5, 784.0, 79, 'SOL5'),
('SOL#', 5, 830.6, 80, 'SOL#5'), ('LA', 5, 880.0, 81, 'LA5'), ('LA#', 5, 932.32, 82, 'LA#5'), ('SI', 5, 987.76, 83, 'SI5');

-- Intervalos
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

-- Escalas
INSERT INTO scales (name, type, intervals_pattern) VALUES 
('Mayor', 'default', '2,2,1,2,2,2,1'),
('Menor natural', 'default', '2,1,2,2,1,2,2'),
('Menor armonica', 'default', '2,1,2,2,1,3,1'),
('Menor melodica', 'default', '2,1,2,2,2,2,1'),
('Pentatonica mayor', 'default', '2,2,3,2,3'),
('Pentatonica menor', 'default', '3,2,2,3,2'),
('Dorica', 'default', '2,1,2,2,2,1,2'),
('Mixolidia', 'default', '2,2,1,2,2,1,2');

-- Badges
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES 
('Primera Nota', E'Completa tu primera sesion de entrenamiento.', '🎵', 'sessions', 1, 10, 5, TRUE),
('Oido de Tiple', E'Alcanza 80% de precision en modo notas.', '🎸', 'accuracy', 80, 25, 10, TRUE),
('Decena', E'Completa 10 sesiones de entrenamiento.', '🏅', 'sessions', 10, 50, 20, TRUE),
('Racha de Fuego', E'Mantén una racha de 7 dias consecutivos.', '🔥', 'streak', 7, 100, 40, TRUE),
('Centurion', E'Responde 100 preguntas correctamente.', '💯', 'correct', 100, 50, 20, TRUE),
('Maestra Andina', E'Completa 50 sesiones de entrenamiento.', '🏆', 'sessions', 50, 200, 80, TRUE),
('Perfeccion', E'Logra 100% de precision en una sesion de 10+.', '⭐', 'perfect', 1, 150, 60, TRUE),
('Explorador', E'Entrena con los 3 instrumentos principales.', '🗺', 'instruments', 3, 75, 30, TRUE);

-- Usuario admin (Contraseña inicial: Semimus2026!)
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified, created_at) VALUES 
('admin', 'admin@semimus.app', '$2b$12$LYkYBg4Y7kIGp2umpzUavexlGAOLDO2Vd9wTgBUXaVzp9AIb5VoMm', 'Admin', 'SEMIMUS', 'admin', TRUE, TRUE, CURRENT_TIMESTAMP);

INSERT INTO progress (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));
INSERT INTO user_statistics (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));
INSERT INTO user_gamification (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));

COMMIT;
