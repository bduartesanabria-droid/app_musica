/**
 * SENAFÓNICA Audio Engine — Web Audio API & Sample Player
 *
 * Provides:
 * 1. High-precision Web Audio API scheduling for scales and intervals.
 * 2. Uniform 2-second teaching notes with a smooth release so resonance stays audible.
 * 3. 3 interval directions: Ascendente, Descendente, Intercalada/Aleatoria.
 * 4. Realistic acoustic synthesis for Colombian folk instruments:
 *    - Tiple (12-string triple orders, metallic chorus shimmer)
 *    - Requinto (crisp, brilliant, high-attack lead plucking)
 *    - Bandola (steel-string plectrum strike, rich folk timbre)
 *    - Guitarra (warm classical base)
 * 5. Direct sample loading and slicing from server catalog.
 * 6. Interactive auditory comparison (Chosen vs Correct interval).
 * 7. Feedback SFX (Celebration arpeggio, error buzz, heart lost, life restored).
 */

class SenafonicaAudioEngine {
  constructor(catalog = {}) {
    this.catalog = catalog; // { "Tiple": [...], "Requinto": [...], ... }
    this.ctx = null;
    this.sampleCache = new Map(); // url -> AudioBuffer
    this.sampleOffsets = new Map(); // url -> first audible sample offset
    this.loadingPromises = new Map();
    this.normalizedGains = new WeakMap();
    this.activeNodes = [];
    this.activeMedia = new Set();
    this.isPlaying = false;
    this.playToken = 0;

    // Teaching tempo: every note rings for 2 seconds with even spacing
    this.scaleNoteDuration = 2.0;
    this.scaleNoteGap = 0.1;
    this.intervalNoteDuration = 2.0;
    this.intervalNoteGap = 0.5;
    this.releaseTime = 0.4;        // Gentle fade so the string resonance is not cut off

    // MIDI Note name map
    this.NOTE_NAMES = ["DO", "DO#", "RE", "RE#", "MI", "FA", "FA#", "SOL", "SOL#", "LA", "LA#", "SI"];
  }

  // Ensure AudioContext is initialized on user interaction
  async initContext() {
    if (!this.ctx) {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioCtx();
    }
    if (this.ctx.state === "suspended") {
      await this.ctx.resume();
    }
    return this.ctx;
  }

  // Preload an audio sample URL to AudioBuffer
  async preloadSample(url) {
    if (!url) return null;
    if (this.sampleCache.has(url)) return this.sampleCache.get(url);
    if (this.loadingPromises.has(url)) return this.loadingPromises.get(url);

    const promise = (async () => {
      try {
        await this.initContext();
        const response = await fetch(url);
        if (!response.ok) return null;
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await this.ctx.decodeAudioData(arrayBuffer);
        this.sampleCache.set(url, audioBuffer);
        this.sampleOffsets.set(url, this._findSampleOffset(audioBuffer));
        return audioBuffer;
      } catch (err) {
        console.warn("Could not preload sample:", url, err);
        return null;
      } finally {
        this.loadingPromises.delete(url);
      }

    })();

    this.loadingPromises.set(url, promise);
    return promise;
  }

  async preloadNotes(instrument, midis) {
    const urls = [...new Set(midis.map(midi => this.getSampleUrl(instrument, midi)).filter(Boolean))];
    await Promise.all(urls.map(url => this.preloadSample(url)));
  }

  _findSampleOffset(buffer) {
    const frameSize = Math.max(1, Math.floor(buffer.sampleRate * 0.01));
    const threshold = 10 ** (-45 / 20);
    const channels = Array.from(
      { length: buffer.numberOfChannels },
      (_, channel) => buffer.getChannelData(channel)
    );
    const frameCount = Math.ceil(buffer.length / frameSize);

    for (let frame = 0; frame < frameCount - 1; frame++) {
      let energy = 0;
      let sampleCount = 0;
      for (const channel of channels) {
        const start = frame * frameSize;
        const end = Math.min(start + frameSize, channel.length);
        for (let index = start; index < end; index++) {
          energy += channel[index] * channel[index];
          sampleCount++;
        }
      }
      const rms = Math.sqrt(energy / Math.max(1, sampleCount));
      if (rms < threshold) continue;

      let nextEnergy = 0;
      let nextSampleCount = 0;
      for (const channel of channels) {
        const start = (frame + 1) * frameSize;
        const end = Math.min(start + frameSize, channel.length);
        for (let index = start; index < end; index++) {
          nextEnergy += channel[index] * channel[index];
          nextSampleCount++;
        }
      }
      if (Math.sqrt(nextEnergy / Math.max(1, nextSampleCount)) >= threshold) {
        return Math.max(0, frame * frameSize / buffer.sampleRate - 0.02);
      }
    }

    return 0;
  }

  // Find sample URL from catalog
  getSampleUrl(instrument, midi) {
    if (!this.catalog) return null;
    const instKey = Object.keys(this.catalog).find(
      k => k.toLowerCase() === (instrument || "").toLowerCase()
    );
    if (!instKey || !this.catalog[instKey]) return null;
    const match = this.catalog[instKey].find(item => item.midi === midi);
    return match ? match.stream_url : null;
  }

  // Convert MIDI note number to frequency in Hz
  midiToFreq(midi) {
    return 440 * Math.pow(2, (midi - 69) / 12);
  }

  // Convert MIDI note number to Note Name (e.g. DO4, SOL#3)
  midiToName(midi) {
    const note = this.NOTE_NAMES[midi % 12];
    const octave = Math.floor(midi / 12) - 1;
    return `${note}${octave}`;
  }

  // Stop all actively playing sounds
  stop() {
    this.playToken++;
    this.isPlaying = false;
    const nodes = this.activeNodes;
    this.activeNodes = [];
    for (const node of nodes) {
      try {
        if (node.stop) node.stop();
        if (node.disconnect) node.disconnect();
      } catch (e) {
        // Ignored
      }
    }
    for (const media of this.activeMedia) {
      media.pause();
    }
    this.activeMedia.clear();
  }

  /**
   * Plays a single note with a natural, resonant sustain.
   * If a real sample exists, uses the AudioBuffer with a gentle release envelope.
   * Otherwise uses high-fidelity Colombian folk synthesis.
   */
  async playNote(instrument, midi, startTime = 0, duration = 0.5, volume = 0.9) {
    await this.initContext();
    const ctx = this.ctx;
    const now = startTime || ctx.currentTime;

    const sampleUrl = this.getSampleUrl(instrument, midi);
    let buffer = sampleUrl ? this.sampleCache.get(sampleUrl) : null;
    if (!buffer && sampleUrl) {
      buffer = await this.preloadSample(sampleUrl);
    }

    if (buffer) {
      return this._playSampleBuffer(
        buffer,
        now,
        duration,
        volume,
        this.sampleOffsets.get(sampleUrl) || 0
      );
    }

    if (sampleUrl && await this._playHtmlSample(sampleUrl, now, duration, volume)) {
      return now + duration;
    }

    return this._synthesizeFolkNote(instrument, midi, now, duration, volume);
  }

  async _playHtmlSample(url, startTime, duration, volume) {
    if (typeof Audio === "undefined") return false;

    const media = new Audio(url);
    media.preload = "auto";
    media.volume = Math.max(0, Math.min(1, volume));
    this.activeMedia.add(media);

    let startTimer;
    let stopTimer;
    let settled = false;
    let resolvePlayback;
    const playback = new Promise(resolve => {
      resolvePlayback = resolve;
    });
    const cleanup = () => {
      clearTimeout(startTimer);
      clearTimeout(stopTimer);
      media.onended = null;
      media.onerror = null;
      this.activeMedia.delete(media);
      this.activeNodes = this.activeNodes.filter(node => node !== controller);
    };
    const controller = {
      stop: () => {
        cleanup();
        media.pause();
        if (!settled) {
          settled = true;
          resolvePlayback(false);
        }
      },
    };
    this.activeNodes.push(controller);

    media.onended = cleanup;
    media.onerror = () => {
      cleanup();
      if (!settled) {
        settled = true;
        resolvePlayback(false);
      }
    };

    startTimer = setTimeout(async () => {
      if (settled) return;
      try {
        await media.play();
        if (settled) return;
        settled = true;
        resolvePlayback(true);
        stopTimer = setTimeout(() => controller.stop(), Math.max(0.1, duration) * 1000);
      } catch (error) {
        cleanup();
        console.warn("Could not play database audio sample:", url, error);
        if (!settled) {
          settled = true;
          resolvePlayback(false);
        }
      }
    }, Math.max(0, (startTime - this.ctx.currentTime) * 1000));

    return playback;
  }

  /**
   * Sample playback that preserves the instrument's natural resonance.
   * Standard sample tail has ~1.8-2.5s; we ramp down quickly to simulate live execution.
   */
  _playSampleBuffer(buffer, startTime, duration, volume, sampleOffset = 0) {
    const ctx = this.ctx;
    const source = ctx.createBufferSource();
    source.buffer = buffer;

    const gainNode = ctx.createGain();
    const normalizedGain = this._getNormalizedGain(buffer, sampleOffset);
    const outputGain = Math.max(0, Math.min(1, volume)) * normalizedGain;
    const stopTime = startTime + Math.max(0.05, duration);
    const attackEnd = Math.min(startTime + 0.01, stopTime - 0.02);
    const release = Math.min(this.releaseTime, Math.max(0.08, duration * 0.6));
    const fadeStart = Math.max(attackEnd, stopTime - release);

    gainNode.gain.setValueAtTime(0.0001, startTime);
    gainNode.gain.linearRampToValueAtTime(outputGain, attackEnd);
    gainNode.gain.setValueAtTime(outputGain, fadeStart);
    gainNode.gain.exponentialRampToValueAtTime(0.0001, stopTime);

    source.connect(gainNode);
    gainNode.connect(ctx.destination);

    source.start(startTime, Math.min(sampleOffset, Math.max(0, buffer.duration - 0.01)));
    source.stop(stopTime);

    this.activeNodes.push(source);
    return stopTime;
  }

  _getNormalizedGain(buffer, sampleOffset) {
    if (this.normalizedGains.has(buffer)) return this.normalizedGains.get(buffer);
    const sampleRate = buffer.sampleRate;
    const start = Math.min(buffer.length - 1, Math.floor(sampleOffset * sampleRate));
    const end = Math.min(buffer.length, start + Math.floor(sampleRate * 0.5));
    let squareSum = 0;
    let peak = 0;
    let count = 0;
    for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
      const samples = buffer.getChannelData(channel);
      for (let index = start; index < end; index++) {
        const value = Math.abs(samples[index]);
        squareSum += value * value;
        peak = Math.max(peak, value);
        count++;
      }
    }
    const rms = Math.sqrt(squareSum / Math.max(count, 1));
    const gain = Math.min(4, 0.18 / Math.max(rms, 0.01), 0.85 / Math.max(peak, 0.01));
    this.normalizedGains.set(buffer, gain);
    return gain;
  }

  /**
   * High-fidelity physical modeling synthesis of Colombian instruments.
   */
  _synthesizeFolkNote(instrument, midi, startTime, duration, volume) {
    const ctx = this.ctx;
    const freq = this.midiToFreq(midi);
    const inst = (instrument || "Tiple").toLowerCase();

    const masterGain = ctx.createGain();
    masterGain.gain.setValueAtTime(0.0001, startTime);
    masterGain.gain.linearRampToValueAtTime(volume, startTime + 0.008); // Sharp plectrum attack
    masterGain.gain.exponentialRampToValueAtTime(0.001, startTime + duration);
    masterGain.connect(ctx.destination);

    if (inst.includes("tiple")) {
      // Tiple: 4 orders of 3 strings (chorus detune + metallic ringing)
      const detunes = [-4, 0, +4];
      detunes.forEach((detune, idx) => {
        const osc = ctx.createOscillator();
        osc.type = idx === 1 ? "sawtooth" : "triangle";
        osc.frequency.setValueAtTime(freq, startTime);
        osc.detune.setValueAtTime(detune, startTime);

        const filter = ctx.createBiquadFilter();
        filter.type = "bandpass";
        filter.frequency.setValueAtTime(freq * 2.2, startTime);
        filter.Q.setValueAtTime(2.0, startTime);

        const plectrumNoise = this._createPlectrumClick(startTime);

        osc.connect(filter);
        filter.connect(masterGain);
        if (plectrumNoise) plectrumNoise.connect(masterGain);

        osc.start(startTime);
        osc.stop(startTime + duration + 0.05);
        this.activeNodes.push(osc);
      });
    } else if (inst.includes("requinto")) {
      // Requinto: bright, high-pitch nylon attack, quick overtone decay
      const osc = ctx.createOscillator();
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(freq, startTime);

      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(freq * 3.8, startTime);
      filter.frequency.exponentialRampToValueAtTime(freq * 1.5, startTime + duration);

      osc.connect(filter);
      filter.connect(masterGain);

      osc.start(startTime);
      osc.stop(startTime + duration + 0.05);
      this.activeNodes.push(osc);
    } else if (inst.includes("bandola")) {
      // Bandola: 6 orders of steel strings, percussive plectrum stroke
      [-2.5, +2.5].forEach(detune => {
        const osc = ctx.createOscillator();
        osc.type = "triangle";
        osc.frequency.setValueAtTime(freq, startTime);
        osc.detune.setValueAtTime(detune, startTime);

        const filter = ctx.createBiquadFilter();
        filter.type = "peaking";
        filter.frequency.setValueAtTime(1400, startTime);
        filter.gain.setValueAtTime(8, startTime);

        osc.connect(filter);
        filter.connect(masterGain);

        osc.start(startTime);
        osc.stop(startTime + duration + 0.05);
        this.activeNodes.push(osc);
      });
    } else {
      // Classical guitar: warm triangular fundamental
      const osc = ctx.createOscillator();
      osc.type = "triangle";
      osc.frequency.setValueAtTime(freq, startTime);

      const filter = ctx.createBiquadFilter();
      filter.type = "lowpass";
      filter.frequency.setValueAtTime(freq * 2.0, startTime);

      osc.connect(filter);
      filter.connect(masterGain);

      osc.start(startTime);
      osc.stop(startTime + duration + 0.05);
      this.activeNodes.push(osc);
    }

    return startTime + duration;
  }

  // Generates brief noise pulse simulating a plectrum (púa) striking the string
  _createPlectrumClick(startTime) {
    if (!this.ctx) return null;
    const bufferSize = this.ctx.sampleRate * 0.012; // 12ms noise click
    const buffer = this.ctx.createBuffer(1, bufferSize, this.ctx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      data[i] = (Math.random() * 2 - 1) * Math.exp(-i / (bufferSize * 0.3));
    }
    const noise = this.ctx.createBufferSource();
    noise.buffer = buffer;

    const gain = this.ctx.createGain();
    gain.gain.setValueAtTime(0.35, startTime);
    gain.gain.exponentialRampToValueAtTime(0.001, startTime + 0.012);
    noise.connect(gain);
    noise.start(startTime);
    this.activeNodes.push(noise);
    return gain;
  }

  /**
   * NÚCLEO 1: INTERVAL PLAYER
   * Plays two notes in the chosen direction (ascendente, descendente, intercalada).
   *
   * @param {string} instrument - 'Tiple', 'Requinto', 'Bandola', etc.
   * @param {number} rootMidi - e.g. 60 (DO4)
   * @param {number} semitones - distance in semitones (0 to 12)
   * @param {string} direction - 'ascendente', 'descendente', 'intercalada'
   * @param {function} onNoteCallback - (noteIndex, midi, noteName)
   */
  async playInterval(instrument, rootMidi, semitones, direction = "ascendente", onNoteCallback = null) {
    this.stop();
    const token = this.playToken;
    this.isPlaying = true;
    await this.initContext();

    let note1Midi, note2Midi;
    const effectiveDir = direction.toLowerCase();

    if (effectiveDir === "descendente") {
      note1Midi = rootMidi + semitones;
      note2Midi = rootMidi;
    } else if (effectiveDir === "intercalada" || effectiveDir === "aleatoria") {
      // Randomly choose ascending or descending for true ear training
      const isAsc = Math.random() > 0.5;
      note1Midi = isAsc ? rootMidi : rootMidi + semitones;
      note2Midi = isAsc ? rootMidi + semitones : rootMidi;
    } else {
      // Ascendente (default)
      note1Midi = rootMidi;
      note2Midi = rootMidi + semitones;
    }

    const dur = this.intervalNoteDuration;
    const gap = this.intervalNoteGap;

    // Note 1
    if (onNoteCallback) onNoteCallback(0, note1Midi, this.midiToName(note1Midi));
    await this.playNote(instrument, note1Midi, 0, dur, 0.95);

    await new Promise(res => setTimeout(res, (dur + gap) * 1000));
    if (token !== this.playToken) return;

    // Note 2
    if (onNoteCallback) onNoteCallback(1, note2Midi, this.midiToName(note2Midi));
    await this.playNote(instrument, note2Midi, 0, dur, 0.95);

    await new Promise(res => setTimeout(res, (dur + gap) * 1000));
    if (token === this.playToken) {
      this.isPlaying = false;
      if (onNoteCallback) onNoteCallback(-1, null, null);
    }
  }

  /**
   * NÚCLEO 2: SCALE PLAYER
   * Plays the full scale at a steady teaching tempo: each note rings for 2 seconds
   * so the student can hear the instrument's resonance before the next one starts.
   *
   * @param {string} instrument - 'Tiple', 'Requinto', 'Bandola'
   * @param {number} rootMidi - Root note (e.g. 55 or 60)
   * @param {Array<number>} pattern - e.g. [2, 2, 1, 2, 2, 2, 1] for Major
   * @param {number} tempoMultiplier - 1.0 = normal, 1.3 = fast
   * @param {function} onNoteCallback - (noteIndex, midi, noteName, totalNotes)
   */
  async playScale(instrument, rootMidi, pattern, tempoMultiplier = 1.0, onNoteCallback = null) {
    this.stop();
    const token = this.playToken;
    this.isPlaying = true;
    await this.initContext();

    // Compute all MIDI notes in the scale
    const notes = [rootMidi];
    let current = rootMidi;
    for (const step of pattern) {
      current += step;
      notes.push(current);
    }

    const noteDuration = this.scaleNoteDuration / tempoMultiplier;
    const gap = this.scaleNoteGap / tempoMultiplier;

    for (let i = 0; i < notes.length; i++) {
      if (token !== this.playToken) return;
      const midi = notes[i];
      if (onNoteCallback) onNoteCallback(i, midi, this.midiToName(midi), notes.length);

      await this.playNote(instrument, midi, 0, noteDuration, 0.95);
      // Wait exactly for the next note without gap
      await new Promise(res => setTimeout(res, (noteDuration + gap) * 1000));
    }

    if (token === this.playToken) {
      this.isPlaying = false;
      if (onNoteCallback) onNoteCallback(-1, null, null, notes.length);
    }
  }

  /**
   * AUDITORY COMPARISON (Chosen vs Correct Interval)
   * Plays the student's selected interval, pauses briefly, then plays the correct interval.
   */
  async playComparison(instrument, rootMidi, chosenSemitones, correctSemitones, onPhaseChange = null) {
    this.stop();
    const token = this.playToken;
    this.isPlaying = true;

    // Phase 1: Chosen
    if (onPhaseChange) onPhaseChange("chosen");
    await this.playInterval(instrument, rootMidi, chosenSemitones, "ascendente");
    await new Promise(res => setTimeout(res, 600));
    if (token !== this.playToken) return;

    // Phase 2: Pause / transition
    if (onPhaseChange) onPhaseChange("transition");
    await new Promise(res => setTimeout(res, 400));
    if (token !== this.playToken) return;

    // Phase 3: Correct
    if (onPhaseChange) onPhaseChange("correct");
    await this.playInterval(instrument, rootMidi, correctSemitones, "ascendente");

    if (token === this.playToken) {
      this.isPlaying = false;
      if (onPhaseChange) onPhaseChange("idle");
    }
  }

  // ── SOUND EFFECTS (SFX) ───────────────────────────────────────────────────

  // Success arpeggio (harmonic celebration)
  async playSuccessSound() {
    await this.initContext();
    const notes = [60, 64, 67, 72, 76]; // C4, E4, G4, C5, E5
    const now = this.ctx.currentTime;
    notes.forEach((midi, i) => {
      this.playNote("Tiple", midi, now + i * 0.08, 0.45, 0.85);
    });
  }

  // Dissonant sound on wrong answer
  async playErrorSound() {
    await this.initContext();
    const now = this.ctx.currentTime;
    // Dissonant low chord
    this.playNote("Guitarra", 45, now, 0.35, 0.8);
    this.playNote("Guitarra", 46, now, 0.35, 0.7);
  }

  // Life lost heart pluck
  async playLifeLostSound() {
    await this.initContext();
    const now = this.ctx.currentTime;
    this.playNote("Requinto", 63, now, 0.25, 0.7);
    this.playNote("Requinto", 59, now + 0.12, 0.4, 0.8);
  }

  // Life restored / bonus chime
  async playLifeRestoredSound() {
    await this.initContext();
    const notes = [67, 71, 74, 79]; // G4, B4, D5, G5
    const now = this.ctx.currentTime;
    notes.forEach((midi, i) => {
      this.playNote("Bandola", midi, now + i * 0.09, 0.5, 0.85);
    });
  }

  // Level completed fanfare
  async playLevelCompleteSound() {
    await this.initContext();
    const notes = [60, 64, 67, 72, 72, 76];
    const delays = [0, 0.1, 0.2, 0.32, 0.45, 0.6];
    const now = this.ctx.currentTime;
    notes.forEach((midi, i) => {
      this.playNote("Tiple", midi, now + delays[i], 0.6, 0.9);
    });
  }
}

// Attach globally
window.SenafonicaAudioEngine = SenafonicaAudioEngine;
