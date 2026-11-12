// Pruebas de digitación y panel de diapasón de score_renderer.js.
// Se ejecuta con: node tests/js/score_renderer_check.js  (lo llama pytest).
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const src = fs.readFileSync(path.join(__dirname, '..', '..', 'app', 'static', 'js', 'score_renderer.js'), 'utf8');

function fakeElement(tag) {
  return {
    tagName: tag, className: '', textContent: '', innerHTML: '', style: {}, children: [],
    firstChild: null,
    appendChild(c) { this.children.push(c); this.firstChild = this.children[0]; return c; },
    removeChild(c) { this.children = this.children.filter(x => x !== c); this.firstChild = this.children[0] || null; },
    querySelector() { return null; }, setAttribute() {}, removeAttribute() {},
  };
}

function loadRenderer(reviewMode) {
  const document = { getElementById: () => null, createElement: fakeElement, head: { appendChild() {} } };
  global.window = { SEMIMUS_REVIEW_MODE: reviewMode };
  return new Function('document', 'window', src + ';return SemimusScore;')(document, global.window);
}

function collect(node, out = []) {
  if (node.className) out.push(node);
  (node.children || []).forEach(child => collect(child, out));
  return out;
}

const S = loadRenderer(false);
const at = (instrument, pitch, options) => S.findFingering(instrument, pitch, options);

// 1. Cuerda al aire: traste 0, dedo 0, posición 1.
assert.deepStrictEqual(at('Guitarra', 'E2'), { string: 0, fret: 0, finger: 0, position: 1 });
assert.deepStrictEqual(at('Tiple', 'C3'), { string: 0, fret: 0, finger: 0, position: 1 });

// 2. Primera posición: dedo = traste.
assert.deepStrictEqual(at('Guitarra', 'D3'), { string: 2, fret: 0, finger: 0, position: 1 });
assert.deepStrictEqual(at('Guitarra', 'F3'), { string: 2, fret: 1, finger: 1, position: 1 });

// 3. Sin primera posición: posición más baja, dedo = traste - posición + 1.
assert.deepStrictEqual(at('Guitarra', 'E5'), { string: 5, fret: 12, finger: 4, position: 9 });
assert.deepStrictEqual(at('Tiple', 'E5'), { string: 3, fret: 14, finger: 4, position: 11 });
assert.deepStrictEqual(at('Requinto', 'E6'), { string: 3, fret: 14, finger: 4, position: 11 });
assert.deepStrictEqual(at('Bandola', 'G6'), { string: 3, fret: 15, finger: 4, position: 12 });

// 4. Cada resultado cumple las reglas: finger entre 0 y 4 y posición coherente.
for (const [instrument, pitch] of [['Guitarra', 'G#3'], ['Requinto', 'A5'], ['Tiple', 'B4']]) {
  const f = at(instrument, pitch);
  assert.ok(f, `${instrument} ${pitch} debe tener digitación`);
  assert.ok(f.finger >= 0 && f.finger <= 4, 'dedo fuera de 0-4');
  if (f.fret > 0) assert.strictEqual(f.finger, f.fret - f.position + 1);
}

// 5. Nota fuera de la afinación: null (conflicto documentado, no se cambia la afinación).
assert.strictEqual(at('Bandola', 'F#3'), null);

// 6. Intervalo: la segunda nota prefiere la misma posición de la mano.
// Guitarra: E3 tiene una opción en primera posición (D3, traste 2) y otra en
// posición 4 (A2, traste 7). Con la mano en posición 4 debe elegir la de posición 4.
assert.strictEqual(at('Guitarra', 'E3').position, 1);
assert.deepStrictEqual(at('Guitarra', 'E3', { handPosition: 4 }), { string: 1, fret: 7, finger: 4, position: 4 });

// 7. Distancia en tonos y trastes (trastes = semitonos).
assert.strictEqual(S.distanceText(60, 64), 'Distancia: 2 tonos (4 trastes)');
assert.strictEqual(S.distanceText(60, 61), 'Distancia: medio tono (1 traste)');
assert.strictEqual(S.distanceText(60, 60), 'Distancia: sin distancia (misma nota) (0 trastes)');

// 8. Pantalla de tiple, requinto y bandola sin validar: aviso, sin SVG.
function panel(instrument, midis, reviewMode, options) {
  const renderer = loadRenderer(reviewMode);
  const container = fakeElement('div');
  renderer.renderNotes(container, instrument, midis, 'x', options);
  const all = collect(container);
  const svgs = all.filter(n => n.innerHTML && n.innerHTML.includes('<svg'));
  return { all, svgs, container };
}
const hidden = panel('Tiple', [48], false);
assert.strictEqual(hidden.svgs.length, 0, 'tiple sin validar no debe mostrar diapasón');
assert.ok(hidden.all.some(n => n.textContent === 'Diagrama en revisión: pendiente de validación por un maestro de cuerdas pulsadas'));

// 9. Modo revisión (administrador): sí se dibuja, marcado SIN VALIDAR.
const review = panel('Tiple', [50], true);
assert.ok(review.svgs.length >= 1, 'en revisión debe mostrarse el diapasón');
assert.ok(review.all.some(n => n.textContent === 'SIN VALIDAR'));

// 10. Guitarra siempre visible, sin depender de la bandera.
const guitar = panel('Guitarra', [52], false);
assert.ok(guitar.svgs.length >= 1, 'la guitarra siempre muestra el diapasón');
assert.ok(!guitar.all.some(n => n.textContent === 'SIN VALIDAR'));

// 11. El Modo Libre puede ocultar el diapasón (diagram: false).
const jam = panel('Guitarra', [40, 47], false, { diagram: false });
assert.strictEqual(jam.all.filter(n => n.className === 'semimus-fingering').length, 0);

// 12. Intervalos: dos figuras con etiqueta "Nota 1" y "Nota 2" y la línea de distancia.
const interval = panel('Guitarra', [40, 47], false);
const labels = interval.all.filter(n => n.className === 'semimus-diagram-title').map(n => n.textContent);
assert.deepStrictEqual(labels, ['Nota 1 · E2', 'Nota 2 · B2']);
assert.ok(interval.all.some(n => n.className === 'semimus-distance' && /Distancia: 7 semitonos|Distancia: 5 tonos y medio|tonos/.test(n.textContent)));

// 13. Columnas: pentagrama y diapasón en la misma fila (responsive en CSS).
const row = interval.all.find(n => n.className === 'semimus-score-row');
assert.ok(row, 'debe existir la fila pentagrama + diapasón');
assert.strictEqual(row.children.length, 2);

console.log('score_renderer_check: OK');
