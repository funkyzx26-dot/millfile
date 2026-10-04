"""Verify FAQPage JSON-LD entries match the visible text of built HTML (stdlib only)."""

import html
import json
import re
import sys
from pathlib import Path

SCRIPT_RE = re.compile(
    r"<script\b[^>]*?\btype\s*=\s*[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
    re.IGNORECASE | re.DOTALL,
)
TAG_RE = re.compile(r"<[^>]+>")
DROP_RE = re.compile(r"<(script|style)\b.*?</\1>", re.IGNORECASE | re.DOTALL)
SPACE_RE = re.compile(r"\s+")


def normalize(text):
    return SPACE_RE.sub(" ", text).strip()


def visible_text(document):
    without_embeds = DROP_RE.sub(" ", document)
    return normalize(html.unescape(TAG_RE.sub(" ", without_embeds)))


def faq_entries(payload):
    documents = payload if isinstance(payload, list) else [payload]
    for document in documents:
        if not isinstance(document, dict):
            continue
        graph = document.get("@graph")
        members = graph if isinstance(graph, list) else [document]
        for member in members:
            if isinstance(member, dict) and member.get("@type") == "FAQPage":
                yield from entries_of(member)


def entries_of(page):
    main_entity = page.get("mainEntity")
    items = main_entity if isinstance(main_entity, list) else [main_entity]
    for item in items:
        if isinstance(item, dict):
            yield item


def strings_of(item):
    question = item.get("name")
    yield "name", question if isinstance(question, str) else None
    answer = item.get("acceptedAnswer")
    answers = answer if isinstance(answer, list) else [answer]
    for entry in answers:
        if isinstance(entry, dict) and isinstance(entry.get("text"), str):
            yield "acceptedAnswer.text", entry["text"]


def check(dist_dir):
    root = Path(dist_dir)
    failures = []
    checked = 0
    verified = 0

    paths = [root] if root.is_file() else sorted(root.rglob("*.html"))
    for path in paths:
        checked += 1
        try:
            document = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            failures.append(f"{path}: unreadable ({error})")
            continue
        text = visible_text(document)

        for block in SCRIPT_RE.findall(document):
            try:
                payload = json.loads(block)
            except json.JSONDecodeError as error:
                print(f"warn: {path}: skipping unparsable JSON-LD ({error})")
                continue
            for item in faq_entries(payload):
                verified += 1
                for field, value in strings_of(item):
                    if value is None:
                        failures.append(f"{path}: FAQ entry missing {field}")
                        continue
                    needle = normalize(value)
                    if needle and needle not in text:
                        failures.append(f"{path}: missing {field} string: {needle[:80]}")

    return checked, verified, failures


def main(argv):
    if len(argv) != 2:
        print("usage: python tests/check_faq.py <dist_dir>", file=sys.stderr)
        return 2

    checked, verified, failures = check(argv[1])
    if failures:
        for failure in failures:
            print(f"FAIL: {failure}")
        print(f"{len(failures)} failure(s) in {checked} file(s)", file=sys.stderr)
        return 1

    print(f"OK: {checked} files checked, {verified} FAQ entries verified")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
