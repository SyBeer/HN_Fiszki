const test = require('node:test');
const assert = require('node:assert/strict');
const { checkVerb } = require('../html/check.js');

const abrir = { inf: 'abrir', es: 'abierto', gap: { a: 'he abierto' } };
const hacer = { inf: 'hacer', es: 'hecho', gap: { a: 'he hecho' } };
const poner = { inf: 'poner', es: 'puesto', gap: { a: 'he puesto' } };
const ver = { inf: 'ver', es: 'visto', gap: { a: 'has visto' } };
const escribir = { inf: 'escribir', es: 'escrito', gap: { a: 'he escrito' } };
const morir = { inf: 'morir', es: 'muerto', gap: { a: 'ha muerto' } };

test('participio: dokładnie, wielkość liter i znaki bez znaczenia', () => {
  assert.deepEqual(checkVerb(abrir, 'abierto', 'part'), { ok: true, note: '' });
  assert.deepEqual(checkVerb(abrir, '  ABIERTO! ', 'part'), { ok: true, note: '' });
});

test('puste pole nie jest oceniane', () => {
  assert.equal(checkVerb(abrir, ' ', 'part'), null);
});

test('forma regularna daje podpowiedź', () => {
  assert.deepEqual(checkVerb(abrir, 'abrido', 'part'), { ok: false, note: 'regular' });
  assert.deepEqual(checkVerb(hacer, 'hacido', 'part'), { ok: false, note: 'regular' });
  assert.deepEqual(checkVerb(poner, 'ponido', 'part'), { ok: false, note: 'regular' });
  assert.deepEqual(checkVerb(ver, 'vido', 'part'), { ok: false, note: 'regular' });
  assert.deepEqual(checkVerb(escribir, 'escribido', 'part'), { ok: false, note: 'regular' });
});

test('bez tolerancji literówek i form odmienionych', () => {
  assert.deepEqual(checkVerb(abrir, 'abiero', 'part'), { ok: false, note: '' });
  assert.deepEqual(checkVerb(abrir, 'abierta', 'part'), { ok: false, note: '' });
  assert.deepEqual(checkVerb(escribir, 'escribto', 'part'), { ok: false, note: '' });
});

test('bezokolicznik z participio', () => {
  assert.deepEqual(checkVerb(abrir, 'abrir', 'inf'), { ok: true, note: '' });
  assert.equal(checkVerb(abrir, 'abierto', 'inf').ok, false);
});

test('zdanie z luką: haber + participio', () => {
  assert.deepEqual(checkVerb(abrir, 'he abierto', 'gap'), { ok: true, note: '' });
  assert.deepEqual(checkVerb(morir, '¡Ha muerto!', 'gap'), { ok: true, note: '' });
  assert.deepEqual(checkVerb(abrir, 'abierto', 'gap'), { ok: false, note: 'auxiliar' });
  assert.deepEqual(checkVerb(abrir, 'ha abierto', 'gap'), { ok: false, note: 'auxiliar' });
  assert.deepEqual(checkVerb(abrir, 'he abrido', 'gap'), { ok: false, note: 'regular' });
  assert.deepEqual(checkVerb(ver, 'has vido', 'gap'), { ok: false, note: 'regular' });
  assert.deepEqual(checkVerb(abrir, 'he cerrado', 'gap'), { ok: false, note: '' });
});
