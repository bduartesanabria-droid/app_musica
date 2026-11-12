/**
 * SEMIMUS Score Renderer — widget de partituras (VexFlow).
 *
 * Implementa la especificación técnica de renderizado de partituras:
 *  - Pentagrama estándar de 5 líneas y 4 espacios en clave de Sol.
 *  - Guitarra clásica: clave de Sol octavada baja ("8" bajo la clave) y
 *    escritura una octava superior a la altura real.
 *  - Padding vertical dinámico para que las líneas adicionales de las
 *    notas extremas (E2 de la guitarra, G6 de la bandola) nunca se corten.
 *  - Nomenclatura en la parte inferior de cada nota (ej. Do 4 / C4).
 *  - Diagrama de diapasón por nota (cuerda, traste y dedo), al estilo de
 *    los diagramas de acordes, para que el estudiante imite la posición.
 *
 * API:
 *  - SemimusScore.render(container, payload)      → dibuja desde un payload
 *  - SemimusScore.renderNotes(container, instrument, midis, intervalType)
 *  - SemimusScore.buildPayload(instrument, midis, intervalType)
 *  - SemimusScore.noteInfoFromMidi(midi)
 *
 * Estructura del payload (especificación de partituras):
 *  {
 *    "instrument": "bandola",
 *    "interval_type": "5_justa_ascendente",
 *    "notation_display": {
 *      "clef": "treble",
 *      "clef_annotation": "8vb" | "",
 *      "written_shift": 0 | 12,
 *      "notes": [{ "pitch": "F", "octave": 3, "accidental": "#",
 *                  "scientific_name": "F#3", "spanish_name": "Fa# 3" }]
 *    }
 *  }
 */
const SemimusScore = (() => {
  const SHARP_PITCHES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
  const SPANISH_PITCHES = ['Do', 'Do#', 'Re', 'Re#', 'Mi', 'Fa', 'Fa#', 'Sol', 'Sol#', 'La', 'La#', 'Si'];
  const SEMITONE_OF_LETTER = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
  const STEP_OF_LETTER = { C: 0, D: 1, E: 2, F: 3, G: 4, A: 5, B: 6 };

  // Directrices de renderizado por instrumento (especificación de partituras).
  const INSTRUMENT_NOTATION = {
    guitarra: { clef: 'treble', clefAnnotation: '8vb', writtenShift: 12 },
    tiple: { clef: 'treble', clefAnnotation: '', writtenShift: 0 },
    requinto: { clef: 'treble', clefAnnotation: '', writtenShift: 0 },
    bandola: { clef: 'treble', clefAnnotation: '', writtenShift: 0 },
  };
  const DEFAULT_NOTATION = { clef: 'treble', clefAnnotation: '', writtenShift: 0 };

  function instrumentNotation(instrument) {
    return INSTRUMENT_NOTATION[String(instrument || '').trim().toLowerCase()] || DEFAULT_NOTATION;
  }

  function noteInfoFromMidi(midi) {
    const index = ((Math.round(Number(midi)) % 12) + 12) % 12;
    const octave = Math.floor(Math.round(Number(midi)) / 12) - 1;
    const pitch = SHARP_PITCHES[index];
    return {
      pitch: pitch[0],
      octave,
      accidental: pitch.endsWith('#') ? '#' : '',
      scientific_name: `${pitch}${octave}`,
      spanish_name: `${SPANISH_PITCHES[index]} ${octave}`,
    };
  }

  function midiOfNote(note) {
    const match = /^([A-G])(#|b)?(-?\d+)$/.exec(String(note.scientific_name || ''));
    if (!match) return null;
    let midi = (parseInt(match[3], 10) + 1) * 12 + SEMITONE_OF_LETTER[match[1].toUpperCase()];
    if (match[2] === '#') midi += 1;
    else if (match[2] === 'b') midi -= 1;
    return midi;
  }

  // Afinación de cada instrumento: MIDI de cada cuerda al aire, de la más
  // grave a la más aguda. La guitarra usa afinación estándar (E A D G B E);
  // las demás son referencias por orden a confirmar con el profesor.
  const TUNINGS = {
    guitarra: { strings: [40, 45, 50, 55, 59, 64] },  // Mi2 La2 Re3 Sol3 Si3 Mi4
    tiple: { strings: [48, 53, 57, 62] },             // Do3 Fa3 La3 Re4
    requinto: { strings: [60, 65, 69, 74] },          // Do4 Fa4 La4 Re5
    bandola: { strings: [55, 62, 69, 76] },           // Sol3 Re4 La4 Mi5
  };
  const MAX_FRET = 15;
  const DIAGRAM_FRETS = 4;
  // Bandera única: mientras un maestro de cuerdas pulsadas no valide las
  // afinaciones de tiple, requinto y bandola, sus diagramas de posición
  // (traste y dedo) quedan ocultos. Cambiar a true para reactivarlos.
  // La guitarra no depende de esta bandera.
  const TUNINGS_VALIDATED = false;
  const UNVALIDATED_NOTICE = 'Diagrama en revisión: pendiente de validación por un maestro de cuerdas pulsadas';

  function instrumentKey(instrument) {
    return String(instrument || '').trim().toLowerCase();
  }

  function tuningFor(instrument) {
    return TUNINGS[instrumentKey(instrument)] || null;
  }

  /*
   * findFingering(instrument, scientificPitch) — regla de digitación.
   * Pendiente de validación del Prof. Ricardo Figueroa.
   *
   * 1. Recorre todas las cuerdas (órdenes) donde la nota existe dentro de
   *    TUNINGS y del traste máximo visible del instrumento.
   * 2. Prefiere la primera posición: un traste entre 1 y 4 (dedo = traste).
   *    Entre esas opciones elige la de menor traste.
   * 3. Si ninguna cae en primera posición, usa la posición más baja posible:
   *    position = traste del dedo 1 y finger = traste - position + 1 (1 a 4).
   * 4. Cuerda al aire (traste 0): finger = 0.
   * En intervalos, options.handPosition es la posición de la nota anterior:
   * si alguna opción de esta nota cae en esa misma posición, se usa esa.
   */
  function findFingering(instrument, scientificPitch, options = {}) {
    const tuning = tuningFor(instrument);
    const midi = midiOfScientific(scientificPitch);
    if (!tuning || midi === null) return null;
    const maxFret = MAX_FRET;
    const candidates = [];
    tuning.strings.forEach((open, index) => {
      const fret = midi - open;
      if (fret < 0 || fret > maxFret) return;
      if (fret <= DIAGRAM_FRETS) {
        candidates.push({ string: index, fret, finger: fret, position: 1 });
      } else {
        const position = fret - (DIAGRAM_FRETS - 1);
        candidates.push({ string: index, fret, finger: fret - position + 1, position });
      }
    });
    if (!candidates.length) return null;

    const pick = list => list.reduce((a, b) => (b.fret < a.fret ? b : a));
    if (Number.isInteger(options.handPosition)) {
      const sameHand = candidates.filter(c => c.position === options.handPosition);
      if (sameHand.length) return pick(sameHand);
    }
    const inFirst = candidates.filter(c => c.position === 1);
    return pick(inFirst.length ? inFirst : candidates);
  }

  // Trastes visibles por instrumento en el diapasón (configurable aquí).
  // Nunca menos de 4, para que quepan las cuatro posiciones de los dedos.
  const VISIBLE_FRETS = { guitarra: 5, tiple: 5, requinto: 5, bandola: 5 };
  function visibleFretsFor(instrument) {
    return Math.max(DIAGRAM_FRETS, VISIBLE_FRETS[instrumentKey(instrument)] || 5);
  }

  // Modo de revisión: ?revision=1 con sesión de administrador (window.SEMIMUS_REVIEW_MODE).
  function reviewMode() {
    return typeof window !== 'undefined' && window.SEMIMUS_REVIEW_MODE === true;
  }

  function midiOfScientific(scientificPitch) {
    return midiOfNote({ scientific_name: scientificPitch });
  }

  function stringName(open) {
    return SPANISH_PITCHES[((open % 12) + 12) % 12];
  }

  // Diagrama de diapasón al estilo de los diagramas de acordes: cuerdas
  // graves a la izquierda, X en las cuerdas que no se tocan, O en la cuerda
  // al aire y el punto con el número del dedo en el traste.
  function diagramSvg(stringCount, fingering, rows, label) {
    const gap = 18;
    const left = 24;
    const top = 22;
    const rowHeight = 20;
    const gridBottom = top + rows * rowHeight;
    const width = left + (stringCount - 1) * gap + 14;
    const height = gridBottom + 18;
    const start = Math.max(1, fingering.position);
    const x = index => left + index * gap;
    const parts = [];

    for (let index = 0; index < stringCount; index++) {
      if (index !== fingering.string) {
        parts.push(`<text x="${x(index)}" y="10" text-anchor="middle" dominant-baseline="central" font-size="11" font-weight="700" fill="#1E293B">×</text>`);
      } else if (fingering.fret === 0) {
        parts.push(`<circle cx="${x(index)}" cy="10" r="5" fill="none" stroke="#1E293B" stroke-width="1.6"/>`);
        parts.push(`<text x="${x(index)}" y="10" text-anchor="middle" dominant-baseline="central" font-size="6" font-weight="700" fill="#1E293B">0</text>`);
      }
      parts.push(`<line x1="${x(index)}" y1="${top}" x2="${x(index)}" y2="${gridBottom}" stroke="#1E293B" stroke-width="1"/>`);
      parts.push(`<text x="${x(index)}" y="${gridBottom + 12}" text-anchor="middle" font-size="8" fill="#475569">${stringCount - index}</text>`);
    }

    for (let line = 0; line <= rows; line++) {
      const y = top + line * rowHeight;
      const nut = line === 0 && start === 1;
      parts.push(`<line x1="${x(0)}" y1="${y}" x2="${x(stringCount - 1)}" y2="${y}" stroke="#1E293B" stroke-width="${nut ? 4 : 1}"/>`);
    }

    // Número de cada traste visible, a la izquierda de la cuerda grave.
    for (let row = 0; row < rows; row++) {
      const cy = top + row * rowHeight + rowHeight / 2;
      parts.push(`<text x="${left - 9}" y="${cy}" text-anchor="middle" dominant-baseline="central" font-size="9" font-weight="700" fill="#1E293B">${start + row}</text>`);
    }

    if (fingering.fret > 0) {
      const row = fingering.fret - start;
      const cy = top + row * rowHeight + rowHeight / 2;
      parts.push(`<circle cx="${x(fingering.string)}" cy="${cy}" r="7" fill="#1E293B"/>`);
      parts.push(`<text x="${x(fingering.string)}" y="${cy}" text-anchor="middle" dominant-baseline="central" font-size="9" font-weight="700" fill="#FFFFFF">${fingering.finger}</text>`);
    }

    return `<svg viewBox="0 0 ${width} ${height}" xmlns="http://www.w3.org/2000/svg" font-family="Arial, sans-serif" role="img" aria-label="${label}">${parts.join('')}</svg>`;
  }

  // Tonos del documento de módulos (trastes = semitonos en los simples).
  const TONOS_BY_SEMITONES = [
    'sin distancia (misma nota)', 'medio tono', '1 tono', '1 tono y medio', '2 tonos',
    '2 tonos y medio', '3 tonos', '3 tonos y medio', '4 tonos', '4 tonos y medio',
    '5 tonos', '5 tonos y medio', '6 tonos',
  ];

  function distanceText(midiA, midiB) {
    const semitones = Math.abs(midiB - midiA);
    let tonos;
    if (semitones < TONOS_BY_SEMITONES.length) {
      tonos = TONOS_BY_SEMITONES[semitones];
    } else {
      // Compuestos: octava justa + simple (p. ej. novena menor = 6 tonos + medio tono).
      const rest = semitones - 12;
      tonos = rest === 0 ? '6 tonos' : `6 tonos + ${TONOS_BY_SEMITONES[rest]}`;
    }
    return `Distancia: ${tonos} (${semitones} ${semitones === 1 ? 'traste' : 'trastes'})`;
  }

  // Panel de diapasón: una figura por nota. En intervalos, la segunda nota usa
  // la misma posición de la mano que la primera cuando es posible.
  function buildFingering(instrument, notes) {
    const tuning = tuningFor(instrument);
    if (!tuning) return null;
    const key = instrumentKey(instrument);
    const validated = TUNINGS_VALIDATED || key === 'guitarra';
    const review = !validated && reviewMode();
    const block = document.createElement('div');
    block.className = 'semimus-fingering';
    const labelled = notes.length > 1;
    let hand = null;

    notes.forEach((note, index) => {
      const figure = document.createElement('figure');
      figure.className = 'semimus-diagram';
      const title = document.createElement('p');
      title.className = 'semimus-diagram-title';
      title.textContent = labelled ? `Nota ${index + 1} · ${note.scientific_name}` : note.scientific_name;
      figure.appendChild(title);

      if (!validated && !review) {
        const notice = document.createElement('p');
        notice.className = 'semimus-diagram-text';
        notice.textContent = UNVALIDATED_NOTICE;
        figure.appendChild(notice);
        block.appendChild(figure);
        return;
      }

      if (review) {
        const badge = document.createElement('p');
        badge.className = 'semimus-diagram-badge';
        badge.textContent = 'SIN VALIDAR';
        figure.appendChild(badge);
      }

      const fingering = findFingering(instrument, note.scientific_name,
        hand === null ? {} : { handPosition: hand });
      const text = document.createElement('p');
      text.className = 'semimus-diagram-text';
      text.setAttribute('aria-live', 'polite');
      if (!fingering) {
        text.textContent = 'Sin posición en esta afinación';
        figure.appendChild(text);
        block.appendChild(figure);
        return;
      }
      if (index === 0) hand = fingering.position;

      const number = tuning.strings.length - fingering.string;
      const label = `${note.scientific_name}: cuerda ${number}, traste ${fingering.fret}, dedo ${fingering.finger}`;
      const svgHost = document.createElement('div');
      svgHost.innerHTML = diagramSvg(tuning.strings.length, fingering, visibleFretsFor(instrument), label);
      figure.appendChild(svgHost);

      text.textContent = fingering.fret === 0
        ? `Cuerda ${number}, traste 0 (al aire), dedo 0`
        : `Cuerda ${number}, traste ${fingering.fret}, dedo ${fingering.finger}`;
      figure.appendChild(text);
      block.appendChild(figure);
    });

    if (labelled && notes.length === 2) {
      const a = midiOfNote(notes[0]);
      const b = midiOfNote(notes[1]);
      if (a !== null && b !== null && (validated || review)) {
        const distance = document.createElement('p');
        distance.className = 'semimus-distance';
        distance.setAttribute('aria-live', 'polite');
        distance.textContent = distanceText(a, b);
        block.appendChild(distance);
      }
    }
    return block;
  }

  // Estructura del documento de partituras. La octava de la guitarra (8vb) y la
  // transposición escrita se resuelven con instrumentNotation(instrument).
  function buildPayload(instrument, midis, intervalType) {
    const notation = instrumentNotation(instrument);
    return {
      instrument: instrumentKey(instrument),
      interval_type: intervalType || '',
      notation_display: {
        clef: notation.clef,
        notes: (Array.isArray(midis) ? midis : []).map(noteInfoFromMidi),
      },
    };
  }

  function noteKey(note) {
    return `${String(note.pitch).toLowerCase()}${note.accidental || ''}/${note.octave}`;
  }

  // Índice diatónico (C0 = 0) usado para estimar líneas adicionales.
  function diatonicIndex(note) {
    return Number(note.octave) * 7 + STEP_OF_LETTER[String(note.pitch)[0].toUpperCase()];
  }

  const STAFF_TOP_LINE = 5 * 7 + 3;      // F5: línea superior del pentagrama.
  const STAFF_BOTTOM_LINE = 4 * 7 + 2;   // E4: línea inferior del pentagrama.
  const LEDGER_LINE_PX = 12;             // Reserva vertical por línea adicional.

  function ledgerPadding(notes) {
    let above = 0;
    let below = 0;
    for (const note of notes) {
      const steps = diatonicIndex(note);
      // Las líneas adicionales caen en pasos pares desde la línea del pentagrama.
      if (steps > STAFF_TOP_LINE) {
        above = Math.max(above, Math.floor((steps - STAFF_TOP_LINE) / 2));
      }
      if (steps < STAFF_BOTTOM_LINE) {
        below = Math.max(below, Math.floor((STAFF_BOTTOM_LINE - steps) / 2));
      }
    }
    return { above: above * LEDGER_LINE_PX + 8, below: below * LEDGER_LINE_PX + 8 };
  }

  function ensureStyles() {
    if (document.getElementById('semimus-score-styles')) return;
    const style = document.createElement('style');
    style.id = 'semimus-score-styles';
    style.textContent = [
      '.semimus-score { display: flex; flex-direction: column; align-items: center; gap: .4rem; width: 100%; }',
      '.semimus-score-paper { background: #FCFAF1; border-radius: .8rem; padding: .4rem .55rem;',
      '  width: 100%; max-width: 21rem; box-shadow: inset 0 0 0 1px rgba(15, 23, 42, .14); }',
      '.semimus-score-paper svg { display: block; width: 100%; height: auto; }',
      '.semimus-score-fallback { font-family: Georgia, serif; font-size: 1rem; text-align: center; color: #1E293B; padding: .5rem 0; }',
      '.semimus-score-caption { font-size: .8rem; font-weight: 700; text-align: center; margin: 0; opacity: .92; }',
      '.semimus-fingering { display: flex; flex-wrap: wrap; justify-content: center; gap: .6rem; width: 100%; }',
      '.semimus-diagram { background: #FCFAF1; border-radius: .7rem; padding: .4rem .5rem; margin: 0; width: 7.5rem; color: #1E293B; text-align: center; box-shadow: inset 0 0 0 1px rgba(15, 23, 42, .14); }',
      '.semimus-diagram svg { display: block; width: 100%; height: auto; }',
      '.semimus-diagram-title { font-size: .8rem; font-weight: 800; margin: 0 0 .2rem; }',
      '.semimus-diagram-text { font-size: .68rem; line-height: 1.25; margin: .3rem 0 0; font-weight: 600; }',
      '.semimus-diagram-badge { display: inline-block; font-size: .66rem; font-weight: 800; color: #1E293B; border: 1px solid #1E293B; border-radius: .3rem; padding: 0 .3rem; margin: 0 0 .2rem; }',
      '.semimus-distance { width: 100%; font-size: .75rem; font-weight: 700; text-align: center; margin: .2rem 0 0; color: inherit; }',
      '.semimus-score-row { display: flex; flex-direction: column; align-items: center; gap: .6rem; width: 100%; }',
      '@media (min-width: 640px) { .semimus-score-row { flex-direction: row; align-items: flex-start; justify-content: center; } .semimus-score-row > .semimus-score-paper { flex: 0 1 21rem; } .semimus-score-row > .semimus-fingering { flex: 0 1 auto; } }',
    ].join('\n');
    document.head.appendChild(style);
  }

  function renderFallback(paper, notes) {
    const fallback = document.createElement('p');
    fallback.className = 'semimus-score-fallback';
    fallback.textContent = notes.map(note => note.scientific_name).join('  →  ');
    paper.appendChild(fallback);
  }

  /**
   * Dibuja el pentagrama dentro de `container` a partir de un payload.
   * Devuelve true si pudo dibujarse con VexFlow.
   */
  function render(container, payload, options = {}) {
    if (!container) return false;
    while (container.firstChild) container.removeChild(container.firstChild);
    const notation = (payload && payload.notation_display) || {};
    const notes = Array.isArray(notation.notes) ? notation.notes : [];
    if (!notes.length) return false;
    ensureStyles();

    const wrapper = document.createElement('div');
    wrapper.className = 'semimus-score';
    const row = document.createElement('div');
    row.className = 'semimus-score-row';
    const paper = document.createElement('div');
    paper.className = 'semimus-score-paper';
    const caption = document.createElement('p');
    caption.className = 'semimus-score-caption';
    caption.textContent = notes
      .map(note => `${note.spanish_name} / ${note.scientific_name}${note.focus ? ' ★' : ''}`)
      .join('  →  ');
    row.appendChild(paper);
    const fingering = options.diagram === false ? null : buildFingering(payload.instrument, notes);
    if (fingering) row.appendChild(fingering);
    wrapper.appendChild(row);
    wrapper.appendChild(caption);
    container.appendChild(wrapper);

    if (typeof Vex === 'undefined' || !Vex.Flow) {
      renderFallback(paper, notes);
      return false;
    }

    const VF = Vex.Flow;
    const instrumentInfo = instrumentNotation(payload.instrument);
    const writtenShift = Number.isFinite(Number(notation.written_shift))
      ? Number(notation.written_shift)
      : instrumentInfo.writtenShift;

    // Altura escrita: la guitarra se escribe una octava arriba de cómo suena.
    // Sin transposición se conserva la ortografía de la nota (bemoles de escalas).
    // La octava escrita también conserva la letra y la alteración (y el foco).
    const written = notes.map(note => {
      const midi = midiOfNote(note);
      if (midi === null || writtenShift === 0) return note;
      if (writtenShift === 12 && note.pitch) {
        const octave = Number(note.octave) + 1;
        const baseName = String(note.spanish_name || note.pitch).replace(/\s*-?\d+$/, '');
        return {
          ...note,
          octave,
          scientific_name: `${note.pitch}${note.accidental || ''}${octave}`,
          spanish_name: `${baseName} ${octave}`,
        };
      }
      const info = noteInfoFromMidi(midi + writtenShift);
      return note.focus ? { ...info, focus: true } : info;
    });

    const width = 320;
    const padding = ledgerPadding(written);
    const height = 118 + padding.above + padding.below;

    try {
      const renderer = new VF.Renderer(paper, VF.Renderer.Backends.SVG);
      renderer.resize(width, height);
      const context = renderer.getContext();

      const stave = new VF.Stave(8, 12 + padding.above, width - 16);
      const annotation = notation.clef_annotation || instrumentInfo.clefAnnotation || '';
      stave.addClef('treble', 'default', annotation || undefined);
      stave.setContext(context).draw();

      const staveNotes = written.map(note => new VF.StaveNote({
        keys: [noteKey(note)],
        duration: 'q',
        clef: 'treble',
        auto_stem: true,
      }));
      written.forEach((note, index) => {
        if (note.accidental) {
          staveNotes[index].addModifier(new VF.Accidental(note.accidental), 0);
        }
        // Grados de foco: color y la marca ★ en la leyenda (no solo color).
        if (note.focus) {
          staveNotes[index].setStyle({ fillStyle: '#B45309', strokeStyle: '#B45309' });
        }
      });

      const voice = new VF.Voice({ num_beats: written.length, beat_value: 4 });
      voice.setMode(VF.Voice.Mode.SOFT);
      voice.addTickables(staveNotes);
      new VF.Formatter().joinVoices([voice]).format([voice], width - 70);
      voice.draw(context, stave);
    } catch (error) {
      console.warn('SemimusScore: no se pudo dibujar el pentagrama.', error);
      renderFallback(paper, notes);
      return false;
    }

    const svg = paper.querySelector('svg');
    if (svg) {
      svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
      svg.setAttribute('width', '100%');
      svg.removeAttribute('height');
      svg.style.width = '100%';
      svg.style.height = 'auto';
    }
    return true;
  }

  function renderNotes(container, instrument, midis, intervalType, options = {}) {
    return render(container, buildPayload(instrument, midis, intervalType), options);
  }

  return {
    buildPayload,
    instrumentNotation,
    noteInfoFromMidi,
    render,
    renderNotes,
    findFingering,
    midiOfScientific,
    distanceText,
    TUNINGS,
    ledgerPadding,
    diatonicIndex,
    midiOfNote,
  };
})();
