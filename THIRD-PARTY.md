# Third-party components

These libraries are vendored into `vendor/` and served from this project's own origin. The site loads nothing from a CDN, so it makes no third-party requests at runtime.

| Library | Version | License | Upstream |
|---|---|---|---|
| PDF.js (`pdf.min.js`, `pdf.worker.min.js`) | 3.11.174 | Apache License 2.0 | <https://github.com/mozilla/pdf.js> |
| pdf-lib (`pdf-lib.min.js`) | 1.17.1 | Apache License 2.0 | <https://github.com/Hopding/pdf-lib> |
| JSZip (`jszip.min.js`) | 3.10.1 | MIT **or** GPLv3 (dual) | <https://github.com/Stuk/jszip> |
| pako (bundled inside JSZip) | — | MIT | <https://github.com/nodeca/pako> |

## These are unmodified upstream builds — verified

The versions above are not stated from memory. Each vendored file was compared byte for byte against the official published package, and all four match exactly:

| File | SHA-256 | Compared against |
|---|---|---|
| `pdf.min.js` | `5b5799e6f8c680663207ac5b42ee14eed2a406fa7af48f50c154f0c0b1566946` | `pdfjs-dist@3.11.174/build/pdf.min.js` |
| `pdf.worker.min.js` | `feabdf309770ed24bba31a5467836cdc8cf639c705af27d52b585b041bb8527b` | `pdfjs-dist@3.11.174/build/pdf.worker.min.js` |
| `pdf-lib.min.js` | `0f9a5cad07941f0826586c94e089d89b918c46e5c17cf2d5a3c6f666e3bc694f` | `pdf-lib@1.17.1/dist/pdf-lib.min.js` |
| `jszip.min.js` | `acc7e41455a80765b5fd9c7ee1b8078a6d160bbbca455aeae854de65c947d59e` | `jszip@3.10.1/dist/jszip.min.js` |

To re-check any of them:

```bash
sha256sum vendor/*.js
# or compare against the published package directly:
curl -sL https://unpkg.com/pdf-lib@1.17.1/dist/pdf-lib.min.js | sha256sum
```

The version discriminates: `pdf-lib@1.17.0` hashes to `5425541839018ca7…`, not to the value above.

**Each vendored file also retains its upstream license banner in full** at the top of the file. The only change is the filename (`pdf.worker.min.js` is pinned by `src/app.js` and must keep that path).

## License scope

This project's own license (`LICENSE`) covers this project's source — `build.py`, `src/`, `tests/`. It does not replace or alter the upstream licenses above, which continue to govern `vendor/`.

## Notes

- The PDF engine and the ZIP packer are loaded only on pages that render the tool; text-only pages ship no engine at all, enforced by a build gate in both directions.
- No upstream library is patched. To update one, drop in the corresponding upstream release, confirm the new hash here, and re-run the tests and the build gates.
