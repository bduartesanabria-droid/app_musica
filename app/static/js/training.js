/**
 * SEMIMUS Training Session — Alpine.js component
 *
 * Renders an AJAX-driven training session without full page reloads.
 * Called from training/session.html: trainingSession(questions, answerUrl, completeUrl)
 */
function trainingSession(questions, answerUrl, completeUrl) {
  return {
    // State
    questions:       questions,
    currentIndex:    0,
    currentQ:        null,
    answered:        false,
    selectedAnswer:  null,
    lastCorrect:     false,
    isPlaying:       false,
    showHint:        false,
    correct:         0,
    wrong:           0,
    elapsed:         0,
    _timer:          null,
    _questionStart:  0,

    // Init (called by Alpine on mount)
    init() {
      this.currentQ = this.questions[0] || null;
      this._questionStart = Date.now();
      this._timer = setInterval(() => { this.elapsed++; }, 1000);
      // Auto-play first audio
      this.$nextTick(() => this.playAudio());
    },

    // Cleanup
    destroy() {
      clearInterval(this._timer);
    },

    // ── Audio ──────────────────────────────────────────────────────────────
    playAudio() {
      if (!this.currentQ || !this.currentQ.audio_url) return;
      const player = document.getElementById('audioPlayer');
      if (!player) return;

      if (!player.paused && player.src.endsWith(this.currentQ.audio_url)) {
        player.pause();
        player.currentTime = 0;
      }

      player.src = this.currentQ.audio_url;
      this.isPlaying = true;

      const btn = document.querySelector('.audio-btn');
      if (btn) btn.classList.add('audio-playing');

      player.play()
        .catch(err => { console.warn('Audio playback error:', err); this.isPlaying = false; });

      player.onended = () => {
        this.isPlaying = false;
        if (btn) btn.classList.remove('audio-playing');
      };
      player.onerror = () => {
        this.isPlaying = false;
        console.error('Audio load error');
      };
    },

    // ── Answer ─────────────────────────────────────────────────────────────
    async submitAnswer(option) {
      if (this.answered || !this.currentQ) return;
      this.answered       = true;
      this.selectedAnswer = option;
      this.showHint       = false;

      const responseTime = (Date.now() - this._questionStart) / 1000;

      try {
        const res = await fetch(answerUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken':  this._csrfToken(),
          },
          body: JSON.stringify({
            question_index: this.currentIndex,
            answer:         option,
            response_time:  responseTime,
            question_data:  this.currentQ,
          }),
        });

        if (!res.ok) throw new Error('Network error');

        const data = await res.json();
        this.lastCorrect = data.is_correct;

        if (data.is_correct) {
          this.correct++;
          // Correct answer sound cue (visual flash)
          this._flashFeedback('correct');
        } else {
          this.wrong++;
          // Update correct_answer in case server provides canonical value
          if (data.correct_answer) {
            this.currentQ.correct_answer = data.correct_answer;
          }
          this._flashFeedback('wrong');
        }

        // Update explanation if server returned one
        if (data.explanation && this.currentQ) {
          this.currentQ.explanation = data.explanation;
        }

      } catch (err) {
        console.error('Answer submission error:', err);
        // Offline fallback: evaluate locally
        this.lastCorrect = (option === this.currentQ.correct_answer);
        if (this.lastCorrect) this.correct++; else this.wrong++;
      }
    },

    // ── Next question ──────────────────────────────────────────────────────
    async nextQuestion() {
      const isLast = this.currentIndex >= this.questions.length - 1;

      if (isLast) {
        await this._completeSession();
        return;
      }

      this.currentIndex++;
      this.currentQ        = this.questions[this.currentIndex];
      this.answered        = false;
      this.selectedAnswer  = null;
      this.lastCorrect     = false;
      this.showHint        = false;
      this._questionStart  = Date.now();

      // Auto-play next audio
      this.$nextTick(() => this.playAudio());
    },

    // ── Complete session ───────────────────────────────────────────────────
    async _completeSession() {
      clearInterval(this._timer);
      try {
        const res = await fetch(completeUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken':  this._csrfToken(),
          },
          body: JSON.stringify({
            correct:      this.correct,
            wrong:        this.wrong,
            total_time:   this.elapsed,
          }),
        });

        if (!res.ok) throw new Error('Complete request failed');

        const data = await res.json();
        if (data.redirect) {
          window.location.href = data.redirect;
        }
      } catch (err) {
        console.error('Session complete error:', err);
        // Fallback: go to training index
        window.location.href = '/training/';
      }
    },

    // ── Keyboard shortcuts ─────────────────────────────────────────────────
    selectOption(index) {
      if (this.answered || !this.currentQ) return;
      const opts = this.currentQ.options;
      if (opts && opts[index] !== undefined) {
        this.submitAnswer(opts[index]);
      }
    },

    // ── Helpers ────────────────────────────────────────────────────────────
    accuracy() {
      const total = this.correct + this.wrong;
      if (!total) return 0;
      return Math.round((this.correct / total) * 100);
    },

    modeLabel() {
      const labels = {
        notas:            'nota',
        intervalos:       'intervalo',
        escalas:          'escala',
        dictado_melodico: 'melodía',
        patrones_andinos: 'patrón',
        guabina:          'patrón de guabina',
        tiple:            'nota en tiple',
        requinto:         'nota en requinto',
        bandola:          'nota en bandola',
      };
      return labels[this.questions[0]?.mode] || 'respuesta';
    },

    formatTime(s) {
      const m = Math.floor(s / 60).toString().padStart(2, '0');
      const sec = (s % 60).toString().padStart(2, '0');
      return `${m}:${sec}`;
    },

    _csrfToken() {
      const meta = document.querySelector('meta[name="csrf-token"]');
      if (meta) return meta.content;
      // Try cookie
      const match = document.cookie.match(/csrf_token=([^;]+)/);
      return match ? match[1] : '';
    },

    _flashFeedback(type) {
      // Brief visual highlight on the answer area
      const el = document.querySelector('[data-feedback]');
      if (!el) return;
      el.classList.add(`feedback-${type}`);
      setTimeout(() => el.classList.remove(`feedback-${type}`), 600);
    },
  };
}
