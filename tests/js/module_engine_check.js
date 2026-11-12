// Pruebas del motor de módulos (Etapa C). Se ejecuta con:
//   node tests/js/module_engine_check.js   (lo llama pytest)
const assert = require('assert');
const path = require('path');

const root = path.join(__dirname, '..', '..');
const M = require(path.join(root, 'app', 'static', 'js', 'module_engine.js'));
const config = require(path.join(root, 'app', 'static', 'data', 'modules_config.json'));
const modules = config.modules;
const PASS = config.progression.passingPercent;
const COUNT = config.progression.challengeQuestions;

// 1. Estructura: 31 módulos (0 a 30) y 80 % en 10 preguntas en un solo lugar.
assert.strictEqual(modules.length, 31);
assert.deepStrictEqual(modules.map(m => m.id), Array.from({ length: 31 }, (_, i) => i));
assert.strictEqual(PASS, 80);
assert.strictEqual(COUNT, 10);
for (const m of modules) {
  assert.strictEqual(m.levels.length, 2, `módulo ${m.id} debe tener Fase .1 y Fase .2`);
  assert.strictEqual(m.levels[0].phase, 'study');
  assert.strictEqual(m.levels[1].phase, 'challenge');
}

// 2. Semitonos según el documento: simples 1–13 (unísono 0 … octava 12),
//    compuestos 14–21 (13, 14, 15, 16, 17, 19, 20, 21).
const simpleExpected = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12];
modules.filter(m => m.group === 'simple').forEach((m, i) => assert.strictEqual(m.semitones, simpleExpected[i], m.name));
const compoundExpected = [13, 14, 15, 16, 17, 19, 20, 21];
modules.filter(m => m.group === 'compound').forEach((m, i) => assert.strictEqual(m.semitones, compoundExpected[i], m.name));
assert.strictEqual(modules.filter(m => m.group === 'scale').length, 9);

// 3. Desbloqueo: el módulo N necesita el reto del N-1 con el 80 %.
assert.strictEqual(M.isModuleUnlocked(modules, {}, 0, PASS), true);
assert.strictEqual(M.isModuleUnlocked(modules, {}, 1, PASS), false);
assert.strictEqual(M.isModuleUnlocked(modules, { '0:2': 79 }, 1, PASS), false);
assert.strictEqual(M.isModuleUnlocked(modules, { '0:2': 80 }, 1, PASS), true);

// 4. Fase .2 se desbloquea solo al completar la Fase .1 (estudio = 100).
assert.strictEqual(M.isLevelUnlocked(modules, { '0:2': 80 }, 1, 1, PASS), true);
assert.strictEqual(M.isLevelUnlocked(modules, { '0:2': 80 }, 1, 2, PASS), false);
assert.strictEqual(M.isLevelUnlocked(modules, { '0:2': 80, '1:1': 100 }, 1, 2, PASS), true);
assert.strictEqual(M.isLevelCompleted({ '1:1': 100 }, 1, 1, PASS), true);
assert.strictEqual(M.isLevelCompleted({ '1:2': 79 }, 1, 2, PASS), false);
assert.strictEqual(M.isLevelCompleted({ '1:2': 80 }, 1, 2, PASS), true);

// 5. Pozo del reto según el documento.
assert.deepStrictEqual(M.challengePool(modules, 2), [1, 2]);            // Mód 2: unísono o 2da menor
assert.deepStrictEqual(M.challengePool(modules, 3), [1, 2, 3]);         // Mód 3: unísono, 2da m o 2da M
assert.deepStrictEqual(M.challengePool(modules, 4), [1, 2, 3, 4]);      // Mód 4: comparar contra anteriores
assert.deepStrictEqual(M.challengePool(modules, 13), Array.from({ length: 13 }, (_, i) => i + 1)); // Reto Maestro simples
assert.deepStrictEqual(M.challengePool(modules, 14), [14, 15]);         // primer compuesto con distractor
assert.deepStrictEqual(M.challengePool(modules, 21), [14, 15, 16, 17, 18, 19, 20, 21]); // Reto Maestro compuestos
assert.deepStrictEqual(M.challengePool(modules, 22), [22, 23]);         // primera escala con distractor
assert.deepStrictEqual(M.challengePool(modules, 30), [22, 23, 24, 25, 26, 27, 28, 29, 30]);
// Mód 1: solo unísono; se agrega 2da menor como distractor.
assert.deepStrictEqual(M.challengePool(modules, 1), [1, 2]);

// 6. Opciones: como máximo 4, sin repetidos, siempre incluyen la correcta.
const rnd = (() => { let s = 7; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
for (let n = 1; n <= 30; n++) {
  const pool = M.challengePool(modules, n);
  for (const target of M.challengeTargets(modules, n, COUNT, rnd)) {
    assert.ok(target.options.length <= 4, `módulo ${n}: más de 4 opciones`);
    assert.ok(target.options.includes(target.targetId), `módulo ${n}: falta la correcta`);
    assert.strictEqual(new Set(target.options).size, target.options.length, `módulo ${n}: opciones repetidas`);
    assert.ok(pool.includes(target.targetId), `módulo ${n}: objetivo fuera del pozo`);
  }
  assert.strictEqual(M.challengeTargets(modules, n, COUNT, rnd).length, COUNT);
}

// 7. Distancias: tonos y trastes, y compuestos como octava + simple.
assert.strictEqual(M.distanceLabel(0), 'sin distancia (misma nota) (0 trastes)');
assert.strictEqual(M.distanceLabel(1), 'medio tono (1 traste)');
assert.strictEqual(M.distanceLabel(7), '3 tonos y medio (7 trastes)');
assert.strictEqual(M.distanceLabel(12), '6 tonos (12 trastes)');
assert.strictEqual(M.distanceLabel(13), '6½ tonos (13 trastes)');
assert.strictEqual(M.distanceLabel(21), '10½ tonos (21 trastes)');

// 8. Escalas escritas desde la raíz (sostenidos o bemoles, sin dobles alteraciones).
const major = [2, 2, 1, 2, 2, 2, 1];
const letters = notes => notes.map(n => `${n.pitch}${n.accidental}`).join(' ');
assert.strictEqual(letters(M.spellScale(60, major)), 'C D E F G A B C');
assert.strictEqual(letters(M.spellScale(58, major)), 'Bb C D Eb F G A Bb'); // Si bemol mayor
assert.strictEqual(letters(M.spellScale(66, major)), 'F# G# A# B C# D# E# F#'); // Fa sostenido mayor
const locrio = [1, 2, 2, 1, 2, 2, 2];
assert.strictEqual(letters(M.spellScale(60, locrio)), 'C Db Eb F Gb Ab Bb C');
const focusNotes = M.spellScale(60, [2, 1, 2, 2, 1, 3, 1], [5, 6]);
assert.deepStrictEqual(focusNotes.map(n => n.focus), [false, false, false, false, false, true, true, false]);
const phrygian = M.spellScale(60, [1, 2, 2, 2, 1, 2, 2], [1]);
assert.strictEqual(phrygian[1].focus, true);
assert.strictEqual(phrygian[1].scientific_name, 'Db4');
assert.strictEqual(phrygian[1].spanish_name, 'Reb 4');

// 9. Todas las escalas del documento se pueden escribir desde Do y desde Sol.
for (const m of modules.filter(x => x.group === 'scale')) {
  assert.ok(M.spellScale(60, m.scale.steps, m.scale.focus), `${m.name} debe escribirse desde Do`);
  assert.ok(M.spellScale(67, m.scale.steps, m.scale.focus), `${m.name} debe escribirse desde Sol`);
}

console.log('module_engine_check: OK');
