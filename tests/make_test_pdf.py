"""Generate a valid uncompressed PDF (stdlib only) for testing a browser PDF compressor."""

import sys
from pathlib import Path

SENTENCES = [
    "The pair distribution function describes how atomic positions are correlated as a "
    "function of real space distance rather than reciprocal space.",
    "Total scattering methods avoid the restrictions of Bragg averaging and therefore "
    "retain information contained in diffuse background intensity.",
    "Before refining a structural model the instrument parameters must be calibrated "
    "using a standard material measured under identical conditions.",
    "Peak broadening at high momentum transfer is dominated by the finite Q resolution "
    "function while low angle peaks reflect correlated microstrain in the lattice.",
    "A careful background subtraction removes the contribution of the capillary air "
    "scattering and leaves the sample signal alone for further processing.",
    "Compressed files load faster on slow connections which matters when a reviewer "
    "opens the supplementary material from a conference laptop.",
    "PDF documents that embed vector figures tend to shrink dramatically when the font "
    "subsets and image streams are reencoded losslessly.",
    "The refinement converged after twelve cycles with a low weighted residual factor "
    "and sensible anisotropic displacement parameters for every atom site.",
    "Care should be taken when truncating the data because sharp termination produces "
    "ripples in real space that mimic genuine short range order.",
    "Synchronization of the detector counter with the motor encoder is essential to "
    "keep the absorption correction geometrically consistent.",
]

LINE_WIDTH = 78


def filler_lines(count):
    words = " ".join(SENTENCES).split()
    lines, current = [], ""
    i = 0
    while len(lines) < count:
        word = words[i % len(words)]
        i += 1
        if current and len(current) + 1 + len(word) > LINE_WIDTH:
            lines.append(current)
            current = word
        else:
            current = f"{current} {word}" if current else word
    if current and len(lines) < count:
        lines.append(current)
    return lines[:count]


def escape(text):
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def content_stream(lines):
    parts = ["BT", "/F1 11 Tf", "1 0 0 1 56 756 Tm", "13 TL"]
    for line in lines:
        parts.append(f"({escape(line)}) Tj T*")
    parts.append("ET")
    return ("\n".join(parts) + "\n").encode("ascii")


def build_pdf(page_count, lines_per_page, include_content=True):
    kids = " ".join(f"{5 + 2 * index} 0 R" for index in range(page_count))
    objects = {
        1: b"<< /Type /Catalog /Pages 2 0 R >>",
        2: f"<< /Type /Pages /Count {page_count} /Kids [{kids}] >>".encode("ascii"),
        3: b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica "
            b"/Encoding /WinAnsiEncoding >>",
        4: b"<< /Producer (make_test_pdf) /Title (Test Document) >>",
    }
    for index in range(page_count):
        page_number = 5 + 2 * index
        stream_number = page_number + 1
        objects[page_number] = (
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 841] "
            f"/Resources << /Font << /F1 3 0 R >> >> "
            f"/Contents {stream_number} 0 R >>"
        ).encode("ascii")
        if include_content:
            body = content_stream(filler_lines(lines_per_page))
            objects[stream_number] = (
                f"<< /Length {len(body)} >>\nstream\n".encode("ascii")
                + body
                + b"endstream"
            )
        else:
            objects[stream_number] = b"<< /Length 0 >>\nstream\nendstream"

    out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xf3\n")
    offsets = {}
    for number in sorted(objects):
        offsets[number] = len(out)
        out += f"{number} 0 obj\n".encode("ascii")
        out += objects[number]
        out += b"\nendobj\n"

    size = len(objects) + 1
    xref_offset = len(out)
    out += f"xref\n0 {size}\n".encode("ascii")
    out += b"0000000000 65535 f \n"
    for number in range(1, size):
        out += f"{offsets[number]:010d} 00000 n \n".encode("ascii")
    out += (
        f"trailer\n<< /Size {size} /Root 1 0 R /Info 4 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode("ascii")
    return bytes(out)


def build_close_to_target(page_count, target_bytes):
    seed = max(8, target_bytes // (LINE_WIDTH * page_count))
    overhead = len(build_pdf(page_count, seed, include_content=False))
    probe = len(build_pdf(page_count, seed + 1))
    per_line = max(1, probe - overhead)

    data = b""
    for _ in range(12):
        lines_per_page = max(1, (target_bytes - overhead) // (page_count * per_line))
        data = build_pdf(page_count, lines_per_page)
        if abs(len(data) - target_bytes) <= max(1024, target_bytes * 0.01):
            break
        per_line = max(1, round(per_line * len(data) / max(1, target_bytes)))
    return data


def main(argv):
    if len(argv) > 1 and argv[1] in ("-h", "--help"):
        print("usage: python tests/make_test_pdf.py <out.pdf> [pages] [target_kb]")
        return 0

    output = Path(argv[1]) if len(argv) > 1 else Path("out.pdf")
    page_count = int(argv[2]) if len(argv) > 2 else 3
    target_kb = int(argv[3]) if len(argv) > 3 else 600
    if page_count < 1:
        raise SystemExit("pages must be >= 1")

    data = build_close_to_target(page_count, target_kb * 1024)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(data)
    print(f"{output} {len(data)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
