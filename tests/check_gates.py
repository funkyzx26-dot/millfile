#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fail-closed tests for build.py's engine-scope gate.

Why this file exists: a gate that only ever runs against a correct build has
never been shown to reject anything. When the PDF engine was first scoped to
tool pages, the gate regex only matched /vendor/ and quietly let a stray
app.js through - the mistake was invisible until a counter-example was fed to
it. With two engines the failure modes multiply: a page can load the wrong
engine, or both, or neither, and each of those is a different bug.

Run: python3 tests/check_gates.py     (exit code 0 = all cases as expected)
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import build  # noqa: E402  (path has to be set first)

PDF_SCRIPTS = (
    '  <script defer src="/vendor/pdf.min.js"></script>\n'
    '  <script defer src="/vendor/pdf-lib.min.js"></script>\n'
    '  <script defer src="/vendor/jszip.min.js"></script>\n'
    '  <script defer src="/assets/app.js"></script>\n'
)
RAW_SCRIPTS = '  <script defer src="/assets/raw.js"></script>\n'
RAW_VENDOR_TAG = '  <script defer src="/vendor/rawconvert/rawconvert-core.js"></script>\n'
PDF_TOOL = '<label class="drop" id="drop"></label>'
RAW_TOOL = '<label class="drop" id="raw-drop"></label>'

# (name, html, expect_problems)
CASES = [
    ("pdf page + pdf engine", PDF_TOOL + PDF_SCRIPTS, False),
    ("pdf page + pdf engine + raw engine", PDF_TOOL + PDF_SCRIPTS + RAW_SCRIPTS, True),
    ("pdf page + no engine", PDF_TOOL, True),
    ("pdf page + raw engine only", PDF_TOOL + RAW_SCRIPTS, True),

    ("raw page + raw engine", RAW_TOOL + RAW_SCRIPTS, False),
    ("raw page + raw vendor tag", RAW_TOOL + RAW_VENDOR_TAG + RAW_SCRIPTS, False),
    ("raw page + no engine", RAW_TOOL, True),
    ("raw page + pdf engine only", RAW_TOOL + PDF_SCRIPTS, True),

    ("text page + nothing", "<p>hello</p>", False),
    ("text page + pdf engine", "<p>hello</p>" + PDF_SCRIPTS, True),
    ("text page + raw engine", "<p>hello</p>" + RAW_SCRIPTS, True),

    ("both tools + both engines", PDF_TOOL + RAW_TOOL + PDF_SCRIPTS + RAW_SCRIPTS, False),
    ("both tools + pdf engine only", PDF_TOOL + RAW_TOOL + PDF_SCRIPTS, True),
]

# A rawconvert file must not be mistaken for the PDF bundle, and vice versa.
# `id="raw-drop"` must not satisfy the PDF marker either.
REGEX_CASES = [
    ("rawconvert path is not the pdf engine",
     bool(build.PDF_ENGINE_RE.search('<script src="/vendor/rawconvert/rawconvert-core.js"></script>')), False),
    ("pdf.min.js is not the raw engine",
     bool(build.RAW_ENGINE_RE.search('<script src="/vendor/pdf.min.js"></script>')), False),
    ("raw.js is the raw engine",
     bool(build.RAW_ENGINE_RE.search('<script src="/assets/raw.js"></script>')), True),
    ("raw-drop does not match the pdf marker",
     bool(build.PDF_TOOL_MARKER.search(RAW_TOOL)), False),
    ("drop marker does not match the raw marker",
     bool(build.RAW_TOOL_MARKER.search(PDF_TOOL)), False),
    ("hashed pdf asset still counts",
     bool(build.PDF_ENGINE_RE.search('<script src="/assets/app.1ff1c74d79.js"></script>')), True),
    ("hashed raw asset still counts",
     bool(build.RAW_ENGINE_RE.search('<script src="/assets/raw.8505f80d6c.js"></script>')), True),
]


def main():
    bad = 0
    for name, html, expect_problems in CASES:
        problems = build.engine_scope_problems("test.html", html)
        got = bool(problems)
        ok = got == expect_problems
        bad += 0 if ok else 1
        print("%s %-38s %s" % ("PASS" if ok else "FAIL", name,
                               ("rejected: " + problems[0]) if problems else "accepted"))

    for name, got, want in REGEX_CASES:
        ok = got == want
        bad += 0 if ok else 1
        print("%s %-38s %s" % ("PASS" if ok else "FAIL", name, got))

    # Integration: the real dist must be clean (nothing to re-check if it has
    # not been built yet).
    dist = ROOT / "dist"
    if (dist / "index.html").exists():
        integration = build.check_engine_scope() + build.check_engine_files()
        ok = not integration
        bad += 0 if ok else 1
        print("%s %-38s %s" % ("PASS" if ok else "FAIL", "built dist passes both gates",
                               integration[:1] or "clean"))
        raw_pages = sum(1 for p in dist.rglob("index.html")
                        if build.RAW_TOOL_MARKER.search(p.read_text(encoding="utf-8")))
        print("     (%d page(s) render the RAW tool)" % raw_pages)
    else:
        print("SKIP built dist not present - run build.py first for the integration case")

    print("\n%s: %d case(s) did not behave as expected" % ("OK" if not bad else "PROBLEMS", bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
