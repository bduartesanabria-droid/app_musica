/**
 * SENAFÓNICA Game Engine — Duolingo-style gamification, reactive mascot, and interactive path
 */

function senafonicaGame(initData) {
  return {
    // ── DATA & CONFIG ────────────────────────────────────────────────────────
    user: initData.user || { name: 'Músico', xp: 0, coins: 0, level: 1, streak: 0 },
    catalog: initData.catalog || {},
    intervals: initData.intervals || [],
    scales: initData.scales || [],
    levels: initData.levels || [],
    theoryQuestions: initData.theoryQuestions || [],
    shopItems: initData.shopItems || [],
    csrfToken: initData.csrfToken || '',

    // ── ACTIVE NAVIGATION / MODE ────────────────────────────────────────────
    currentTab: 'path', // 'path' | 'training' | 'jam' | 'shop' | 'theory'

    // ── GAMIFICATION STATE ──────────────────────────────────────────────────
    lives: 5,
    maxLives: 5,
    xp: 0,
    coins: 0,
    streak: 1,
    levelStars: {},       // { levelId: stars (1-3) }
    unlockedLevels: [1],  // Level 1 unlocked by default
    equippedSkin: 'skin_tiple_noble',
    equippedAccessories: { hat: '', body: '', eyes: '' },
    unlockedItems: ['skin_tiple_noble'],

    // ── ACTIVE LEVEL / SESSION STATE ────────────────────────────────────────
    activeLevel: null,
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
    comparePhase: 'idle', // 'chosen' | 'transition' | 'correct' | 'idle'

    // ── RESCUE / THEORETICAL MODAL ──────────────────────────────────────────
    showRescueModal: false,
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

    // ── MASCOT CONTROLLER ───────────────────────────────────────────────────
    mascotState: 'idle', // 'idle' | 'celebrating' | 'sad' | 'listening' | 'rescue'
    mascotSpeech: '¡Bienvenido a SENAFÓNICA! Entrena tu oído folclórico.',
    mascotImg: '/static/img/niños_traje.png',

    // ── AUDIO ENGINE INSTANCE ───────────────────────────────────────────────
    audio: null,
    isPlaying: false,

    // ── INITIALIZATION ──────────────────────────────────────────────────────
    init() {
      this.audio = new SenafonicaAudioEngine(this.catalog);

      // Restore saved progress from localStorage or user data
      this._loadLocalState();

      // Set initial mascot speech
      this._updateMascot('idle', `¡Hola, ${this.user.name}! Elige un nivel en la Ruta de Aprendizaje.`);

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
          }
        }
      });
    },

    // ── LOCAL STORAGE PERSISTENCE ───────────────────────────────────────────
    _loadLocalState() {
      const saved = localStorage.getItem('senafonica_gamification_v2');
      if (saved) {
        try {
          const parsed = JSON.parse(saved);
          this.lives = parsed.lives !== undefined ? Math.min(parsed.lives, this.maxLives) : 5;
          this.xp = Math.max(parsed.xp || 0, this.user.xp || 0);
          this.coins = Math.max(parsed.coins || 0, this.user.coins || 0);
          this.streak = Math.max(parsed.streak || 1, this.user.streak || 1);
          this.levelStars = parsed.levelStars || {};
          this.unlockedLevels = parsed.unlockedLevels || [1];
          this.equippedSkin = parsed.equippedSkin || 'skin_tiple_noble';
          this.equippedAccessories = parsed.equippedAccessories || { hat: '', body: '', eyes: '' };
          this.unlockedItems = parsed.unlockedItems || ['skin_tiple_noble'];
          return;
        } catch (e) {
          console.warn('Could not parse local gamification state', e);
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
        equippedSkin: this.equippedSkin,
        equippedAccessories: this.equippedAccessories,
        unlockedItems: this.unlockedItems,
      };
      localStorage.setItem('senafonica_gamification_v2', JSON.stringify(state));
    },

    // ── MASCOT STATE ────────────────────────────────────────────────────────
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

    // ── NAVIGATION ──────────────────────────────────────────────────────────
    setTab(tab) {
      if (this.currentTab === 'training' && this.answered === false && this.activeLevel) {
        if (!confirm('¿Deseas salir del nivel? Perderás el progreso de esta lección.')) {
          return;
        }
      }
      this.audio.stop();
      this.currentTab = tab;
      if (tab === 'path') {
        this._updateMascot('idle', '¡Selecciona una lección para continuar tu viaje musical!');
      } else if (tab === 'jam') {
        this._updateMascot('idle', 'Modo Libre: Explora cualquier escala o intervalo sin presión.');
      } else if (tab === 'shop') {
        this._updateMascot('idle', '¡Personaliza tus instrumentos y viste a la mascota con tus logros!');
      }
    },

    // ── LEVEL LAUNCH & QUESTION GENERATOR ────────────────────────────────────
    startLevel(level) {
      if (!this.unlockedLevels.includes(level.id)) {
        this._updateMascot('sad', 'Este nivel está bloqueado. Completa los niveles anteriores para desbloquearlo.');
        return;
      }

      if (this.lives <= 0) {
        this.openRescueModal();
        return;
      }

      this.activeLevel = level;
      this.qIndex = 0;
      this.sessionCorrect = 0;
      this.sessionWrong = 0;
      this.levelQuestions = this._generateQuestionsForLevel(level);
      this.currentQ = this.levelQuestions[0];
      this.answered = false;
      this.selectedOption = null;
      this.currentTab = 'training';

      this._updateMascot('listening', `Nivel ${level.id}: ${level.title}. ¡Escucha con atención!`);

      // Auto-play the first question audio
      this.$nextTick(() => {
        setTimeout(() => this.playCurrentAudio(), 400);
      });
    },

    _generateQuestionsForLevel(level) {
      const questions = [];
      const count = level.questions_count || 5;

      if (level.type === 'theory') {
        // Pure theoretical checkpoint
        const shuffled = [...this.theoryQuestions].sort(() => 0.5 - Math.random());
        return shuffled.slice(0, count).map((t, idx) => ({
          id: idx + 1,
          type: 'theory',
          title: 'Desafío Teórico Folclórico',
          question: t.question,
          options: t.options,
          correct: t.correct,
          explanation: t.explanation,
          instrument: level.instrument || 'Tiple',
        }));
      }

      if (level.type === 'scale') {
        // Scale recognition level
        const scaleObj = this.scales.find(s => s.name.toLowerCase() === level.scale_name.toLowerCase()) || this.scales[0];
        const allScaleNames = this.scales.map(s => s.name);

        for (let i = 0; i < count; i++) {
          // Select root note from realistic range for instrument
          const rootMidi = 55 + (i % 6); // G3 to C4
          const targetScale = (i % 2 === 0) ? scaleObj : this.scales[Math.floor(Math.random() * this.scales.length)];
          const pattern = targetScale.pattern ? targetScale.pattern.split(',').map(Number) : [2, 2, 1, 2, 2, 2, 1];

          // 4 options
          const options = this._makeOptions(targetScale.name, allScaleNames, 4);

          questions.push({
            id: i + 1,
            type: 'scale',
            title: `Reconoce la Escala (${level.instrument})`,
            instruction: 'Escucha la secuencia continua de notas e identifica qué escala suena.',
            instrument: level.instrument,
            rootMidi: rootMidi,
            pattern: pattern,
            correct: targetScale.name,
            options: options,
            explanation: targetScale.description || `La escala ${targetScale.name} se caracteriza por su patrón sonoro único.`
          });
        }
        return questions;
      }

      // Interval recognition level (Core 1)
      const targetIntervalNames = level.intervals && level.intervals.length ? level.intervals : this.intervals.map(i => i.name);
      const allIntervalNames = this.intervals.map(i => i.name);

      for (let i = 0; i < count; i++) {
        const intervalName = targetIntervalNames[i % targetIntervalNames.length];
        const intervalObj = this.intervals.find(item => item.name === intervalName) || this.intervals[1];
        const rootMidi = 55 + (i % 8); // G3 to D4

        const allowedDirs = level.directions || ['ascendente'];
        const chosenDir = allowedDirs[Math.floor(Math.random() * allowedDirs.length)];

        const options = this._makeOptions(intervalName, allIntervalNames, 4);

        questions.push({
          id: i + 1,
          type: 'interval',
          title: `¿Qué intervalo escuchas? (${level.instrument})`,
          instruction: `Reproduce las dos notas (${chosenDir}) y reconoce la distancia.`,
          instrument: level.instrument,
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

    // ── AUDIO PLAYBACK IN SESSION ───────────────────────────────────────────
    async playCurrentAudio() {
      if (!this.currentQ || this.isPlaying) return;
      this.isPlaying = true;
      this._updateMascot('listening', 'Escucha atentamente el sonido del instrumento...');

      const q = this.currentQ;
      if (q.type === 'scale') {
        await this.audio.playScale(
          q.instrument,
          q.rootMidi,
          q.pattern,
          1.0,
          (idx, midi, name, total) => {
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

      if (this.isCorrect) {
        // Correct answer!
        this.sessionCorrect++;
        this.xp += 15;
        this.coins += 3;
        this.audio.playSuccessSound();
        this._updateMascot('celebrating', '¡Excelente oído! Respuesta correcta.');
        this._triggerConfetti();
      } else {
        // Wrong answer
        this.sessionWrong++;
        this.lives = Math.max(0, this.lives - 1);
        this.audio.playLifeLostSound();
        this._updateMascot('sad', `¡Oh, no! La respuesta correcta era: ${this.currentQ.correct}.`);

        // Check if lives hit 0
        if (this.lives <= 0) {
          setTimeout(() => {
            this.openRescueModal();
          }, 1200);
        }
      }

      this._saveLocalState();
    },

    // ── AUDITORY COMPARISON ─────────────────────────────────────────────────
    async playAudioComparison() {
      if (!this.currentQ || this.currentQ.type !== 'interval' || this.isComparingAudio) return;
      const chosenName = this.selectedOption;
      const correctName = this.currentQ.correct;

      const chosenObj = this.intervals.find(i => i.name === chosenName) || { semitones: 2 };
      const correctObj = this.intervals.find(i => i.name === correctName) || { semitones: 7 };

      this.isComparingAudio = true;
      this._updateMascot('listening', `Comparando: Primero ${chosenName}, luego ${correctName}...`);

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

    // ── NEXT QUESTION OR COMPLETE LEVEL ─────────────────────────────────────
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
        this._completeLevel();
      }
    },

    _completeLevel() {
      const total = this.levelQuestions.length;
      const accuracy = Math.round((this.sessionCorrect / total) * 100);
      let stars = 1;
      if (accuracy >= 90) stars = 3;
      else if (accuracy >= 65) stars = 2;

      const levelId = this.activeLevel.id;
      const previousStars = this.levelStars[levelId] || 0;
      if (stars > previousStars) {
        this.levelStars[levelId] = stars;
      }

      // Unlock next level
      const nextLevelId = levelId + 1;
      if (stars >= 1 && !this.unlockedLevels.includes(nextLevelId)) {
        this.unlockedLevels.push(nextLevelId);
      }

      const xpBonus = this.activeLevel.xp_reward || 50;
      const coinBonus = this.activeLevel.coins_reward || 10;
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
        `¡Nivel completado con ${stars} estrella(s) y ${accuracy}% de precisión! Ganaste +${xpBonus} XP y +${coinBonus} Púas.`
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
        this._updateMascot('celebrating', '¡Respuesta correcta! Has recuperado vidas al instante.');
      } else {
        this.audio.playErrorSound();
        this._updateMascot('sad', `Incorrecto. ${q.explanation}`);
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
        // Finished rescue questions
        if (this.lives === 0) {
          this.lives = 2; // Mercy fallback so student is never stranded
        }
        this.showRescueModal = false;
        this._saveLocalState();
        this._updateMascot('idle', `¡Vidas recuperadas (${this.lives}/${this.maxLives})! Puedes continuar practicando.`);
      }
    },

    // ── FREE JAM (MODO LIBRE / EXPLORADOR) ──────────────────────────────────
    async playJamScale() {
      if (this.isPlaying) return;
      this.isPlaying = true;
      const scaleObj = this.scales[this.jamScaleIndex] || this.scales[0];
      const pattern = scaleObj.intervals_pattern ? scaleObj.intervals_pattern.split(',').map(Number) : [2, 2, 1, 2, 2, 2, 1];

      this._updateMascot('listening', `Reproduciendo ${scaleObj.name} en ${this.jamInstrument} (optimizado y fluido)...`);

      await this.audio.playScale(
        this.jamInstrument,
        Number(this.jamRootMidi),
        pattern,
        Number(this.jamTempo),
        (idx, midi, name) => {
          this.jamActiveNoteIndex = idx;
        }
      );

      this.isPlaying = false;
      this.jamActiveNoteIndex = -1;
      this._updateMascot('idle', '¡Escala reproducida! Prueba cambiar la tónica o el instrumento.');
    },

    async playJamInterval() {
      if (this.isPlaying) return;
      this.isPlaying = true;
      const intervalObj = this.intervals.find(i => i.semitones === Number(this.jamIntervalSemitones)) || this.intervals[1];

      this._updateMascot('listening', `Intervalo: ${intervalObj.name} (${this.jamDirection}) en ${this.jamInstrument}...`);

      await this.audio.playInterval(
        this.jamInstrument,
        Number(this.jamRootMidi),
        Number(this.jamIntervalSemitones),
        this.jamDirection,
        (idx, midi, name) => {
          this.jamActiveNoteIndex = idx;
        }
      );

      this.isPlaying = false;
      this.jamActiveNoteIndex = -1;
      this._updateMascot('idle', `${intervalObj.name}: ${intervalObj.semitones} semitonos.`);
    },

    // ── SHOP & REWARDS ──────────────────────────────────────────────────────
    buyItem(item) {
      if (this.unlockedItems.includes(item.id)) {
        // Already unlocked, equip it
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
      this._updateMascot('celebrating', `¡Desbloqueaste ${item.title}! Ya está equipado.`);
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

      for (let i = 0; i < 65; i++) {
        particles.push({
          x: canvas.width / 2,
          y: canvas.height * 0.35,
          vx: (Math.random() - 0.5) * 14,
          vy: (Math.random() - 1.0) * 12,
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
          p.vy += 0.35; // gravity
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
        console.warn('Sync with server failed, local state preserved:', err);
      }
    },
  };
}

// Global hook
window.senafonicaGame = senafonicaGame;
