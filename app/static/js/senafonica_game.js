/**
 * Senafónico Game Engine — Videojuego Web Autónomo e Integrado
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
  const initialLevels = data.levels || [];
  const hasModuleLevels = initialLevels.some(item =>
    item && (item.id === 0 || Array.isArray(item.levels))
  );

  return {
    // ── DATA & CONFIG ──────────────────────────────────────────────────────
    user: data.user || { name: 'Aprendiz Veleño', xp: 0, coins: 0, level: 1, streak: 1 },
    catalog: data.catalog || {},
    intervals: data.intervals || [],
    scales: data.scales || [],
    levels: data.modules || (hasModuleLevels ? initialLevels : []),
    progression: data.progression || { passingPercent: 80, challengeQuestions: 10, studyCompletePct: 100 },
    stations: data.stations || (hasModuleLevels ? [] : initialLevels),
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
    tvMode: new URLSearchParams(window.location.search).get('tv') === '1',
    selectedInstrument: 'Tiple',
    instrumentAccent: '#D99A45',
    instrumentAccents: { Tiple: '#D99A45', Requinto: '#3AA6A0', Bandola: '#B889D6', Guitarra: '#60A5FA' },
    backgroundImage: '',
    backgroundColor: '#0B111A',
    backgroundVisible: false,
    backgroundTimer: null,
    showStationModal: false,
    selectedStation: null,
    showLevelIntro: false,
    introModule: null,
    introLevel: null,
    introIntervals: [],
    introRootMidi: null,
    introPlaying: false,
    introDemoPlayed: false,
    showStatsModal: false,
    showShopModal: false,
    showRescueModal: false,
    replayCount: 0,
    replayLimit: 2,
    timeTrialSeconds: 30,
    timeTrialTimer: null,
    timeTrialScore: 0,
    timeTrialAttempted: 0,
    timeTrialFinished: false,
    dailyQuestions: [],
    dailyScore: 0,
    dailyAnswers: [],
    dailyFinished: false,
    dailyLoading: false,
    dailyMessage: '',
    dailyDate: '',
    dailyStreak: 0,
    tonicScales: [],
    tonicChallengeOptions: [],
    tonicChallengeMessage: '',
    tonicChallengeAttempts: 0,
    tonicChallengeIdentified: false,
    bandolaCorrectStreak: 0,
    achievementSyncPending: false,

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
    moduleProgress: {},
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
    mascotSpeech: '¡Bienvenido a Senafónico! Recorreremos la hermosa Provincia de Vélez.',
    mascotImg: '/static/img/ninos_traje.png',

    // ── AUDIO ENGINE ──────────────────────────────────────────────────────
    audio: null,
    isPlaying: false,

    // ══════════════════════════════════════════════════════════════════════
    // INITIALIZATION
    // ══════════════════════════════════════════════════════════════════════
    init() {
      this.audio = new SenafonicaAudioEngine(this.catalog);
      this.selectedInstrument = ['Tiple', 'Requinto', 'Bandola', 'Guitarra'].includes(this.user.selected_instrument)
        ? this.user.selected_instrument
        : 'Tiple';
      this.instrumentAccent = this.instrumentAccents[this.selectedInstrument];
      this.tonicScales = Array.isArray(this.user.tonic_scales) ? this.user.tonic_scales : [];
      this.dailyStreak = this.user.daily_streak || 0;
      this.bandolaCorrectStreak = this.user.bandola_correct_streak || 0;
      this.prepareTonicChallenge();

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
          const localProgress = parsed.moduleProgress || {};
          const serverProgress = this.user.module_progress || {};
          this.moduleProgress = Object.fromEntries(
            [...new Set([...Object.keys(localProgress), ...Object.keys(serverProgress)])]
              .map(key => [key, Math.max(Number(localProgress[key]) || 0, Number(serverProgress[key]) || 0)])
          );
          this.totalQuestionsAnswered = parsed.totalQuestionsAnswered || 0;
          this.totalCorrectAnswered = parsed.totalCorrectAnswered || 0;
          this.unlockedCollectibles = parsed.unlockedCollectibles || [];
          this.equippedSkin = parsed.equippedSkin || 'skin_tiple_noble';
          this.equippedAccessories = parsed.equippedAccessories || { hat: '', body: '', eyes: '' };
          this.tonicScales = this.user.authenticated
            ? (this.user.tonic_scales || [])
            : (parsed.tonicScales || []);
          this.bandolaCorrectStreak = this.user.authenticated
            ? (this.user.bandola_correct_streak || 0)
            : (parsed.bandolaCorrectStreak || 0);
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
      this.moduleProgress = this.user.module_progress || {};
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
        moduleProgress: this.moduleProgress,
        totalQuestionsAnswered: this.totalQuestionsAnswered,
        totalCorrectAnswered: this.totalCorrectAnswered,
        unlockedCollectibles: this.unlockedCollectibles,
        equippedSkin: this.equippedSkin,
        equippedAccessories: this.equippedAccessories,
        unlockedItems: this.unlockedItems,
        tonicScales: this.tonicScales,
        bandolaCorrectStreak: this.bandolaCorrectStreak,
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
      if (this.$refs.learnScore && typeof SemimusScore !== 'undefined') {
        SemimusScore.render(this.$refs.learnScore, null);
      }
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
      // Módulo de exploración: al tocar una nota se renderiza en el
      // pentagrama con su nomenclatura (especificación de partituras).
      this._renderLearnScore(inst, [midi]);
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
      if (station.moduleId !== undefined
        ? !this.isModuleLevelUnlocked(station.moduleId, station.moduleLevel)
        : !this.unlockedLevels.includes(station.id)) {
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
      this.levelQuestions = station.moduleId !== undefined
        ? this._generateQuestionsForModule(station.moduleId, station.moduleLevel)
        : this._generateQuestionsForStation(station);
      if (!this.levelQuestions.length) {
        this._updateMascot('sad', `No hay muestras de audio disponibles para ${station.station_name}. No se generaron notas sintéticas.`);
        return;
      }
      this.levelQuestions.forEach((question, index) => {
        if (station.moduleId === undefined && station.id === 3) {
          question.instrument = index % 2 === 0 ? 'Tiple' : 'Requinto';
        } else if (station.moduleId === undefined && question.type !== 'pitch') {
          question.instrument = this.selectedInstrument;
        }
      });
      this._preloadQuestionAudio(this.levelQuestions);
      this.currentQ = this.levelQuestions[0];
      this.answered = false;
      this.replayCount = 0;
      this.selectedOption = null;
      this.currentTab = 'training';

      this._updateMascot('listening', `¡Llegamos a ${station.station_name}! Escucha con atención.`);

      this.$nextTick(() => {
        setTimeout(() => this.playCurrentAudio(), 400);
      });
    },

    isModuleUnlocked(moduleId) {
      return SemimusModules.isModuleUnlocked(this.levels, this.moduleProgress, moduleId, this.passingPercent());
    },

    isModuleLevelUnlocked(moduleId, levelNumber) {
      return SemimusModules.isLevelUnlocked(this.levels, this.moduleProgress, moduleId, levelNumber, this.passingPercent());
    },

    isModuleCompleted(moduleId) {
      return SemimusModules.isModuleCompleted(this.moduleProgress, moduleId, this.passingPercent());
    },

    isModuleLevelCompleted(moduleId, levelConfig) {
      return SemimusModules.isLevelCompleted(this.moduleProgress, moduleId, levelConfig.level, this.passingPercent());
    },

    passingPercent() {
      return Number(this.progression?.passingPercent ?? 80);
    },

    challengeCount() {
      return Number(this.progression?.challengeQuestions ?? 10);
    },

    introPhaseLabel() {
      return this.introLevel === SemimusModules.STUDY_LEVEL
        ? 'Fase .1 · Estudio aislado'
        : 'Fase .2 · Reto acumulado';
    },

    moduleGroupLabel(module) {
      const labels = {
        pitch: 'Alturas',
        simple: 'Intervalos simples',
        compound: 'Intervalos compuestos',
        scale: 'Escalas y modos',
      };
      return labels[module.group] || 'Módulo';
    },

    moduleDistance(module) {
      if (module.type === 'scale') return module.scale ? module.scale.formula : '';
      if (module.type === 'pitch') return 'Sonido grave y agudo';
      return `Distancia: ${SemimusModules.distanceLabel(module.semitones)}`;
    },

    introDescription() {
      const module = this.introModule;
      if (!module) return '';
      if (this.introLevel === SemimusModules.STUDY_LEVEL) return module.description || '';
      return `Reto acumulado: ${module.levels[1].prompt}.`;
    },

    introDistanceText() {
      const module = this.introModule;
      if (!module || module.type !== 'interval') return '';
      return `Distancia: ${SemimusModules.distanceLabel(module.semitones)}`;
    },

    startModuleLevel(moduleId, levelNumber = SemimusModules.STUDY_LEVEL) {
      const module = this.levels.find(item => item.id === moduleId);
      if (!module) {
        this._updateMascot('sad', 'No se encontró la configuración del módulo.');
        return;
      }
      if (!this.isModuleLevelUnlocked(moduleId, levelNumber)) {
        this._updateMascot('idle', levelNumber === SemimusModules.CHALLENGE_LEVEL
          ? 'Termina primero el estudio (Fase .1) para abrir el reto.'
          : 'Supera el reto del módulo anterior para abrir este.');
        return;
      }
      this.introModule = module;
      this.introLevel = levelNumber;
      this.introDemoPlayed = false;
      this.introRootMidi = this._introRoot(module);
      this.showLevelIntro = true;
      this.$nextTick(() => this._clearIntroScore());
    },

    _introRoot(module) {
      if (module.type === 'scale') {
        return this._scaleRoots(this.selectedInstrument, module.scale.steps)[0] ?? null;
      }
      const semitones = module.type === 'pitch' ? 12 : module.semitones;
      return this._validRootMidis(this.selectedInstrument, semitones)[0] ?? null;
    },

    _scaleRoots(instrument, steps) {
      return this._validRootMidis(instrument, 12)
        .filter(root => SemimusModules.spellScale(root, steps) !== null);
    },

    _clearIntroScore() {
      const container = this.$refs.introScore;
      if (container && typeof SemimusScore !== 'undefined') SemimusScore.render(container, null);
    },

    _renderIntroScore() {
      const container = this.$refs.introScore;
      const module = this.introModule;
      if (!container || !module || typeof SemimusScore === 'undefined' || this.introRootMidi === null) return;
      if (module.type === 'scale') {
        const notes = SemimusModules.spellScale(this.introRootMidi, module.scale.steps, module.scale.focus) || [];
        SemimusScore.render(container, {
          instrument: this.selectedInstrument,
          interval_type: 'escala',
          notation_display: { clef: 'treble', notes },
        });
        return;
      }
      const semitones = module.type === 'pitch' ? 12 : module.semitones;
      SemimusScore.renderNotes(
        container,
        this.selectedInstrument,
        [this.introRootMidi, this.introRootMidi + semitones],
        `${module.id}_demo`
      );
    },

    async playLevelIntroExample() {
      if (this.introPlaying || !this.introModule) return;
      const module = this.introModule;
      const rootMidi = this.introRootMidi;
      if (rootMidi === null) {
        console.warn('No real sample root is available for this introduction.');
        return;
      }
      this.introPlaying = true;
      try {
        if (module.type === 'scale') {
          await this.audio.playScale(this.selectedInstrument, rootMidi, module.scale.steps, 1.2);
        } else {
          await this.audio.playInterval(
            this.selectedInstrument,
            rootMidi,
            module.type === 'pitch' ? 12 : module.semitones,
            'ascendente'
          );
        }
        this.introDemoPlayed = true;
        if (this.introLevel === SemimusModules.STUDY_LEVEL) this._renderIntroScore();
      } catch (error) {
        console.warn('Could not play level introduction example:', error);
      } finally {
        this.introPlaying = false;
      }
    },

    completeModuleStudy() {
      if (!this.introModule || !this.introDemoPlayed) return;
      const id = this.introModule.id;
      this.moduleProgress[SemimusModules.progressKey(id, SemimusModules.STUDY_LEVEL)] = this.progression?.studyCompletePct ?? 100;
      this._saveLocalState();
      void this._syncWithServer({ module_progress: this.moduleProgress });
      this.showLevelIntro = false;
      this._clearIntroScore();
      this._updateMascot('celebrating', `¡Fase .1 de ${this.introModule.name} completada! Ya puedes abrir el reto.`);
    },

    continueLevelIntro() {
      if (!this.introModule || !this.introDemoPlayed) return;
      const module = this.introModule;
      this.showLevelIntro = false;
      this.startStation({
        id: module.id,
        moduleId: module.id,
        moduleLevel: SemimusModules.CHALLENGE_LEVEL,
        moduleLevelConfig: { level: SemimusModules.CHALLENGE_LEVEL, minCorrectPct: this.passingPercent() },
        station_name: `Módulo ${module.id} · Reto`,
        instrument: this.selectedInstrument,
        type: module.type,
        intervals: [],
        questions_count: this.challengeCount(),
      });
    },

    _validRootMidis(instrument, semitones) {
      // Rangos acústicos por instrumento (especificación técnica de
      // partituras): el generador no debe producir notas fuera de ellos.
      // Requinto: Do 4 (60) → Mi 6 (88); Tiple: Do 3 (48) → Mi 5 (76);
      // Bandola: Fa# 3 (54) → Sol 6 (91); Guitarra: Mi 2 (40) → Mi 5 (76).
      const acousticRanges = {
        Requinto: [60, 88],
        Tiple: [48, 76],
        Bandola: [54, 91],
        Guitarra: [40, 76],
      };
      const range = acousticRanges[instrument];
      if (!range) return [];
      const notes = new Set((this.catalog[instrument] || [])
        .map(sample => Number(sample.midi))
        .filter(Number.isInteger));
      return [...notes]
        .filter(midi => midi >= range[0] && midi + semitones <= range[1] && notes.has(midi + semitones))
        .sort((a, b) => a - b);
    },

    _generateQuestionsForModule(moduleId, levelNumber) {
      // La Fase .1 es de estudio: no tiene preguntas.
      if (levelNumber !== SemimusModules.CHALLENGE_LEVEL) return [];
      const module = this.levels.find(item => item.id === moduleId);
      if (!module) return [];
      const instrument = this.selectedInstrument;
      const count = this.challengeCount();
      const pick = list => list[Math.floor(Math.random() * list.length)];

      if (module.type === 'pitch') {
        const roots = this._validRootMidis(instrument, 12);
        if (!roots.length) return [];
        const questions = [];
        for (let i = 0; i < count; i++) {
          const ascending = Math.random() < 0.5;
          questions.push({
            id: i + 1,
            type: 'pitch',
            title: '¿Cuál nota fue más grave/aguda?',
            instruction: 'Compara la altura de las dos notas.',
            instrument,
            rootMidi: pick(roots),
            semitones: 12,
            direction: ascending ? 'ascendente' : 'descendente',
            correct: ascending ? 'Agudo' : 'Grave',
            options: ['Agudo', 'Grave'],
            explanation: ascending
              ? 'La segunda nota tiene una frecuencia más alta: es aguda.'
              : 'La segunda nota tiene una frecuencia más baja: es grave.',
          });
        }
        return questions;
      }

      const byId = id => this.levels.find(item => item.id === id);
      const pool = SemimusModules.challengePool(this.levels, moduleId);
      const rootsOf = item => (item.type === 'scale'
        ? this._scaleRoots(instrument, item.scale.steps)
        : this._validRootMidis(instrument, item.semitones));
      const targets = pool.filter(id => byId(id) && rootsOf(byId(id)).length);
      if (!targets.length) return [];

      const questions = [];
      for (let i = 0; i < count; i++) {
        const targetId = pick(targets);
        const item = byId(targetId);
        const optionNames = SemimusModules.challengeOptions(pool, targetId)
          .map(id => byId(id).name);
        if (item.type === 'scale') {
          questions.push({
            id: i + 1,
            type: 'scale',
            title: '¿Qué escala escuchas?',
            instruction: `Reto del módulo ${module.id}: identifica la escala.`,
            instrument,
            rootMidi: pick(rootsOf(item)),
            pattern: item.scale.steps,
            focus: item.scale.focus,
            scale_name: item.name,
            correct: item.name,
            options: optionNames,
            explanation: `${item.name}: ${item.scale.formula}. En trastes: ${item.scale.steps.join(', ')}. ${item.scale.focusText}`,
          });
        } else {
          questions.push({
            id: i + 1,
            type: 'interval',
            title: `¿Qué intervalo escuchas? (${instrument})`,
            instruction: `Reto del módulo ${module.id}: identifica la distancia entre las dos notas.`,
            instrument,
            rootMidi: pick(rootsOf(item)),
            semitones: item.semitones,
            intervalId: item.intervalId || null,
            direction: 'ascendente',
            correct: item.name,
            options: optionNames,
            explanation: item.structure
              ? `${item.name}: ${item.structure}. Distancia: ${SemimusModules.distanceLabel(item.semitones)}.`
              : `${item.name}: ${SemimusModules.distanceLabel(item.semitones)}.`,
          });
        }
      }
      return questions;
    },

    _preloadQuestionAudio(questions) {
      const notesByInstrument = new Map();
      questions.forEach(question => {
        const questionNotes = question.type === 'melody'
          ? question.melodyNotes
          : question.type === 'scale'
            ? (() => {
              const scaleNotes = [question.rootMidi];
              question.pattern.reduce((midi, semitones) => {
                const nextMidi = midi + semitones;
                scaleNotes.push(nextMidi);
                return nextMidi;
              }, question.rootMidi);
              return scaleNotes;
            })()
            : [question.rootMidi, question.rootMidi + question.semitones];
        const group = notesByInstrument.get(question.instrument) || [];
        group.push(...questionNotes);
        notesByInstrument.set(question.instrument, group);
      });
      for (const [instrument, instrumentNotes] of notesByInstrument) {
        void this.audio.preloadNotes(instrument, [...new Set(instrumentNotes)]);
      }
    },

    _generateQuestionsForStation(station) {
      const questions = [];
      const count = station.questions_count || 5;

      if (station.type === 'pitch') {
        const instrument = this.selectedInstrument;
        const roots = this._validRootMidis(instrument, 12);
        for (let i = 0; i < Math.min(count, roots.length); i++) {
          const direction = i % 2 === 0 ? 'ascendente' : 'descendente';
          questions.push({
            id: i + 1,
            type: 'pitch',
            title: '¿El segundo sonido es agudo o grave?',
            instruction: 'Compara la altura de las dos notas.',
            instrument,
            rootMidi: roots[i],
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

      for (let i = 0; i < count; i++) {
        const instrument = station.id === 3
          ? (i % 2 === 0 ? 'Tiple' : 'Requinto')
          : this.selectedInstrument;
        const eligible = poolIntervalNames
          .map(name => this.intervals.find(item => item.name === name))
          .filter(interval => interval && this._validRootMidis(instrument, interval.semitones).length);
        if (!eligible.length) continue;
        const intervalObj = eligible[Math.floor(Math.random() * eligible.length)];
        const intervalName = intervalObj.name;
        const roots = this._validRootMidis(instrument, intervalObj.semitones);
        const rootMidi = roots[Math.floor(Math.random() * roots.length)];
        const allowedDirs = station.directions || ['ascendente'];
        const chosenDir = allowedDirs[Math.floor(Math.random() * allowedDirs.length)];

        // Generate 4 options: correct + 3 plausible distractors
        const beginnerStage = station.id <= 2;
        const optionPool = beginnerStage ? targetIntervalNames : allIntervalNames;
        const options = this._makeOptions(intervalName, optionPool, beginnerStage ? 2 : 4);

        questions.push({
          id: i + 1,
          type: 'interval',
          title: `¿Qué intervalo escuchas? (${station.instrument === 'Todos' ? 'Tiple' : station.instrument})`,
          instruction: `Identifica la distancia entre las notas tocadas en ${station.station_name}.`,
          instrument,
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
      try {
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
      } catch (error) {
        console.warn('Could not play question audio:', error);
      } finally {
        this.isPlaying = false;
        this.activeNotePlayingIndex = -1;
      }
    },

    replayAudio() {
      if (this.isPlaying || this.answered || this.replayCount >= this.replayLimit) return;
      this.replayCount++;
      this.playCurrentAudio();
    },

    changeDirection(dir) {
      this.intervalDirection = dir;
      if (!this.answered) {
        this.replayAudio();
      }
    },

    async selectInstrument(instrument) {
      if (!['Tiple', 'Requinto', 'Bandola', 'Guitarra'].includes(instrument) || this.isPlaying) return;
      if (this.currentQ && this.currentTab === 'training') {
        this._updateMascot('idle', 'Termina esta pregunta antes de cambiar de instrumento.');
        return;
      }
      this.selectedInstrument = instrument;
      this.instrumentAccent = this.instrumentAccents[instrument];
      this.jamInstrument = instrument;
      const chord = [60, 64, 67, 72];
      this.isPlaying = true;
      try {
        await Promise.all(chord.map(midi => this.audio.playNote(instrument, midi, 0, 0.8, 0.55)));
      } catch (error) {
        console.error('Could not play instrument chord:', error);
        this._updateMascot('sad', 'No se pudo reproducir el acorde. Inténtalo de nuevo.');
      } finally {
        this.isPlaying = false;
      }
      if (this.currentQ && !this.answered && this.currentTab === 'training') {
        this.levelQuestions.forEach((question, index) => {
          question.instrument = this.activeStation && this.activeStation.id === 3
            ? (index % 2 === 0 ? 'Tiple' : 'Requinto')
            : instrument;
        });
        this.currentQ.instrument = this.levelQuestions[this.qIndex].instrument;
        this._preloadQuestionAudio(this.levelQuestions.slice(this.qIndex));
      }
    },

    // ══════════════════════════════════════════════════════════════════════
    // ANSWER SUBMISSION
    // ══════════════════════════════════════════════════════════════════════
    async selectOption(optionIndex) {
      if (this.answered || this.isPlaying || !this.currentQ) return;
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
        if (!['time-trial', 'daily'].includes(this.currentTab)) {
          this.sessionWrong++;
          this.lives = Math.max(0, this.lives - 1);
          this.audio.playLifeLostSound();
          if (this.lives <= 0) {
            setTimeout(() => this.openRescueModal(), 1200);
          }
        } else {
          this.audio.playErrorSound();
        }
        this._updateMascot('sad', `La respuesta correcta era: ${this.currentQ.correct}. ¡Compara los sonidos!`);
      }

      if (this.currentTab === 'time-trial' && this.isCorrect) this.timeTrialScore++;
      if (this.currentTab === 'time-trial') this.timeTrialAttempted++;
      if (this.currentTab === 'daily' && this.isCorrect) this.dailyScore++;
      if (this.currentTab === 'daily') {
        this.dailyAnswers.push({ id: this.currentQ.id, answer: option });
      }
      // Módulo evaluativo: compás con la tónica origen y el intervalo
      // alcanzado (especificación de partituras).
      this._renderAnswerScore();
      if (this.currentTab === 'training' || this.currentTab === 'time-trial' || this.currentTab === 'daily') {
        this.achievementSyncPending = true;
        try {
          await this._recordAchievement(this.currentQ.instrument, this.isCorrect);
        } finally {
          this.achievementSyncPending = false;
        }
      }
      this._saveLocalState();
    },

    // ══════════════════════════════════════════════════════════════════════
    // AUDITORY COMPARISON (Chosen vs Correct)
    // ══════════════════════════════════════════════════════════════════════
    async playAudioComparison() {
      if (!this.currentQ || this.isComparingAudio || this.isPlaying) return;
      const chosenName = this.selectedOption;
      const correctName = this.currentQ.correct;

      this.isComparingAudio = true;
      this.isPlaying = true;
      this._updateMascot('listening', `1. Tu respuesta (${chosenName}) → 2. Respuesta correcta (${correctName})`);
      try {
        this.comparePhase = 'chosen';
        await this._playQuestionVariant(this.currentQ, chosenName);
        await new Promise(resolve => setTimeout(resolve, 350));
        this.comparePhase = 'correct';
        await this._playQuestionVariant(this.currentQ, correctName);
      } catch (error) {
        console.error('Could not compare answer audio:', error);
      } finally {
        this.isPlaying = false;
        this.isComparingAudio = false;
        this.comparePhase = 'idle';
      }
    },

    async _playQuestionVariant(question, answer) {
      if (question.type === 'scale') {
        const scale = this.scales.find(item => item.name === answer);
        if (!scale) return;
        const pattern = (scale.intervals_pattern || '2,2,1,2,2,2,1').split(',').map(Number);
        await this.audio.playScale(question.instrument, question.rootMidi, pattern, 1.0);
        return;
      }
      if (question.type === 'melody') {
        const melody = (this.activeStation.melodies || []).find(item => item.name === answer);
        const notes = answer === question.correct
          ? question.melodyNotes
          : melody
            ? melody.offsets.map(offset => question.melodyNotes[0] - melody.offsets[0] + offset)
            : question.melodyNotes;
        for (const midi of notes) {
          await this.audio.playNote(question.instrument, midi, 0, this.audio.scaleNoteDuration, 0.95);
          await new Promise(resolve => setTimeout(resolve, (this.audio.scaleNoteDuration + this.audio.scaleNoteGap) * 1000));
        }
        return;
      }
      const interval = this.intervals.find(item => item.name === answer);
      const semitones = interval ? interval.semitones : question.semitones;
      const direction = question.type === 'pitch'
        ? (answer === 'Agudo' ? 'ascendente' : 'descendente')
        : question.direction || this.intervalDirection;
      await this.audio.playInterval(
        question.instrument,
        question.rootMidi,
        semitones,
        direction,
        null,
        false
      );
    },

    // ══════════════════════════════════════════════════════════════════════
    // NEXT QUESTION OR COMPLETE STATION
    // ══════════════════════════════════════════════════════════════════════
    nextQuestion() {
      if (this.achievementSyncPending) return;
      if (this.currentTab === 'time-trial') {
        if (this.timeTrialFinished || this.timeTrialSeconds <= 0) return;
        this.qIndex = (this.qIndex + 1) % this.levelQuestions.length;
        this.currentQ = this.levelQuestions[this.qIndex];
        this._resetQuestionAttempt();
        this.$nextTick(() => setTimeout(() => this.playCurrentAudio(), 150));
        return;
      }
      if (this.currentTab === 'daily') {
        if (this.qIndex < this.dailyQuestions.length - 1) {
          this.qIndex++;
          this.currentQ = this.dailyQuestions[this.qIndex];
          this._resetQuestionAttempt();
          this.$nextTick(() => setTimeout(() => this.playCurrentAudio(), 150));
        } else {
          void this.finishDailyChallenge();
        }
        return;
      }
      if (this.lives <= 0) {
        this.openRescueModal();
        return;
      }

      if (this.qIndex < this.levelQuestions.length - 1) {
        this.qIndex++;
        this.currentQ = this.levelQuestions[this.qIndex];
        this.answered = false;
        this.replayCount = 0;
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

    _resetQuestionAttempt() {
      this.answered = false;
      this.selectedOption = null;
      this.isCorrect = false;
      this.replayCount = 0;
      this.activeNotePlayingIndex = -1;
      if (this.$refs.answerScore && typeof SemimusScore !== 'undefined') {
        SemimusScore.render(this.$refs.answerScore, null);
      }
    },

    getOptionSymbol(option, question = this.currentQ) {
      if (!question) return '♪';
      if (question.type === 'pitch') return option === 'Agudo' ? '↑' : '↓';
      if (question.type === 'scale') {
        const name = option.toLowerCase();
        if (name.includes('mayor')) return '☀️';
        if (name.includes('menor armónica') || name.includes('menor armonica')) return '🌙';
        if (name.includes('pentatónica') || name.includes('pentatonica')) return '🌾';
        if (name.includes('menor')) return '🌧️';
        return '🎼';
      }
      if (question.type === 'melody') return ['♪', '♫', '♬', '𝄞'][question.options.indexOf(option) % 4];
      const module = this.levels.find(item => item.name === option);
      if (module) {
        if (module.semitones === 0) return '≡';
        if (module.semitones <= 2) return '↗';
        if (module.semitones <= 4) return '↗↗';
        if (module.semitones <= 7) return '⤴';
        return '⤴⤴';
      }
      const interval = this.intervals.find(item => item.name === option);
      if (!interval) return '♪';
      if (interval.semitones === 0) return '≡';
      if (interval.semitones <= 2) return '↗';
      if (interval.semitones <= 4) return '↗↗';
      if (interval.semitones <= 7) return '⤴';
      return '⤴⤴';
    },

    getOptionHint(option, question = this.currentQ) {
      if (!question) return '';
      if (question.type === 'pitch') return option === 'Agudo' ? 'Sube el sonido' : 'Baja el sonido';
      if (question.type === 'scale') {
        const scale = this.scales.find(item => item.name === option);
        return scale ? scale.description || 'Escucha el carácter de la escala' : 'Escucha su carácter';
      }
      if (question.type === 'melody') return 'Reconoce el orden de las notas';
      const module = this.levels.find(item => item.name === option);
      if (module) {
        if (module.semitones === 0) return 'Misma nota';
        if (module.semitones <= 2) return 'Paso corto';
        if (module.semitones <= 4) return 'Paso mediano';
        if (module.semitones <= 7) return 'Salto amplio';
        return 'Salto grande';
      }
      const interval = this.intervals.find(item => item.name === option);
      if (!interval) return 'Escucha la distancia';
      if (interval.semitones === 0) return 'Misma nota';
      if (interval.semitones <= 2) return 'Paso corto';
      if (interval.semitones <= 4) return 'Paso mediano';
      if (interval.semitones <= 7) return 'Salto amplio';
      return 'Salto grande';
    },

    getAnswerFeedback() {
      const question = this.currentQ;
      if (!question) return '';
      if (question.type === 'scale') {
        return question.explanation || 'Escucha el patrón de la escala.';
      }
      if (question.type !== 'interval') return question.explanation;
      const interval = this.intervals.find(item =>
        item.id === question.intervalId
        || (item.semitones === question.semitones && item.name === question.correct)
      ) || this.intervals.find(item => item.semitones === question.semitones);
      if (!interval) return question.explanation;
      const module = this.levels.find(item => item.name === question.correct);
      const intervalName = (question.correct || interval.name)
        .split(' ')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
      const article = interval.id === 'U' || interval.id === '4A' ? 'un' : 'una';
      const opening = this.isCorrect
        ? `¡Excelente! Identificaste ${article} ${intervalName}.`
        : `No pasa nada. La respuesta correcta es ${intervalName}.`;
      const neutralInstrumentNote = ['4A', '6m', '6M', '7m', '7M', '8J'].includes(interval.id)
        ? 'Este salto se toca cambiando de cuerda o de posición; consúltalo con tu profesor.'
        : '';
      const tonos = module?.distance?.tonos || interval.tonos;
      const trastes = module?.distance?.trastes ?? interval.trastes;
      let fretText;
      if (Number(trastes) === 0) {
        fretText = 'Trastes: 0. Es la misma nota repetida: no te mueves por el mástil.';
      } else {
        fretText = interval.texto_instrumento
          || `Trastes: ${trastes}. ${neutralInstrumentNote
            || `En tu ${question.instrument.toLowerCase()}: avanzar ${trastes} ${trastes === 1 ? 'traste' : 'trastes'} en la misma cuerda.`}`;
      }
      return `${opening} Distancia: ${tonos}. ${fretText}`;
    },

    // ══════════════════════════════════════════════════════════════════════
    // PARTITURAS (VexFlow) — especificación técnica de renderizado
    // ══════════════════════════════════════════════════════════════════════
    _renderLearnScore(instrument, midis) {
      const container = this.$refs.learnScore;
      if (!container || typeof SemimusScore === 'undefined') return;
      SemimusScore.renderNotes(container, instrument, midis.map(Number), 'nota_simple');
    },

    _renderAnswerScore() {
      const container = this.$refs.answerScore;
      if (!container || typeof SemimusScore === 'undefined') return;
      const question = this.currentQ;
      if (!this.answered || !question) {
        SemimusScore.render(container, null);
        return;
      }
      if (question.type === 'scale') {
        // Feedback de escala: la escala escrita desde la raíz, con los grados de foco.
        const notes = SemimusModules.spellScale(Number(question.rootMidi), question.pattern, question.focus || []) || [];
        SemimusScore.render(container, {
          instrument: question.instrument,
          interval_type: 'escala',
          notation_display: { clef: 'treble', notes },
        });
        return;
      }
      if (question.type !== 'interval' && question.type !== 'pitch') {
        SemimusScore.render(container, null);
        return;
      }
      const semitones = Number(question.semitones) || 0;
      const rootMidi = Number(question.rootMidi);
      const direction = this.intervalDirection || question.direction || 'ascendente';
      const midis = direction === 'descendente'
        ? [rootMidi + semitones, rootMidi]
        : [rootMidi, rootMidi + semitones];
      const intervalObj = this.intervals.find(item => item.semitones === semitones);
      SemimusScore.renderNotes(
        container,
        question.instrument,
        midis,
        `${intervalObj ? intervalObj.id : 'intervalo'}_${direction}`
      );
    },

    _renderJamScore() {
      const container = this.$refs.jamScore;
      if (!container || typeof SemimusScore === 'undefined') return;
      const semitones = Number(this.jamIntervalSemitones);
      const rootMidi = Number(this.jamRootMidi);
      const direction = this.jamDirection || 'ascendente';
      const midis = direction === 'descendente'
        ? [rootMidi + semitones, rootMidi]
        : [rootMidi, rootMidi + semitones];
      const intervalObj = this.intervals.find(item => item.semitones === semitones);
      SemimusScore.renderNotes(
        container,
        this.jamInstrument,
        midis,
        `${intervalObj ? intervalObj.id : 'intervalo'}_${direction}`,
        { diagram: false }
      );
    },

    replayAnsweredAudio() {
      if (!this.answered || this.isPlaying) return;
      void this.playCurrentAudio();
    },

    async _recordAchievement(instrument, correct, tonicScaleId = null) {
      if (!this.user.authenticated || !this.csrfToken) {
        if (instrument === 'Bandola') {
          this.bandolaCorrectStreak = correct ? this.bandolaCorrectStreak + 1 : 0;
        }
        return;
      }
      try {
        const response = await fetch('/api/senafonica/achievements', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
          body: JSON.stringify({
            instrument,
            correct,
            tonic_scale_id: tonicScaleId,
          }),
        });
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'No se pudo guardar el progreso de logros.');
        this.bandolaCorrectStreak = result.bandola_correct_streak;
        this.tonicScales = result.tonic_scales;
        if (result.unlocked.length) {
          this._updateMascot('celebrating', `¡Logro desbloqueado: ${result.unlocked.join(', ')}!`);
          this._triggerConfetti();
        }
      } catch (error) {
        console.error('Could not sync achievement progress:', error);
      }
    },

    startTimeTrial() {
      clearInterval(this.timeTrialTimer);
      this.currentTab = 'time-trial';
      this.timeTrialSeconds = 30;
      this.timeTrialScore = 0;
      this.timeTrialAttempted = 0;
      this.timeTrialFinished = false;
      this.qIndex = 0;
      this.sessionCorrect = 0;
      this.sessionWrong = 0;
      this.levelQuestions = Array.from({ length: 30 }, (_, index) => {
        const interval = this.intervals[Math.floor(Math.random() * this.intervals.length)];
        const pool = this.intervals.map(item => item.name);
        return {
          id: index + 1,
          type: 'interval',
          title: '¿A qué suena este salto?',
          instruction: 'Escucha el intervalo y elige su nombre.',
          instrument: index % 2 === 0 ? 'Tiple' : 'Requinto',
          rootMidi: 60,
          semitones: interval.semitones,
          direction: 'ascendente',
          correct: interval.name,
          options: this._makeOptions(interval.name, pool, 4),
          explanation: `Era ${interval.name}: ${interval.semitones} semitonos.`,
        };
      });
      this.currentQ = this.levelQuestions[0];
      this.activeStation = { station_name: 'Contrarreloj', instrument: 'Tiple y Requinto' };
      this._resetQuestionAttempt();
      this._preloadQuestionAudio(this.levelQuestions);
      this.timeTrialTimer = setInterval(() => {
        this.timeTrialSeconds--;
        if (this.timeTrialSeconds <= 0) this.finishTimeTrial();
      }, 1000);
      this.$nextTick(() => setTimeout(() => this.playCurrentAudio(), 100));
    },

    finishTimeTrial() {
      if (this.timeTrialFinished) return;
      clearInterval(this.timeTrialTimer);
      this.timeTrialFinished = true;
      this.audio.stop();
      this.isPlaying = false;
      const earnedXp = this.timeTrialScore * 5;
      this.xp += earnedXp;
      if (this.timeTrialAttempted > 0) {
        void this._syncWithServer({
          xp_earned: (this.timeTrialScore * 15) + earnedXp,
          coins_earned: this.timeTrialScore * 3,
          correct_count: this.timeTrialScore,
          total_count: this.timeTrialAttempted,
        });
      }
    },

    async startDailyChallenge() {
      this.currentTab = 'daily';
      this.dailyLoading = true;
      this.dailyMessage = '';
      this.dailyFinished = false;
      this.dailyScore = 0;
      this.dailyAnswers = [];
      this.qIndex = 0;
      try {
        const response = await fetch('/api/senafonica/daily-challenge');
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'No se pudo cargar el desafío diario.');
        if (!data.questions.length) throw new Error('No hay intervalos cargados para preparar el reto.');
        this.dailyDate = data.date;
        this.dailyStreak = data.daily_streak || this.dailyStreak;
        if (data.completed) {
          this.dailyFinished = true;
          this.dailyMessage = 'Ya completaste el desafío de hoy. ¡Vuelve mañana para otra medalla!';
          return;
        }
        this.dailyQuestions = data.questions.map(question => ({
          ...question,
          type: 'interval',
          title: 'Desafío diario · ¿Qué intervalo escuchas?',
          instruction: `Pregunta ${question.id} de 3 · ${question.instrument}`,
          direction: 'ascendente',
          explanation: `La respuesta era ${question.correct}.`,
        }));
        this.levelQuestions = this.dailyQuestions;
        this.currentQ = this.dailyQuestions[0];
          this.activeStation = { station_name: 'Desafío diario', instrument: 'Tiple, Requinto y Bandola' };
        this._resetQuestionAttempt();
        this._preloadQuestionAudio(this.dailyQuestions);
        this.$nextTick(() => setTimeout(() => this.playCurrentAudio(), 100));
      } catch (error) {
        this.dailyMessage = error.message || 'No se pudo cargar el desafío diario.';
      } finally {
        this.dailyLoading = false;
      }
    },

    async finishDailyChallenge() {
      if (this.dailyFinished) return;
      this.dailyFinished = true;
      try {
        const response = await fetch('/api/senafonica/daily-challenge', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-CSRFToken': this.csrfToken },
          body: JSON.stringify({ answers: this.dailyAnswers }),
        });
        const result = await response.json();
        if (response.status === 401) {
          this.dailyMessage = `Completaste ${this.dailyScore}/3. Inicia sesión para guardar tu racha y reclamar la recompensa.`;
          return;
        }
        if (!response.ok) throw new Error(result.error || 'No se pudo guardar el desafío diario.');
        this.dailyStreak = result.daily_streak;
        this.dailyScore = result.score;
        this.xp = result.total_xp;
        this.coins = result.coins;
        this.dailyMessage = result.status === 'already_completed'
          ? 'El desafío de hoy ya estaba registrado.'
          : `¡Desafío completado! ${this.dailyScore}/3 · +25 XP · +5 púas${result.medal ? ' · ¡Medalla diaria!' : ''}`;
        this.audio.playLevelCompleteSound();
        this._triggerConfetti();
      } catch (error) {
        this.dailyFinished = false;
        this.dailyMessage = error.message || 'No se pudo guardar el desafío diario.';
      }
    },

    prepareTonicChallenge() {
      this.tonicChallengeMessage = '';
      this.tonicChallengeAttempts = 0;
      this.tonicChallengeIdentified = false;
      const root = Number(this.jamRootMidi);
      this.tonicChallengeOptions = [root, root + 2, root + 4, root + 7]
        .sort(() => Math.random() - 0.5);
    },

    async playTonicChallenge() {
      await this.audio.playNote(this.jamInstrument, Number(this.jamRootMidi), 0, 0.75, 0.95);
    },

    async answerTonicChallenge(midi) {
      const scale = this.scales[Number(this.jamScaleIndex)];
      if (this.tonicChallengeIdentified) return;
      const correct = Number(midi) === Number(this.jamRootMidi);
      const firstTry = this.tonicChallengeAttempts === 0;
      this.tonicChallengeAttempts++;
      this.tonicChallengeMessage = correct
        ? `¡Correcto! ${this.audio.midiToName(Number(midi))} es la tónica.`
        : 'No es esa nota. Escucha de nuevo y vuelve a intentarlo.';
      if (correct) this.tonicChallengeIdentified = true;
      if (correct && firstTry && scale && !this.tonicScales.includes(scale.id)) {
        this.tonicScales.push(scale.id);
        await this._recordAchievement(null, true, scale.id);
        this._triggerConfetti();
      }
    },

    _completeStation() {
      const total = this.levelQuestions.length;
      const accuracy = Math.round((this.sessionCorrect / total) * 100);
      if (this.activeStation.moduleId !== undefined) {
        const { moduleId, moduleLevel } = this.activeStation;
        const progressKey = SemimusModules.progressKey(moduleId, moduleLevel);
        this.moduleProgress[progressKey] = Math.max(this.moduleProgress[progressKey] || 0, accuracy);
        const threshold = this.passingPercent();
        const passed = accuracy >= threshold;
        const hasNextModule = Boolean(this.levels.find(item => item.id === moduleId + 1));
        this._saveLocalState();
        void this._syncWithServer({ module_progress: this.moduleProgress });
        this.currentTab = 'path';
        this._updateMascot(
          passed ? 'celebrating' : 'sad',
          passed
            ? `¡Reto superado con ${accuracy}%!${hasNextModule ? ` Desbloqueaste el módulo ${moduleId + 1}.` : ''}`
            : `Obtuviste ${accuracy}%. Necesitas ${threshold}% para desbloquear el módulo siguiente.`
        );
        if (passed) {
          this.audio.playLevelCompleteSound();
          this._triggerConfetti();
        }
        return;
      }
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
      // Renderiza el compás en paralelo con la reproducción del intervalo.
      this._renderJamScore();

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
      if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
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
      if (!this.csrfToken) {
        if (this.user.authenticated) {
          console.error('Authenticated progress was not synced because the CSRF token is missing.');
        }
        return;
      }
      try {
        const res = await fetch('/api/senafonica/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': this.csrfToken,
          },
          body: JSON.stringify(payload),
        });
        if (!res.ok) {
          console.error(`Server sync failed with HTTP ${res.status}.`);
          return;
        }
        const serverData = await res.json();
        if (serverData.total_xp !== undefined) this.xp = serverData.total_xp;
        if (serverData.coins !== undefined) this.coins = serverData.coins;
        if (serverData.streak !== undefined) this.streak = serverData.streak;
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
