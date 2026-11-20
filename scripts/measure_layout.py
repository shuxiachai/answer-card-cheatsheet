"""Measure a 5-column cheatsheet PDF built by build_cheatsheet.py.

Usage: python measure_layout.py sheet.pdf [--font PT] [--margin-cm CM] [--gap-cm 0.1] [--short 0.25] [--no-points]
                                          [--find TEXT ...] [--lines TEXT ...]
Prints:
- page count and spare lines at the end (or overflow onto page 3+), counting figures as well as text; when the
  content fills clearly less than two sides, the font size that would roughly fill them;
- column-bottom gaps: columns that end one or more lines early because the next block (card title + Q line +
  first point, a code block, a figure) is kept together and did not fit — saving 1–2 lines above such a gap
  pulls the block back and gains the whole gap;
- paragraphs whose last printed line is less than --short of the column width (cheapest places to save a line),
  marked "pt" for answer-card points (--no-points hides them);
- where each --find text sits; for each --lines text, every printed line of that paragraph with its fill.
--font and --margin-cm are read from the PDF when omitted (the most common text size, and the left edge of
the text); give them explicitly only if the detected values printed on the first line look wrong.
"""
from collections import Counter
import argparse
import math
import sys

import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--font", type=float, default=None, help="font size in pt (default: detected)")
ap.add_argument("--margin-cm", type=float, default=None, help="page margin in cm (default: detected)")
ap.add_argument("--gap-cm", type=float, default=0.1)
ap.add_argument("--short", type=float, default=0.25)
ap.add_argument("--no-points", action="store_true", help="leave answer-card points out of the short-line list")
ap.add_argument("--find", nargs="*", default=[])
ap.add_argument("--lines", nargs="*", default=[], help="print every line of the paragraph containing this text")
a = ap.parse_args()

CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
doc = fitz.open(a.pdf)
W, H = doc[0].rect.width, doc[0].rect.height
spans = [s for page in doc for b in page.get_text("dict")["blocks"] for l in b.get("lines", []) for s in l["spans"]
         if s["text"].strip()]
if not spans:
    sys.exit("No text found in the PDF.")
if a.font is None:                      # body size = the size that carries the most characters
    sizes = Counter()
    for s in spans:
        sizes[round(s["size"] * 2) / 2] += len(s["text"])
    a.font = sizes.most_common(1)[0][0]
if a.margin_cm is None:                 # the first line of every paragraph starts at the left margin
    a.margin_cm = round(max(0.0, min(s["bbox"][0] for s in spans)) / 72 * 2.54 * 20) / 20
m = a.margin_cm / 2.54 * 72
gap = a.gap_cm / 2.54 * 72
colw = (W - 2 * m - 4 * gap) / 5
colh = H - 2 * m
line_h = a.font * 1.18
col_lines = colh / line_h
print(f"font {a.font:g} pt, margin {a.margin_cm:g} cm, gap {a.gap_cm:g} cm")
SIDES = "ABCDEFG"


def col_name(key):
    return f"{SIDES[key[0]]}{key[1] + 1}"


bottoms, rows = {}, []
for pno, page in enumerate(doc):
    bars = [d["rect"] for d in page.get_drawings() if d.get("fill") and d["rect"].width > colw * 0.9
            and d["rect"].height < 8 and min(d["fill"]) < 0.8]
    for c in range(5):
        cx0 = m + c * (colw + gap)
        r = {}
        for b in page.get_text("dict")["blocks"]:
            for l in b.get("lines", []):
                for s in l["spans"]:
                    if not s["text"].strip() or not (cx0 - 2 <= s["bbox"][0] < cx0 + colw - 1):
                        continue
                    k = round(s["origin"][1], 1)
                    e = r.setdefault(k, [1e9, 0.0, ""])
                    # Word often draws the space between two runs as a gap, not a character: put it back
                    if e[2] and s["bbox"][0] - cx0 - e[1] > 0.4 and not e[2].endswith(" ") \
                            and not s["text"].startswith(" "):
                        e[2] += " "
                    e[0] = min(e[0], s["bbox"][0] - cx0)
                    e[1] = max(e[1], s["bbox"][2] - cx0)
                    e[2] += s["text"]
                    bottoms[(pno, c)] = max(bottoms.get((pno, c), 0), s["bbox"][3])
        for k in sorted(r):
            bar = any(bb.x0 >= cx0 - 2 and bb.x0 < cx0 + colw and bb.y0 - 1 <= k <= bb.y1 + 1 for bb in bars)
            rows.append((pno, c, k, *r[k], bar))
    for im in page.get_image_info():        # figures take column height too
        x0, y0, x1, y1 = im["bbox"]
        c = max(0, min(4, int((x0 - m + 1) // (colw + gap))))
        bottoms[(pno, c)] = max(bottoms.get((pno, c), 0), min(y1, H - m))
        rows.append((pno, c, round(y0, 1), 0.0, x1 - x0, "[figure]", False))
rows.sort(key=lambda row: row[:3])

last = max(bottoms)
total_lines = 10 * col_lines
if len(doc) > 2:
    over = sum((colh if key != last else bottoms[key] - m) for key in bottoms if key[0] >= 2) / line_h
    print(f"pages={len(doc)}  OVERFLOW ≈ {over:.1f} lines onto page 3+")
else:
    spare = ((H - m - bottoms[last]) + (4 - last[1]) * colh + (1 - last[0]) * 5 * colh) / line_h
    print(f"pages={len(doc)}  ends side {SIDES[last[0]]} column {last[1] + 1}  spare ≈ {spare:.1f} lines")
    if spare > col_lines:               # more than a column empty: suggest a size that roughly fills two sides
        used = (total_lines - spare) / total_lines
        best = math.floor(a.font * math.sqrt(0.97 / used) * 2) / 2
        print(f"  content fills ≈ {used:.0%} of two sides; at ≈ {best:g} pt it would roughly fill them "
              f"(rebuild with font {best:g}, measure again, print-test) — see fitting.md 'Too little content'")

# columns that end early: the next block was kept together and pushed on
gaps = []
remainder = col_lines % 1                 # part of a line that never fits at a column bottom
for key in [(p, c) for p in range(len(doc)) for c in range(5) if (p, c) < last]:
    free = (H - m - bottoms.get(key, m)) / line_h
    whole = int(free - remainder + 0.3)
    if whole >= 1:
        nxt = (key[0], key[1] + 1) if key[1] < 4 else (key[0] + 1, 0)
        first = next((row[5] for row in rows if row[:2] == nxt), "")
        gaps.append((key, free, nxt, first))
if gaps:
    print(f"{len(gaps)} columns end early (the next block did not fit; save 1–2 lines above to pull it back):")
    for key, free, nxt, first in gaps:
        print(f"  {col_name(key)} bottom empty ≈ {free:.1f} lines → {col_name(nxt)} starts with: {first[:60]}")

paras, cur = [], None
for row in rows:
    if row[5] == "[figure]":
        cur = None
        continue
    if row[3] < 1.0 or row[6] or cur is None:
        cur = [row]
        paras.append(cur)
    else:
        cur.append(row)


def is_point(p):
    return p[0][5].lstrip()[:1] in CIRCLED


short = sorted(((p[-1][4] / colw, p) for p in paras if not p[0][6] and len(p) > 1 and p[-1][4] / colw < a.short
                and not (a.no_points and is_point(p))), key=lambda x: x[0])
print(f"{len(short)} paragraphs end with a line < {a.short:.0%} full"
      f"{' (answer-card points hidden)' if a.no_points else ' (pt = answer-card point)'}:")
for f, p in short:
    kind = "pt" if is_point(p) else "  "
    print(f"  {f:.2f}  {col_name(p[0][:2])}  {kind}  {p[0][5][:45]} … {p[-1][5][-30:]}")

for text in a.find:
    for pno, page in enumerate(doc):
        hits = page.search_for(text)
        if hits:
            r = hits[0]
            c = max(0, min(4, int((r.x0 - m) // (colw + gap))))
            print(f"  '{text}': side {SIDES[pno]}, column {c + 1}, {(r.y0 - m) / colh:.0%} down")
            break
    else:
        print(f"  '{text}': not found")

for text in a.lines:
    hit = [p for p in paras if text in " ".join(row[5] for row in p)]
    if not hit:
        print(f"  '{text}': not found (a paragraph broken across columns is listed per column)")
    for p in hit:
        print(f"  '{text}' — {len(p)} lines in {col_name(p[0][:2])}:")
        for row in p:
            print(f"    {row[4] / colw:4.0%}  {row[5]}")
