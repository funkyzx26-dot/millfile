/* RAW to JPG. Loaded only on pages that render the RAW tool.
 *
 * The decode runs in a Web Worker (LibRaw compiled to WebAssembly), because a
 * 26 MP frame takes a couple of seconds on the main thread and would freeze the
 * page while it works. The worker is created on first use, not on load, so a
 * visitor who never drops a file never pays for the ~1 MB WASM download.
 *
 * The file is read into this tab and stays here: there is no upload step and no
 * server side to receive one.
 */
(function () {
  'use strict';

  var drop = document.getElementById('raw-drop');
  if (!drop) return;                    // a page without the tool: nothing to do

  var input = document.getElementById('raw-input');
  var statusEl = document.getElementById('raw-status');
  var queueEl = document.getElementById('raw-queue');
  var chipsEl = document.getElementById('raw-quality');
  var labelEl = document.getElementById('raw-quality-label');

  var QUALITY_LABEL = { '0.92': 'High', '0.85': 'Standard', '0.72': 'Small' };
  var state = { quality: 0.85, pending: [], busy: false, engine: null, engineFailed: false,
                done: 0, failed: 0 };

  // Past this size the decoder plus the JPEG encode hold several copies of a
  // very large buffer, and phones give up. Warn instead of letting it die.
  var BIG_FILE = 60 * 1024 * 1024;

  function $(id) { return document.getElementById(id); }

  function fmtSize(bytes) {
    if (bytes >= 1048576) return (bytes / 1048576).toFixed(1) + ' MB';
    if (bytes >= 1024) return Math.round(bytes / 1024) + ' KB';
    return bytes + ' B';
  }

  function announce(msg, kind) {
    statusEl.textContent = msg;
    statusEl.className = 'status' + (kind ? ' status--' + kind : '');
  }

  // ---- quality chips ----
  function syncChips() {
    var buttons = chipsEl.querySelectorAll('button[data-q]');
    for (var i = 0; i < buttons.length; i++) {
      var on = parseFloat(buttons[i].getAttribute('data-q')) === state.quality;
      buttons[i].setAttribute('aria-pressed', on ? 'true' : 'false');
      buttons[i].className = 'chip' + (on ? ' chip--on' : '');
      if (on) labelEl.textContent = QUALITY_LABEL[buttons[i].getAttribute('data-q')] || '';
    }
  }

  chipsEl.addEventListener('click', function (e) {
    var btn = e.target.closest ? e.target.closest('button[data-q]') : null;
    if (!btn) return;
    state.quality = parseFloat(btn.getAttribute('data-q'));
    syncChips();
  });

  // ---- the engine, created on first use ----
  function getEngine() {
    if (state.engineFailed) return Promise.reject(new Error('engine unavailable'));
    if (state.engine) return Promise.resolve(state.engine);
    announce('Loading the RAW engine…');
    return import('/vendor/rawconvert/worker-client.js').then(function (mod) {
      return mod.RawConvertWorker.init({
        workerUrl: '/vendor/rawconvert/worker.js',
        coreUrl: '/vendor/rawconvert/rawconvert-core.js',
        wasmUrl: '/vendor/rawconvert/rawconvert-core.wasm'
      });
    }).then(function (engine) {
      state.engine = engine;
      return engine;
    }).catch(function (err) {
      state.engineFailed = true;
      throw err;
    });
  }

  // ---- pixels -> JPEG, using the browser's own encoder ----
  function pixelsToJpeg(width, height, data, channels, quality) {
    var canvas = document.createElement('canvas');
    canvas.width = width;
    canvas.height = height;
    var ctx = canvas.getContext('2d');
    var image = ctx.createImageData(width, height);
    var out = image.data;
    var n = width * height;
    if (channels === 3) {
      for (var i = 0, j = 0; i < n; i++) {
        var s = i * 3;
        out[j++] = data[s]; out[j++] = data[s + 1]; out[j++] = data[s + 2]; out[j++] = 255;
      }
    } else {
      out.set(data.subarray(0, n * 4));
    }
    ctx.putImageData(image, 0, 0);
    return new Promise(function (resolve, reject) {
      canvas.toBlob(function (blob) {
        // Release the backing store as soon as the encode is done: on a 26 MP
        // frame this canvas is a ~100 MB allocation and the next file needs it.
        canvas.width = 0; canvas.height = 0;
        blob ? resolve(blob) : reject(new Error('the browser could not encode the JPEG'));
      }, 'image/jpeg', quality);
    });
  }

  function outputName(name) {
    var base = String(name || 'image').replace(/[\\/\0]/g, '_').replace(/\.\./g, '_');
    var dot = base.lastIndexOf('.');
    if (dot > 0) base = base.slice(0, dot);
    return base + '.jpg';
  }

  // ---- rows ----
  function makeRow(file) {
    var li = document.createElement('li');
    li.className = 'row';
    li.innerHTML =
      '<span class="row__name"></span>' +
      '<span class="row__sizes"><span class="row__from"></span> <span class="row__arrow">&rarr;</span> ' +
      '<span class="row__to"></span></span>' +
      '<span class="row__badge"></span>' +
      '<button class="btn btn--sm row__dl" type="button" hidden>Download</button>';
    li.querySelector('.row__name').textContent = file.name;
    li.querySelector('.row__from').textContent = fmtSize(file.size);
    return li;
  }

  function attachDownload(btn, blob, name) {
    if (btn._url) URL.revokeObjectURL(btn._url);
    var url = URL.createObjectURL(blob);
    btn._url = url;
    btn.hidden = false;
    btn.onclick = function () {
      var a = document.createElement('a');
      a.href = url; a.download = name;
      document.body.appendChild(a); a.click(); a.remove();
      setTimeout(function () {
        if (btn._url === url) { URL.revokeObjectURL(url); btn._url = null; }
      }, 10000);
    };
  }

  function mark(row, text, kind) {
    var badge = row.querySelector('.row__badge');
    badge.textContent = text;
    badge.className = 'row__badge row__badge--' + kind;
  }

  // ---- the queue ----
  function enqueue(files) {
    for (var i = 0; i < files.length; i++) state.pending.push(files[i]);
    if (!state.busy) drain();
  }

  function drain() {
    if (state.engineFailed) {
      if (state.pending.length) {
        announce('The RAW engine could not load, so the remaining ' + state.pending.length +
                 ' file(s) were not converted.', 'warn');
        state.pending = [];
      }
      state.busy = false;
      return;
    }
    if (!state.pending.length) {
      state.busy = false;
      // Never report success over a failure: the per-file message is gone by
      // now, so the summary has to carry it.
      if (state.failed) {
        announce('Converted ' + state.done + ' of ' + (state.done + state.failed) +
                 ' file(s); ' + state.failed + ' could not be decoded.', 'warn');
      } else {
        announce('Done.', 'ok');
      }
      return;
    }
    state.busy = true;
    var file = state.pending.shift();
    // processOne reports its own failures, so one bad file never stops the queue.
    processOne(file).then(drain, drain);
  }

  function processOne(file) {
    var row = makeRow(file);
    queueEl.appendChild(row);
    mark(row, 'working…', 'warn');

    if (file.size > BIG_FILE) {
      announce(file.name + ' is ' + fmtSize(file.size) +
               ' — this may run out of memory on a phone.', 'warn');
    } else {
      announce('Converting ' + file.name + '…');
    }

    var started = Date.now();
    return getEngine().then(function (engine) {
      return file.arrayBuffer().then(function (buffer) {
        // The worker client hands `data` to postMessage as a transferable, and
        // only an ArrayBuffer qualifies - a Uint8Array view throws DataCloneError.
        // It transfers the buffer, so it is detached afterwards; we do not reuse it.
        return engine.load(buffer, file.name);
      }).then(function (info) {
        var dims = info.width + '×' + info.height;
        row.querySelector('.row__to').textContent = dims;
        announce('Decoding ' + file.name + ' (' + dims +
                 (info.cameraModel ? ', ' + [info.cameraMake, info.cameraModel].join(' ') : '') + ')…');
        return engine.process({ outputBps: 8, colorSpace: 'srgb' });
      }).then(function (image) {
        var channels = image.colors || 3;
        return pixelsToJpeg(image.width, image.height, image.data, channels, state.quality)
          .then(function (blob) {
            attachDownload(row.querySelector('.row__dl'), blob, outputName(file.name));
            row.querySelector('.row__to').textContent = fmtSize(blob.size);
            mark(row, fmtSize(blob.size), 'ok');
            state.done++;
            announce('Converted ' + file.name + ' to ' + image.width + '×' + image.height + ' JPEG, ' +
                     fmtSize(blob.size) + ' (' + Math.round(blob.size / file.size * 100) + '% of the original) in ' +
                     ((Date.now() - started) / 1000).toFixed(1) + 's.', 'ok');
          });
      }).then(function () {
        // Let the worker drop its per-file state before the next frame.
        return engine.reset();
      });
    }).catch(function (err) {
      var msg = (err && err.message) ? err.message : String(err);
      state.failed++;
      // Keep the reason in the console as well: the status line is a summary by
      // the time a batch finishes, and a failure needs to stay diagnosable.
      if (window.console && console.error) console.error('MillFile RAW: ' + msg, err);
      mark(row, 'failed', 'err');
      announce(file.name + ' could not be decoded: ' + msg +
               '. Some camera compression formats are not supported by the decoder.', 'warn');
      // A failed decode leaves the worker's state unclear; rebuild it next time.
      if (state.engine) { try { state.engine.dispose(); } catch (e) { /* already gone */ } }
      state.engine = null;
    });
  }

  // ---- input ----
  input.addEventListener('change', function () {
    if (input.files && input.files.length) enqueue(input.files);
    input.value = '';
  });

  ['dragenter', 'dragover'].forEach(function (name) {
    drop.addEventListener(name, function (e) {
      e.preventDefault(); e.stopPropagation();
      drop.className = 'drop drop--on';
    });
  });
  ['dragleave', 'dragend'].forEach(function (name) {
    drop.addEventListener(name, function () { drop.className = 'drop'; });
  });
  drop.addEventListener('drop', function (e) {
    e.preventDefault(); e.stopPropagation();
    drop.className = 'drop';
    var files = e.dataTransfer && e.dataTransfer.files;
    if (files && files.length) enqueue(files);
  });

  syncChips();
})();
