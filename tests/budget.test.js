// Regression tests for the raster budget in src/app.js.
// Run: node --test tests/budget.test.js
//
// The fake pdf.js / pdf-lib / canvas below share the size model the budget was
// calibrated against: a page encodes to
//     weight * 120000 * scale^2 * quality
// so the byte figures asserted here are the ones that model predicts.
'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const APP_SRC = fs.readFileSync(path.join(__dirname, '..', 'src', 'app.js'), 'utf8');
const KB = 1024;
const TARGET_300 = 300 * KB;
const sizeOf = (weight, scale, q) => Math.round(weight * 120000 * scale * scale * q);
const TEXT_FLOOR = sizeOf(0.4, 0.62, 0.18);   // 3321 B, the floor for a light page
const PHOTO_FLOOR = sizeOf(30, 0.62, 0.18);   // 249091 B, the floor for a photo page

function loadApp(env) {
  const window = { pdfjsLib: env.pdfjsLib, PDFLib: env.PDFLib };
  window.document = env.document;
  new Function('window', 'document', APP_SRC)(window, env.document);
  return { MillFile: window.MillFile, stats: env.stats };
}

function makeEnv(opts) {
  const weights = opts.weights;
  const sheet = opts.pageSize || [612, 792];
  const maxPx = opts.browserCanvasPx || Infinity;
  const maxEdge = opts.browserCanvasEdge || Infinity;
  const stats = { toBlobCalls: 0, destroyCalls: 0, maxCanvasPx: 0, maxCanvasEdge: 0 };

  const canvasFactory = () => {
    const canvas = {
      width: 1, height: 1, _vp: null, _weight: 0,
      getContext() {
        if (this.width * this.height > maxPx || Math.max(this.width, this.height) > maxEdge) {
          return null;                       // browser refuses the surface
        }
        return { fillStyle: null, _canvas: this, fillRect() {} };
      },
      toBlob(cb, _type, q) {
        stats.toBlobCalls++;
        const size = sizeOf(this._weight, this._vp.scale, q);
        cb({ size, arrayBuffer: async () => new ArrayBuffer(size) });
      }
    };
    return canvas;
  };

  const pages = weights.map((weight, index) => ({
    number: index + 1,
    getViewport({ scale }) {
      return { width: sheet[0] * scale, height: sheet[1] * scale, scale };
    },
    render({ canvasContext, viewport }) {
      const canvas = canvasContext._canvas;
      canvas._vp = viewport;
      canvas._weight = weight;
      stats.maxCanvasPx = Math.max(stats.maxCanvasPx, canvas.width * canvas.height);
      stats.maxCanvasEdge = Math.max(stats.maxCanvasEdge, canvas.width, canvas.height);
      if (opts.failRender && (!opts.failRender.scales || opts.failRender.scales.includes(viewport.scale))) {
        return { promise: Promise.reject(new Error('render refused')) };
      }
      return { promise: Promise.resolve() };
    },
    cleanup() {}
  }));

  const doc = () => {
    const created = { pages: [], lossless: false };
    return {
      async copyPages() { created.lossless = true; return []; },
      addPage() {
        const p = { drawImage(img) { p._bytes = img._size; } };
        created.pages.push(p);
        return p;
      },
      async embedJpg(bytes) { return { _size: bytes.length }; },
      async save() {
        const n = created.pages.length;
        const bytes = created.lossless
          ? (opts.losslessBytes || 0)
          : 4096 + n * 350 + created.pages.reduce((a, p) => a + p._bytes, 0);
        return new Uint8Array(bytes);
      }
    };
  };

  const env = {
    stats,
    document: {
      getElementById: () => null,            // no #drop -> app.js skips the UI half
      createElement: canvasFactory,
      body: { getAttribute: () => null }
    },
    pdfjsLib: {
      GlobalWorkerOptions: {},
      getDocument() {
        return {
          promise: Promise.resolve({
            numPages: pages.length,
            async getPage(i) {
              if (opts.failGetPage === i) throw new Error('render refused');
              return pages[i - 1];
            },
            async destroy() { stats.destroyCalls++; }
          })
        };
      }
    },
    PDFLib: {
      StandardFonts: { Helvetica: 'Helvetica' },
      rgb: () => [0, 0, 0],
      PDFDocument: {
        async load() {
          if (opts.losslessFails !== false) throw new Error('no lossless repack in this test');
          return { getPageIndices: () => [] };
        },
        create: () => Promise.resolve(doc())
      }
    }
  };
  return env;
}

function fakeFile(bytes) {
  const buf = new Uint8Array(bytes);
  '%PDF-1.7'.split('').forEach((c, i) => { buf[i] = c.charCodeAt(0); });
  return { name: 'test.pdf', size: bytes, type: 'application/pdf', arrayBuffer: async () => buf.buffer };
}

const compress = (opts, targetBytes = TARGET_300) => {
  const env = makeEnv(opts);
  const { MillFile, stats } = loadApp(env);
  return MillFile.compressOne(fakeFile(targetBytes * 4), targetBytes).then((res) => ({ res, stats, MillFile }));
};

/* ---------------- the budget must not be poisoned by one heavy page ---------------- */

const HEAVY_FIRST = [30, 0.4, 0.4, 0.4, 0.4, 0.4];   // photo-heavy page in slot 1
const HEAVY_THIRD = [0.4, 0.4, 30, 0.4, 0.4, 0.4];   // same file, photo-heavy page in slot 3

test('photo page first still reaches the 300 KB target', async () => {
  const { res, stats } = await compress({ weights: HEAVY_FIRST });
  assert.equal(res.method, 'raster');
  assert.equal(res.reached, true);
  assert.equal(res.minHit, false);
  assert.ok(res.bytes.length <= TARGET_300, `got ${res.bytes.length}`);
  assert.equal(stats.destroyCalls, 1);
});

test('moving the photo page to slot 3 no longer ruins the pages after it', async () => {
  const { res, stats } = await compress({ weights: HEAVY_THIRD });
  assert.equal(res.reached, true, 'pre-fix this was false (349 KB out of a 300 KB target)');
  assert.equal(res.minHit, false);
  assert.ok(res.bytes.length <= TARGET_300, `got ${res.bytes.length}`);

  const text = res.plan.filter((_, i) => i !== 2).map((p) => p.size);
  assert.ok(Math.min(...text) > 2 * TEXT_FLOOR,
    `light pages after the photo were starved to the floor: ${text}`);
  assert.ok(Math.max(...text) / Math.min(...text) <= 2,
    `light pages treated unevenly: ${text}`);
  assert.equal(stats.destroyCalls, 1);
});

test('page order does not change what each page is allowed to use', async () => {
  const a = await compress({ weights: HEAVY_FIRST });
  const b = await compress({ weights: HEAVY_THIRD });
  const sizes = (r) => r.plan.map((p) => p.size).sort((x, y) => x - y);
  assert.deepEqual(sizes(a.res), sizes(b.res));
  assert.equal(a.res.bytes.length, b.res.bytes.length);
});

test('no page is handed a budget that its own encoding then breaks', async () => {
  const { res } = await compress({ weights: HEAVY_THIRD });
  res.plan.forEach((p) => assert.ok(p.size <= p.target, `page budget broken: ${p.size} > ${p.target}`));
});

test('a 300 KB target the document cannot reach is reported, not faked', async () => {
  const { res, stats, MillFile } = await compress({ weights: [30, 0.4, 30, 0.4, 0.4, 0.4] });
  const floorBytes = 2 * PHOTO_FLOOR + 4 * TEXT_FLOOR + 4096 + 6 * 350;
  assert.equal(res.reached, false);
  assert.equal(res.minHit, true, 'the engine measured the floor, so "min" is a true claim');
  assert.equal(res.floor, floorBytes);
  assert.equal(res.bytes.length, floorBytes);
  assert.deepEqual(MillFile.badgeFor(res), { text: 'min 506 KB', cls: 'row__badge row__badge--warn' });
  // every page stops at its floor instead of running the whole 60-step ladder
  assert.ok(stats.toBlobCalls <= 2 * 6, `encoded ${stats.toBlobCalls} times`);
});

test('the next workable target is suggested from the chips, not guessed', async () => {
  const chips = [100, 200, 300, 500, 1024, 2048].map((kb) => kb * KB);
  const { res, MillFile } = await compress({ weights: [30, 0.4, 30, 0.4, 0.4, 0.4] });
  assert.equal(MillFile.nextTargetAbove(chips, res.floor), 1024 * KB);
  assert.equal(MillFile.nextTargetAbove(chips, 3 * 1024 * KB), null);
});

/* ---------------- P0-3: canvas size caps ---------------- */

test('a 200 in sheet is clamped to a canvas the browser can actually hold', async () => {
  const { res, stats } = await compress({ weights: [1, 1, 1], pageSize: [14400, 14400] });
  assert.ok(stats.maxCanvasEdge <= 16384, `canvas edge ${stats.maxCanvasEdge}`);
  assert.ok(stats.maxCanvasPx <= 16000000, `canvas area ${stats.maxCanvasPx}`);
  assert.equal(res.method, 'raster');
});

test('a browser that rejects a big canvas loses that scale, not the file', async () => {
  const { res, stats } = await compress({
    weights: [1, 1], pageSize: [2000, 2000], browserCanvasPx: 12000000
  });
  assert.equal(res.reached, true);
  assert.equal(stats.destroyCalls, 1);
});

/* ---------------- P0-4 / P0-6: memory hygiene and honest badges ---------------- */

test('the pdf.js document is released even when a page fails midway', async () => {
  const { res, stats, MillFile } = await compress({
    weights: [0.4, 0.4, 0.4],
    failGetPage: 2,
    losslessFails: false,
    losslessBytes: 500 * KB
  });
  assert.equal(stats.destroyCalls, 1);
  assert.equal(res.method, 'lossless');
  assert.equal(res.reached, false);
  assert.ok(!res.minHit, 'nothing was probed, so the result must not claim a floor');
  assert.equal(MillFile.badgeFor(res).text, 'best effort 500 KB');
});

test('badges: already / percentage / true floor / best effort', () => {
  const { MillFile } = loadApp(makeEnv({ weights: [1] }));
  const size = (n) => ({ length: n });
  assert.equal(MillFile.badgeFor({ reached: true, method: 'already', bytes: size(50 * KB), original: 50 * KB }).text, 'already 50 KB');
  assert.equal(MillFile.badgeFor({ reached: true, method: 'raster', bytes: size(100 * KB), original: 400 * KB }).text, '75% smaller');
  assert.equal(MillFile.badgeFor({ reached: false, minHit: true, bytes: size(600 * KB), original: 4 * 1024 * KB }).text, 'min 600 KB');
  assert.equal(MillFile.badgeFor({ reached: false, minHit: false, bytes: size(600 * KB), original: 4 * 1024 * KB }).text, 'best effort 600 KB');
});
