-- ===============================================================
-- SEMIMUS - Esquema PostgreSQL
-- Generado automaticamente el 2026-08-19 14:09:22.050883
-- ===============================================================

BEGIN;

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ------------------------------------------------------------------
-- Tabla: instruments
-- ------------------------------------------------------------------
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
	is_active BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

-- ------------------------------------------------------------------
-- Tabla: users
-- ------------------------------------------------------------------
CREATE TABLE users (
	id SERIAL NOT NULL, 
	username VARCHAR(50) NOT NULL, 
	email VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	first_name VARCHAR(80) NOT NULL, 
	last_name VARCHAR(80) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	is_active BOOLEAN, 
	is_verified BOOLEAN, 
	avatar_url VARCHAR(255), 
	bio TEXT, 
	reset_token VARCHAR(255), 
	reset_token_expires TIMESTAMP WITHOUT TIME ZONE, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	last_login TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_users_email ON users (email);

CREATE UNIQUE INDEX ix_users_username ON users (username);

-- ------------------------------------------------------------------
-- Tabla: notes
-- ------------------------------------------------------------------
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

-- ------------------------------------------------------------------
-- Tabla: audios
-- ------------------------------------------------------------------
CREATE TABLE audios (
	id SERIAL NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	original_filename VARCHAR(255) NOT NULL, 
	file_path VARCHAR(500) NOT NULL, 
	audio_data BYTEA,
	technique VARCHAR(50),
	rhythm VARCHAR(50),
	octave INTEGER,
	instrument_id INTEGER, 
	note_id INTEGER, 
	duration FLOAT, 
	sample_rate INTEGER, 
	bit_depth INTEGER, 
	channels INTEGER, 
	peak_amplitude FLOAT, 
	file_size INTEGER, 
	difficulty VARCHAR(20) NOT NULL, 
	is_active BOOLEAN, 
	waveform_data TEXT, 
	tags VARCHAR(255), 
	description TEXT, 
	uploaded_by INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(instrument_id) REFERENCES instruments (id), 
	FOREIGN KEY(note_id) REFERENCES notes (id), 
	FOREIGN KEY(uploaded_by) REFERENCES users (id)
);

CREATE INDEX ix_audios_instrument_id ON audios (instrument_id);

CREATE INDEX ix_audios_note_id ON audios (note_id);

-- ------------------------------------------------------------------
-- Tabla: questions
-- ------------------------------------------------------------------
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
	is_active BOOLEAN, 
	times_answered INTEGER, 
	times_correct INTEGER, 
	created_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(audio_id) REFERENCES audios (id), 
	FOREIGN KEY(instrument_id) REFERENCES instruments (id)
);

CREATE INDEX ix_questions_mode ON questions (mode);

-- ------------------------------------------------------------------
-- Tabla: training_sessions
-- ------------------------------------------------------------------
CREATE TABLE training_sessions (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	mode VARCHAR(30) NOT NULL, 
	instrument_id INTEGER, 
	difficulty_level INTEGER, 
	total_questions INTEGER, 
	correct_answers INTEGER, 
	total_time_secs FLOAT, 
	avg_response_time FLOAT, 
	xp_earned INTEGER, 
	coins_earned INTEGER, 
	is_completed BOOLEAN, 
	started_at TIMESTAMP WITHOUT TIME ZONE, 
	completed_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(instrument_id) REFERENCES instruments (id)
);

CREATE INDEX ix_training_sessions_user_id ON training_sessions (user_id);

-- ------------------------------------------------------------------
-- Tabla: answers
-- ------------------------------------------------------------------
CREATE TABLE answers (
	id SERIAL NOT NULL, 
	session_id INTEGER NOT NULL, 
	question_id INTEGER, 
	user_answer VARCHAR(255) NOT NULL, 
	is_correct BOOLEAN NOT NULL, 
	response_time FLOAT, 
	answered_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(session_id) REFERENCES training_sessions (id), 
	FOREIGN KEY(question_id) REFERENCES questions (id)
);

CREATE INDEX ix_answers_question_id ON answers (question_id);

CREATE INDEX ix_answers_session_id ON answers (session_id);

-- ------------------------------------------------------------------
-- Tabla: badges
-- ------------------------------------------------------------------
CREATE TABLE badges (
	id SERIAL NOT NULL, 
	name VARCHAR(80) NOT NULL, 
	description TEXT, 
	icon VARCHAR(10), 
	category VARCHAR(30), 
	requirement_type VARCHAR(30), 
	requirement_value INTEGER, 
	xp_reward INTEGER, 
	coin_reward INTEGER, 
	is_active BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);

-- ------------------------------------------------------------------
-- Tabla: intervals
-- ------------------------------------------------------------------
CREATE TABLE intervals (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	semitones INTEGER NOT NULL, 
	abbreviation VARCHAR(10), 
	consonance VARCHAR(20), 
	description TEXT, 
	PRIMARY KEY (id)
);

-- ------------------------------------------------------------------
-- Tabla: progress
-- ------------------------------------------------------------------
CREATE TABLE progress (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	total_sessions INTEGER, 
	total_questions_answered INTEGER, 
	total_correct INTEGER, 
	total_time_minutes FLOAT, 
	current_streak_days INTEGER, 
	longest_streak_days INTEGER, 
	last_activity_date DATE, 
	weakest_notes_json TEXT, 
	weakest_intervals_json TEXT, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- ------------------------------------------------------------------
-- Tabla: scales
-- ------------------------------------------------------------------
CREATE TABLE scales (
	id SERIAL NOT NULL, 
	name VARCHAR(50) NOT NULL, 
	type VARCHAR(30), 
	intervals_pattern VARCHAR(100) NOT NULL, 
	description TEXT, 
	PRIMARY KEY (id)
);

-- ------------------------------------------------------------------
-- Tabla: user_gamification
-- ------------------------------------------------------------------
CREATE TABLE user_gamification (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	total_xp INTEGER, 
	current_level INTEGER, 
	coins INTEGER, 
	total_coins_earned INTEGER, 
	weekly_xp INTEGER, 
	monthly_xp INTEGER, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

-- ------------------------------------------------------------------
-- Tabla: user_badges
-- ------------------------------------------------------------------
CREATE TABLE user_badges (
	id SERIAL NOT NULL, 
	user_gamification_id INTEGER NOT NULL, 
	badge_id INTEGER NOT NULL, 
	earned_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_gamification_id) REFERENCES user_gamification (id), 
	FOREIGN KEY(badge_id) REFERENCES badges (id)
);

-- ------------------------------------------------------------------
-- Tabla: user_statistics
-- ------------------------------------------------------------------
CREATE TABLE user_statistics (
	id SERIAL NOT NULL, 
	user_id INTEGER NOT NULL, 
	accuracy_by_mode_json TEXT, 
	accuracy_by_instr_json TEXT, 
	weekly_sessions_json TEXT, 
	avg_response_time FLOAT, 
	updated_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	UNIQUE (user_id), 
	FOREIGN KEY(user_id) REFERENCES users (id)
);

COMMIT;
