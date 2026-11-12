// Genera docs/afinaciones_para_validar.csv a partir de la misma función
// findFingering que usa el widget (app/static/js/score_renderer.js).
// Uso: node scripts/gen_afinaciones_csv.js
// No modifica TUNINGS: las notas inalcanzables se listan como CONFLICTO.
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const src = fs.readFileSync(path.join(root, 'app', 'static', 'js', 'score_renderer.js'), 'utf8');

function fakeElement(tag) {
  return {
    tagName: tag, className: '', textContent: '', innerHTML: '', style: {}, children: [],
    firstChild: null,
    appendChild(c) { this.children.push(c); this.firstChild = this.children[0]; return c; },
    removeChild(c) { this.children = this.children.filter(x => x !== c); this.firstChild = this.children[0] || null; },
    querySelector() { return null; }, setAttribute() {}, removeAttribute() {},
  };
}
const document = { getElementById: () => null, createElement: fakeElement, head: { appendChild() {} } };
const S = new Function('document', src + ';return SemimusScore;')(document);

// Rangos del documento "Especificación técnica: renderizado de partituras" (MIDI).
const DOC_RANGES = [
  { instrument: 'Guitarra', key: 'guitarra', low: 40, high: 76, rango: 'Mi 2 → Mi 5 (E2–E5)' },
  { instrument: 'Tiple', key: 'tiple', low: 48, high: 76, rango: 'Do 3 → Mi 5 (C3–E5)' },
  { instrument: 'Requinto', key: 'requinto', low: 60, high: 88, rango: 'Do 4 → Mi 6 (C4–E6)' },
  { instrument: 'Bandola', key: 'bandola', low: 54, high: 91, rango: 'Fa# 3 → Sol 6 (F#3–G6)' },
];

const cell = value => {
  const text = String(value);
  return /[",\n;]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text;
};
const rows = [[
  'instrumento', 'orden_o_cuerda', 'nota_al_aire', 'rango_documento', 'tipo',
  'nota', 'midi', 'cuerda', 'traste', 'dedo', 'posicion', 'estado',
]];

for (const spec of DOC_RANGES) {
  const strings = S.TUNINGS[spec.key].strings;
  strings.forEach((open, index) => {
    rows.push([
      spec.instrument, strings.length - index, S.noteInfoFromMidi(open).spanish_name,
      spec.rango, 'AFINACION', '', open, '', '', '', '', 'pendiente de validación',
    ]);
  });
  for (let midi = spec.low; midi <= spec.high; midi++) {
    const info = S.noteInfoFromMidi(midi);
    const name = info.scientific_name;
    const f = S.findFingering(spec.instrument, name);
    if (!f) {
      rows.push([spec.instrument, '', '', spec.rango, 'DIGITACION', name, midi, '', '', '', '', 'CONFLICTO: no se puede tocar con esta afinación']);
    } else {
      rows.push([spec.instrument, '', '', spec.rango, 'DIGITACION', name, midi,
        strings.length - f.string, f.fret, f.finger, f.position, 'calculada, pendiente de validación']);
    }
  }
}

const out = path.join(root, 'docs', 'afinaciones_para_validar.csv');
fs.mkdirSync(path.dirname(out), { recursive: true });
fs.writeFileSync(out, '\ufeff' + rows.map(r => r.map(cell).join(',')).join('\n') + '\n', 'utf8');
console.log(`CSV escrito: ${out} (${rows.length - 1} filas)`);
