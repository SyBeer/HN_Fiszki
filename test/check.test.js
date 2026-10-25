const test = require('node:test');
const assert = require('node:assert/strict');
const { check } = require('../html/check.js');

const gorra = { es: 'gorra', art: 'la', pl: 'czapka z daszkiem' };
const debil = { es: 'débil', esF: '', pl: 'słaby / słaba' };
const alto = { es: 'alto', esF: 'alta', pl: 'wysoki / wysoka' };
const castano = { es: 'castaño', esF: 'castaña', pl: 'szatyn / szatynka' };
const gris = { es: 'blanco / gris', esF: '', pl: 'siwe' };
const listo = { es: 'inteligente / listo', esF: 'lista', pl: 'mądry / mądra' };
const sonrisa = { es: 'una sonrisa bonita', esF: '', pl: 'ładny uśmiech' };
const botas = { es: 'botas', art: 'las', pl: 'kozaki, buty zimowe' };
const rubio = { es: 'rubio', esF: '', pl: 'blond (włosy)' };
const gafasSol = { es: 'gafas de sol', art: 'las', pl: 'okulary przeciwsłoneczne' };

test('dokładna odpowiedź, wielkość liter i znaki interpunkcyjne bez znaczenia', () => {
  assert.deepEqual(check(gorra, 'gorra', 'es'), { ok: true, note: '' });
  assert.equal(check(gorra, '  GORRA! ', 'es').note, '');
  assert.equal(check(alto, '¡Alto!', 'es').ok, true);
});

test('puste pole nie jest oceniane', () => {
  assert.equal(check(gorra, '   ', 'es'), null);
});

test('forma żeńska i warianty po ukośniku', () => {
  assert.equal(check(alto, 'alta', 'es').ok, true);
  assert.equal(check(gris, 'gris', 'es').note, '');
  assert.equal(check(gris, 'blanco', 'es').note, '');
  assert.equal(check(listo, 'listo', 'es').note, '');
  assert.equal(check(listo, 'lista', 'es').note, '');
  assert.equal(check(listo, 'inteligente', 'es').note, '');
});

test('rodzajnik opcjonalny, zły rodzajnik daje uwagę', () => {
  assert.equal(check(gorra, 'la gorra', 'es').note, '');
  assert.equal(check(gorra, 'una gorra', 'es').note, '');
  assert.deepEqual(check(gorra, 'el gorra', 'es'), { ok: true, note: 'rodzajnik' });
  assert.equal(check(gafasSol, 'las gafas de sol', 'es').note, '');
  assert.equal(check(sonrisa, 'una sonrisa bonita', 'es').note, '');
  assert.equal(check(sonrisa, 'sonrisa bonita', 'es').note, '');
});

test('brak akcentu lub tyldy zaliczony z uwagą', () => {
  assert.deepEqual(check(debil, 'debil', 'es'), { ok: true, note: 'akcent' });
  assert.deepEqual(check(castano, 'castano', 'es'), { ok: true, note: 'akcent' });
});

test('jedna literówka w dłuższym słowie zaliczona z uwagą', () => {
  assert.deepEqual(check(castano, 'castaño'.replace('ñ', 'ñn'), 'es'), { ok: true, note: 'literowka' });
  assert.deepEqual(check(gafasSol, 'gafas de sool', 'es'), { ok: true, note: 'literowka' });
  assert.equal(check(alto, 'alfo', 'es').ok, false);
});

test('zła odpowiedź', () => {
  assert.deepEqual(check(gorra, 'gorro', 'es'), { ok: false, note: '' });
  assert.equal(check(alto, 'bajo', 'es').ok, false);
});

test('polski: jeden z wariantów, nawias opcjonalny, brak polskich znaków', () => {
  assert.equal(check(alto, 'wysoka', 'pl').note, '');
  assert.equal(check(botas, 'kozaki', 'pl').note, '');
  assert.equal(check(botas, 'buty zimowe', 'pl').note, '');
  assert.equal(check(rubio, 'blond', 'pl').note, '');
  assert.equal(check(rubio, 'blond włosy', 'pl').note, '');
  assert.deepEqual(check(debil, 'slaby', 'pl'), { ok: true, note: 'akcent' });
  assert.equal(check(gorra, 'czapka zimowa', 'pl').ok, false);
});
