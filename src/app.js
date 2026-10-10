/* MillFile engine + UI — pure frontend, files never leave the device.
   The PDF libraries (pdf.js, pdf-lib, JSZip) are fetched on first use rather
   than on page load; see ensureEngine() below. */
(function () {
  'use strict';

  /* ---------------- the engine, fetched on demand ----------------
     The bundle is ~921 KB raw and ~314 KB gzipped, and it used to be a <script>
     tag on every tool page, so a visitor who only read the page paid for all of
     it. Now the tags are injected on the first file, which is also when the
     worker starts being needed. Nothing below touches pdfjsLib or PDFLib until
     ensureEngine() resolves — that is why both start as null. */
  var ENGINE_FILES = ['/vendor/pdf.min.js',
                      '/vendor/pdf-lib.min.js',
                      '/vendor/jszip.min.js'];
  var pdfjsLib = null, PDFLib = null;
  var engineReady = null;

  function loadScript(src) {
    return new Promise(function (resolve, reject) {
      var s = document.createElement('script');
      s.src = src;
      s.onload = function () { resolve(); };
      s.onerror = function () { reject(new Error('could not load ' + src)); };
      document.head.appendChild(s);
    });
  }

  function adoptEngine() {
    pdfjsLib = window.pdfjsLib || null;
    PDFLib = window.PDFLib || null;
    if (!pdfjsLib || !PDFLib) throw new Error('the PDF engine did not initialise');
    if (pdfjsLib.GlobalWorkerOptions) {
      pdfjsLib.GlobalWorkerOptions.workerSrc = '/vendor/pdf.worker.min.js';
    }
  }

  function ensureEngine() {
    if (engineReady) return engineReady;
    // Libraries already on the page: nothing to fetch, just adopt them. That is
    // how tests/harness.html drives the engine directly, and how the regression
    // suite stands in for it — so the loader must not insist on a download.
    if (window.pdfjsLib && window.PDFLib) {
      engineReady = Promise.resolve().then(adoptEngine);
      return engineReady;
    }
    // Serial rather than parallel: the three do not depend on each other, but
    // loading one at a time makes the failing file obvious when something 404s.
    engineReady = ENGINE_FILES.reduce(function (chain, src) {
      return chain.then(function () { return loadScript(src); });
    }, Promise.resolve()).then(adoptEngine).catch(function (err) {
      engineReady = null;   // a later attempt should be able to start over
      throw err;
    });
    return engineReady;
  }

  // Begin the download as soon as the visitor shows intent, so the wait overlaps
  // with the file picker or the drag instead of following it.
  function warmEngine() {
    if (!engineReady) ensureEngine().catch(function () { /* the real attempt reports */ });
  }

  /* ---------------- compression core ---------------- */

  function fmtSize(b) {
    if (b < 1024) return b + ' B';
    if (b < 1024 * 1024) return Math.round(b / 1024) + ' KB';
    return (b / (1024 * 1024)).toFixed(2) + ' MB';
  }

  function pdfMagic(bytes) {
    return bytes.length > 5 &&
      bytes[0] === 0x25 && bytes[1] === 0x50 && bytes[2] === 0x44 &&
      bytes[3] === 0x46 && bytes[4] === 0x2d; // %PDF-
  }

  // 1) lossless repack (object streams). Hits target for many text PDFs.
  async function losslessRepack(buf) {
    var src = await PDFLib.PDFDocument.load(buf, { updateMetadata: false });
    var out = await PDFLib.PDFDocument.create();
    var pages = await out.copyPages(src, src.getPageIndices());
    pages.forEach(function (p) { out.addPage(p); });
    var bytes = await out.save({ useObjectStreams: true });
    return new Uint8Array(bytes);
  }

  var SCALES = [2.0, 1.6, 1.3, 1.0, 0.8, 0.62];
  var QUALITIES = [0.82, 0.75, 0.68, 0.6, 0.52, 0.45, 0.38, 0.3, 0.24, 0.18];
  var MIN_Q = QUALITIES[QUALITIES.length - 1];

  // A1/A0 sheets at scale 2 would need a canvas past the browser's 16384px edge
  // limit, and iOS Safari gives up on canvas area well before that.
  var MAX_CANVAS_EDGE = 16384;
  var MAX_CANVAS_PX = 16000000;

  function safeScale(baseVp, requested) {
    var w = Math.max(1, baseVp.width), h = Math.max(1, baseVp.height);
    return Math.min(requested,
      MAX_CANVAS_EDGE / Math.max(w, h),
      Math.sqrt(MAX_CANVAS_PX / (w * h)));
  }

  function scaleLadder(baseVp) {
    var ladder = [], seen = {};
    for (var i = 0; i < SCALES.length; i++) {
      var s = safeScale(baseVp, SCALES[i]);
      if (!(s > 0)) continue;
      var key = s.toFixed(5);
      if (seen[key]) continue;
      seen[key] = 1;
      ladder.push(s);
    }
    return ladder;
  }

  function renderPageToCanvas(page, scale) {
    var vp = page.getViewport({ scale: scale });
    var canvas = document.createElement('canvas');
    canvas.width = Math.max(1, Math.ceil(vp.width));
    canvas.height = Math.max(1, Math.ceil(vp.height));
    var ctx = canvas.getContext('2d', { alpha: false });
    if (!ctx) {
      canvas.width = canvas.height = 0;
      throw new Error('canvas-unavailable');
    }
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    return page.render({ canvasContext: ctx, viewport: vp }).promise.then(function () {
      return { canvas: canvas, vp: vp };
    });
  }

  function canvasToJpeg(canvas, q) {
    return new Promise(function (resolve) {
      canvas.toBlob(function (blob) { resolve(blob); }, 'image/jpeg', q);
    });
  }

  // Each resolution step up keeps the bottom of the quality ladder in reserve
  // for the steps below it: give pixels up before you give JPEG quality up, so a
  // page never ends at full resolution + q 0.18 when a mid resolution at a mid
  // quality costs the same bytes. The lowest resolution always keeps
  // the whole range, so a page can still reach the floor pass 1 measured for it.
  var RESERVE = 3;

  function qualityGroups(ladder) {
    var groups = [];
    for (var i = 0; i < ladder.length; i++) {
      var reserve = (i === ladder.length - 1) ? 0 : Math.max(0, Math.min(RESERVE - i, QUALITIES.length - 1));
      groups.push({ scale: ladder[i], qualities: QUALITIES.slice(0, QUALITIES.length - reserve) });
    }
    return groups;
  }

  // Highest-quality encoding of one page that still fits perTarget, falling
  // back to the smallest encoding the browser can produce for that page.
  async function encodePage(page, ladder, perTarget) {
    var chosen = null, smallest = null;
    var groups = qualityGroups(ladder);
    for (var s = 0; s < groups.length && !chosen; s++) {
      var r;
      try {
        r = await renderPageToCanvas(page, groups[s].scale);
      } catch (e) {
        continue;                  // this scale is beyond the browser; try the next
      }
      var qs = groups[s].qualities;
      for (var q = 0; q < qs.length; q++) {
        var blob = await canvasToJpeg(r.canvas, qs[q]);
        if (!blob) continue;
        var cand = { size: blob.size, blob: blob, scale: groups[s].scale, q: qs[q] };
        if (!smallest || cand.size < smallest.size) smallest = cand;
        if (cand.size <= perTarget) { chosen = cand; break; }
      }
      r.canvas.width = 0; r.canvas.height = 0;
    }
    if (!chosen && !smallest) throw new Error('canvas-unavailable');
    return chosen || smallest;
  }

  // Smallest bytes a page can possibly reach: lowest safe scale, lowest quality.
  async function encodeAtFloor(page, ladder) {
    var scale = ladder[ladder.length - 1];
    var r = await renderPageToCanvas(page, scale);
    var blob = await canvasToJpeg(r.canvas, MIN_Q);
    r.canvas.width = 0; r.canvas.height = 0;
    if (!blob) throw new Error('canvas-unavailable');
    return { size: blob.size, blob: blob, scale: scale, q: MIN_Q };
  }

  // 2) rasterize. Pass 1 measures every page's floor, pass 2 spends the budget:
  //    each page is guaranteed its floor plus an equal share of what is left, so
  //    a photo page cannot starve the text pages that come after it.
  async function rasterCompress(buf, targetBytes, onProgress) {
    var task = pdfjsLib.getDocument({ data: buf, disableAutoFetch: true, isEvalSupported: false });
    var pdf = await task.promise;
    try {
      var n = pdf.numPages;
      var overhead = 4096 + n * 350;             // wrapper + xref estimate
      var budget = Math.max(2048, targetBytes - overhead);
      var ladders = [], floorSizes = [], minTotal = 0, i, page, baseVp;

      for (i = 1; i <= n; i++) {
        if (onProgress) onProgress(i, n, 'measure');
        page = await pdf.getPage(i);
        baseVp = page.getViewport({ scale: 1 });
        ladders[i - 1] = scaleLadder(baseVp);
        var measured = await encodeAtFloor(page, ladders[i - 1]);
        measured.blob = null;
        floorSizes[i - 1] = measured.size;
        minTotal += measured.size;
        page.cleanup();
      }

      var reachable = minTotal <= budget;
      var floorSuffix = [];                       // floorSizes[k] + ... + floorSizes[n-1]
      floorSuffix[n] = 0;
      for (i = n - 1; i >= 0; i--) floorSuffix[i] = floorSuffix[i + 1] + floorSizes[i];

      var outDoc = await PDFLib.PDFDocument.create();
      var plan = [], remaining = budget;

      for (i = 1; i <= n; i++) {
        if (onProgress) onProgress(i, n, reachable ? 'compress' : 'floor');
        page = await pdf.getPage(i);
        baseVp = page.getViewport({ scale: 1 });
        var perTarget = floorSizes[i - 1];
        if (reachable) {
          var spare = Math.max(0, remaining - floorSuffix[i - 1]);
          perTarget = floorSizes[i - 1] + spare / (n - i + 1);
        }
        // Nothing can fit when the whole document is already over budget, so
        // take each page's floor without walking the 60-step ladder again.
        var use = reachable
          ? await encodePage(page, ladders[i - 1], perTarget)
          : await encodeAtFloor(page, ladders[i - 1]);
        remaining = Math.max(0, remaining - use.size);
        plan.push({ size: use.size, scale: use.scale, q: use.q, target: Math.round(perTarget) });

        var jpgBytes = new Uint8Array(await use.blob.arrayBuffer());
        use.blob = null;
        var jpg = await outDoc.embedJpg(jpgBytes);
        jpgBytes = null;
        var p = outDoc.addPage([baseVp.width, baseVp.height]);
        p.drawImage(jpg, { x: 0, y: 0, width: baseVp.width, height: baseVp.height });
        page.cleanup();
      }

      var out = await outDoc.save({ useObjectStreams: true });
      return {
        bytes: new Uint8Array(out),
        meta: { pages: n, method: 'raster', plan: plan, hitFloor: !reachable,
                floorBytes: minTotal + overhead }
      };
    } finally {
      pdf.destroy();
    }
  }

  async function compressOne(file, targetBytes, onProgress) {
    // Self-contained: the queue awaits this too, but the regression tests call
    // compressOne() directly, so the guarantee belongs here rather than only in
    // the caller.
    await ensureEngine();
    var buf = new Uint8Array(await file.arrayBuffer());
    if (!pdfMagic(buf)) throw new Error('not-pdf');
    if (buf.length <= targetBytes) {
      return { bytes: buf, original: buf.length, method: 'already', reached: true, target: targetBytes };
    }
    var original = buf.length;
    var lossless = null;
    try { lossless = await losslessRepack(buf); } catch (e) { lossless = null; }
    if (lossless && lossless.length <= targetBytes) {
      return { bytes: lossless, original: original, method: 'lossless', reached: true, target: targetBytes };
    }
    var encErr = null, r = null;
    try {
      r = await rasterCompress(buf, targetBytes, onProgress);
    } catch (e) {
      encErr = e;
    }
    buf = null;
    if (r) {
      lossless = null;
      return {
        bytes: r.bytes, original: original, method: r.meta.method, target: targetBytes,
        reached: r.bytes.length <= targetBytes, minHit: !!r.meta.hitFloor,
        floor: r.meta.floorBytes, plan: r.meta.plan
      };
    }
    // last resort: return the lossless repack if it at least shrank
    if (lossless && lossless.length < original) {
      return { bytes: lossless, original: original, method: 'lossless',
               reached: false, target: targetBytes, fallback: true };
    }
    if (encErr && /password/i.test(String(encErr.name || encErr.message || ''))) throw new Error('password');
    if (encErr && /InvalidPDF|empty|structure/i.test(String(encErr.message || ''))) throw new Error('not-pdf');
    if (encErr && encErr.message === 'canvas-unavailable') throw new Error('canvas-unavailable');
    throw new Error('failed');
  }

  // Only claim "min" when the engine actually measured the floor of this file.
  function badgeFor(res) {
    var warn = 'row__badge row__badge--warn', ok = 'row__badge row__badge--ok';
    if (res.reached) {
      if (res.method === 'already') return { text: 'already ' + fmtSize(res.bytes.length), cls: ok };
      var cut = Math.round((1 - res.bytes.length / res.original) * 100);
      return { text: cut > 0 ? cut + '% smaller' : 'under target', cls: ok };
    }
    if (res.minHit) return { text: 'min ' + fmtSize(res.bytes.length), cls: warn };
    return { text: 'best effort ' + fmtSize(res.bytes.length), cls: warn };
  }

  function nextTargetAbove(candidates, needBytes) {
    var best = null;
    for (var i = 0; i < candidates.length; i++) {
      if (candidates[i] >= needBytes && (best === null || candidates[i] < best)) best = candidates[i];
    }
    return best;
  }

  window.MillFile = {
    compressOne: compressOne, fmtSize: fmtSize, pdfMagic: pdfMagic,
    badgeFor: badgeFor, nextTargetAbove: nextTargetAbove
  };

  /* ---------------- UI ---------------- */

  var $ = function (id) { return document.getElementById(id); };
  if (!$('drop')) return;

  var state = { targetKB: null, queue: [], busy: false };
  var DEFAULT_KB = 300;

  function targetBytes() { return state.targetKB * 1024; }

  function announce(msg, kind) {
    var el = $('status');
    el.textContent = msg;
    el.className = 'status' + (kind ? ' status--' + kind : '');
  }

  function parseTargetFromPage() {
    var t = document.body.getAttribute('data-target-kb');
    state.targetKB = t ? parseInt(t, 10) : DEFAULT_KB;
    document.querySelectorAll('#chips .chip').forEach(function (c) {
      var on = parseInt(c.getAttribute('data-kb'), 10) === state.targetKB;
      c.classList.toggle('chip--on', on);
      c.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    var lbl = $('target-label');
    if (lbl) lbl.textContent = state.targetKB >= 1024 ? (state.targetKB / 1024) + ' MB' : state.targetKB + ' KB';
  }

  function makeRow(file) {
    var li = document.createElement('li');
    li.className = 'row';
    li.innerHTML =
      '<span class="row__name"></span>' +
      '<span class="row__sizes"><span class="row__from"></span> <span class="row__arrow">&rarr;</span> <span class="row__to"></span></span>' +
      '<span class="row__badge"></span>' +
      '<button class="btn btn--sm row__dl" type="button" hidden>Download</button>';
    li.querySelector('.row__name').textContent = file.name;
    li.querySelector('.row__from').textContent = fmtSize(file.size);
    return li;
  }

  function setStatusBadge(badgeEl, res) {
    var b = badgeFor(res);
    badgeEl.textContent = b.text;
    badgeEl.className = b.cls;
  }

  function attachDownload(btn, bytes, name) {
    if (btn._url) URL.revokeObjectURL(btn._url);   // a re-run replaces this row's file
    var url = URL.createObjectURL(new Blob([bytes], { type: 'application/pdf' }));
    btn._url = url;
    btn.hidden = false;
    btn.onclick = function () {
      var a = document.createElement('a');
      a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      // Once handed to the browser the URL only pins the result in memory.
      setTimeout(function () {
        if (btn._url === url) { URL.revokeObjectURL(url); btn._url = null; }
      }, 10000);
    };
  }

  function fmtTarget(bytes) {
    var kb = Math.round(bytes / 1024);
    return kb >= 1024 ? (kb / 1024) + ' MB' : kb + ' KB';
  }

  // Result names: the input name alone overwrites the original file in the
  // downloads folder and cannot be told apart from it.
  function outName(name) {
    var base = String(name || 'document').replace(/[\\/\0]/g, '_').replace(/\.\./g, '_');
    if (/\.pdf$/i.test(base)) base = base.slice(0, -4);
    return base + '-compressed.pdf';
  }

  // Two files named "report.pdf" in one batch would otherwise collide in the zip.
  function uniqueZipName(used, name) {
    var stem = name.slice(0, -4), n = 2;
    while (name in used) { name = stem + ' (' + n + ').pdf'; n++; }
    used[name] = 1;
    return name;
  }

  function sizeList(map) {
    return Object.keys(map).map(Number).sort(function (a, b) { return a - b; })
      .map(fmtTarget).join(' or ');
  }

  function chipBytes() {
    var out = [];
    document.querySelectorAll('#chips .chip').forEach(function (c) {
      var kb = parseInt(c.getAttribute('data-kb'), 10);
      if (kb > 0) out.push(kb * 1024);
    });
    return out;
  }

  async function processQueue() {
    if (state.busy) return;
    state.busy = true;
    $('download-all').hidden = true;
    // The engine is not on the page yet. Fail here, before any row looks like it
    // is working, so a network problem reads as one message rather than one
    // error per file.
    if (state.queue.some(function (it) { return !it.done; })) {
      try {
        announce('Loading the PDF engine…');
        await ensureEngine();
      } catch (err) {
        state.busy = false;
        announce('The PDF engine could not load (' +
          (err && err.message ? err.message : err) +
          '). Check your connection, then drop the file again.', 'warn');
        return;
      }
    }
    var failed = 0, broken = 0, hitFloor = 0;
    var doneTargets = {}, missTargets = {};
    for (var i = 0; i < state.queue.length; i++) {
      var item = state.queue[i];
      if (item.done) continue;
      var target = targetBytes();   // fixed per file: chips may move mid-queue
      announce('Compressing ' + item.file.name + ' (' + (i + 1) + '/' + state.queue.length + ')…');
      try {
        var res = await compressOne(item.file, target, function (p, n, phase) {
          announce('Compressing ' + item.file.name + ' — ' +
            (phase === 'measure' ? 'measuring' : 'reducing') + ' page ' + p + '/' + n + '…');
        });
        item.res = res;
        doneTargets[res.target] = 1;
        item.row.querySelector('.row__to').textContent = fmtSize(res.bytes.length);
        setStatusBadge(item.row.querySelector('.row__badge'), res);
        attachDownload(item.row.querySelector('.row__dl'), res.bytes, outName(item.file.name));
        item.done = true;
        if (!res.reached) {
          failed++;
          missTargets[res.target] = 1;
          if (res.minHit && res.floor > target) hitFloor++;
        }
      } catch (e) {
        var msg = 'failed';
        if (e.message === 'password') msg = 'password-protected';
        else if (e.message === 'not-pdf') msg = 'not a PDF';
        else if (e.message === 'canvas-unavailable') msg = 'too big to render here';
        var b = item.row.querySelector('.row__badge');
        b.textContent = msg; b.className = 'row__badge row__badge--err';
        item.row.querySelector('.row__to').textContent = '—';
        item.failed = true;
        broken++;
      }
    }
    var okCount = state.queue.filter(function (q) { return q.done; }).length;
    if (okCount > 1) $('download-all').hidden = false;
    if (!failed && !broken) {
      announce('Done — all files under ' + sizeList(doneTargets) +
        '. Your files never left this device.', 'ok');
    } else {
      var note = 'Done — ' + okCount + ' compressed';
      if (failed) note += ', ' + failed + ' could not reach ' + sizeList(missTargets);
      if (broken) note += ', ' + broken + ' could not be processed';
      note += '.';
      if (hitFloor) {
        var floor = Math.max.apply(null, state.queue.filter(function (q) {
          return q.res && q.res.minHit && !q.res.reached;
        }).map(function (q) { return q.res.floor; }));
        var next = nextTargetAbove(chipBytes(), floor);
        note += next
          ? ' The tightest floor here is about ' + fmtSize(floor) + ' — pick ' + fmtTarget(next) + ' and drop it again.'
          : ' The tightest floor here is about ' + fmtSize(floor) + ' — re-scan that file at a lower resolution.';
      }
      announce(note, 'warn');
    }
    state.busy = false;
  }

  function addFiles(files) {
    var list = Array.prototype.slice.call(files).filter(function (f) {
      return f.type === 'application/pdf' || /\.pdf$/i.test(f.name);
    });
    if (!list.length) { announce('Please drop PDF files.', 'warn'); return; }
    var ul = $('queue');
    list.forEach(function (f) {
      var row = makeRow(f);
      ul.appendChild(row);
      state.queue.push({ file: f, row: row, done: false });
    });
    processQueue();
  }

  /* wiring */
  var dz = $('drop'), fi = $('file-input');
  // #drop is the <label> for #file-input, so click and keyboard activation are
  // native; a JS click here would open the picker twice.
  fi.addEventListener('change', function () { addFiles(fi.files); fi.value = ''; });
  // Both routes to a file — opening the picker or starting a drag — are preceded
  // by one of these, which is early enough to hide the download behind.
  ['pointerdown', 'keydown'].forEach(function (ev) { dz.addEventListener(ev, warmEngine); });
  ['dragenter', 'dragover'].forEach(function (ev) {
    dz.addEventListener(ev, function (e) {
      e.preventDefault();
      dz.classList.add('drop--on');
      if (ev === 'dragenter') warmEngine();
    });
  });
  ['dragleave', 'drop'].forEach(function (ev) {
    dz.addEventListener(ev, function (e) { e.preventDefault(); dz.classList.remove('drop--on'); });
  });
  dz.addEventListener('drop', function (e) {
    if (e.dataTransfer && e.dataTransfer.files) addFiles(e.dataTransfer.files);
  });

  document.querySelectorAll('#chips .chip').forEach(function (c) {
    c.addEventListener('click', function () {
      state.targetKB = parseInt(c.getAttribute('data-kb'), 10);
      document.querySelectorAll('#chips .chip').forEach(function (x) {
        x.classList.remove('chip--on');
        x.setAttribute('aria-pressed', 'false');
      });
      c.classList.add('chip--on');
      c.setAttribute('aria-pressed', 'true');
      var lbl = $('target-label');
      if (lbl) lbl.textContent = state.targetKB >= 1024 ? (state.targetKB / 1024) + ' MB' : state.targetKB + ' KB';
      if (state.queue.some(function (q) { return q.done; })) {
        // re-run not automatic; user can drop again. Keep honest & simple.
        announce('Target set to ' + (state.targetKB >= 1024 ? (state.targetKB / 1024) + ' MB' : state.targetKB + ' KB') + ' — drop files to compress.');
      } else {
        announce('Target set to ' + (state.targetKB >= 1024 ? (state.targetKB / 1024) + ' MB' : state.targetKB + ' KB') + '.');
      }
    });
  });

  $('download-all').addEventListener('click', async function () {
    var btn = this;
    btn.disabled = true; btn.textContent = 'Zipping…';
    try {
      var zip = new JSZip();
      var used = Object.create(null), any = false;
      state.queue.forEach(function (q) {
        if (q.res) { zip.file(uniqueZipName(used, outName(q.file.name)), q.res.bytes); any = true; }
      });
      if (!any) return;
      var blob = await zip.generateAsync({ type: 'blob' });
      var url = URL.createObjectURL(blob);
      var a = document.createElement('a');
      a.href = url; a.download = 'millfile-compressed.zip';
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () { URL.revokeObjectURL(url); }, 30000);
    } finally {
      btn.disabled = false; btn.textContent = 'Download all (.zip)';
    }
  });

  parseTargetFromPage();
  announce('Ready — target ' + (state.targetKB >= 1024 ? (state.targetKB / 1024) + ' MB' : state.targetKB + ' KB') + '. Files are processed on this device only.');
})();
