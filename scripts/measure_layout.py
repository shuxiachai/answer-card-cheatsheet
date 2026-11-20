"""Measure a 5-column cheatsheet PDF built by build_cheatsheet.py.

Usage: python measure_layout.py sheet.pdf [--font 5] [--gap-cm 0.1] [--short 0.25] [--find TEXT ...]
Prints: page count; spare lines at the end (or overflow onto page 3+); paragraphs whose last printed line is
less than --short of the column width (cheapest places to save a line); where each --find text sits.
"""
import argparse
import sys

import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser()
ap.add_argument("pdf")
ap.add_argument("--font", type=float, default=5.0)
ap.add_argument("--gap-cm", type=float, default=0.1)
ap.add_argument("--short", type=float, default=0.25)
ap.add_argument("--find", nargs="*", default=[])
a = ap.parse_args()

doc = fitz.open(a.pdf)
W, H = doc[0].rect.width, doc[0].rect.height
gap = a.gap_cm / 2.54 * 72
colw = (W - 4 * gap) / 5
line_h = a.font * 1.18
SIDES = "ABCDEFG"

bottoms, rows = {}, []
for pno, page in enumerate(doc):
    bars = [d["rect"] for d in page.get_drawings() if d.get("fill") and d["rect"].width > colw * 0.9
            and d["rect"].height < 8 and min(d["fill"]) < 0.8]
    for c in range(5):
        cx0 = c * (colw + gap)
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
    over = sum((H if key != last else bottoms[key]) for key in bottoms if key[0] >= 2) / line_h
    print(f"pages={len(doc)}  OVERFLOW ≈ {over:.1f} lines onto page 3+")
else:
    spare = ((H - bottoms[last]) + (4 - last[1]) * H + (1 - last[0]) * 5 * H) / line_h
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
            c = min(4, int(r.x0 // (colw + gap)))
            print(f"  '{text}': side {SIDES[pno]}, column {c + 1}, {r.y0 / H:.0%} down")
            break
    else:
        print(f"  '{text}': not found")
