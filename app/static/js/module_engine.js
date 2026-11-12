/**
 * SEMIMUS — motor de módulos (funciones puras, sin DOM).
 *
 * Reglas según "Estructura detallada de módulos SEMIMUS":
 *  - Cada módulo tiene Fase .1 (estudio aislado) y Fase .2 (reto acumulado).
 *  - La Fase .2 se desbloquea al completar la Fase .1.
 *  - El módulo N se desbloquea al superar el reto (Fase .2) del módulo N-1,
 *    con el umbral progression.passingPercent (modules_config.json).
 *  - El reto de un módulo usa sus propios elementos y los dominados del mismo
 *    grupo (simples, compuestos o escalas). Si hay menos de dos opciones, se
 *    incluye el siguiente módulo del grupo como distractor.
 *  - Las opciones del reto son como máximo 4 (correcta + 3 distractores).
 */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) {
    module.exports = api;
  } else {
    root.SemimusModules = api;
  }
})(typeof window !== 'undefined' ? window : globalThis, function () {
  const STUDY_LEVEL = 1;
  const CHALLENGE_LEVEL = 2;
  const MAX_OPTIONS = 4;
  const STUDY_COMPLETE_PCT = 100;

  const LETTERS = ['C', 'D', 'E', 'F', 'G', 'A', 'B'];
  const NATURAL_PC = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  // Ortografías posibles de cada clase de altura (sostenido o bemol).
  const SPELLINGS = [
    [['C', '']], [['C', '#'], ['D', 'b']], [['D', '']], [['D', '#'], ['E', 'b']],
    [['E', '']], [['F', '']], [['F', '#'], ['G', 'b']], [['G', '']],
    [['G', '#'], ['A', 'b']], [['A', '']], [['A', '#'], ['B', 'b']], [['B', '']],
  ];
  const SPANISH = { C: 'Do', D: 'Re', E: 'Mi', F: 'Fa', G: 'Sol', A: 'La', B: 'Si' };

  function progressKey(moduleId, level) {
    return `${moduleId}:${level}`;
  }

  function moduleById(modules, id) {
    return modules.find(item => item.id === id) || null;
  }

  function progressOf(progress, moduleId, level) {
    return Number((progress || {})[progressKey(moduleId, level)] || 0);
  }

  function isModuleUnlocked(modules, progress, moduleId, passingPercent) {
    if (moduleId === 0) return Boolean(moduleById(modules, 0));
    const previous = moduleById(modules, moduleId - 1);
    if (!previous || !moduleById(modules, moduleId)) return false;
    return progressOf(progress, previous.id, CHALLENGE_LEVEL) >= passingPercent;
  }

  function isLevelUnlocked(modules, progress, moduleId, level, passingPercent) {
    if (!isModuleUnlocked(modules, progress, moduleId, passingPercent)) return false;
    if (level === STUDY_LEVEL) return true;
    if (level === CHALLENGE_LEVEL) {
      return progressOf(progress, moduleId, STUDY_LEVEL) >= STUDY_COMPLETE_PCT;
    }
    return false;
  }

  function isLevelCompleted(progress, moduleId, level, passingPercent) {
    if (level === STUDY_LEVEL) return progressOf(progress, moduleId, STUDY_LEVEL) >= STUDY_COMPLETE_PCT;
    return progressOf(progress, moduleId, CHALLENGE_LEVEL) >= passingPercent;
  }

  function isModuleCompleted(progress, moduleId, passingPercent) {
    return isLevelCompleted(progress, moduleId, CHALLENGE_LEVEL, passingPercent);
  }

  /** Módulos que forman el pozo del reto de un módulo (mismo grupo, dominados + actual). */
  function challengePool(modules, moduleId) {
    const current = moduleById(modules, moduleId);
    if (!current) return [];
    const pool = modules
      .filter(item => item.group === current.group && item.id <= moduleId)
      .map(item => item.id);
    if (pool.length < 2 && current.group !== 'pitch') {
      const next = modules.find(item => item.group === current.group && item.id === moduleId + 1);
      if (next) pool.push(next.id);
    }
    return pool;
  }

  /** Mezcla de Fisher-Yates con generador inyectable (para pruebas). */
  function shuffle(list, random = Math.random) {
    const copy = [...list];
    for (let i = copy.length - 1; i > 0; i--) {
      const j = Math.floor(random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  /** Opciones del reto: la correcta y hasta MAX_OPTIONS-1 distractores del pozo. */
  function challengeOptions(pool, targetId, random = Math.random) {
    const others = shuffle(pool.filter(id => id !== targetId), random);
    return shuffle([targetId, ...others.slice(0, MAX_OPTIONS - 1)], random);
  }

  /** Objetivos de las preguntas del reto, cada uno con su pozo de opciones. */
  function challengeTargets(modules, moduleId, count, random = Math.random) {
    const pool = challengePool(modules, moduleId);
    if (!pool.length) return [];
    const targets = [];
    for (let i = 0; i < count; i++) {
      const targetId = pool[Math.floor(random() * pool.length)];
      targets.push({ targetId, options: challengeOptions(pool, targetId, random) });
    }
    return targets;
  }

  const TONOS = [
    'sin distancia (misma nota)', 'medio tono', '1 tono', '1 tono y medio', '2 tonos',
    '2 tonos y medio', '3 tonos', '3 tonos y medio', '4 tonos', '4 tonos y medio',
    '5 tonos', '5 tonos y medio', '6 tonos',
  ];

  /** Distancia en tonos y trastes para semitonos (trastes = semitonos). Compuestos: total en tonos. */
  function distanceLabel(semitones) {
    const n = Number(semitones);
    const trastes = `${n} ${n === 1 ? 'traste' : 'trastes'}`;
    if (n < TONOS.length) return `${TONOS[n]} (${trastes})`;
    const whole = Math.floor(n / 2);
    const tonos = n % 2 === 1 ? `${whole}½ tonos` : `${whole} tonos`;
    return `${tonos} (${trastes})`;
  }

  function spellWith(rootMidi, steps, focus, letter0, acc0) {
    const rootIndex = LETTERS.indexOf(letter0);
    const rootPc = NATURAL_PC[letter0] + (acc0 === '#' ? 1 : acc0 === 'b' ? -1 : 0);
    const notes = [];
    let cumulative = 0;
    const degrees = [0, ...steps];
    for (let i = 0; i < degrees.length; i++) {
      cumulative += degrees[i];
      const midi = rootMidi + cumulative;
      const letter = LETTERS[(rootIndex + i) % 7];
      const targetPc = (((rootPc + cumulative) % 12) + 12) % 12;
      let diff = (targetPc - NATURAL_PC[letter] + 12) % 12;
      if (diff > 6) diff -= 12;
      if (Math.abs(diff) > 1) return null;
      const accidental = diff === 0 ? '' : diff === 1 ? '#' : 'b';
      const octave = Math.floor((midi - diff) / 12) - 1;
      notes.push({
        pitch: letter,
        octave,
        accidental,
        scientific_name: `${letter}${accidental}${octave}`,
        spanish_name: `${SPANISH[letter]}${accidental} ${octave}`,
        midi,
        focus: focus.includes(i),
      });
    }
    return notes;
  }

  /**
   * Escribe una escala desde la raíz (MIDI) con sus pasos en semitonos: 8 notas
   * (grado 1 a 8). Prueba cada ortografía de la raíz y usa la primera que no
   * necesite doble alteración. Devuelve null si ninguna sirve.
   */
  function spellScale(rootMidi, steps, focus = []) {
    const root = Math.round(Number(rootMidi));
    const pc = ((root % 12) + 12) % 12;
    for (const [letter, acc] of SPELLINGS[pc]) {
      const notes = spellWith(root, steps, focus, letter, acc);
      if (notes) return notes;
    }
    return null;
  }

  return {
    STUDY_LEVEL,
    CHALLENGE_LEVEL,
    MAX_OPTIONS,
    progressKey,
    isModuleUnlocked,
    isLevelUnlocked,
    isLevelCompleted,
    isModuleCompleted,
    challengePool,
    challengeOptions,
    challengeTargets,
    distanceLabel,
    spellScale,
    shuffle,
  };
});
