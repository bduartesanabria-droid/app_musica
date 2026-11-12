// Pruebas de partitura (Etapa B): payload, claves, 8vb, accidentales,
// líneas adicionales y dirección de la plica. Se ejecuta con:
//   node tests/js/notation_check.js   (lo llama pytest)
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', '..', 'app', 'static', 'js', 'score_renderer.js'), 'utf8');

// VexFlow falso que graba lo que el widget le pide dibujar.
const recorded = { annotations: [], keys: [], modifiers: [] };
const FakeVex = {
  Flow: {
    Renderer: class {
      constructor() {}
      static get Backends() { return { SVG: 'svg' }; }
      resize() {}
      getContext() { return {}; }
    },
    Stave: class {
      constructor() {}
      addClef(clef, size, annotation) { recorded.annotations.push(annotation === undefined ? null : annotation); return this; }
      setContext() { return this; }
      draw() { return this; }
    },
    StaveNote: class {
      constructor(opts) { recorded.keys.push(opts.keys[0]); }
      addModifier() { return this; }
    },
    Accidental: class { constructor(type) { recorded.modifiers.push(type); } },
    Voice: class {
      constructor() {}
      static get Mode() { return { SOFT: 2 }; }
      setMode() {}
      addTickables() {}
      draw() {}
    },
    Formatter: class {
      joinVoices() { return this; }
      format() { return this; }
    },
  },
};

function fakeElement(tag) {
  return {
    tagName: tag, className: '', textContent: '', innerHTML: '', style: {}, children: [],
    firstChild: null,
    appendChild(c) { this.children.push(c); this.firstChild = this.children[0]; return c; },
    removeChild(c) { this.children = this.children.filter(x => x !== c); this.firstChild = this.children[0] || null; },
    querySelector() { return null; }, setAttribute() {}, removeAttribute() {},
  };
}

function loadRenderer(withVex) {
  const document = { getElementById: () => null, createElement: fakeElement, head: { appendChild() {} } };
  global.window = { SEMIMUS_REVIEW_MODE: false };
  const Vex = withVex ? FakeVex : undefined;
  return new Function('document', 'window', 'Vex', src + ';return SemimusScore;')(document, global.window, Vex);
}

function drawn(instrument, midis) {
  recorded.annotations.length = 0;
  recorded.keys.length = 0;
  recorded.modifiers.length = 0;
  const S = loadRenderer(true);
  const container = fakeElement('div');
  S.renderNotes(container, instrument, midis, 'x');
  return { S, annotation: recorded.annotations[0] || '', keys: recorded.keys.slice(), modifiers: recorded.modifiers.slice() };
}

// 1. Payload con la estructura del documento (sin campos extra).
{
  const S = loadRenderer(false);
  const payload = S.buildPayload('Guitarra', [40], '3_mayor_ascendente');
  assert.deepStrictEqual(Object.keys(payload), ['instrument', 'interval_type', 'notation_display']);
  assert.deepStrictEqual(Object.keys(payload.notation_display), ['clef', 'notes']);
  assert.strictEqual(payload.instrument, 'guitarra');
  assert.deepStrictEqual(payload.notation_display.notes[0], {
    pitch: 'E', octave: 2, accidental: '', scientific_name: 'E2', spanish_name: 'Mi 2',
  });
}

// 2. Guitarra E2: clave de sol con 8vb y nota escrita una octava arriba (E3).
{
  const r = drawn('Guitarra', [40]);
  assert.strictEqual(r.annotation, '8vb');
  assert.deepStrictEqual(r.keys, ['e/3']);
}

// 3. Tiple C3: clave de sol estándar, sin 8vb, bajo la 4.ª línea adicional.
{
  const r = drawn('Tiple', [48]);
  assert.strictEqual(r.annotation, '');
  assert.deepStrictEqual(r.keys, ['c/3']);
}

// 3b. E5 en tiple (76) y E5 en guitarra escrita en 8vb (suena E5, se escribe E6).
{
  assert.deepStrictEqual(drawn('Tiple', [76]).keys, ['e/5']);
  const guitarE5 = drawn('Guitarra', [76]);
  assert.strictEqual(guitarE5.annotation, '8vb');
  assert.deepStrictEqual(guitarE5.keys, ['e/6']);
}

// 4. Requinto C4 y E6 (tres líneas adicionales superiores).
{
  assert.deepStrictEqual(drawn('Requinto', [60]).keys, ['c/4']);
  const e6 = drawn('Requinto', [88]);
  assert.deepStrictEqual(e6.keys, ['e/6']);
  assert.strictEqual(e6.annotation, '');
}

// 5. Bandola F#3 con sostenido a la izquierda (accidental "#") y G6.
{
  const fs3 = drawn('Bandola', [54]);
  assert.deepStrictEqual(fs3.keys, ['f#/3']);
  assert.deepStrictEqual(fs3.modifiers, ['#']);
  assert.deepStrictEqual(drawn('Bandola', [91]).keys, ['g/6']);
}

// 6. Padding vertical según la nota más grave y la más aguda (líneas adicionales).
{
  const S = loadRenderer(false);
  const note = name => S.noteInfoFromMidi(S.midiOfNote({ scientific_name: name }));
  // E6: tres líneas adicionales arriba → 3 × 12 + 8 px.
  assert.deepStrictEqual(S.ledgerPadding([note('E6')]), { above: 44, below: 8 });
  // G6: cuatro líneas adicionales arriba.
  assert.deepStrictEqual(S.ledgerPadding([note('G6')]), { above: 56, below: 8 });
  // C3: cuatro líneas adicionales abajo.
  assert.deepStrictEqual(S.ledgerPadding([note('C3')]), { above: 8, below: 56 });
  // E3 (E2 escrita en 8vb): tres líneas adicionales abajo.
  assert.deepStrictEqual(S.ledgerPadding([note('E3')]), { above: 8, below: 44 });
  // C4: una línea adicional abajo.
  assert.deepStrictEqual(S.ledgerPadding([note('C4')]), { above: 8, below: 20 });
  // Pentagrama sin líneas adicionales: solo el margen.
  assert.deepStrictEqual(S.ledgerPadding([note('B4')]), { above: 8, below: 8 });
}

// 7. Dirección de la plica con VexFlow real: E6 hacia abajo, C3 hacia arriba.
{
  const VF = require(path.join(__dirname, '..', '..', 'node_modules', 'vexflow')).Flow;
  const stem = key => new VF.StaveNote({ keys: [key], duration: 'q', clef: 'treble', auto_stem: true }).getStemDirection();
  assert.strictEqual(stem('e/6'), VF.Stem.DOWN, 'E6 debe tener la plica hacia abajo');
  assert.strictEqual(stem('c/3'), VF.Stem.UP, 'C3 debe tener la plica hacia arriba');
}

console.log('notation_check: OK');
