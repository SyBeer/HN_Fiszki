/* Sprawdzanie odpowiedzi w quizie - zasady w SPEC.md. Działa w przeglądarce (window.FiszkiCheck) i w Node (testy). */
(function (root) {
  const ARTS = ['el', 'la', 'los', 'las', 'un', 'una', 'unos', 'unas'];
  const INDEF = { el: 'un', la: 'una', los: 'unos', las: 'unas' };

  const clean = s => s.toLowerCase().replace(/[¡!¿?.,;:"'«»()]/g, ' ').replace(/\s+/g, ' ').trim();
  const strip = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/ł/g, 'l');

  function lev(a, b) {
    const d = Array.from({ length: a.length + 1 }, (_, i) => [i]);
    for (let j = 1; j <= b.length; j++) d[0][j] = j;
    for (let i = 1; i <= a.length; i++)
      for (let j = 1; j <= b.length; j++)
        d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
    return d[a.length][b.length];
  }

  function splitArt(s) {
    const m = s.match(/^(\S+) (.+)$/);
    return m && ARTS.includes(m[1]) ? [m[1], m[2]] : ['', s];
  }

  function variants(card, lang) {
    const out = new Set();
    if (lang === 'es') {
      for (const form of [card.es, card.esF].filter(Boolean))
        for (const part of form.split('/')) {
          const v = clean(part);
          if (!v) continue;
          out.add(v);
          out.add(splitArt(v)[1]);
        }
    } else {
      const noParen = card.pl.replace(/\([^)]*\)/g, ' ');
      for (const src of [card.pl, noParen])
        for (const part of [src, ...src.split(/[\/,]/)]) {
          const v = clean(part);
          if (v) out.add(v);
        }
    }
    return [...out];
  }

  function match(cands, s) {
    if (cands.includes(s)) return 'exact';
    const ss = strip(s);
    if (cands.some(c => strip(c) === ss)) return 'akcent';
    if (cands.some(c => c.length >= 6 && lev(strip(c), ss) <= 1)) return 'literowka';
    return null;
  }

  /* Zwraca null dla pustej odpowiedzi, inaczej { ok, note }; note: '' | 'akcent' | 'literowka' | 'rodzajnik'. */
  function check(card, input, lang) {
    const x = clean(input || '');
    if (!x) return null;
    const cands = variants(card, lang);
    if (lang !== 'es') {
      const r = match(cands, x);
      return { ok: !!r, note: r && r !== 'exact' ? r : '' };
    }
    const [art, body] = splitArt(x);
    const r = match(cands, x) || (art ? match(cands, body) : null);
    if (!r) return { ok: false, note: '' };
    if (card.art && art && art !== card.art && art !== INDEF[card.art]) return { ok: true, note: 'rodzajnik' };
    return { ok: true, note: r === 'exact' ? '' : r };
  }

  /* Czasowniki (lekcja 2): expect = 'part' | 'inf' | 'gap'. Bez tolerancji literówek; note: '' | 'akcent' | 'regular' | 'auxiliar'. */
  function checkVerb(card, input, expect) {
    const x = clean(input || '');
    if (!x) return null;
    const want = clean(expect === 'inf' ? card.inf : expect === 'gap' ? card.gap.a : card.es);
    if (x === want) return { ok: true, note: '' };
    if (strip(x) === strip(want)) return { ok: true, note: 'akcent' };
    if (expect === 'inf') return { ok: false, note: '' };
    const regular = card.inf.slice(0, -2) + (card.inf.endsWith('ar') ? 'ado' : 'ido');
    const last = strip(x.split(' ').pop());
    if (last === strip(regular)) return { ok: false, note: 'regular' };
    if (expect === 'gap' && last === strip(clean(card.es))) return { ok: false, note: 'auxiliar' };
    return { ok: false, note: '' };
  }

  const api = { check, checkVerb, clean, strip, lev };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.FiszkiCheck = api;
})(typeof window !== 'undefined' ? window : globalThis);
