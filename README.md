# MillFile

A PDF compressor that runs entirely in the browser. Pick a target size — 100 KB, 200 KB, 300 KB, 500 KB, 1 MB, 2 MB — drop a PDF, and download the result. **The file is never uploaded**: there is no backend, no account, and no server-side copy.

Live site: <https://millfile.com>

## Why it works this way

Upload forms across the web enforce fixed PDF limits (100 KB for an ID scan, 300 KB for an application, 1 MB for an attachment). The usual fix is to send your document to someone else's server — which is a strange thing to do with a passport scan, a payslip, or a signed contract.

MillFile does the work locally instead. That removes the upload step, and with it the queue, the daily cap, and the watermark, because there is no server to pay for. The trade is time: a large document takes longer here, because every page is rendered on your own machine.

The build is static HTML/CSS/JS. Deploying it means serving a folder.

## How compression works

Two stages, in order:

1. **Lossless rebuild.** The document is repacked without changing any pixels, which keeps text selectable and searchable. Many exported documents fit under the target with this pass alone.
2. **Progressive re-rendering.** Only if the file still overshoots is page detail reduced, in small steps, checking the size after each step. The tool stops as soon as the target is met, so the output keeps the highest quality that still fits.

**Known trade-off:** pages that get re-rendered become images. Selectable text, links, form fields, and signatures on those pages do not survive that step, and the bookmark outline and stored document title are not carried into the new file. The site says this in its FAQ and Terms rather than hiding it.

If a document cannot reach the chosen target, the tool reports the smallest size it actually reached instead of claiming success.

## Requirements

- Node 18+ (or any runtime that provides `Blob`, only needed to run the tests)
- Python 3.8+ (build script and some checks; standard library only)
- A modern browser to use the site

No package installs, no bundler, no build toolchain, no network access at runtime.

## Build

```bash
python3 build.py
```

Output goes to `dist/`. The build merges `src/` and `vendor/` into 11 static pages, writes content-hashed assets to `dist/assets/`, copies the vendor libraries, and rewrites every reference to point at the hashed filenames. It also runs four gates and **fails the build** if any of them trips:

| Gate | What it enforces |
|---|---|
| FAQ structured equality | The `FAQPage` JSON-LD entries and the visible `<details>` pairs must be the same set — not a substring match |
| Links + uniqueness | Every same-site `href`/`src` must land on a real file; no two pages may share a title or meta description |
| Content-hashed assets | `dist/assets/` holds exactly the hashed artifacts, and nothing still references unhashed names |
| Engine scope | A page that renders the tool must load the engine, and a page that does not must not (`941 KB` raw / `~314 KB` gzipped is kept off text-only pages) |

To look at the result locally:

```bash
python3 -m http.server -d dist 8000
```

Use an HTTP server rather than opening `dist/index.html` directly — the pages use absolute paths, and the browser's file-scheme restrictions will block the engine.

## Tests

```bash
# Raster budget regression (10 tests). Fakes pdf.js / pdf-lib / canvas and
# asserts the size model the budget was calibrated against.
node --test tests/budget.test.js

# FAQ JSON-LD must match the visible text of the built HTML
python3 tests/check_faq.py dist

# Generate a valid uncompressed PDF to try by hand
python3 tests/make_test_pdf.py out.pdf 3 600     # <out> [pages] [target KB]
```

`tests/harness.html` is a browser harness: it runs the engine directly, then drives the real homepage in an iframe with an actual drop event and reads the UI badge back, and finally forces the re-render path with a target the lossless pass cannot reach. Serve the site and open `/tests/harness.html`. It is `noindex` and blocked in `robots.txt`.

The vendor libraries are vendored deliberately — nothing is loaded from a CDN, so the site makes no third-party requests at all.

## Layout

```
build.py            static site generator; the gates live here
src/app.js          the engine: lossless path, raster budget, UI wiring
src/copy.py         all page text, kept out of the templates
src/style.css       stylesheet
vendor/             pdf.js, pdf-lib, JSZip (vendored, not from a CDN)
tests/              budget regression, FAQ check, sample-PDF generator, browser harness
vercel.json         build command and cache headers for the live deployment
```

`src/copy.py` holds the copy for every page as plain text, and `build.py` renders it. Markup stays in the templates, so a stray quote in a sentence cannot break an attribute.

## Privacy

Your file never leaves your device. There is no upload endpoint, no analytics, no third-party tracker, and no cookie set by the site. All JavaScript — including the PDF engine and the ZIP packer used for batch downloads — is served from the same origin, so the page does not talk to anyone else. The site keeps working after you disconnect from the network.

## Scope and limitations

- **PDF input only.** No OCR, no other formats.
- Re-rendered pages lose selectable text, links, form fields, and signatures (see above).
- Very large documents are slow, and the ceiling depends on the memory of the device you are using.
- No API, no accounts, no cloud queue — by design, since there is no server.
- Mobile browsers work, but a low-end phone will struggle with a heavy document.

## License

Released under the MIT License — see [LICENSE](LICENSE).

---

This repository contains the site only. Internal planning notes, keyword research, and operational records are kept elsewhere and are not part of this project's public source.
