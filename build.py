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
    return ('<footer class="site-foot"><div class="wrap">'
            '<div class="cols">'
            '<div><b>By target size</b><ul>\n%s\n    </ul></div>'
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
            '<p class="legal">© %d %s — free browser-based PDF compression. '
            'Your documents are processed on this device and never uploaded.</p>'
            '</div></footer>') % (size_items, esc(BRAND), datetime.date.today().year, esc(BRAND))


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


def tool_block():
    # aria-pressed carries the selection to assistive tech: the --on class is
    # CSS only, so without it a screen reader cannot tell which target is set.
    chips = "\n".join(
        '      <button class="chip" type="button" data-kb="%d" aria-pressed="false">%s</button>' % (kb, label(kb))
        for kb in SIZE_ORDER)
    return ('  <section class="tool" id="tool">\n'
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
            '  </section>') % chips


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


ASSET_NAMES = ("app.js", "style.css")


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


TOOL_MARKER = re.compile(r'id="drop"')
# The tool's bundle is the three vendor libraries plus the hashed app bundle.
# The stylesheet is deliberately NOT included: every page needs that one.
ENGINE_SRC_RE = re.compile(r'<script[^>]+src="/(?:vendor/|assets/app\.)[^"]*"')


def check_engine_scope():
    """A page loads the PDF engine exactly when it renders the tool. Shipping
    pdf.js, pdf-lib and JSZip to /how-it-works/ and /privacy/ costs a first-time
    visitor ~314 KB gzipped to parse code that returns at once, and the mirror
    mistake (a tool page with no engine) breaks the site outright. The harness
    drives the engine itself and is exempt."""
    failures = []
    for path in sorted(DIST.rglob("*.html")):
        rel = path.relative_to(DIST).as_posix()
        if rel.startswith("tests/"):
            continue
        doc = path.read_text(encoding="utf-8")
        has_tool = bool(TOOL_MARKER.search(doc))
        has_engine = bool(ENGINE_SRC_RE.search(doc))
        if has_tool and not has_engine:
            failures.append("%s: renders the tool but loads no engine" % rel)
        if has_engine and not has_tool:
            failures.append("%s: loads the engine but renders no tool" % rel)
    return failures


def scripts(with_tool=True):
    # defer keeps the four files executing in document order while freeing the
    # parser to finish the DOM first; app.js only reads the page, so it still
    # runs before DOMContentLoaded.
    #
    # Pages that render no tool must not pull in the engine: pdf.js, pdf-lib and
    # JSZip are 941 KB raw / ~314 KB gzipped, and on /how-it-works/ and /privacy/
    # app.js returns immediately at its `if (!$('drop')) return;` guard, so every
    # byte of that download and parse was wasted on a plain text page.
    if not with_tool:
        return '</body>\n</html>\n'
    return ('  <script defer src="/vendor/pdf.min.js"></script>\n'
            '  <script defer src="/vendor/pdf-lib.min.js"></script>\n'
            '  <script defer src="/vendor/jszip.min.js"></script>\n'
            '  <script defer src="/assets/app.js"></script>\n'
            '</body>\n</html>\n')


def page(title, desc, page_url, ld_objs, body_attr, inner, with_tool=True):
    return (head(title, desc, page_url, ld_objs, body_attr)
            + inner + "\n" + footer() + "\n" + scripts(with_tool))


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


def build():
    failures = []
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir(parents=True)
    hashed = hashed_assets()
    write_assets(hashed)
    (DIST / "vendor").mkdir()
    for f in VENDOR.glob("*.js"):
        shutil.copy(f, DIST / "vendor" / f.name)

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
    body = (
        '  <section class="hero wrap">\n'
        '    <h1>%s</h1>\n'
        '    <p class="sub">%s</p>\n'
        '    <p class="lede">%s</p>\n'
        '  </section>\n'
        '  <div class="wrap">\n'
        '%s\n'
        '    <div class="note"><b>Files never uploaded.</b> Compression runs in this tab — drop a document, '
        'download the result. Works for confidential scans and IDs.</div>\n'
        '    <section class="content"><h2>How it works</h2>\n'
        '      <ol class="steps">\n%s\n      </ol>\n'
        '    </section>\n'
        '%s\n'
        '%s\n'
        '  </div>\n') % (esc(idx["h1"]), bold(idx["sub"]), esc(idx["intro"]),
                         tool_block(), steps, sizelinks(), faq_section("Frequently asked questions", idx["faq"]))
    emit("index.html", page(
        "Compress PDF to an Exact Size — Free, No Upload | %s" % BRAND,
        idx["meta_desc"], "/", ld_index, "", body))

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

    # ---- how it works ----
    hw = copy.HOW
    emit("how-it-works/index.html", page(
        "%s — Lossless First | %s" % (hw["h1"], BRAND),
        hw["meta_desc"], "/how-it-works/", [], "",
        prose_page(hw["h1"], hw["lede"], hw["sections"],
                   'Try it yourself: drop a file on the <a href="/">homepage</a> '
                   'and watch the badge — the numbers it reports are real.'),
        with_tool=False))

    # ---- privacy ----
    pv = copy.PRIVACY
    emit("privacy/index.html", page(
        "%s | %s" % (pv["h1"], BRAND), pv["meta_desc"], "/privacy/", [], "",
        prose_page(pv["h1"], pv["lede"], pv["sections"],
                   'The claim is checkable: open DevTools → Network, drop a file, '
                   'and confirm no request carries it. Start on the <a href="/">homepage</a>.'),
        with_tool=False))

    # ---- about ----
    # AdSense reviewers look for an About page alongside the privacy policy, and
    # a plain-text contact address is part of what makes the site creditable.
    ab = copy.ABOUT
    emit("about/index.html", page(
        "%s | %s" % (ab["h1"], BRAND), ab["meta_desc"], "/about/", [], "",
        prose_page(ab["h1"], ab["lede"], ab["sections"],
                   'Ready to try it? Drop a PDF on the <a href="/">homepage</a>, or start from the '
                   'exact target your form asks for with the <a href="/compress-pdf-to-300kb/">size pages</a>.'),
        with_tool=False))

    # ---- terms of use ----
    tm = copy.TERMS
    emit("terms/index.html", page(
        "%s | %s" % (tm["h1"], BRAND), tm["meta_desc"], "/terms/", [], "",
        prose_page(tm["h1"], tm["lede"], tm["sections"],
                   'These terms cover use of the site only. Your files stay yours and never leave '
                   'your device — see <a href="/privacy/">Privacy</a>.'),
        with_tool=False))

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
               ["/how-it-works/", "/about/", "/privacy/", "/terms/"]
        today = datetime.date.today().isoformat()
        xml = ['<?xml version="1.0" encoding="UTF-8"?>',
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for u in urls:
            xml.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod></url>" % (BASE_URL, u, today))
        xml.append("</urlset>")
        (DIST / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
        written.append("sitemap.xml")
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")
    written.append("robots.txt")

    version_asset_refs(hashed)
    failures.extend(check_assets(hashed))
    failures.extend(check_engine_scope())
    failures.extend(check_dist())

    if failures:
        print("BUILD FAILED — integrity checks:")
        for f in failures:
            print("  -", f)
        sys.exit(1)

    expected_html = 1 + len(SIZE_ORDER) + 4
    print("BUILD OK: %d HTML pages (%d expected), %d files total"
          % (len(html_pages), expected_html, len(written)))
    print("FAQ structured check (JSON-LD == visible details): PASS")
    print("Link + title/description uniqueness: PASS")
    print("Engine scope (only tool pages load the PDF engine): PASS")
    print("Assets content-hashed: %s" % ", ".join(sorted(hashed.values())))
    if not BASE_URL:
        print("NOTE: BASE_URL not set — canonical/OG/sitemap skipped (set after domain purchase).")


if __name__ == "__main__":
    build()
