-- ===============================================================
-- SEMIMUS - Datos iniciales (seed)
-- Generado el 2026-08-19T19:06:44.531911
-- ===============================================================

BEGIN;

-- Instrumentos
INSERT INTO instruments (name, description, emoji, is_active) VALUES ('Tiple', E'Instrumento de cuerdas tipico de la musica andina colombiana, con 12 cuerdas agrupadas en cuatro ordenes.', '🎸', TRUE);
INSERT INTO instruments (name, description, emoji, is_active) VALUES ('Requinto', E'Guitarra pequena de cuerdas de nylon, usada en duetos y trios colombianos.', '🎻', TRUE);
INSERT INTO instruments (name, description, emoji, is_active) VALUES ('Bandola', E'Instrumento de cuerdas pulsadas del folclore andino colombiano, similar al laud.', '🪕', TRUE);
INSERT INTO instruments (name, description, emoji, is_active) VALUES ('Guitarra', E'Guitarra clasica usada como base armonica en la musica andina.', '🎸', TRUE);

-- Notas (octavas 2 a 5)
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO', 2, 65.41, 36, 'DO2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO#', 2, 69.3, 37, 'DO#2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE', 2, 73.42, 38, 'RE2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE#', 2, 77.78, 39, 'RE#2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('MI', 2, 82.41, 40, 'MI2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA', 2, 87.31, 41, 'FA2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA#', 2, 92.5, 42, 'FA#2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL', 2, 98.0, 43, 'SOL2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL#', 2, 103.83, 44, 'SOL#2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA', 2, 110.0, 45, 'LA2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA#', 2, 116.54, 46, 'LA#2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SI', 2, 123.47, 47, 'SI2');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO', 3, 130.81, 48, 'DO3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO#', 3, 138.59, 49, 'DO#3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE', 3, 146.83, 50, 'RE3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE#', 3, 155.56, 51, 'RE#3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('MI', 3, 164.81, 52, 'MI3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA', 3, 174.62, 53, 'FA3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA#', 3, 185.0, 54, 'FA#3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL', 3, 196.0, 55, 'SOL3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL#', 3, 207.65, 56, 'SOL#3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA', 3, 220.0, 57, 'LA3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA#', 3, 233.08, 58, 'LA#3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SI', 3, 246.94, 59, 'SI3');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO', 4, 261.63, 60, 'DO4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO#', 4, 277.18, 61, 'DO#4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE', 4, 293.66, 62, 'RE4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE#', 4, 311.13, 63, 'RE#4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('MI', 4, 329.63, 64, 'MI4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA', 4, 349.23, 65, 'FA4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA#', 4, 369.99, 66, 'FA#4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL', 4, 392.0, 67, 'SOL4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL#', 4, 415.3, 68, 'SOL#4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA', 4, 440.0, 69, 'LA4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA#', 4, 466.16, 70, 'LA#4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SI', 4, 493.88, 71, 'SI4');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO', 5, 523.26, 72, 'DO5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('DO#', 5, 554.36, 73, 'DO#5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE', 5, 587.32, 74, 'RE5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('RE#', 5, 622.26, 75, 'RE#5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('MI', 5, 659.26, 76, 'MI5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA', 5, 698.46, 77, 'FA5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('FA#', 5, 739.98, 78, 'FA#5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL', 5, 784.0, 79, 'SOL5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SOL#', 5, 830.6, 80, 'SOL#5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA', 5, 880.0, 81, 'LA5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('LA#', 5, 932.32, 82, 'LA#5');
INSERT INTO notes (name, octave, frequency, midi_number, scientific_name) VALUES ('SI', 5, 987.76, 83, 'SI5');

-- Intervalos
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Unisono', 0, 'U', 'perfecto');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Segunda menor', 1, '2m', 'disonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Segunda mayor', 2, '2M', 'disonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Tercera menor', 3, '3m', 'consonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Tercera mayor', 4, '3M', 'consonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Cuarta justa', 5, '4J', 'perfecto');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Cuarta aumentada', 6, '4A', 'disonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Quinta justa', 7, '5J', 'perfecto');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Sexta menor', 8, '6m', 'consonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Sexta mayor', 9, '6M', 'consonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Septima menor', 10, '7m', 'disonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Septima mayor', 11, '7M', 'disonante');
INSERT INTO intervals (name, semitones, abbreviation, consonance) VALUES ('Octava', 12, '8J', 'perfecto');

-- Escalas
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Mayor', 'default', '2,2,1,2,2,2,1');
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Menor natural', 'default', '2,1,2,2,1,2,2');
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Menor armonica', 'default', '2,1,2,2,1,3,1');
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Menor melodica', 'default', '2,1,2,2,2,2,1');
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Pentatonica mayor', 'default', '2,2,3,2,3');
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Pentatonica menor', 'default', '3,2,2,3,2');
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Dorica', 'default', '2,1,2,2,2,1,2');
INSERT INTO scales (name, type, intervals_pattern) VALUES ('Mixolidia', 'default', '2,2,1,2,2,1,2');

-- Badges
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Primera Nota', E'Completa tu primera sesion de entrenamiento.', '🎵', 'sessions', 1, 10, 5, TRUE);
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Oido de Tiple', E'Alcanza 80% de precision en modo notas.', '🎸', 'accuracy', 80, 25, 10, TRUE);
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Decena', E'Completa 10 sesiones de entrenamiento.', '🏅', 'sessions', 10, 50, 20, TRUE);
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Racha de Fuego', E'Mantén una racha de 7 dias consecutivos.', '🔥', 'streak', 7, 100, 40, TRUE);
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Centurion', E'Responde 100 preguntas correctamente.', '💯', 'correct', 100, 50, 20, TRUE);
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Maestra Andina', E'Completa 50 sesiones de entrenamiento.', '🏆', 'sessions', 50, 200, 80, TRUE);
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Perfeccion', E'Logra 100% de precision en una sesion de 10+.', '⭐', 'perfect', 1, 150, 60, TRUE);
INSERT INTO badges (name, description, icon, requirement_type, requirement_value, xp_reward, coin_reward, is_active) VALUES ('Explorador', E'Entrena con los 3 instrumentos principales.', '🗺', 'instruments', 3, 75, 30, TRUE);

-- Usuario admin (password por defecto: Semimus2026!)
INSERT INTO users (username, email, password_hash, first_name, last_name, role, is_active, is_verified, created_at) VALUES ('admin', 'admin@semimus.app', '$2b$12$LYkYBg4Y7kIGp2umpzUavexlGAOLDO2Vd9wTgBUXaVzp9AIb5VoMm', 'Admin', 'SEMIMUS', 'admin', TRUE, TRUE, CURRENT_TIMESTAMP);
INSERT INTO progress (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));
INSERT INTO user_statistics (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));
INSERT INTO user_gamification (user_id) VALUES ((SELECT id FROM users WHERE email='admin@semimus.app'));

COMMIT;
