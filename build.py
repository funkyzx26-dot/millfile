#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""millfile builder: src/ (app.js, style.css, copy.py) + vendor/ -> dist/

Usage:  python build.py
Checks: FAQ JSON-LD must equal the visible <details> set; every same-site
href/src must exist in dist; titles and meta descriptions must be unique;
/assets must hold exactly the hashed build artifacts and nothing may still
reference the unhashed names.
Deployment: vercel.json runs `python3 build.py`, outputDirectory=dist.
"""
import datetime
import hashlib
import html
import importlib.util
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "src"
VENDOR = ROOT / "vendor"
DIST = ROOT / "dist"

# Set once the domain exists, e.g. "https://millfile.com" — regenerates
# canonical/OG tags and sitemap.xml. None = skip them (no placeholders left).
BASE_URL = "https://millfile.com"

spec = importlib.util.spec_from_file_location("copy", SRC / "copy.py")
copy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(copy)

BRAND = copy.BRAND
SIZES = copy.SIZES
NAV = ('<header class="site-head"><div class="wrap">'
       '<a class="brand" href="/">Mill<span>File</span></a>'
       '<nav class="nav"><a href="/how-it-works/">How it works</a>'
       '<a href="/raw-to-jpg/">RAW to JPG</a>'
       '<a href="/about/">About</a>'
       '<a href="/privacy/">Privacy</a></nav></div></header>')

SIZE_ORDER = [100, 200, 300, 500, 1024, 2048]

# copy.py is plain text: a stray quote would truncate the very attribute it
# landed in, and markup belongs in the templates, not in the copy.
TEXT_OK = re.compile(r'^[^<>"]*$')
BOLD_ONLY = re.compile(r"^(?:[^<>]|<b>|</b>)*$")


def esc(text):
    text = str(text)
    if not TEXT_OK.match(text):
        sys.exit('BUILD FAILED: copy must be plain text (no < > "): %r' % text[:80])
    return html.escape(text, quote=False)


def bold(text):
    """The one escape hatch: copy that is allowed to carry inline <b>."""
    text = str(text)
    if not BOLD_ONLY.match(text):
        sys.exit('BUILD FAILED: only inline <b> is allowed here: %r' % text[:80])
    return text


def label(kb):
    return "1 MB" if kb == 1024 else ("2 MB" if kb == 2048 else "%d KB" % kb)


def slug_of(kb):
    return "compress-pdf-to-" + SIZES[kb]["slug"]


def footer():
    size_items = "\n".join(
        '        <li><a href="/%s/">Compress to %s</a></li>' % (slug_of(kb), label(kb))
        for kb in SIZE_ORDER)
    raw_items = "\n".join(
        '        <li><a href="/%s/">%s</a></li>' % (slug, esc(copy.RAW[slug]["short"]))
        for slug in copy.RAW_ORDER)
    return ('<footer class="site-foot"><div class="wrap">'
            '<div class="cols">'
            '<div><b>By target size</b><ul>\n%s\n    </ul></div>'
            '<div><b>By format</b><ul>\n%s\n    </ul></div>'
            '<div><b>%s</b><ul>'
            '        <li><a href="/how-it-works/">How it works</a></li>'
            '        <li><a href="/about/">About</a></li>'
            '        <li><a href="/privacy/">Privacy</a></li>'
            '        <li><a href="/terms/">Terms of Use</a></li>'
            '    </ul></div>'
            '<div><b>Why this exists</b><ul>'
            '        <li>Upload caps on application portals</li>'
            '        <li>Files processed on your device</li>'
            '        <li>Free, unlimited, no sign-up</li>'
            '    </ul></div>'
            '</div>'
            '<p class="legal">© %d %s — free browser-based PDF compression and RAW '
            'conversion. Your files are processed on this device and never uploaded.</p>'
            '</div></footer>') % (size_items, raw_items, esc(BRAND),
                                  datetime.date.today().year, esc(BRAND))


def head(title, desc, page_url, ld_objs, body_attr=""):
    ld = "\n".join(
        '  <script type="application/ld+json">%s</script>' % json.dumps(o, ensure_ascii=False)
        for o in ld_objs)
    if BASE_URL:
        canonical = '  <link rel="canonical" href="%s%s">\n' % (BASE_URL, page_url)
        og = ('  <meta property="og:title" content="%s">\n'
              '  <meta property="og:description" content="%s">\n'
              '  <meta property="og:url" content="%s%s">\n'
              '  <meta property="og:type" content="website">\n') % (esc(title), esc(desc), BASE_URL, page_url)
    else:
        canonical, og = "", ""
    return (
        '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
        '  <meta charset="utf-8">\n'
        '  <meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '  <title>%s</title>\n'
        '  <meta name="description" content="%s">\n'
        '%s%s'
        '  <link rel="icon" href="data:image/svg+xml,%%3Csvg xmlns=\'http://www.w3.org/2000/svg\' viewBox=\'0 0 32 32\'%%3E'
        '<rect width=\'32\' height=\'32\' rx=\'7\' fill=\'%%230f7b4f\'/%%3E'
        '<text x=\'16\' y=\'22\' font-size=\'17\' font-family=\'Arial\' font-weight=\'bold\' fill=\'white\' text-anchor=\'middle\'%%3EM%%3C/text%%3E%%3C/svg%%3E">\n'
        '  <link rel="apple-touch-icon" href="/favicon.svg">\n'
        '  <link rel="stylesheet" href="/assets/style.css">\n'
        '%s</head>\n<body%s>\n%s\n') % (
        esc(title), esc(desc), canonical, og, ld, body_attr, NAV)


def tool_block(heading=None):
    # aria-pressed carries the selection to assistive tech: the --on class is
    # CSS only, so without it a screen reader cannot tell which target is set.
    chips = "\n".join(
        '      <button class="chip" type="button" data-kb="%d" aria-pressed="false">%s</button>' % (kb, label(kb))
        for kb in SIZE_ORDER)
    # The heading only appears when the page shows more than one tool, where the
    # panels have to be told apart.
    head = '    <h2 class="tool__name">%s</h2>\n' % esc(heading) if heading else ''
    return ('  <section class="tool" id="tool">\n'
            '%s'
            '    <div class="chips" id="chips" role="group" aria-label="Target size">\n'
            '      <span class="tool__target" style="margin:0 8px 0 0;align-self:center">Target size:</span>\n'
            '%s\n'
            '    </div>\n'
            '    <p class="tool__target">Selected: <strong id="target-label">300 KB</strong></p>\n'
            '    <label class="drop" id="drop">\n'
            '      <strong>Drop your PDF here</strong>\n'
            '      <span class="hint">or click to choose files — processed on this device, never uploaded</span>\n'
            '      <input class="file-input" type="file" id="file-input" accept="application/pdf,.pdf" multiple>\n'
            '    </label>\n'
            '    <p class="status" id="status" role="status" aria-live="polite"></p>\n'
            '    <ul class="queue" id="queue"></ul>\n'
            '    <button class="btn" type="button" id="download-all" hidden>Download all (.zip)</button>\n'
            '  </section>') % (head, chips)


RAW_QUALITY = (("High", "0.92"), ("Standard", "0.85"), ("Small", "0.72"))

# The RAW drop box uses a different id on purpose: the scope gate tells the two
# tool families apart by marker, so "raw-drop" must not match the PDF marker.
RAW_ACCEPT = (".arw,.srf,.sr2,.cr2,.cr3,.nef,.nrw,.dng,.orf,.raf,.rw2,.raw,.pef,"
              ".srw,.erf,.kdc,.dcr,.mos,.3fr,.iiq,.rwl,.mef,.mrw,.x3f,.jpg,.jpeg")


def raw_tool_block(heading=None):
    chips = "\n".join(
        '      <button class="chip%s" type="button" data-q="%s" aria-pressed="%s">%s</button>'
        % (" chip--on" if name == "Standard" else "", q,
           "true" if name == "Standard" else "false", name)
        for name, q in RAW_QUALITY)
    head = '    <h2 class="tool__name">%s</h2>\n' % esc(heading) if heading else ''
    return ('  <section class="tool" id="raw-tool">\n'
            '%s'
            '    <div class="chips" id="raw-quality" role="group" aria-label="JPEG quality">\n'
            '      <span class="tool__target" style="margin:0 8px 0 0;align-self:center">Quality:</span>\n'
            '%s\n'
            '    </div>\n'
            '    <p class="tool__target">Selected: <strong id="raw-quality-label">Standard</strong></p>\n'
            '    <label class="drop" id="raw-drop">\n'
            '      <strong>Drop a RAW file here</strong>\n'
            '      <span class="hint">or click to choose files — converted on this device, never uploaded</span>\n'
            '      <input class="file-input" type="file" id="raw-input" accept="%s" multiple>\n'
            '    </label>\n'
            '    <p class="status" id="raw-status" role="status" aria-live="polite"></p>\n'
            '    <ul class="queue" id="raw-queue"></ul>\n'
            '  </section>') % (head, chips, RAW_ACCEPT)


def rawlinks(current=None):
    parts = []
    for slug in copy.RAW_ORDER:
        if slug == current:
            continue
        parts.append('<a href="/%s/">%s</a>' % (slug, esc(copy.RAW[slug]["short"])))
    prefix = "Other formats: " if current else "Convert a different format: "
    return '<p class="sizelinks">%s%s</p>' % (prefix, "".join(parts))


def sizelinks(current_kb=None):
    parts = []
    for kb in SIZE_ORDER:
        if kb == current_kb:
            continue
        parts.append('<a href="/%s/">%s</a>' % (slug_of(kb), label(kb)))
    prefix = "Other targets: " if current_kb else "Common targets: "
    return '<p class="sizelinks">%s%s</p>' % (prefix, "".join(parts))


def faq_block(faq):
    items = "\n".join(
        '    <details><summary>%s</summary><p>%s</p></details>' % (esc(q), esc(a)) for q, a in faq)
    return '  <div class="faq">\n%s\n  </div>' % items


def faq_ld(faq):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in faq],
    }


def faq_section(title, faq):
    return '  <section class="content faq"><h2>%s</h2>\n%s\n  </section>' % (
        esc(title), faq_block(faq).lstrip())


FAQ_ITEM_RE = re.compile(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", re.S)
LD_BLOCK_RE = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def norm(text):
    return re.sub(r"\s+", " ", text).strip()


def check_faq(doc, path, failures):
    """Structured equality: the visible <details> pairs and the FAQPage
    mainEntity pairs must be the same set. A substring test would let any prefix
    of an answer through, and because both sides read the same copy list, an
    edit that only reached one of them would pass unnoticed."""
    visible = {(norm(html.unescape(q)), norm(html.unescape(a)))
               for q, a in FAQ_ITEM_RE.findall(doc)}
    for obj in LD_BLOCK_RE.findall(doc):
        try:
            data = json.loads(obj)
        except ValueError:
            failures.append("%s: unparsable JSON-LD" % path)
            continue
        if not isinstance(data, dict) or data.get("@type") != "FAQPage":
            continue
        items = data.get("mainEntity")
        if not isinstance(items, list) or not items:
            failures.append("%s: FAQPage without a mainEntity list" % path)
            continue
        pairs = []
        for item in items:
            answer = item.get("acceptedAnswer") if isinstance(item, dict) else None
            q = norm(item.get("name") or "") if isinstance(item, dict) else ""
            a = norm(answer.get("text") or "") if isinstance(answer, dict) else ""
            if not q or not a:
                failures.append("%s: FAQ entry missing name or acceptedAnswer.text" % path)
                continue
            pairs.append((q, a))
        if len(pairs) != len(visible):
            failures.append("%s: %d JSON-LD FAQ entries but %d visible questions on the page"
                            % (path, len(pairs), len(visible)))
        for pair in pairs:
            if pair not in visible:
                failures.append("%s: JSON-LD entry does not match a visible question+answer: %r"
                                % (path, pair[0][:70]))
        for pair in visible:
            if pair not in pairs:
                failures.append("%s: visible question is not in the JSON-LD: %r"
                                % (path, pair[0][:70]))


REF_RE = re.compile(r'(?:href|src)="(/[^"]*)"')
TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S)
DESC_RE = re.compile(r'<meta name="description" content="([^"]*)"', re.S)


def check_dist():
    """Post-build gates: every same-site href/src must land on a real file, and
    no two pages may share a title or a meta description."""
    failures = []
    seen = {"title": {}, "meta description": {}}
    for path in sorted(DIST.rglob("*.html")):
        rel = path.relative_to(DIST).as_posix()
        doc = path.read_text(encoding="utf-8")
        for tag, where in ((TITLE_RE, "title"), (DESC_RE, "meta description")):
            match = tag.search(doc)
            if not match:
                continue
            value = norm(html.unescape(match.group(1)))
            bucket = seen[where]
            if value in bucket:
                failures.append("%s: %s duplicates %s: %r" % (rel, where, bucket[value], value[:70]))
            else:
                bucket[value] = rel
        for ref in REF_RE.findall(doc):
            target = DIST / ref.strip("/")
            if not (target.exists() or (target / "index.html").exists()):
                failures.append("%s: link to a file that is not in dist: %s" % (rel, ref))
    return failures


ASSET_NAMES = ("app.js", "raw.js", "style.css")


def hashed_assets():
    """:"/assets is served with max-age=31536000, immutable, so an unversioned
    filename pins the old bytes on every returning visitor for a year. A digest
    in the name makes new content a new URL instead."""
    out = {}
    for name in ASSET_NAMES:
        stem, ext = pathlib.Path(name).stem, pathlib.Path(name).suffix
        digest = hashlib.sha256((SRC / name).read_bytes()).hexdigest()[:10]
        out[name] = "%s.%s%s" % (stem, digest, ext)
    return out


def write_assets(hashed):
    out = DIST / "assets"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for name, digest_name in hashed.items():
        shutil.copy(SRC / name, out / digest_name)


def version_asset_refs(hashed):
    """Templates emit the stable /assets/<name> path and one pass rewrites it
    everywhere in dist, so pages and the copied-in harness share the same URL."""
    for path in sorted(DIST.rglob("*.html")):
        doc = path.read_text(encoding="utf-8")
        for name, digest_name in hashed.items():
            doc = doc.replace('"/assets/%s"' % name, '"/assets/%s"' % digest_name)
        path.write_text(doc, encoding="utf-8")


def check_assets(hashed):
    failures = []
    wanted = set(hashed.values())
    present = {p.name for p in (DIST / "assets").glob("*")}
    for stale in sorted(present - wanted):
        failures.append("dist/assets: stale artifact: %s" % stale)
    for missing in sorted(wanted - present):
        failures.append("dist/assets: artifact was not written: %s" % missing)
    for path in sorted(DIST.rglob("*.html")):
        doc = path.read_text(encoding="utf-8")
        for name in ASSET_NAMES:
            if '"/assets/%s"' % name in doc:
                failures.append("%s: still references the unhashed /assets/%s"
                                % (path.relative_to(DIST).as_posix(), name))
    return failures


PDF_TOOL_MARKER = re.compile(r'id="drop"')
RAW_TOOL_MARKER = re.compile(r'id="raw-drop"')

# Two independent engines, one controller each. The stylesheet is deliberately in
# neither: every page needs it.
#   PDF: pdf.js + pdf-lib + JSZip (~921 KB raw / ~314 KB gzipped), fetched by app.js
#   RAW: LibRaw compiled to WebAssembly (~1.0 MB wasm, ~385 KB gzipped), fetched by raw.js
#
# Neither bundle is a script tag any more, so "this page has a PDF tool" is now
# exactly "this page ships app.js" — the controller is the only trace left.
PDF_ENGINE_RE = re.compile(r'<script[^>]+src="/assets/app\.[^"]*"')
RAW_ENGINE_RE = re.compile(r'<script[^>]+src="/assets/raw\.[^"]*"')

# Nothing may point straight at an engine file. If one did, the download would be
# back on page load while the scope check still passed, so this is checked
# separately rather than folded into it.
EAGER_ENGINE_RE = re.compile(
    r'<script[^>]+src="/vendor/(?:pdf\.min|pdf\.worker\.min|pdf-lib\.min|jszip\.min)\.js"'
    r'|<script[^>]+src="/vendor/rawconvert/')

# Engine paths a controller names. They are no longer visible in the HTML, so a
# typo in one would only surface when a real visitor dropped a file.
ENGINE_URL_RE = re.compile(r'["\'](/(?:vendor|assets)/[A-Za-z0-9._/-]+)["\']')


def engine_scope_problems(rel, doc):
    """Pure check over one page, so the gate and its regression tests share it.

    A page must load an engine exactly when it renders that engine's tool. Both
    directions cost real money: shipping the PDF bundle to a text page wastes
    ~314 KB gzipped per visitor, and a RAW page that forgets the WASM is simply
    broken. With two engines the old two-way check is not enough either, since a
    page could load the wrong one and still pass.
    """
    problems = []
    want_pdf = bool(PDF_TOOL_MARKER.search(doc))
    want_raw = bool(RAW_TOOL_MARKER.search(doc))
    got_pdf = bool(PDF_ENGINE_RE.search(doc))
    got_raw = bool(RAW_ENGINE_RE.search(doc))

    if want_pdf and not got_pdf:
        problems.append("%s: renders the PDF tool but loads no PDF engine" % rel)
    if got_pdf and not want_pdf:
        problems.append("%s: loads the PDF engine but renders no PDF tool" % rel)
    if want_raw and not got_raw:
        problems.append("%s: renders the RAW tool but loads no RAW engine" % rel)
    if got_raw and not want_raw:
        problems.append("%s: loads the RAW engine but renders no RAW tool" % rel)
    return problems


def check_engine_scope():
    """The harness drives both engines itself and is exempt."""
    failures = []
    for path in sorted(DIST.rglob("*.html")):
        rel = path.relative_to(DIST).as_posix()
        if rel.startswith("tests/"):
            continue
        failures.extend(engine_scope_problems(rel, path.read_text(encoding="utf-8")))
    return failures


def check_no_eager_engines():
    """No page may pull an engine bundle in as a script tag.

    Both bundles are fetched by their controller on demand now. Re-adding a tag
    would quietly put ~921 KB back on every tool page, and the scope check would
    still pass because it only asks whether the controller is there. The harness
    is exempt: it deliberately loads both engines to drive them directly.
    """
    failures = []
    for path in sorted(DIST.rglob("*.html")):
        rel = path.relative_to(DIST).as_posix()
        if rel.startswith("tests/"):
            continue
        for m in EAGER_ENGINE_RE.finditer(path.read_text(encoding="utf-8")):
            failures.append("%s: loads an engine directly (%s) — it must go through "
                            "the controller, or every visitor pays for it on load"
                            % (rel, m.group(0)[:70]))
    return failures


def check_engine_urls():
    """Every engine path a controller names must exist in dist/.

    These paths used to be visible in the HTML, where a missing file showed up as
    a dead link in the scope check. They are JavaScript strings now, so the only
    thing that can catch a typo before a user does is reading them back out.
    """
    failures = []
    for stem in ("app", "raw"):
        for path in sorted(DIST.glob("assets/%s.*.js" % stem)):
            text = path.read_text(encoding="utf-8")
            rel = path.relative_to(DIST).as_posix()
            for url in sorted(set(ENGINE_URL_RE.findall(text))):
                if not (DIST / url.lstrip("/")).exists():
                    failures.append("%s names %s, which is not in dist/" % (rel, url))
    return failures


# Files each engine needs at runtime. The RAW engine is loaded by JavaScript
# (the worker does importScripts(coreUrl) and resolves the .wasm through
# wasmUrl), so none of it appears as a <script src> in the HTML and the scope
# gate above cannot see it. Without this check, a page could be shipped with the
# engine directory missing and the build would still report success.
PDF_ENGINE_FILES = ("pdf.min.js", "pdf-lib.min.js", "jszip.min.js", "pdf.worker.min.js")
RAW_ENGINE_FILES = ("index.js", "worker-client.js", "worker-bridge.js", "worker.js",
                    "rawconvert-core.js", "rawconvert-core.wasm")


def check_engine_files():
    failures = []
    docs = [(p.relative_to(DIST).as_posix(), p.read_text(encoding="utf-8"))
            for p in sorted(DIST.rglob("*.html"))
            if not p.relative_to(DIST).as_posix().startswith("tests/")]
    for marker, folder, names in (
            (PDF_TOOL_MARKER, "vendor", PDF_ENGINE_FILES),
            (RAW_TOOL_MARKER, "vendor/rawconvert", RAW_ENGINE_FILES)):
        if not any(marker.search(doc) for _, doc in docs):
            continue
        for name in names:
            if not (DIST / folder / name).exists():
                failures.append("dist/%s/%s is missing but pages rendering that tool exist"
                                % (folder, name))
    return failures


def scripts(kind="pdf"):
    """kind is "pdf", "raw" or "none" — which engine bundle this page needs.

    defer keeps the files executing in document order while freeing the parser to
    finish the DOM first; the controllers only read the page, so they still run
    before DOMContentLoaded.

    Neither bundle is fetched at load. The PDF controller injects its three
    library files the moment a visitor shows intent to drop a file, and the RAW
    controller imports its worker the same way. What a page ships is therefore
    the controller only — which is exactly what the scope gate keys off, so
    sending app.js to a text page is still the mistake it was written to catch.
    """
    if kind == "none":
        return '</body>\n</html>\n'
    if kind == "both":
        # The homepage renders both tools. Both bundles are still fetched on
        # demand, so the only thing this costs a visitor is the second controller
        # (~10 KB); nobody downloads an engine they do not use.
        return ('  <script defer src="/assets/app.js"></script>\n'
                '  <script defer src="/assets/raw.js"></script>\n'
                '</body>\n</html>\n')
    if kind == "raw":
        # The RAW engine (worker, glue, WASM) is fetched by raw.js on demand.
        return ('  <script defer src="/assets/raw.js"></script>\n'
                '</body>\n</html>\n')
    # pdf.js, pdf-lib and JSZip are fetched by app.js on demand.
    return ('  <script defer src="/assets/app.js"></script>\n'
            '</body>\n</html>\n')


def page(title, desc, page_url, ld_objs, body_attr, inner, kind="pdf"):
    return (head(title, desc, page_url, ld_objs, body_attr)
            + inner + "\n" + footer() + "\n" + scripts(kind))


def prose_page(h1, lede, sections, note_html):
    """The four prose pages (how-it-works, privacy, about, terms) share one
    shape: a hero, h2 sections of paragraphs, and a closing note."""
    secs = "\n".join('      <h2>%s</h2>\n%s' % (
        esc(t), "\n".join('      <p>%s</p>' % esc(p) for p in paras))
        for t, paras in sections)
    return ('  <section class="hero wrap">\n'
            '    <h1>%s</h1>\n'
            '    <p class="lede">%s</p>\n'
            '  </section>\n'
            '  <div class="wrap">\n'
            '    <section class="content">\n%s\n'
            '    </section>\n'
            '    <div class="note">%s</div>\n'
            '  </div>\n') % (esc(h1), esc(lede), secs, note_html)


MANIFEST_NAME = ".build-manifest.json"


def produced_set(written, hashed):
    """Everything this build writes into dist, as dist-relative paths."""
    files = set(written)
    files.update("assets/%s" % name for name in hashed.values())
    for item in VENDOR.rglob("*"):
        if item.is_file():
            files.add("vendor/" + item.relative_to(VENDOR).as_posix())
    return files


def clean_stale(produced):
    """Remove files a previous build wrote that this one did not.

    Wiping dist/ would be simpler, but it deletes the whole tree every time and
    a stale page would otherwise stay live forever - the asset gate only covers
    dist/assets. Comparing against the previous manifest removes exactly the
    leftovers and nothing else."""
    manifest = DIST / MANIFEST_NAME
    previous = set()
    if manifest.exists():
        try:
            previous = set(json.loads(manifest.read_text(encoding="utf-8")))
        except (ValueError, OSError):
            previous = set()

    removed = []
    for rel in sorted(previous - produced):
        path = DIST / rel
        if path.is_file():
            path.unlink()
            removed.append(rel)

    # Drop directories the removals left empty, shallowest last.
    for path in sorted((p for p in DIST.rglob("*") if p.is_dir()),
                       key=lambda p: len(p.parts), reverse=True):
        try:
            path.rmdir()
        except OSError:
            pass

    manifest.write_text(json.dumps(sorted(produced), indent=1), encoding="utf-8")
    return removed


# The files whose contents end up in the pages. A change to any of them is a
# change to every page, which is why one date serves the whole sitemap.
CONTENT_SOURCES = ("src", "build.py", "vercel.json")


def _git(args):
    try:
        out = subprocess.run(["git"] + args, cwd=str(ROOT),
                             capture_output=True, text=True, timeout=15)
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    stamp = out.stdout.strip()
    return stamp if re.match(r"^\d{4}-\d{2}-\d{2}$", stamp) else None


def content_date():
    """The date the page content last changed, or None if that cannot be known.

    This used to be datetime.date.today(), which meant every deploy stamped all
    fifteen pages with the build date. Google's sitemap documentation says it
    ignores a lastmod that moves on every build, so the field was doing nothing —
    worse than nothing, since an unreliable lastmod costs trust in the rest of
    the file. Taking the date of the last commit that touched the sources makes
    it move only when something actually changed.

    None means "no reliable answer", and the caller then omits lastmod entirely.
    The fallback is deliberately not today's date or a file mtime: a fresh
    checkout's mtimes are the checkout time, which is the same lie in different
    clothes. Google's own guidance is to omit the field rather than guess.
    """
    # The last commit that touched the sources. In a shallow clone this can come
    # back empty even though HEAD is usable, hence the second attempt.
    return (_git(["log", "-1", "--format=%cs", "--"] + list(CONTENT_SOURCES))
            or _git(["log", "-1", "--format=%cs"]))


def build():
    failures = []
    # dist/ is not wiped. A recursive delete of the whole tree is a bulk delete
    # of every page and vendored file, and it is also unnecessary: this build
    # overwrites everything it produces, so the only thing left to do is remove
    # what a previous build left behind (see clean_stale). That keeps the number
    # of deletions per build small enough to see in a diff.
    DIST.mkdir(parents=True, exist_ok=True)
    hashed = hashed_assets()
    write_assets(hashed)
    vendor_out = DIST / "vendor"
    vendor_out.mkdir(exist_ok=True)
    # Copy the whole vendor tree, not just the top-level files: the RAW engine
    # is a directory of its own (glue + .wasm + worker + client).
    for item in sorted(VENDOR.iterdir()):
        if item.is_dir():
            shutil.copytree(item, vendor_out / item.name, dirs_exist_ok=True)
        else:
            shutil.copy(item, vendor_out / item.name)

    written = []
    html_pages = []

    def emit(rel, html):
        p = DIST / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(html, encoding="utf-8")
        check_faq(html, rel, failures)
        written.append(rel)
        html_pages.append(rel)

    # ---- index ----
    idx = copy.INDEX
    ld_index = [
        {"@context": "https://schema.org", "@type": "WebApplication",
         "name": BRAND, "url": (BASE_URL or "") + "/",
         "applicationCategory": "BusinessApplication", "operatingSystem": "Any",
         "browserRequirements": "Requires JavaScript",
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}},
        faq_ld(idx["faq"]),
    ]
    steps = "\n".join(
        '      <li><b>%s</b>%s</li>' % (esc(t), esc(d)) for t, d in idx["steps"])
    # Both tools go on the homepage, side by side. They serve audiences that do
    # not overlap, so neither belongs below the other: someone who came for the
    # RAW converter should not have to scroll past a PDF tool to reach it. The
    # engines are fetched on demand, so hosting both here costs one extra ~10 KB
    # controller and nothing else — a visitor downloads only what they use.
    tools = ('  <div class="tools">\n%s\n%s\n  </div>'
             % (tool_block(idx["tool_pdf"]), raw_tool_block(idx["tool_raw"])))
    body = (
        '  <section class="hero wrap">\n'
        '    <h1>%s</h1>\n'
        '    <p class="sub">%s</p>\n'
        '  </section>\n'
        '  <div class="wrap">\n'
        '%s\n'
        '    <div class="note"><b>Neither file is uploaded.</b> Both tools run in this tab — drop a file, '
        'download the result. Works for confidential scans and IDs.</div>\n'
        '    <section class="content"><h2>Compressing a PDF</h2>\n'
        '      <p class="lede">%s</p>\n'
        '      <ol class="steps">\n%s\n      </ol>\n'
        '    </section>\n'
        '%s\n'
        '%s\n'
        '  </div>\n') % (esc(idx["h1"]), bold(idx["sub"]), tools, esc(idx["intro"]),
                         steps, sizelinks(),
                         faq_section("Frequently asked questions", idx["faq"]))
    emit("index.html", page(
        "Compress PDF or Convert RAW to JPG — No Upload | %s" % BRAND,
        idx["meta_desc"], "/", ld_index, "", body, kind="both"))

    # ---- size landing pages ----
    for kb in SIZE_ORDER:
        c = SIZES[kb]
        url = "/%s/" % slug_of(kb)
        ld = [faq_ld(c["faq"])]
        why = "\n".join('      <p>%s</p>' % esc(p) for p in c["why"])
        body = (
            '  <section class="hero wrap">\n'
            '    <h1>%s</h1>\n'
            '    <p class="lede">%s</p>\n'
            '  </section>\n'
            '  <div class="wrap">\n'
            '%s\n'
            '%s\n'
            '    <section class="content">\n'
            '      <h2>%s</h2>\n%s\n'
            '      <div class="note"><b>Free and unlimited.</b> No account, no watermark, no daily cap — '
            'and the file is processed on your device, never on a server.</div>\n'
            '    </section>\n'
            '%s\n'
            '  </div>\n') % (esc(c["h1"]), esc(c["lead"]), tool_block(), sizelinks(kb),
                             esc(c["why_title"]), why,
                             faq_section("Questions about compressing to %s" % label(kb), c["faq"]))
        emit("%s/index.html" % slug_of(kb), page(
            "%s Online — Free & Unlimited | %s" % (c["h1"], BRAND),
            c["meta_desc"], url, ld, ' data-target-kb="%d"' % kb, body))

    # ---- RAW to JPG family ----
    # Same page shape as the size pages, different engine: these load the LibRaw
    # WASM bundle through /assets/raw.js instead of the PDF libraries.
    for slug in copy.RAW_ORDER:
        c = copy.RAW[slug]
        url = "/%s/" % slug
        why = "\n".join('      <p>%s</p>' % esc(p) for p in c["why"])
        body = (
            '  <section class="hero wrap">\n'
            '    <h1>%s</h1>\n'
            '    <p class="lede">%s</p>\n'
            '  </section>\n'
            '  <div class="wrap">\n'
            '%s\n'
            '%s\n'
            '    <section class="content">\n'
            '      <h2>%s</h2>\n%s\n'
            '      <div class="note"><b>Nothing is uploaded.</b> The RAW file is decoded in this tab by '
            'LibRaw compiled to WebAssembly — no upload step, no server copy, no account.</div>\n'
            '    </section>\n'
            '%s\n'
            '  </div>\n') % (esc(c["h1"]), esc(c["lead"]), raw_tool_block(), rawlinks(slug),
                             esc(c["why_title"]), why,
                             faq_section("Questions about converting %s" % c["short"], c["faq"]))
        emit("%s/index.html" % slug, page(
            c["title"], c["meta_desc"], url, [faq_ld(c["faq"])], "", body, kind="raw"))

    # ---- how it works ----
    hw = copy.HOW
    emit("how-it-works/index.html", page(
        "%s — Lossless First | %s" % (hw["h1"], BRAND),
        hw["meta_desc"], "/how-it-works/", [], "",
        prose_page(hw["h1"], hw["lede"], hw["sections"],
                   'Try it yourself: drop a file on the <a href="/">homepage</a> '
                   'and watch the badge — the numbers it reports are real.'),
        kind="none"))

    # ---- privacy ----
    pv = copy.PRIVACY
    emit("privacy/index.html", page(
        "%s | %s" % (pv["h1"], BRAND), pv["meta_desc"], "/privacy/", [], "",
        prose_page(pv["h1"], pv["lede"], pv["sections"],
                   'The claim is checkable: open DevTools → Network, drop a file, '
                   'and confirm no request carries it. Start on the <a href="/">homepage</a>.'),
        kind="none"))

    # ---- about ----
    # AdSense reviewers look for an About page alongside the privacy policy, and
    # a plain-text contact address is part of what makes the site creditable.
    ab = copy.ABOUT
    emit("about/index.html", page(
        "%s | %s" % (ab["h1"], BRAND), ab["meta_desc"], "/about/", [], "",
        prose_page(ab["h1"], ab["lede"], ab["sections"],
                   'Ready to try it? Drop a PDF on the <a href="/">homepage</a>, or start from the '
                   'exact target your form asks for with the <a href="/compress-pdf-to-300kb/">size pages</a>.'),
        kind="none"))

    # ---- terms of use ----
    tm = copy.TERMS
    emit("terms/index.html", page(
        "%s | %s" % (tm["h1"], BRAND), tm["meta_desc"], "/terms/", [], "",
        prose_page(tm["h1"], tm["lede"], tm["sections"],
                   'These terms cover use of the site only. Your files stay yours and never leave '
                   'your device — see <a href="/privacy/">Privacy</a>.'),
        kind="none"))

    # ---- robots + sitemap ----
    # A browser requests /favicon.ico on a cold load even though every page
    # declares a data: SVG icon, so that request used to 404. Write a real
    # icon file as well, and point the pages at it.
    (DIST / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32">'
        '<rect width="32" height="32" rx="7" fill="#0f7b4f"/>'
        '<text x="16" y="22" font-size="17" font-family="Arial" font-weight="bold" '
        'fill="white" text-anchor="middle">M</text></svg>\n', encoding="utf-8")
    (DIST / "favicon.ico").write_bytes((DIST / "favicon.svg").read_bytes())
    written.extend(["favicon.svg", "favicon.ico"])
    robots = "User-agent: *\nAllow: /\nDisallow: /tests/\n"
    harness = ROOT / "tests" / "harness.html"
    if harness.exists():
        (DIST / "tests").mkdir(exist_ok=True)
        shutil.copy(harness, DIST / "tests" / "harness.html")
        written.append("tests/harness.html")
    if BASE_URL:
        robots += "\nSitemap: %s/sitemap.xml\n" % BASE_URL
        urls = ["/"] + ["/%s/" % slug_of(kb) for kb in SIZE_ORDER] + \
               ["/%s/" % slug for slug in copy.RAW_ORDER] + \
               ["/how-it-works/", "/about/", "/privacy/", "/terms/"]
        # lastmod is omitted rather than guessed when the date is unknown: see
        # content_date() for why a build-date stamp is worse than no stamp.
        stamp = content_date()
        xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for u in urls:
            if stamp:
                xml.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (BASE_URL, u, stamp))
            else:
                xml.append("  <url><loc>%s%s</loc></url>" % (BASE_URL, u))
        xml.append("</urlset>")
        (DIST / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
        written.append("sitemap.xml")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")
    written.append("robots.txt")

    removed = clean_stale(produced_set(written, hashed))
    version_asset_refs(hashed)
    failures.extend(check_assets(hashed))
    failures.extend(check_engine_scope())
    failures.extend(check_no_eager_engines())
    failures.extend(check_engine_urls())
    failures.extend(check_engine_files())
    failures.extend(check_dist())

    if failures:
        print("BUILD FAILED — integrity checks:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    expected_html = 1 + len(SIZE_ORDER) + len(copy.RAW_ORDER) + 4
    print("BUILD OK: %d HTML pages (%d expected), %d files total"
          % (len(html_pages), expected_html, len(written)))
    print("FAQ structured check (JSON-LD == visible details): PASS")
    print("Link + title/description uniqueness: PASS")
    print("Engine scope (PDF pages get the PDF controller, RAW pages the RAW one, text pages neither): PASS")
    print("No page loads an engine bundle directly (both are fetched on demand): PASS")
    print("Every engine path named by a controller exists in dist/: PASS")
    print("Engine files present for every tool page: PASS")
    print("Assets content-hashed: %s" % ", ".join(sorted(hashed.values())))
    # Printed because the fallback is silent otherwise: if a build environment has
    # no usable git metadata the sitemap simply loses lastmod, and this line is
    # how that becomes visible in the deploy log instead of being guessed at.
    print("Sitemap lastmod: %s" % (content_date() or "omitted - no usable git metadata"))
    if removed:
        print("Removed %d stale file(s) from a previous build: %s"
              % (len(removed), ", ".join(removed[:6])))
    if not BASE_URL:
        print("NOTE: BASE_URL not set — canonical/OG/sitemap skipped (set after domain purchase).")


if __name__ == "__main__":
    build()
