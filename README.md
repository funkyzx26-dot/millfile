# MillFile

Two browser tools that run entirely on your device:

- **Compress a PDF to an exact size** — 100 KB, 200 KB, 300 KB, 500 KB, 1 MB, 2 MB.
- **Convert a camera RAW file to JPEG** — ARW, CR2/CR3, NEF, DNG, ORF, RAF, RW2 and more.

**Your file is never uploaded.** There is no backend, no account, and no server-side copy. Every page is a static file; all the work happens in your browser.

Live site: <https://millfile.com>

## Why it works this way

Upload forms across the web enforce fixed limits (100 KB for an ID scan, 300 KB for an application, 1 MB for an attachment), and the usual fix is to hand your document to someone else's server — a strange thing to do with a passport scan, a payslip, or a signed contract.

MillFile does the work locally instead. That removes the upload step, and with it the queue, the daily cap, and the watermark, because there is no server to pay for. The trade is time and memory: a large file takes longer here, because every page is decoded on your own machine.

The build is static HTML/CSS/JS. Deploying it means serving a folder.

## How PDF compression works

Two stages, in order:

1. **Lossless rebuild.** The document is repacked without changing any pixels, which keeps text selectable and searchable. Many exported documents fit under the target with this pass alone.
2. **Progressive re-rendering.** Only if the file still overshoots is page detail reduced, in small steps, checking the size after each step. The tool stops as soon as the target is met, so the output keeps the highest quality that still fits.

**Known trade-off:** pages that get re-rendered become images. Selectable text, links, form fields, and signatures on those pages do not survive that step, and the bookmark outline and stored document title are not carried into the new file. The site says this in its FAQ and Terms rather than hiding it.

If a document cannot reach the chosen target, the tool reports the smallest size it actually reached instead of claiming success.

## How RAW conversion works

The RAW file is decoded by **LibRaw**, compiled to WebAssembly, inside a Web Worker — so the page stays responsive while a 30 MB frame is being processed. The decoded pixels are drawn to a canvas and encoded as JPEG by the browser itself; there is no separate JPEG library.

Three quality tiers, and that is the whole control surface: **High**, **Standard**, **Small**. Multiple files are processed one at a time, and each result is offered as a separate download.

**Known trade-offs, stated plainly:**

- **Edits are not applied.** A RAW file stores the sensor data; adjustments you made in Lightroom, Capture One or your camera's own software live in a catalog or a sidecar file, not inside the RAW. The output is the decoder's rendering of the raw data, not your edit.
- **EXIF is not carried over.** The JPEG does not keep the camera metadata.
- A very large RAW file is slow, and the peak memory depends on the device. A phone will struggle with a 26 MP frame.
- If a camera's compression variant is not supported, that file fails with an explicit error rather than producing a wrong image.

## Requirements

- Node 18+ (or any runtime that provides `Blob` and `Worker`, only needed to run the tests)
- Python 3.8+ (build script and some checks; standard library only)
- A modern browser to use the site

No package installs, no bundler, no build toolchain, no network access at runtime.

## Build

```bash
python3 build.py
```

Output goes to `dist/`. The build merges `src/` and `vendor/` into 15 static pages, writes content-hashed assets to `dist/assets/`, copies the vendor trees, and rewrites every reference to point at the hashed filenames. It also runs five gates and **fails the build** if any of them trips:

| Gate | What it enforces |
|---|---|
| FAQ structured equality | The `FAQPage` JSON-LD entries and the visible `<details>` pairs must be the same set — not a substring match |
| Links + uniqueness | Every same-site `href`/`src` must land on a real file; no two pages may share a title or meta description |
| Engine scope (three-way) | A PDF page loads the PDF engine and not the RAW one; a RAW page the reverse; a text page neither. Getting this wrong either breaks a page or makes every visitor download an engine they cannot reach |
| Engine files present | A page that renders a tool must have that engine's runtime files in `dist/`. The RAW `.wasm` is fetched by the worker at runtime, so it never appears in the HTML — a page-level check alone would miss it |
| Content-hashed assets | `dist/assets/` holds exactly the hashed artifacts, and nothing still references unhashed names |

The gates are themselves tested: `tests/check_gates.py` feeds each one a deliberately broken input and asserts it is rejected, so a gate cannot quietly stop working.

To look at the result locally:

```bash
python3 -m http.server -d dist 8000
```

Use an HTTP server rather than opening `dist/index.html` directly — the pages use absolute paths, and the browser's file-scheme restrictions will block the engines.

## Tests

```bash
# PDF raster budget regression (10 tests). Fakes pdf.js / pdf-lib / canvas and
# asserts the size model the budget was calibrated against.
node --test tests/budget.test.js

# FAQ JSON-LD must match the visible text of the built HTML
python3 tests/check_faq.py dist

# Every build gate must reject a broken input (fail-closed)
python3 tests/check_gates.py

# Generate a valid uncompressed PDF to try by hand
python3 tests/make_test_pdf.py out.pdf 3 600     # <out> [pages] [target KB]
```

`tests/harness.html` is a browser harness: it runs the engine directly, then drives the real homepage in an iframe with an actual drop event and reads the UI badge back, and finally forces the re-render path with a target the lossless pass cannot reach. Serve the site and open `/tests/harness.html`. It is `noindex` and blocked in `robots.txt`.

The vendor libraries are vendored deliberately — nothing is loaded from a CDN, so the site makes no third-party requests at all. See [THIRD-PARTY.md](THIRD-PARTY.md) for versions, licenses, and the SHA-256 of every file.

## Layout

```
build.py              static site generator; the gates live here
src/app.js            PDF engine: lossless path, raster budget, UI wiring
src/raw.js            RAW engine: worker client, quality tiers, canvas to JPEG
src/copy.py           all page text, kept out of the templates
src/style.css         stylesheet
vendor/               pdf.js, pdf-lib, JSZip
vendor/rawconvert/    LibRaw compiled to WebAssembly, plus its worker and glue
tests/                budget regression, FAQ check, gate tests, sample-PDF
                      generator, browser harness
vercel.json           build command and cache headers for the live deployment
```

`src/copy.py` holds the copy for every page as plain text, and `build.py` renders it. Markup stays in the templates, so a stray quote in a sentence cannot break an attribute.

## Privacy

Your file never leaves your device. There is no upload endpoint, no analytics, no third-party tracker, and no cookie set by the site. Both engines — the PDF libraries and the RAW WebAssembly — are served from the same origin, and the RAW `.wasm` is only fetched after you drop a file, so even the download is a same-origin request you triggered. The site keeps working after you disconnect from the network.

## Scope and limitations

- **No OCR.** Text in a PDF stays text; there is no text recognition step.
- **PDF pages:** re-rendered pages lose selectable text, links, form fields, and signatures (see above).
- **RAW conversion:** your edits are not applied and EXIF is not preserved (see above). The output is full-resolution JPEG, not a downsized preview.
- Very large files are slow, and the ceiling depends on the memory of the device you are using.
- No API, no accounts, no cloud queue — by design, since there is no server.
- Mobile browsers work, but a low-end phone will struggle with a heavy PDF or a large RAW.

## License

Released under the MIT License — see [LICENSE](LICENSE). Vendored components keep their own licenses; see [THIRD-PARTY.md](THIRD-PARTY.md).

---

This repository contains the site only. Internal planning notes, keyword research, and operational records are kept elsewhere and are not part of this project's public source.
