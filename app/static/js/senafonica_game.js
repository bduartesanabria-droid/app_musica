/**
 * SENAFÓNICA Game Engine — Videojuego Web Autónomo e Integrado
 * Recorrido Cultural por la Provincia de Vélez
 */

function senafonicaGame(initData) {
  return {
    // ── DATA & CONFIG ────────────────────────────────────────────────────────
    user: initData.user || { name: 'Aprendiz Veleño', xp: 0, coins: 0, level: 1, streak: 1 },
    catalog: initData.catalog || {},
    intervals: initData.intervals || [],
    scales: initData.scales || [],
    stations: initData.levels || [], // 9 Estaciones de Vélez
    theoryQuestions: initData.theoryQuestions || [],
    inductionQuestions: initData.inductionQuestions || [],
    shopItems: initData.shopItems || [],
    csrfToken: initData.csrfToken || '',

    // ── ONBOARDING & LEGAL FLOW ─────────────────────────────────────────────
    // Steps: 'legal' -> 'tutorial' -> 'induction_cards' -> 'induction_quiz' -> 'completed'
    onboardingStep: 'completed', // Checked on init from localStorage
    playerAge: '',
    legalConsent: false,
    inductionIndex: 0,
    inductionSelected: null,
    inductionAnswered: false,
    inductionIsCorrect: false,

    // ── IN-GAME MODALS & TABS ───────────────────────────────────────────────
    currentTab: 'path', // 'path' (mapa) | 'training' (ejercicio activo) | 'jam' (modo libre)
    showStationModal: false,
    selectedStation: null,
    showStatsModal: false,
    showShopModal: false,
    showRescueModal: false,

    // ── GAMIFICATION HUD STATE ──────────────────────────────────────────────
    lives: 5,
    maxLives: 5,
    xp: 0,
    coins: 0,
    streak: 1,
    levelStars: {},       // { stationId: stars (1-3) }
    unlockedLevels: [1],  // Barbosa (Station 1) unlocked by default
    totalQuestionsAnswered: 0,
    totalCorrectAnswered: 0,
    unlockedCollectibles: [],
    equippedSkin: 'skin_tiple_noble',
    equippedAccessories: { hat: '', body: '', eyes: '' },
    unlockedItems: ['skin_tiple_noble'],

    // ── ACTIVE EXERCISE STATE ───────────────────────────────────────────────
    activeStation: null,
    levelQuestions: [],
    qIndex: 0,
    currentQ: null,
    answered: false,
    selectedOption: null,
    isCorrect: false,
    sessionCorrect: 0,
    sessionWrong: 0,
    intervalDirection: 'ascendente', // 'ascendente' | 'descendente' | 'intercalada'
    activeNotePlayingIndex: -1,
    activeNoteName: '',
    isComparingAudio: false,
    comparePhase: 'idle',

    // ── RESCUE CHALLENGE STATE ──────────────────────────────────────────────
    rescueQuestions: [],
    rescueIndex: 0,
    rescueAnswered: false,
    rescueSelected: null,
    rescueIsCorrect: false,

    // ── FREE JAM (MODO LIBRE) STATE ─────────────────────────────────────────
    jamInstrument: 'Tiple',
    jamScaleIndex: 0,
    jamRootMidi: 60, // DO4
    jamTempo: 1.0,
    jamIntervalSemitones: 7, // 5ª Justa
    jamDirection: 'ascendente',
    jamActiveNoteIndex: -1,

    // ── MASCOT CONTROLLER (PNG SIN FONDO) ───────────────────────────────────
    mascotState: 'idle', // 'idle' | 'celebrating' | 'sad' | 'listening'
    mascotSpeech: '¡Bienvenido a SENAFÓNICA! Recorreremos la hermosa Provincia de Vélez.',
    mascotImg: '/static/img/niños_traje.png',

    // ── AUDIO ENGINE ────────────────────────────────────────────────────────
    audio: null,
    isPlaying: false,

    // ── INITIALIZATION ──────────────────────────────────────────────────────
    init() {
      this.audio = new SenafonicaAudioEngine(this.catalog);

      // Check onboarding status
      const savedOnboarding = localStorage.getItem('senafonica_onboarding_done');
      if (!savedOnboarding) {
        this.onboardingStep = 'legal';
      } else {
        this.onboardingStep = 'completed';
      }

      this._loadLocalState();

      // Keyboard shortcuts: Space to replay, 1-4 for options
      window.addEventListener('keydown', (e) => {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.code === 'Space') {
          e.preventDefault();
          this.replayAudio();
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

    // ── ONBOARDING FLOW METHODS ─────────────────────────────────────────────
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
        // Complete onboarding
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

    // ── LOCAL STORAGE PERSISTENCE ───────────────────────────────────────────
    _loadLocalState() {
      const saved = localStorage.getItem('senafonica_gamification_velez_v1');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          this.lives = parsed.lives !== undefined ? Math.min(parsed.lives, this.maxLives) : 5;
          this.xp = Math.max(parsed.xp || 0, this.user.xp || 0);
          this.coins = Math.max(parsed.coins || 0, this.user.coins || 0);
          this.streak = Math.max(parsed.streak || 1, this.user.streak || 1);
          this.levelStars = parsed.levelStars || {};
          this.unlockedLevels = parsed.unlockedLevels || [1];
          this.totalQuestionsAnswered = parsed.totalQuestionsAnswered || 0;
          this.totalCorrectAnswered = parsed.totalCorrectAnswered || 0;
          this.unlockedCollectibles = parsed.unlockedCollectibles || [];
          this.equippedSkin = parsed.equippedSkin || 'skin_tiple_noble';
          this.equippedAccessories = parsed.equippedAccessories || { hat: '', body: '', eyes: '' };
          this.unlockedItems = parsed.unlockedItems || ['skin_tiple_noble'];
          return;
        } catch (e) {
          console.warn('Could not parse local state', e);
        }
      }
      this.xp = this.user.xp || 0;
      this.coins = this.user.coins || 0;
      this.streak = this.user.streak || 1;
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
      localStorage.setItem('senafonica_gamification_velez_v1', JSON.stringify(state));
    },

    // ── MASCOT CONTROLLER ───────────────────────────────────────────────────
    _updateMascot(state, speech) {
      this.mascotState = state;
      if (speech) this.mascotSpeech = speech;
      if (state === 'celebrating') {
        this.mascotImg = '/static/img/niños_acertaste.png';
      } else if (state === 'sad') {
        this.mascotImg = '/static/img/niños_tristes.png';
      } else {
        this.mascotImg = '/static/img/niños_traje.png';
      }
    },

    // ── STATIONS & MAP NAVIGATION ───────────────────────────────────────────
    previewStation(station) {
      this.selectedStation = station;
      this.showStationModal = true;
      this._updateMascot('listening', `${station.station_name}: ${station.subtitle}`);
    },

    startStationFromModal() {
      this.showStationModal = false;
      if (this.selectedStation) {
        this.startStation(this.selectedStation);
      }
    },

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
      this.qIndex = 0;
      this.sessionCorrect = 0;
      this.sessionWrong = 0;
      this.levelQuestions = this._generateQuestionsForStation(station);
      this.currentQ = this.levelQuestions[0];
      this.answered = false;
      this.selectedOption = null;
      this.currentTab = 'training';

      this._updateMascot('listening', `¡Llegamos a ${station.station_name}! Escucha con atención.`);

      this.$nextTick(() => {
        setTimeout(() => this.playCurrentAudio(), 400);
      });
    },

    _generateQuestionsForStation(station) {
      const questions = [];
      const count = station.questions_count || 5;

      if (station.type === 'scale') {
        const targetScale = this.scales.find(s => s.name.toLowerCase() === (station.scale_name || '').toLowerCase()) || this.scales[0];
        const allScaleNames = this.scales.map(s => s.name);

        for (let i = 0; i < count; i++) {
          const rootMidi = 55 + (i % 6);
          const chosenScale = (i % 2 === 0) ? targetScale : this.scales[Math.floor(Math.random() * this.scales.length)];
          const pattern = chosenScale.intervals_pattern ? chosenScale.intervals_pattern.split(',').map(Number) : [2, 2, 1, 2, 2, 2, 1];
          const options = this._makeOptions(chosenScale.name, allScaleNames, 4);

          questions.push({
            id: i + 1,
            type: 'scale',
            title: `Reconoce la Escala (${station.instrument})`,
            instruction: `Escucha la ejecución continua en ${station.station_name}.`,
            instrument: station.instrument,
            rootMidi: rootMidi,
            pattern: pattern,
            correct: chosenScale.name,
            options: options,
            explanation: chosenScale.description || `La escala ${chosenScale.name} le da el carácter folclórico a esta estación.`
          });
        }
        return questions;
      }

      // Interval questions
      const targetIntervalNames = station.intervals && station.intervals.length ? station.intervals : this.intervals.map(i => i.name);
      const allIntervalNames = this.intervals.map(i => i.name);

      for (let i = 0; i < count; i++) {
        const intervalName = targetIntervalNames[i % targetIntervalNames.length];
        const intervalObj = this.intervals.find(item => item.name === intervalName) || this.intervals[1];
        const rootMidi = 55 + (i % 8);
        const allowedDirs = station.directions || ['ascendente'];
        const chosenDir = allowedDirs[Math.floor(Math.random() * allowedDirs.length)];
        const options = this._makeOptions(intervalName, allIntervalNames, 4);

        questions.push({
          id: i + 1,
          type: 'interval',
          title: `¿Qué intervalo escuchas? (${station.instrument})`,
          instruction: `Identifica la distancia entre las notas tocadas en ${station.station_name}.`,
          instrument: station.instrument,
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

    // ── AUDIO PLAYBACK ──────────────────────────────────────────────────────
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
      } else if (q.type === 'interval') {
        await this.audio.playInterval(
          q.instrument,
          q.rootMidi,
          q.semitones,
          this.intervalDirection || q.direction || 'ascendente',
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

    // ── ANSWER SUBMISSION ───────────────────────────────────────────────────
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

    // ── AUDITORY COMPARISON (CHOSEN VS CORRECT) ─────────────────────────────
    async playAudioComparison() {
      if (!this.currentQ || this.currentQ.type !== 'interval' || this.isComparingAudio) return;
      const chosenName = this.selectedOption;
      const correctName = this.currentQ.correct;

      const chosenObj = this.intervals.find(i => i.name === chosenName) || { semitones: 2 };
      const correctObj = this.intervals.find(i => i.name === correctName) || { semitones: 7 };

      this.isComparingAudio = true;
      this._updateMascot('listening', `1. Tu respuesta (${chosenName}) -> 2. Respuesta correcta (${correctName})`);

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

    // ── NEXT QUESTION OR COMPLETE STATION ───────────────────────────────────
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
        `¡Estación ${this.activeStation.station_name} completada con ${stars} estrella(s)! Ganaste +${xpBonus} XP y +${coinBonus} Púas.`
      );
    },

    // ── RESCUE & MUSIC THEORY CHALLENGE ─────────────────────────────────────
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
          this.lives = 2; // Mercy fallback so player is never stranded
        }
        this.showRescueModal = false;
        this._saveLocalState();
        this._updateMascot('idle', `¡Vidas recuperadas (${this.lives}/${this.maxLives})! Continúa tu viaje por Vélez.`);
      }
    },

    // ── FREE JAM (MODO LIBRE) ───────────────────────────────────────────────
    async playJamScale() {
      if (this.isPlaying) return;
      this.isPlaying = true;
      const scaleObj = this.scales[this.jamScaleIndex] || this.scales[0];
      const pattern = scaleObj.intervals_pattern ? scaleObj.intervals_pattern.split(',').map(Number) : [2, 2, 1, 2, 2, 2, 1];

      this._updateMascot('listening', `Reproduciendo ${scaleObj.name} en ${this.jamInstrument} (sostenido recortado fluido)...`);

      await this.audio.playScale(
        this.jamInstrument,
        Number(this.jamRootMidi),
        pattern,
        Number(this.jamTempo),
        (idx) => {
          this.jamActiveNoteIndex = idx;
        }
      );

      this.isPlaying = false;
      this.jamActiveNoteIndex = -1;
      this._updateMascot('idle', '¡Escala terminada! Prueba cambiar el instrumento o la velocidad.');
    },

    async playJamInterval() {
      if (this.isPlaying) return;
      this.isPlaying = true;
      const intervalObj = this.intervals.find(i => i.semitones === Number(this.jamIntervalSemitones)) || this.intervals[1];

      this._updateMascot('listening', `Sonando ${intervalObj.name} (${this.jamDirection}) en ${this.jamInstrument}...`);

      await this.audio.playInterval(
        this.jamInstrument,
        Number(this.jamRootMidi),
        Number(this.jamIntervalSemitones),
        this.jamDirection,
        (idx) => {
          this.jamActiveNoteIndex = idx;
        }
      );

      this.isPlaying = false;
      this.jamActiveNoteIndex = -1;
      this._updateMascot('idle', `${intervalObj.name}: ${intervalObj.semitones} semitonos.`);
    },

    // ── SHOP & IN-GAME INVENTORY ────────────────────────────────────────────
    buyItem(item) {
      if (this.unlockedItems.includes(item.id)) {
        this.equipItem(item);
        return;
      }

      if (this.coins < item.cost_coins || this.xp < item.cost_xp) {
        this._updateMascot('sad', `Necesitas ${item.cost_xp} XP y ${item.cost_coins} Púas para desbloquear este artículo.`);
        return;
      }

      this.coins -= item.cost_coins;
      this.unlockedItems.push(item.id);
      this.equipItem(item);
      this.audio.playLifeRestoredSound();
      this._triggerConfetti();
      this._saveLocalState();
      this._updateMascot('celebrating', `¡Desbloqueaste ${item.title}! Ya lo llevas equipado.`);
    },

    equipItem(item) {
      if (item.type === 'skin') {
        this.equippedSkin = item.id;
      } else if (item.type === 'accessory') {
        if (item.slot === 'hat') this.equippedAccessories.hat = item.id;
        else if (item.slot === 'body') this.equippedAccessories.body = item.id;
        else if (item.slot === 'eyes') this.equippedAccessories.eyes = item.id;
      }
      this._saveLocalState();
    },

    // ── CONFETTI & PARTICLES ────────────────────────────────────────────────
    _triggerConfetti() {
      const canvas = document.getElementById('senafonica-confetti');
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;

      const particles = [];
      const colors = ['#39A900', '#FBBF24', '#3B82F6', '#EC4899', '#10B981', '#FFFFFF'];

      for (let i = 0; i < 75; i++) {
        particles.push({
          x: canvas.width / 2,
          y: canvas.height * 0.35,
          vx: (Math.random() - 0.5) * 16,
          vy: (Math.random() - 1.0) * 13,
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

    // ── BACKEND SERVER SYNC ─────────────────────────────────────────────────
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
          const data = await res.json();
          if (data.total_xp) this.xp = data.total_xp;
          if (data.coins) this.coins = data.coins;
          if (data.streak) this.streak = data.streak;
        }
      } catch (err) {
        console.warn('Server sync failed, local state preserved:', err);
      }
    },

    // ── STATS HELPER ────────────────────────────────────────────────────────
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
