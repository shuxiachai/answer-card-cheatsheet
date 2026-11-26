"""Measure a 5-column cheatsheet PDF built by build_cheatsheet.py.

Usage: python measure_layout.py sheet.pdf [--font PT] [--margin-cm CM] [--gap-cm 0.1] [--short 0.25] [--no-points]
                                          [--find TEXT ...] [--lines TEXT ...] [--cards sheet.md]
Prints:
- page count and spare lines at the end (or overflow onto page 3+), counting figures as well as text; when the
  content fills clearly less than two sides, the font size that would roughly fill them;
- whether the letters sit on a 0.75 pt (96 dpi) grid, which makes small text look unevenly spaced;
- column-bottom gaps: columns that end one or more lines early because the next block is kept together and did
  not fit — a code block, a figure, a table's header row with its first row, a two-line title bar or Q line, and
  in a sheet built with --keep-with-next also card title + Q line + first point; saving 1–2 lines above such a
  gap pulls the block back and gains the whole gap;
- columns that end with a card title or its Q line (the card goes on at the top of the next column), so that
  one stranded at the bottom of side A, where the reader has to turn the sheet, is easy to spot;
- paragraphs whose last printed line is less than --short of the column width (cheapest places to save a line),
  marked "pt" for answer-card points (--no-points hides them);
- every place each --find text appears; for each --lines text, every printed line of that paragraph with its fill;
- with --cards, where each card, mini card and one-liner of the Markdown master starts (side, column, % down)
  and, for one that runs on, the column it ends in — the positions to cite in an answer key.
--font and --margin-cm are read from the PDF when omitted (the most common text size, and the left edge of
the text); give them explicitly only if the detected values printed on the first line look wrong.
"""
from collections import Counter
import argparse
import math
import re
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
ap.add_argument("--cards", metavar="MASTER", help="list where every card and one-liner of this Markdown master starts")
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

# Word puts every letter on a 0.75 pt (96 dpi) grid in compatibility mode or when the default printer cannot be
# reached; small text then looks unevenly spaced. A good export has almost no letter steps on that grid.
steps = on_grid = 0
for page in doc:
    for span in page.get_texttrace():
        xs = [ch[2][0] for ch in span["chars"]]
        for x0, x1 in zip(xs, xs[1:]):
            if x1 - x0 > 0.3:
                steps += 1
                on_grid += abs((x1 - x0) / 0.75 - round((x1 - x0) / 0.75)) * 0.75 < 0.01
if steps and on_grid / steps > 0.5:
    print(f"WARNING uneven letter spacing: {on_grid / steps:.0%} of letter steps fall on a 0.75 pt (96 dpi) grid — "
          "export with export_pdf.ps1 from a .docx built by build_cheatsheet.py (fitting.md → Pitfalls)")
elif steps:
    print(f"letter spacing ok ({on_grid / steps:.1%} of letter steps on the 0.75 pt grid)")

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


def card_start_at_bottom(col):
    """(kind, row) when a column's last paragraph is a card's title bar or its Q line: kind is 'title',
    'title + Q' or 'Q', and row is where that title (or, for 'Q', the Q line) begins."""
    end = len(col)
    for j in range(len(col) - 1, max(-1, len(col) - 4), -1):   # a Q line: 1–3 rows at the left edge, no point
        r = col[j]
        if r[6] or r[3] >= 1.0 or r[5] == "[figure]" or r[5].lstrip()[:1] in CIRCLED:
            break
        if r[5].lstrip().startswith(("Q:", "用法")):
            end = j
            break
    t = end
    while t > 0 and col[t - 1][6]:                              # the title bar above it (one or two rows)
        t -= 1
    if t < end:
        return ("title" if end == len(col) else "title + Q"), t
    return ("Q", end) if end < len(col) else (None, None)


# a build without --keep-with-next lets a column end with a card's title or Q line; list where that happened
ends = []
for key in [(p, c) for p in range(len(doc)) for c in range(5) if (p, c) < last]:
    col = [row for row in rows if row[:2] == key]
    kind, j = card_start_at_bottom(col)
    if kind:
        nxt = (key[0], key[1] + 1) if key[1] < 4 else (key[0] + 1, 0)
        ends.append((key, kind, nxt, col[j][5]))
if ends:
    print(f"{len(ends)} columns end with a card title or Q line (the card goes on at the top of the next column):")
    for key, kind, nxt, text in ends:
        turn = "  ← end of the side: the reader turns the sheet" if nxt[0] != key[0] else ""
        print(f"  {col_name(key)} ends with {kind:9} → {col_name(nxt)}: {text[:45]}{turn}")

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

for text in a.find:                         # every place the text appears: a phrase can occur in several cards
    found = []
    for pno, page in enumerate(doc):
        prev = None
        for r in page.search_for(text):
            c = max(0, min(4, int(((r.x0 + r.x1) / 2 - m) // (colw + gap))))
            wrapped = prev is not None and prev[0] == c and 0 <= r.y0 - prev[1] < line_h
            prev = (c, r.y1)
            if not wrapped:                 # the second part of a hit that wraps onto the next line is skipped
                found.append(f"side {SIDES[pno]}, column {c + 1}, {max(0, r.y0 - m) / colh:.0%} down")
    if not found:
        print(f"  '{text}': not found")
    else:
        print(f"  '{text}': " + (found[0] if len(found) == 1 else f"{len(found)} places — " + "; ".join(found)))


def para_text(p):
    """A paragraph's printed lines joined with single spaces (a line ending in a hyphen joins without one)."""
    out = ""
    for row in p:
        t = row[5].strip()
        out += t if not out or out.endswith("-") else " " + t
    return re.sub(r"\s+", " ", out)


for text in a.lines:
    want = re.sub(r"\s+", " ", text).strip()
    hit = [p for p in paras if want in para_text(p)]
    if not hit:
        print(f"  '{text}': not found (a paragraph broken across columns is listed per column)")
    for p in hit:
        print(f"  '{text}' — {len(p)} lines in {col_name(p[0][:2])}:")
        for row in p:
            print(f"    {row[4] / colw:4.0%}  {row[5]}")

if a.cards:                                 # where each block of the master starts, in master order
    TITLE_RE = re.compile(r"^(?:\{[^}]*\}\s*)?\*\*(★★★★|★★★ |★★ )\s*(.*?)\*\*")
    master = "\n" + open(a.cards, encoding="utf-8").read().replace("\r\n", "\n")
    if "\n## 答题卡\n" in master:
        master = master.split("\n## 答题卡\n", 1)[1]
    blocks, fence = [], False
    for line in master.split("\n"):
        if line.startswith("```"):
            fence = not fence
        elif not fence and TITLE_RE.match(line):
            blocks.append(TITLE_RE.match(line).groups())
    flat = [(row, re.sub(r"\s", "", row[5])) for row in rows if row[5] != "[figure]"]
    flat.append(((0, 0, 0), ""))
    starts, i = [], 0
    for kind, title in blocks:              # the printed title (stars stripped) begins a row; search on in order
        key = re.sub(r"\s", "", title.replace("`", ""))[:14]
        j = next((j for j in range(i, len(flat) - 1) if (flat[j][1] + flat[j + 1][1]).startswith(key)), None)
        starts.append(j)
        if j is not None:
            i = j + 1
    found = [j for j in starts if j is not None]
    print(f"{len(blocks)} blocks in the master, {len(found)} found (start: side+column, % down; → column it ends in):")
    for (kind, title), j in zip(blocks, starts):
        if j is None:
            print(f"  ??         {kind:4} {title[:50]}  (not found)")
            continue
        nxt = next((k for k in found if k > j), len(flat) - 1)   # the last entry of flat is an empty sentinel
        row, end = flat[j][0], flat[nxt - 1][0]
        runs_on = f" → {col_name(end[:2])}" if end[:2] != row[:2] else ""
        down = max(0, row[2] - a.font - m) / colh
        print(f"  {col_name(row[:2])} {down:4.0%}{runs_on:6} {kind:4} {title[:50]}")
