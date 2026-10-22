/**
 * SENAFÓNICA Game Engine — Videojuego Web Autónomo e Integrado
 * Recorrido Cultural por la Provincia de Vélez
 *
 * Implementa el flujo EXPLORACIÓN → EVALUACIÓN:
 *   1. Fase de exploración: el usuario escucha notas individuales, el intervalo
 *      completo y lee la mnemotecnia antes de poder iniciar el quiz.
 *   2. Fase de evaluación: preguntas de reconocimiento auditivo con feedback.
 */

function senafonicaGame(initData) {
  // ── PARSE INIT DATA ────────────────────────────────────────────────────────
  let data = initData;
  if (!data || typeof data !== 'object') {
    try {
      const el = document.getElementById('senafonica-init-data');
      data = el ? JSON.parse(el.textContent) : {};
    } catch (e) {
      console.warn('Could not parse senafonica-init-data', e);
      data = {};
    }
  }

  return {
    // ── DATA & CONFIG ──────────────────────────────────────────────────────
    user: data.user || { name: 'Aprendiz Veleño', xp: 0, coins: 0, level: 1, streak: 1 },
    catalog: data.catalog || {},
    intervals: data.intervals || [],
    scales: data.scales || [],
    stations: data.levels || [],
    theoryQuestions: data.theoryQuestions || [],
    inductionQuestions: data.inductionQuestions || [],
    shopItems: data.shopItems || [],
    csrfToken: data.csrfToken || '',

    // ── ONBOARDING & LEGAL FLOW ───────────────────────────────────────────
    // Steps: 'legal' → 'tutorial' → 'induction_cards' → 'induction_quiz' → 'completed'
    onboardingStep: 'completed',
    playerAge: '',
    legalConsent: false,
    inductionIndex: 0,
    inductionSelected: null,
    inductionAnswered: false,
    inductionIsCorrect: false,

    // ── IN-GAME MODALS & TABS ─────────────────────────────────────────────
    currentTab: 'path',           // 'path' | 'learn' | 'training' | 'jam'
    backgroundImage: '',
    backgroundColor: '#0B111A',
    backgroundVisible: false,
    backgroundTimer: null,
    showStationModal: false,
    selectedStation: null,
    showStatsModal: false,
    showShopModal: false,
    showRescueModal: false,

    // ── LEARN PHASE (Exploración Activa) ──────────────────────────────────
    learnStation: null,           // station currently in learn mode
    learnPhase: 'intro',          // 'intro' | 'note1' | 'note2' | 'interval' | 'ready'
    learnNote1Played: false,
    learnNote2Played: false,
    learnIntervalPlayed: false,
    learnDescendingPlayed: false,
    learnChordPlayed: false,
    learnDemoNotes: [],
    learnNotePlayed: [],
    learnSamples: [],
    learnCheckMessage: '',
    learnReadyToPlay: false,      // true when user has explored enough to unlock eval

    // ── GAMIFICATION HUD STATE ────────────────────────────────────────────
    lives: 5,
    maxLives: 5,
    xp: 0,
    coins: 0,
    streak: 1,
    levelStars: {},
    unlockedLevels: [1],
    totalQuestionsAnswered: 0,
    totalCorrectAnswered: 0,
    unlockedCollectibles: [],
    equippedSkin: 'skin_tiple_noble',
    equippedAccessories: { hat: '', body: '', eyes: '' },
    unlockedItems: ['skin_tiple_noble'],

    // ── ACTIVE EXERCISE STATE ─────────────────────────────────────────────
    activeStation: null,
    levelQuestions: [],
    qIndex: 0,
    currentQ: null,
    answered: false,
    selectedOption: null,
    isCorrect: false,
    sessionCorrect: 0,
    sessionWrong: 0,
    intervalDirection: 'ascendente',
    activeNotePlayingIndex: -1,
    activeNoteName: '',
    isComparingAudio: false,
    comparePhase: 'idle',

    // ── RESCUE CHALLENGE STATE ────────────────────────────────────────────
    rescueQuestions: [],
    rescueIndex: 0,
    rescueAnswered: false,
    rescueSelected: null,
    rescueIsCorrect: false,

    // ── FREE JAM (MODO LIBRE) STATE ───────────────────────────────────────
    jamInstrument: 'Tiple',
    jamScaleIndex: 0,
    jamRootMidi: 60,
    jamTempo: 1.0,
    jamIntervalSemitones: 7,
    jamDirection: 'ascendente',
    jamActiveNoteIndex: -1,

    // ── MASCOT CONTROLLER ─────────────────────────────────────────────────
    mascotState: 'idle',
    mascotSpeech: '¡Bienvenido a SENAFÓNICA! Recorreremos la hermosa Provincia de Vélez.',
    mascotImg: '/static/img/ninos_traje.png',

    // ── AUDIO ENGINE ──────────────────────────────────────────────────────
    audio: null,
    isPlaying: false,

    // ══════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ══════════════════════════════════════════════════════════════════════
    init() {
      this.audio = new SenafonicaAudioEngine(this.catalog);

      const savedOnboarding = localStorage.getItem('senafonica_onboarding_done');
      if (!savedOnboarding) {
        this.onboardingStep = 'legal';
      } else {
        this.onboardingStep = 'completed';
      }

      this._loadLocalState();

      // Keyboard shortcuts: Space to replay, 1–4 for options
      window.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.code === 'Space') {
          e.preventDefault();
          if (this.currentTab === 'training') {
            this.replayAudio();
          } else if (this.currentTab === 'learn') {
            this.learnPlayInterval();
          }
        } else if (['Digit1', 'Digit2', 'Digit3', 'Digit4'].includes(e.code)) {
          const idx = parseInt(e.code.replace('Digit', '')) - 1;
          if (this.currentTab === 'training' && !this.answered) {
            this.selectOption(idx);
          } else if (this.showRescueModal && !this.rescueAnswered) {
            this.selectRescueOption(idx);
          } else if (this.onboardingStep === 'induction_quiz' && !this.inductionAnswered) {
            this.selectInductionOption(idx);
          }
        }
      });
    },

    // ══════════════════════════════════════════════════════════════════════
    // ONBOARDING FLOW
    // ══════════════════════════════════════════════════════════════════════
    submitLegalConsent() {
      if (!this.playerAge || !this.legalConsent) return;
      this.onboardingStep = 'tutorial';
      this._updateMascot('celebrating', '¡Excelente! Iniciemos nuestro recorrido por la cuna del Tiple.');
    },

    startInductionCards() {
      this.onboardingStep = 'induction_cards';
      this._updateMascot('listening', 'Minilección: Comprende qué es un Intervalo y una Escala.');
    },

    startInductionQuiz() {
      this.onboardingStep = 'induction_quiz';
      this.inductionIndex = 0;
      this.inductionAnswered = false;
      this.inductionSelected = null;
      this._updateMascot('idle', 'Mini-Quiz de Inducción: 3 preguntas rápidas para calibrar tu oído.');
    },

    selectInductionOption(optIdx) {
      if (this.inductionAnswered) return;
      const q = this.inductionQuestions[this.inductionIndex];
      const opt = q.options[optIdx];
      if (!opt) return;

      this.inductionAnswered = true;
      this.inductionSelected = opt;
      this.inductionIsCorrect = (opt === q.correct);

      if (this.inductionIsCorrect) {
        this.audio.playSuccessSound();
        this._updateMascot('celebrating', '¡Muy bien contestado!');
      } else {
        this.audio.playErrorSound();
        this._updateMascot('sad', q.explanation);
      }
    },

    nextInductionQuestion() {
      if (this.inductionIndex < this.inductionQuestions.length - 1) {
        this.inductionIndex++;
        this.inductionAnswered = false;
        this.inductionSelected = null;
        this.inductionIsCorrect = false;
      } else {
        this.onboardingStep = 'completed';
        localStorage.setItem('senafonica_onboarding_done', 'true');
        this.xp += 30;
        this.coins += 10;
        this.audio.playLevelCompleteSound();
        this._triggerConfetti();
        this._updateMascot('celebrating', '¡Inducción superada! Llegamos a Barbosa, Puerta de Oro de Santander.');
        this._saveLocalState();
      }
    },

    // ══════════════════════════════════════════════════════════════════════
    // LOCAL STORAGE PERSISTENCE
    // ══════════════════════════════════════════════════════════════════════
    _loadLocalState() {
      const saved = localStorage.getItem('senafonica_gamification_velez_v2');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          this.lives = parsed.lives !== undefined ? Math.min(parsed.lives, this.maxLives) : 5;
          this.xp = this.user.authenticated
            ? this.user.xp || 0
            : Math.max(parsed.xp || 0, this.user.xp || 0);
          this.coins = this.user.authenticated
            ? this.user.coins || 0
            : Math.max(parsed.coins || 0, this.user.coins || 0);
          this.streak = Math.max(parsed.streak || 1, this.user.streak || 1);
          this.levelStars = parsed.levelStars || {};
          this.unlockedLevels = parsed.unlockedLevels || [1];
          this.totalQuestionsAnswered = parsed.totalQuestionsAnswered || 0;
          this.totalCorrectAnswered = parsed.totalCorrectAnswered || 0;
          this.unlockedCollectibles = parsed.unlockedCollectibles || [];
          this.equippedSkin = parsed.equippedSkin || 'skin_tiple_noble';
          this.equippedAccessories = parsed.equippedAccessories || { hat: '', body: '', eyes: '' };
          const localItems = parsed.unlockedItems || ['skin_tiple_noble'];
          if (this.user.authenticated) {
            const skins = this.user.unlocked_skins || ['skin_tiple_noble'];
            this.equippedSkin = this.user.equipped_skin || 'skin_tiple_noble';
            this.unlockedItems = [...new Set([
              ...localItems.filter(id => !this.shopItems.some(item => item.id === id && item.type === 'skin')),
              ...skins,
            ])];
          } else {
            this.unlockedItems = localItems;
          }
          return;
        } catch (e) {
          console.warn('Could not parse local state', e);
        }
      }
      this.xp = this.user.xp || 0;
      this.coins = this.user.coins || 0;
      this.streak = this.user.streak || 1;
      this.equippedSkin = this.user.equipped_skin || 'skin_tiple_noble';
      this.unlockedItems = this.user.unlocked_skins || ['skin_tiple_noble'];
    },

    _saveLocalState() {
      const state = {
        lives: this.lives,
        xp: this.xp,
        coins: this.coins,
        streak: this.streak,
        levelStars: this.levelStars,
        unlockedLevels: this.unlockedLevels,
        totalQuestionsAnswered: this.totalQuestionsAnswered,
        totalCorrectAnswered: this.totalCorrectAnswered,
        unlockedCollectibles: this.unlockedCollectibles,
        equippedSkin: this.equippedSkin,
        equippedAccessories: this.equippedAccessories,
        unlockedItems: this.unlockedItems,
      };
      localStorage.setItem('senafonica_gamification_velez_v2', JSON.stringify(state));
    },

    // ══════════════════════════════════════════════════════════════════════
    // MASCOT CONTROLLER
    // ══════════════════════════════════════════════════════════════════════
    _updateMascot(state, speech) {
      this.mascotState = state;
      if (speech) this.mascotSpeech = speech;
      if (state === 'celebrating') {
        this.mascotImg = '/static/img/ninos_acertaste.png';
      } else if (state === 'sad') {
        this.mascotImg = '/static/img/ninos_tristes.png';
      } else {
        this.mascotImg = '/static/img/ninos_traje.png';
      }
    },

    // ══════════════════════════════════════════════════════════════════════
    // STATIONS & MAP NAVIGATION
    // ══════════════════════════════════════════════════════════════════════
    previewStation(station) {
      this.selectedStation = station;
      this.changeBackground(station.background_image, station.theme_color);
      this.showStationModal = true;
      this._updateMascot('listening', `${station.station_name}: ${station.subtitle}`);
    },

    startStationFromModal() {
      this.showStationModal = false;
      if (this.selectedStation) {
        this.startLearnPhase(this.selectedStation);
      }
    },

    // ══════════════════════════════════════════════════════════════════════
    // FASE DE EXPLORACIÓN / APRENDIZAJE (LEARN PHASE)
    // El usuario DEBE explorar el contenido antes de poder iniciar el quiz.
    // ══════════════════════════════════════════════════════════════════════
    startLearnPhase(station) {
      if (!this.unlockedLevels.includes(station.id)) {
        this._updateMascot('sad', 'Esta estación está bloqueada. Completa las estaciones previas para avanzar.');
        return;
      }

      if (this.lives <= 0) {
        this.openRescueModal();
        return;
      }

      this.learnStation = station;
      this.changeBackground(station.background_image, station.theme_color);
      this.learnPhase = 'intro';
      this.learnNote1Played = false;
      this.learnNote2Played = false;
      this.learnIntervalPlayed = false;
      this.learnDescendingPlayed = false;
      this.learnChordPlayed = false;
      this.learnReadyToPlay = false;
      this.learnCheckMessage = '';
      const content = station.learn_content || {};
      this.learnDemoNotes = content.demo_notes || [60, 67];
      this.learnNotePlayed = this.learnDemoNotes.map(() => false);
      const sampleNotes = [this.learnDemoNotes];
      if (content.demo_notes_b && content.demo_notes_b.length) {
        sampleNotes.push(content.demo_notes_b);
      }
      this.learnSamples = sampleNotes.map((notes, index) => {
        const correct = station.id === 1
          ? 'Agudo'
          : station.type === 'melody'
            ? content.identification
          : station.type === 'scale'
          ? station.scale_name
          : station.id === 2
            ? 'Notas naturales'
          : station.type === 'final_boss' && notes.length > 2
            ? 'Acorde mayor'
            : this._intervalNameForNotes(notes, index === 1
              ? (station.intervals || [content.interval_name])[1] || content.interval_name
              : content.interval_name);
        const pool = station.id === 1
          ? ['Agudo', 'Grave']
          : station.type === 'melody'
            ? station.melodies.map(melody => melody.name)
          : station.type === 'scale'
          ? this.scales.map(scale => scale.name)
          : station.id === 2
            ? ['Notas naturales', 'Escala mayor', 'Escala menor natural', 'Escala pentatónica mayor']
          : station.type === 'final_boss' && correct === 'Acorde mayor'
            ? ['Acorde mayor', 'Acorde menor', 'Quinta justa', 'Tercera mayor']
            : (station.intervals || []).concat(this.intervals.map(interval => interval.name));
        return {
          label: index === 0 ? 'Muestra principal' : 'Muestra alternativa',
          notes,
          correct,
          options: this._makeOptions(correct, [...new Set(pool)], 4),
          played: false,
          identified: false,
          selected: '',
        };
      });
      const instrument = station.instrument === 'Todos' ? 'Tiple' : station.instrument;
      const preloadNotes = [...new Set([
        ...this.learnDemoNotes,
        ...sampleNotes.flat(),
      ])];
      void this.audio.preloadNotes(instrument, preloadNotes);
      this.currentTab = 'learn';

      this._updateMascot('listening', `Aprendiendo en ${station.station_name}. ${content.title || station.subtitle}`);
    },

    _intervalNameForNotes(notes, fallback) {
      if (!notes || notes.length < 2) return fallback;
      const semitones = Math.abs(notes[notes.length - 1] - notes[0]);
      return (this.intervals.find(interval => interval.semitones === semitones) || {}).name || fallback;
    },

    async _runLearnPlayback(playback) {
      if (this.isPlaying || !this.learnStation) return false;
      this.isPlaying = true;
      try {
        await playback();
        return true;
      } catch (error) {
        console.error('Could not play learning sample:', error);
        this.learnCheckMessage = 'No se pudo reproducir la muestra. Inténtalo de nuevo.';
        return false;
      } finally {
        this.isPlaying = false;
      }
    },

    async learnPlayNote(index) {
      const midi = this.learnDemoNotes[index];
      if (midi === undefined) return;
      const inst = this.learnStation.instrument === 'Todos' ? 'Tiple' : this.learnStation.instrument;
      this._updateMascot('listening', `Escucha la nota ${this.audio.midiToName(midi)}`);
      const played = await this._runLearnPlayback(async () => {
        const duration = this.audio.scaleNoteDuration;
        await this.audio.playNote(inst, midi, 0, duration, 0.95);
        await new Promise(resolve => setTimeout(resolve, (duration + this.audio.scaleNoteGap) * 1000));
      });
      if (played) {
        this.learnNotePlayed[index] = true;
        this.learnNote1Played = Boolean(this.learnNotePlayed[0]);
        this.learnNote2Played = Boolean(this.learnNotePlayed[1]);
        this._checkLearnReady();
      }
    },

    learnPlayNote1() {
      return this.learnPlayNote(0);
    },

    learnPlayNote2() {
      return this.learnPlayNote(1);
    },

    async playLearnSample(index) {
      const sample = this.learnSamples[index];
      if (!sample) return;
      const inst = this.learnStation.instrument === 'Todos' ? 'Tiple' : this.learnStation.instrument;
      this._updateMascot('listening', `Escucha la ${sample.label.toLowerCase()} e identifica lo que oyes.`);
      const played = await this._runLearnPlayback(async () => {
        if (this.learnStation.type === 'scale' && index === 0) {
          const pattern = this.learnStation.learn_content.scale_pattern;
          await this.audio.playScale(inst, sample.notes[0], pattern, 1.0, (noteIndex, midi, name) => {
            this.activeNoteName = name || '';
          });
        } else {
          const duration = this.audio.scaleNoteDuration;
          for (const midi of sample.notes) {
            await this.audio.playNote(inst, midi, 0, duration, 0.95);
            await new Promise(resolve => setTimeout(resolve, (duration + this.audio.scaleNoteGap) * 1000));
          }
          this.activeNoteName = '';
        }
      });
      if (played) {
        sample.played = true;
        this._checkLearnReady();
      }
    },

    learnPlayInterval() {
      return this.playLearnSample(0);
    },

    identifyLearnSample(index, answer) {
      const sample = this.learnSamples[index];
      if (!sample || !sample.played || sample.identified) return;
      sample.selected = answer;
      sample.identified = answer === sample.correct;
      this.learnCheckMessage = sample.identified
        ? '¡Correcto! Identificaste la muestra.'
        : 'Aún no. Vuelve a escuchar la muestra e inténtalo otra vez.';
      if (sample.identified) this._checkLearnReady();
    },

    async learnPlaySequence(direction) {
      const notes = [...this.learnDemoNotes];
      if (direction === 'descendente') notes.reverse();
      const inst = this.learnStation.instrument === 'Todos' ? 'Tiple' : this.learnStation.instrument;
      const played = await this._runLearnPlayback(async () => {
        const duration = this.audio.scaleNoteDuration;
        for (const midi of notes) {
          await this.audio.playNote(inst, midi, 0, duration, 0.95);
          await new Promise(resolve => setTimeout(resolve, (duration + this.audio.scaleNoteGap) * 1000));
        }
      });
      if (played) {
        if (direction === 'descendente') this.learnDescendingPlayed = true;
        else this.learnIntervalPlayed = true;
        this._checkLearnReady();
      }
    },

    async learnPlayChord() {
      const inst = this.learnStation.instrument === 'Todos' ? 'Tiple' : this.learnStation.instrument;
      const root = this.learnDemoNotes[0] || 60;
      const chord = this.learnStation.learn_content.harmonic_notes || [root, root + 4, root + 7, root + 12];
      const played = await this._runLearnPlayback(async () => {
        const duration = this.audio.scaleNoteDuration;
        await Promise.all(chord.map(midi => this.audio.playNote(inst, midi, 0, duration, 0.65)));
        await new Promise(resolve => setTimeout(resolve, (duration + this.audio.scaleNoteGap) * 1000));
      });
      if (played) {
        this.learnChordPlayed = true;
        this._checkLearnReady();
      }
    },

    _checkLearnReady() {
      const requiredNotes = this.learnStation && this.learnStation.id === 2
        ? this.learnNotePlayed.length
        : Math.min(2, this.learnNotePlayed.length);
      const notesExplored = this.learnNotePlayed.slice(0, requiredNotes).every(Boolean);
      const samplesIdentified = this.learnSamples.length > 0
        && this.learnSamples.every(sample => sample.identified);
      this.learnReadyToPlay = notesExplored
        && this.learnIntervalPlayed
        && this.learnDescendingPlayed
        && this.learnChordPlayed
        && samplesIdentified;
      if (this.learnReadyToPlay) {
        this._updateMascot('celebrating', '¡Exploraste e identificaste las muestras! Ya puedes iniciar el desafío.');
      }
    },

    // Transition from LEARN phase to EVALUATION/QUIZ phase
    startEvaluationFromLearn() {
      if (!this.learnReadyToPlay || !this.learnStation) return;
      this.startStation(this.learnStation);
    },

    // ══════════════════════════════════════════════════════════════════════
    // STATION QUIZ INITIALIZATION
    // ══════════════════════════════════════════════════════════════════════
    startStation(station) {
      if (!this.unlockedLevels.includes(station.id)) {
        this._updateMascot('sad', 'Esta estación está bloqueada. Completa las estaciones previas para avanzar.');
        return;
      }

      if (this.lives <= 0) {
        this.openRescueModal();
        return;
      }

      this.activeStation = station;
      this.changeBackground(station.background_image, station.theme_color);
      this.qIndex = 0;
      this.sessionCorrect = 0;
      this.sessionWrong = 0;
      this.levelQuestions = this._generateQuestionsForStation(station);
      this._preloadQuestionAudio(this.levelQuestions);
      this.currentQ = this.levelQuestions[0];
      this.answered = false;
      this.selectedOption = null;
      this.currentTab = 'training';

      this._updateMascot('listening', `¡Llegamos a ${station.station_name}! Escucha con atención.`);

      this.$nextTick(() => {
        setTimeout(() => this.playCurrentAudio(), 400);
      });
    },

    _preloadQuestionAudio(questions) {
      const notes = questions.flatMap(question => {
        if (question.type === 'melody') return question.melodyNotes;
        if (question.type === 'scale') {
          const scaleNotes = [question.rootMidi];
          question.pattern.reduce((midi, semitones) => {
            const nextMidi = midi + semitones;
            scaleNotes.push(nextMidi);
            return nextMidi;
          }, question.rootMidi);
          return scaleNotes;
        }
        const direction = question.direction === 'descendente' ? -1 : 1;
        return [question.rootMidi, question.rootMidi + question.semitones * direction];
      });
      const instrument = questions[0] ? questions[0].instrument : 'Tiple';
      void this.audio.preloadNotes(instrument, [...new Set(notes)]);
    },

    _generateQuestionsForStation(station) {
      const questions = [];
      const count = station.questions_count || 5;

      if (station.type === 'pitch') {
        for (let i = 0; i < count; i++) {
          const direction = i % 2 === 0 ? 'ascendente' : 'descendente';
          questions.push({
            id: i + 1,
            type: 'pitch',
            title: '¿El segundo sonido es agudo o grave?',
            instruction: 'Compara la altura de las dos notas.',
            instrument: station.instrument,
            rootMidi: 48,
            semitones: 12,
            direction,
            correct: direction === 'ascendente' ? 'Agudo' : 'Grave',
            options: ['Agudo', 'Grave'],
            explanation: direction === 'ascendente'
              ? 'La segunda nota tiene una frecuencia más alta: es aguda.'
              : 'La segunda nota tiene una frecuencia más baja: es grave.'
          });
        }
        return questions;
      }

      if (station.type === 'melody') {
        const melodies = station.melodies || [];
        for (let i = 0; i < count && melodies.length; i++) {
          const melody = melodies[i % melodies.length];
          const rootMidi = 60 + (i % 4);
          questions.push({
            id: i + 1,
            type: 'melody',
            title: '¿Qué melodía de tres notas escuchas?',
            instruction: 'Identifica el patrón melódico que se repite.',
            instrument: station.instrument,
            melodyNotes: melody.offsets.map(offset => rootMidi + offset),
            correct: melody.name,
            options: this._makeOptions(melody.name, melodies.map(item => item.name), melodies.length),
            explanation: `La respuesta es ${melody.name}: escucha el orden y la distancia entre sus tres notas.`
          });
        }
        return questions;
      }

      // ── SCALE QUESTIONS ─────────────────────────────────────────────────
      if (station.type === 'scale') {
        const targetScale = this.scales.find(
          s => s.name.toLowerCase() === (station.scale_name || '').toLowerCase()
        ) || this.scales[0];

        if (!targetScale) return questions;

        const allScaleNames = this.scales.map(s => s.name);

        for (let i = 0; i < count; i++) {
          const rootMidi = 55 + (i % 6);
          // Alternate between target scale and random scales for variety
          const chosenScale = (i % 2 === 0)
            ? targetScale
            : this.scales[Math.floor(Math.random() * this.scales.length)];

          const pattern = chosenScale.intervals_pattern
            ? chosenScale.intervals_pattern.split(',').map(Number)
            : [2, 2, 1, 2, 2, 2, 1];

          const options = this._makeOptions(chosenScale.name, allScaleNames, 4);

          questions.push({
            id: i + 1,
            type: 'scale',
            title: `Reconoce la Escala (${station.instrument})`,
            instruction: `Escucha la ejecución continua en ${station.station_name}.`,
            instrument: station.instrument === 'Todos' ? 'Tiple' : station.instrument,
            rootMidi: rootMidi,
            pattern: pattern,
            correct: chosenScale.name,
            options: options,
            explanation: chosenScale.description || `La escala ${chosenScale.name} le da el carácter folclórico a esta estación.`
          });
        }
        return questions;
      }

      // ── INTERVAL QUESTIONS (interval + final_boss) ──────────────────────
      const targetIntervalNames = (station.intervals && station.intervals.length)
        ? station.intervals
        : this.intervals.map(i => i.name);

      // For final boss, use ALL intervals
      const poolIntervalNames = station.type === 'final_boss'
        ? this.intervals.map(i => i.name)
        : targetIntervalNames;

      const allIntervalNames = this.intervals.map(i => i.name);

      // Mix station-specific and pool intervals for variety
      const questionIntervals = [];
      for (let i = 0; i < count; i++) {
        const fromStation = targetIntervalNames[i % targetIntervalNames.length];
        const fromPool = poolIntervalNames[Math.floor(Math.random() * poolIntervalNames.length)];
        questionIntervals.push(i % 3 === 0 ? fromPool : fromStation);
      }

      for (let i = 0; i < count; i++) {
        const intervalName = questionIntervals[i];
        const intervalObj = this.intervals.find(item => item.name === intervalName)
          || this.intervals[Math.floor(Math.random() * this.intervals.length)];

        if (!intervalObj) continue;

        const rootMidi = 55 + (i % 8);
        const allowedDirs = station.directions || ['ascendente'];
        const chosenDir = allowedDirs[Math.floor(Math.random() * allowedDirs.length)];

        // Generate 4 options: correct + 3 plausible distractors
        const options = this._makeOptions(intervalName, allIntervalNames, 4);

        questions.push({
          id: i + 1,
          type: 'interval',
          title: `¿Qué intervalo escuchas? (${station.instrument === 'Todos' ? 'Tiple' : station.instrument})`,
          instruction: `Identifica la distancia entre las notas tocadas en ${station.station_name}.`,
          instrument: station.instrument === 'Todos' ? 'Tiple' : station.instrument,
          rootMidi: rootMidi,
          semitones: intervalObj.semitones,
          direction: chosenDir,
          correct: intervalName,
          options: options,
          explanation: `El intervalo de ${intervalName} consta de ${intervalObj.semitones} semitonos.`
        });
      }

      return questions;
    },

    _makeOptions(correct, pool, count = 4) {
      const opts = [correct];
      const others = pool.filter(x => x !== correct).sort(() => 0.5 - Math.random());
      opts.push(...others.slice(0, count - 1));
      return opts.sort(() => 0.5 - Math.random());
    },

    // ══════════════════════════════════════════════════════════════════════
    // AUDIO PLAYBACK (uses real DB samples via stream_url, fallback synthesis)
    // ══════════════════════════════════════════════════════════════════════
    async playCurrentAudio() {
      if (!this.currentQ || this.isPlaying) return;
      this.isPlaying = true;
      this._updateMascot('listening', 'Escucha atentamente las cuerdas folclóricas...');

      const q = this.currentQ;
      if (q.type === 'scale') {
        await this.audio.playScale(
          q.instrument,
          q.rootMidi,
          q.pattern,
          1.0,
          (idx, midi, name) => {
            this.activeNotePlayingIndex = idx;
            this.activeNoteName = name || '';
          }
        );
      } else if (q.type === 'melody') {
        const duration = this.audio.scaleNoteDuration;
        for (let i = 0; i < q.melodyNotes.length; i++) {
          const midi = q.melodyNotes[i];
          this.activeNotePlayingIndex = i;
          this.activeNoteName = this.audio.midiToName(midi);
          await this.audio.playNote(q.instrument, midi, 0, duration, 0.95);
          await new Promise(resolve => setTimeout(resolve, (duration + this.audio.scaleNoteGap) * 1000));
        }
      } else if (q.type === 'interval' || q.type === 'pitch') {
        await this.audio.playInterval(
          q.instrument,
          q.rootMidi,
          q.semitones,
          q.type === 'pitch' ? q.direction : this.intervalDirection || q.direction || 'ascendente',
          (idx, midi, name) => {
            this.activeNotePlayingIndex = idx;
            this.activeNoteName = name || '';
          }
        );
      }
      this.isPlaying = false;
      this.activeNotePlayingIndex = -1;
    },

    replayAudio() {
      if (!this.isPlaying) {
        this.playCurrentAudio();
      }
    },

    changeDirection(dir) {
      this.intervalDirection = dir;
      if (!this.answered) {
        this.playCurrentAudio();
      }
    },

    // ══════════════════════════════════════════════════════════════════════
    // ANSWER SUBMISSION
    // ══════════════════════════════════════════════════════════════════════
    async selectOption(optionIndex) {
      if (this.answered || !this.currentQ) return;
      const option = this.currentQ.options[optionIndex];
      if (!option) return;

      this.answered = true;
      this.selectedOption = option;
      this.isCorrect = (option === this.currentQ.correct);
      this.totalQuestionsAnswered++;

      if (this.isCorrect) {
        this.sessionCorrect++;
        this.totalCorrectAnswered++;
        this.xp += 15;
        this.coins += 3;
        this.audio.playSuccessSound();
        this._updateMascot('celebrating', '¡Excelente oído! Respuesta correcta.');
        this._triggerConfetti();
      } else {
        this.sessionWrong++;
        this.lives = Math.max(0, this.lives - 1);
        this.audio.playLifeLostSound();
        this._updateMascot('sad', `La respuesta correcta era: ${this.currentQ.correct}. ¡Compara los sonidos!`);

        if (this.lives <= 0) {
          setTimeout(() => {
            this.openRescueModal();
          }, 1200);
        }
      }

      this._saveLocalState();
    },

    // ══════════════════════════════════════════════════════════════════════
    // AUDITORY COMPARISON (Chosen vs Correct)
    // ══════════════════════════════════════════════════════════════════════
    async playAudioComparison() {
      if (!this.currentQ || this.currentQ.type !== 'interval' || this.isComparingAudio) return;
      const chosenName = this.selectedOption;
      const correctName = this.currentQ.correct;

      const chosenObj = this.intervals.find(i => i.name === chosenName) || { semitones: 2 };
      const correctObj = this.intervals.find(i => i.name === correctName) || { semitones: 7 };

      this.isComparingAudio = true;
      this._updateMascot('listening', `1. Tu respuesta (${chosenName}) → 2. Respuesta correcta (${correctName})`);

      await this.audio.playComparison(
        this.currentQ.instrument,
        this.currentQ.rootMidi,
        chosenObj.semitones,
        correctObj.semitones,
        (phase) => {
          this.comparePhase = phase;
        }
      );

      this.isComparingAudio = false;
      this.comparePhase = 'idle';
    },

    // ══════════════════════════════════════════════════════════════════════
    // NEXT QUESTION OR COMPLETE STATION
    // ══════════════════════════════════════════════════════════════════════
    nextQuestion() {
      if (this.lives <= 0) {
        this.openRescueModal();
        return;
      }

      if (this.qIndex < this.levelQuestions.length - 1) {
        this.qIndex++;
        this.currentQ = this.levelQuestions[this.qIndex];
        this.answered = false;
        this.selectedOption = null;
        this.isCorrect = false;
        this.activeNotePlayingIndex = -1;
        this._updateMascot('idle', `Pregunta ${this.qIndex + 1} de ${this.levelQuestions.length}.`);
        this.$nextTick(() => {
          setTimeout(() => this.playCurrentAudio(), 300);
        });
      } else {
        this._completeStation();
      }
    },

    _completeStation() {
      const total = this.levelQuestions.length;
      const accuracy = Math.round((this.sessionCorrect / total) * 100);
      let stars = 1;
      if (accuracy >= 90) stars = 3;
      else if (accuracy >= 65) stars = 2;

      const stationId = this.activeStation.id;
      const previousStars = this.levelStars[stationId] || 0;
      if (stars > previousStars) {
        this.levelStars[stationId] = stars;
      }

      // Collectible reward on 3 stars
      if (stars === 3 && this.activeStation.reward_item) {
        if (!this.unlockedCollectibles.includes(this.activeStation.reward_item)) {
          this.unlockedCollectibles.push(this.activeStation.reward_item);
        }
      }

      // Unlock next station
      const nextStationId = stationId + 1;
      if (stars >= 1 && !this.unlockedLevels.includes(nextStationId) && nextStationId <= this.stations.length) {
        this.unlockedLevels.push(nextStationId);
      }

      const xpBonus = this.activeStation.xp_reward || 60;
      const coinBonus = this.activeStation.coins_reward || 12;
      this.xp += xpBonus;
      this.coins += coinBonus;

      this.audio.playLevelCompleteSound();
      this._triggerConfetti();

      this._syncWithServer({
        xp_earned: xpBonus + (this.sessionCorrect * 10),
        coins_earned: coinBonus + (this.sessionCorrect * 2),
        correct_count: this.sessionCorrect,
        total_count: total,
      });

      this._saveLocalState();
      this.currentTab = 'path';
      this._updateMascot(
        'celebrating',
        `¡Estación ${this.activeStation.station_name} completada con ${stars}★! Ganaste +${xpBonus} XP y +${coinBonus} Púas.`
      );
    },

    // ══════════════════════════════════════════════════════════════════════
    // RESCUE & MUSIC THEORY CHALLENGE
    // ══════════════════════════════════════════════════════════════════════
    openRescueModal() {
      this.rescueQuestions = [...this.theoryQuestions].sort(() => 0.5 - Math.random()).slice(0, 3);
      this.rescueIndex = 0;
      this.rescueAnswered = false;
      this.rescueSelected = null;
      this.showRescueModal = true;
      this._updateMascot('sad', '¡Te has quedado sin vidas! Responde estas preguntas teóricas para recuperarlas.');
    },

    selectRescueOption(optionIndex) {
      if (this.rescueAnswered) return;
      const q = this.rescueQuestions[this.rescueIndex];
      const option = q.options[optionIndex];
      if (!option) return;

      this.rescueAnswered = true;
      this.rescueSelected = option;
      this.rescueIsCorrect = (option === q.correct);

      if (this.rescueIsCorrect) {
        this.lives = Math.min(this.maxLives, this.lives + 2);
        this.xp += 20;
        this.coins += 5;
        this.audio.playLifeRestoredSound();
        this._updateMascot('celebrating', '¡Respuesta correcta! +2 Vidas recuperadas al instante.');
      } else {
        this.audio.playErrorSound();
        this._updateMascot('sad', `Incorrecto: ${q.explanation}`);
      }

      this._saveLocalState();
    },

    nextRescueQuestion() {
      if (this.rescueIndex < this.rescueQuestions.length - 1) {
        this.rescueIndex++;
        this.rescueAnswered = false;
        this.rescueSelected = null;
        this.rescueIsCorrect = false;
      } else {
        if (this.lives === 0) {
          this.lives = 2; // Mercy fallback
        }
        this.showRescueModal = false;
        this._saveLocalState();
        this._updateMascot('idle', `¡Vidas recuperadas (${this.lives}/${this.maxLives})! Continúa tu viaje por Vélez.`);
      }
    },

    // ══════════════════════════════════════════════════════════════════════
    // FREE JAM (MODO LIBRE)
    // ══════════════════════════════════════════════════════════════════════
    async playJamScale() {
      if (this.isPlaying) return;
      this.isPlaying = true;
      const scaleObj = this.scales[this.jamScaleIndex] || this.scales[0];
      const pattern = scaleObj.intervals_pattern
        ? scaleObj.intervals_pattern.split(',').map(Number)
        : [2, 2, 1, 2, 2, 2, 1];

      this._updateMascot('listening', `Reproduciendo ${scaleObj.name} en ${this.jamInstrument} (notas de 2 s con resonancia natural)...`);

      await this.audio.playScale(
        this.jamInstrument,
        Number(this.jamRootMidi),
        pattern,
        Number(this.jamTempo),
        (idx) => { this.jamActiveNoteIndex = idx; }
      );

      this.isPlaying = false;
      this.jamActiveNoteIndex = -1;
      this._updateMascot('idle', '¡Escala terminada! Prueba cambiar el instrumento o la velocidad.');
    },

    async playJamInterval() {
      if (this.isPlaying) return;
      this.isPlaying = true;
      const intervalObj = this.intervals.find(i => i.semitones === Number(this.jamIntervalSemitones))
        || this.intervals[1];

      this._updateMascot('listening', `Sonando ${intervalObj.name} (${this.jamDirection}) en ${this.jamInstrument}...`);

      await this.audio.playInterval(
        this.jamInstrument,
        Number(this.jamRootMidi),
        Number(this.jamIntervalSemitones),
        this.jamDirection,
        (idx) => { this.jamActiveNoteIndex = idx; }
      );

      this.isPlaying = false;
      this.jamActiveNoteIndex = -1;
      this._updateMascot('idle', `${intervalObj.name}: ${intervalObj.semitones} semitonos.`);
    },

    // ══════════════════════════════════════════════════════════════════════
    // SHOP & IN-GAME INVENTORY
    // ══════════════════════════════════════════════════════════════════════
    async buyItem(item) {
      if (this.unlockedItems.includes(item.id)) {
        await this.equipItem(item);
        return;
      }

      if (this.coins < item.cost_coins || this.xp < item.cost_xp) {
        this._updateMascot('sad', `Necesitas ${item.cost_xp} XP y ${item.cost_coins} Púas para desbloquear este artículo.`);
        return;
      }

      if (this.user.authenticated) {
        try {
          const response = await fetch('/api/senafonica/skins', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
            body: JSON.stringify({ action: 'purchase', item_id: item.id }),
          });
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'No se pudo comprar la skin.');
          this._applyServerSkinState(result);
        } catch (error) {
          this._updateMascot('sad', error.message || 'No se pudo comprar la skin.');
          return;
        }
      } else {
        this.coins -= item.cost_coins;
        this.unlockedItems.push(item.id);
        await this.equipItem(item);
      }
      this.audio.playLifeRestoredSound();
      this._triggerConfetti();
      this._saveLocalState();
      this._updateMascot('celebrating', `¡Desbloqueaste ${item.title}! Ya lo llevas equipado.`);
    },

    async equipItem(item) {
      if (item.type === 'skin' && this.user.authenticated) {
        try {
          const response = await fetch('/api/senafonica/skins', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
            body: JSON.stringify({ action: 'equip', item_id: item.id }),
          });
          const result = await response.json();
          if (!response.ok) throw new Error(result.error || 'No se pudo equipar la skin.');
          this._applyServerSkinState(result);
        } catch (error) {
          this._updateMascot('sad', error.message || 'No se pudo equipar la skin.');
        }
        return;
      }
      if (item.type === 'skin') {
        this.equippedSkin = item.id;
      } else if (item.type === 'accessory') {
        if (item.slot === 'hat') this.equippedAccessories.hat = item.id;
        else if (item.slot === 'body') this.equippedAccessories.body = item.id;
        else if (item.slot === 'eyes') this.equippedAccessories.eyes = item.id;
      }
      this._saveLocalState();
    },

    _applyServerSkinState(data) {
      this.xp = data.total_xp;
      this.coins = data.coins;
      this.equippedSkin = data.equipped_skin;
      const accessories = this.unlockedItems.filter(
        id => !this.shopItems.some(item => item.id === id && item.type === 'skin')
      );
      this.unlockedItems = [...new Set([...accessories, ...data.unlocked_skins])];
      this._saveLocalState();
    },

    changeBackground(imageUrl, themeColor) {
      const nextColor = themeColor || '#0B111A';
      if (!imageUrl || (imageUrl === this.backgroundImage && nextColor === this.backgroundColor)) return;
      this.backgroundVisible = false;
      clearTimeout(this.backgroundTimer);
      this.backgroundTimer = setTimeout(() => {
        this.backgroundImage = imageUrl;
        this.backgroundColor = nextColor;
        this.$nextTick(() => {
          requestAnimationFrame(() => { this.backgroundVisible = true; });
        });
      }, 250);
    },

    // ══════════════════════════════════════════════════════════════════════
    // CONFETTI & PARTICLES
    // ══════════════════════════════════════════════════════════════════════
    _triggerConfetti() {
      const canvas = document.getElementById('senafonica-confetti');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      const particles = [];
      const colors = ['#39A900', '#FBBF24', '#3B82F6', '#EC4899', '#10B981', '#FFFFFF'];

      for (let i = 0; i < 80; i++) {
        particles.push({
          x: canvas.width / 2,
          y: canvas.height * 0.35,
          vx: (Math.random() - 0.5) * 18,
          vy: (Math.random() - 1.0) * 14,
          size: Math.random() * 7 + 4,
          color: colors[Math.floor(Math.random() * colors.length)],
          rotation: Math.random() * 360,
          vrot: (Math.random() - 0.5) * 8,
          alpha: 1.0,
        });
      }

      let frame = 0;
      const render = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        frame++;
        let alive = false;
        particles.forEach(p => {
          p.x += p.vx;
          p.y += p.vy;
          p.vy += 0.38;
          p.rotation += p.vrot;
          p.alpha -= 0.015;

          if (p.alpha > 0) {
            alive = true;
            ctx.save();
            ctx.globalAlpha = Math.max(0, p.alpha);
            ctx.translate(p.x, p.y);
            ctx.rotate((p.rotation * Math.PI) / 180);
            ctx.fillStyle = p.color;
            ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 1.5);
            ctx.restore();
          }
        });

        if (alive && frame < 90) {
          requestAnimationFrame(render);
        } else {
          ctx.clearRect(0, 0, canvas.width, canvas.height);
        }
      };
      render();
    },

    // ══════════════════════════════════════════════════════════════════════
    // BACKEND SERVER SYNC
    // ══════════════════════════════════════════════════════════════════════
    async _syncWithServer(payload) {
      if (!this.csrfToken) return;
      try {
        const res = await fetch('/api/senafonica/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
          body: JSON.stringify(payload),
        });
        if (res.ok) {
          const serverData = await res.json();
          if (serverData.total_xp !== undefined) this.xp = serverData.total_xp;
          if (serverData.coins !== undefined) this.coins = serverData.coins;
          if (serverData.streak !== undefined) this.streak = serverData.streak;
        }
      } catch (err) {
        console.warn('Server sync failed, local state preserved:', err);
      }
    },

    // ══════════════════════════════════════════════════════════════════════
    // STATS HELPERS
    // ══════════════════════════════════════════════════════════════════════
    getAccuracy() {
      if (!this.totalQuestionsAnswered) return 0;
      return Math.round((this.totalCorrectAnswered / this.totalQuestionsAnswered) * 100);
    },

    getTotalStars() {
      return Object.values(this.levelStars).reduce((acc, val) => acc + val, 0);
    }
  };
}

window.senafonicaGame = senafonicaGame;
