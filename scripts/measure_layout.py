"""Measure a 5-column cheatsheet PDF built by build_cheatsheet.py.

Usage: python measure_layout.py sheet.pdf [--font PT] [--margin-cm CM] [--gap-cm 0.1] [--short 0.25] [--find TEXT ...]
Prints: page count; spare lines at the end (or overflow onto page 3+); paragraphs whose last printed line is
less than --short of the column width (cheapest places to save a line); where each --find text sits.
--font and --margin-cm are read from the PDF when omitted (the most common text size, and the left edge of
the text); give them explicitly only if the detected values printed on the first line look wrong.
"""
from collections import Counter
import argparse
import sys

import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--font", type=float, default=None, help="font size in pt (default: detected)")
ap.add_argument("--margin-cm", type=float, default=None, help="page margin in cm (default: detected)")
ap.add_argument("--gap-cm", type=float, default=0.1)
ap.add_argument("--short", type=float, default=0.25)
ap.add_argument("--find", nargs="*", default=[])
a = ap.parse_args()

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
print(f"font {a.font:g} pt, margin {a.margin_cm:g} cm, gap {a.gap_cm:g} cm")
SIDES = "ABCDEFG"

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
                    e[0] = min(e[0], s["bbox"][0] - cx0)
                    e[1] = max(e[1], s["bbox"][2] - cx0)
                    e[2] += s["text"]
                    bottoms[(pno, c)] = max(bottoms.get((pno, c), 0), s["bbox"][3])
        for k in sorted(r):
            bar = any(bb.x0 >= cx0 - 2 and bb.x0 < cx0 + colw and bb.y0 - 1 <= k <= bb.y1 + 1 for bb in bars)
            rows.append((pno, c, k, *r[k], bar))

last = max(bottoms)
if len(doc) > 2:
    over = sum((colh if key != last else bottoms[key] - m) for key in bottoms if key[0] >= 2) / line_h
    print(f"pages={len(doc)}  OVERFLOW ≈ {over:.1f} lines onto page 3+")
else:
    spare = ((H - m - bottoms[last]) + (4 - last[1]) * colh + (1 - last[0]) * 5 * colh) / line_h
    print(f"pages={len(doc)}  ends side {SIDES[last[0]]} column {last[1] + 1}  spare ≈ {spare:.1f} lines")

paras, cur = [], None
for row in rows:
    if row[3] < 1.0 or row[6] or cur is None:
        cur = [row]
        paras.append(cur)
    else:
        cur.append(row)
short = sorted(((p[-1][4] / colw, p) for p in paras if not p[0][6] and len(p) > 1 and p[-1][4] / colw < a.short),
               key=lambda x: x[0])
print(f"{len(short)} paragraphs end with a line < {a.short:.0%} full:")
for f, p in short:
    print(f"  {f:.2f}  {SIDES[p[0][0]]}{p[0][1] + 1}  {p[0][5][:45]} … {p[-1][5][-30:]}")

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
