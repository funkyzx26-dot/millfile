# Third-party components

These libraries are vendored into `vendor/` and served from this project's own origin. The site loads nothing from a CDN, so it makes no third-party requests at runtime.

## PDF engine (loaded on the PDF pages only)

| Library | Version | License | Upstream |
|---|---|---|---|
| PDF.js (`pdf.min.js`, `pdf.worker.min.js`) | 3.11.174 | Apache License 2.0 | <https://github.com/mozilla/pdf.js> |
| pdf-lib (`pdf-lib.min.js`) | 1.17.1 | Apache License 2.0 | <https://github.com/Hopding/pdf-lib> |
| JSZip (`jszip.min.js`) | 3.10.1 | MIT **or** GPLv3 (dual) | <https://github.com/Stuk/jszip> |
| pako (bundled inside JSZip) | — | MIT | <https://github.com/nodeca/pako> |

## RAW engine (loaded on the RAW pages only, and only after a file is dropped)

| Component | File(s) | License | Upstream |
|---|---|---|---|
| rawconvert-wasm wrapper | `vendor/rawconvert/index.js`, `worker-client.js`, `worker-bridge.js`, `worker.js` | MIT | `rawconvert-wasm@0.1.1` on npm |
| Emscripten glue | `vendor/rawconvert/rawconvert-core.js` | MIT (wrapper) | same |
| LibRaw, compiled to WebAssembly | `vendor/rawconvert/rawconvert-core.wasm` | **CDDL-1.0** (see below) | <https://www.libraw.org/> |

`rawconvert-core.wasm` embeds **LibRaw 0.22.1** — the version is stated in the package's own README, and it is not recoverable from the binary itself (the `.wasm` contains no version string).

### Why CDDL-1.0

LibRaw is dual-licensed: **LGPL-2.1 or CDDL-1.0, the user's choice**. This project takes **CDDL-1.0**. The package's README reaches the same conclusion for this exact case:

> LibRaw is dual-licensed under LGPL-2.1 or CDDL-1.0 (your choice). For WASM static linking, CDDL-1.0 is recommended — file-level copyleft on LibRaw source modifications only, no relinking requirement.

CDDL is file-level copyleft: it does not reach this project's own source, and it carries no relinking obligation, which is the awkward part of LGPL when the library is statically compiled into a single `.wasm` binary.

**Obligation we carry:** the license text and attribution must travel with the binary, and LibRaw must not be relicensed as MIT. This file and the upstream banner satisfy the attribution; `LICENSE` (MIT) covers this project's source only.

## These are unmodified upstream builds — verified

The versions above are not stated from memory. Every vendored file was compared byte for byte against the official published package, and **all ten match exactly**:

| File | SHA-256 | Compared against |
|---|---|---|
| `pdf.min.js` | `5b5799e6f8c680663207ac5b42ee14eed2a406fa7af48f50c154f0c0b1566946` | `pdfjs-dist@3.11.174/build/pdf.min.js` |
| `pdf.worker.min.js` | `feabdf309770ed24bba31a5467836cdc8cf639c705af27d52b585b041bb8527b` | `pdfjs-dist@3.11.174/build/pdf.worker.min.js` |
| `pdf-lib.min.js` | `0f9a5cad07941f0826586c94e089d89b918c46e5c17cf2d5a3c6f666e3bc694f` | `pdf-lib@1.17.1/dist/pdf-lib.min.js` |
| `jszip.min.js` | `acc7e41455a80765b5fd9c7ee1b8078a6d160bbbca455aeae854de65c947d59e` | `jszip@3.10.1/dist/jszip.min.js` |
| `rawconvert/index.js` | `9de28b7bdd830772dfea92b754db3dfe2fc7a933491abecd6f5a122548ea96bc` | `rawconvert-wasm@0.1.1/dist/index.js` |
| `rawconvert/worker-client.js` | `3fb009e7d9c644927ad4a8a23d7ca6628f464b91c8372268abd0b2e74cfc436f` | `rawconvert-wasm@0.1.1/dist/worker-client.js` |
| `rawconvert/worker-bridge.js` | `c6c34fb851e96289dc435fcffae0cdc595017988f3c64d7444fe2d377f4c0490` | `rawconvert-wasm@0.1.1/dist/worker-bridge.js` |
| `rawconvert/worker.js` | `f54d4878b2efd90e1fc419671f69137f40148bcd5e768c43b5916cffc3379463` | `rawconvert-wasm@0.1.1/dist/worker.js` |
| `rawconvert/rawconvert-core.js` | `43d0138215d27af0ba39a7609d42599233e3b73031166a1737e219399e236250` | `rawconvert-wasm@0.1.1/dist/rawconvert-core.js` |
| `rawconvert/rawconvert-core.wasm` | `79a414b9d19db6a091053daddc488d3f1e3280ce6169a9c4d5dc6fb4b403332d` | `rawconvert-wasm@0.1.1/dist/rawconvert-core.wasm` |

To re-check any of them:

```bash
sha256sum vendor/*.js vendor/rawconvert/*
# or compare against the published package directly:
curl -sL https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js | sha256sum
curl -sL https://cdn.jsdelivr.net/npm/rawconvert-wasm@0.1.1/dist/rawconvert-core.wasm | sha256sum
```

The version discriminates: `pdf-lib@1.17.0` hashes to `5425541839018ca7…`, not to the value above. `rawconvert-wasm` has only one published release, so there is no second version to discriminate against.

**Each vendored file retains its upstream license banner in full** at the top of the file. The only change anywhere is a filename (`pdf.worker.min.js` is pinned by `src/app.js` and must keep that path).

## A caveat about the RAW engine's source

`rawconvert-wasm@0.1.1` declares its repository as `github.com/anthonygreco/rawconvert-wasm`, and **that repository returns 404** (the account exists; the repository does not). There is no publicly reachable source for this package.

What that means in practice: the vendored bytes are verified to equal the published npm artifact, but if the package has a bug there is no upstream source to patch. Rebuilding LibRaw ourselves is the escape hatch — the same author's `LibRaw-Wasm` project ships an emscripten build script, and compiling with threads disabled would also avoid the shared-memory import that `libraw-wasm` uses. That work has not been done.

## License scope

This project's own license (`LICENSE`) covers this project's source — `build.py`, `src/`, `tests/`. It does not replace or alter the upstream licenses above, which continue to govern `vendor/`.

## Notes

- Both engines are loaded only on the pages that render their tool; text-only pages ship no engine at all. This is enforced by a build gate in both directions.
- The RAW engine's `.wasm` is fetched at runtime by the worker, after a file is dropped — so it does not appear in the page's HTML and a page-level check would miss it. A second gate verifies the runtime files exist for every tool page.
- No upstream library is patched. To update one, drop in the corresponding upstream release, confirm the new hash here, and re-run the tests and the build gates.
