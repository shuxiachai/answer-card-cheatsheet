"""Measure a 5-column cheatsheet PDF built by build_cheatsheet.py.

Usage: python measure_layout.py sheet.pdf [--font PT] [--margin-cm CM] [--gap-cm 0.1] [--short 0.25] [--no-points]
                                          [--titles] [--find TEXT ...] [--lines TEXT ...] [--cards sheet.md
                                          [--update DOC ...]]
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
- how many lines the answer-card titles take (a title of 3+ lines is listed), and Q lines that wrap onto a
  second line with the fill of their last line; --titles lists every title with its line count and how full its
  last line is (room for one more keyword or not);
- paragraphs whose last printed line is less than --short of the column width (cheapest places to save a line),
  marked "pt" for answer-card points (--no-points hides them);
- every place each --find text appears; for each --lines text, every printed line of that paragraph with its fill;
- with --cards, where each card, mini card and one-liner of the Markdown master starts (side, column, % down)
  and, for one that runs on, the column it ends in — the positions to cite in an answer key;
- with --cards and --update, rewrites the card positions cited in other Markdown documents (an answer key, a
  rehearsal, a question-by-question check) to the new layout: a position is a bracket right after a card name,
  optionally with point numbers — "TCP 与 UDP ③（A1 17%）", "子网划分（B 面第 2 栏 84%）", "(B2, 50% down)" —
  and keeps its own style; the card name is the start of the card's title (the Chinese name is enough).
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
ap.add_argument("--titles", action="store_true", help="list every answer-card title with its lines and last-line fill")
ap.add_argument("--find", nargs="*", default=[])
ap.add_argument("--lines", nargs="*", default=[], help="print every line of the paragraph containing this text")
ap.add_argument("--cards", metavar="MASTER", help="list where every card and one-liner of this Markdown master starts")
ap.add_argument("--update", nargs="+", metavar="DOC", default=[],
                help="with --cards: rewrite the card positions cited in these Markdown documents")
a = ap.parse_args()
if a.update and not a.cards:
    ap.error("--update needs --cards sheet.md (the master the documents cite)")

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
                    e = r.setdefault(k, [1e9, 0.0, "", None])
                    # Word often draws the space between two runs as a gap, not a character: put it back
                    if e[2] and s["bbox"][0] - cx0 - e[1] > 0.4 and not e[2].endswith(" ") \
                            and not s["text"].startswith(" "):
                        e[2] += " "
                    if s["bbox"][0] - cx0 < e[0]:
                        e[3] = s["color"]            # colour of the row's first letters
                    e[0] = min(e[0], s["bbox"][0] - cx0)
                    e[1] = max(e[1], s["bbox"][2] - cx0)
                    e[2] += s["text"]
                    bottoms[(pno, c)] = max(bottoms.get((pno, c), 0), s["bbox"][3])
        for k in sorted(r):
            bar = any(bb.x0 >= cx0 - 2 and bb.x0 < cx0 + colw and bb.y0 - 1 <= k <= bb.y1 + 1 for bb in bars)
            x0, x1, t, colour = r[k]
            rows.append((pno, c, k, x0, x1, t, bar, colour))
    for im in page.get_image_info():        # figures take column height too
        x0, y0, x1, y1 = im["bbox"]
        c = max(0, min(4, int((x0 - m + 1) // (colw + gap))))
        bottoms[(pno, c)] = max(bottoms.get((pno, c), 0), min(y1, H - m))
        rows.append((pno, c, round(y0, 1), 0.0, x1 - x0, "[figure]", False, None))
Q_GREY = 0x404040                           # Q lines and 用法 lines are printed in this grey


def starts_point(row):
    """A row that begins with ①… in a point's colour; a Q line's second row can begin with ⑤ too, but in grey."""
    return row[5].lstrip()[:1] in CIRCLED and row[7] != Q_GREY
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
        if r[6] or r[3] >= 1.0 or r[5] == "[figure]" or starts_point(r):
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

# answer-card titles (rows on a dark bar; a new title starts with 〔) and Q lines that wrap onto a second row
titles, qlines, q_cur = [], [], None
for i, row in enumerate(rows):
    prev = rows[i - 1] if i else None
    follows = prev is not None and prev[:2] == row[:2] and 0 < row[2] - prev[2] < line_h * 1.5
    if row[6]:
        if titles and follows and prev[6] and not row[5].lstrip().startswith("〔"):
            titles[-1].append(row)
        else:
            titles.append([row])
    if not row[6] and row[5].lstrip().startswith("Q:"):
        q_cur = [row]
        qlines.append(q_cur)
    elif q_cur is not None and follows and q_cur[-1] is prev and not row[6] and row[5] != "[figure]" \
            and row[3] < 1.0 and not starts_point(row):
        q_cur.append(row)
    else:
        q_cur = None
if titles:
    n_lines = Counter(len(t) for t in titles)
    print(f"{len(titles)} answer-card titles: " + ", ".join(
        f"{n} take{'s' if n == 1 else ''} {k} line{'s' if k > 1 else ''}" for k, n in sorted(n_lines.items())))
    for t in titles:
        if len(t) >= 3 and not a.titles:
            print(f"  {len(t)} lines  {col_name(t[0][:2])}  {t[0][5][:45]}")
    if a.titles:                            # last-line fill: room for one more keyword or not
        for t in titles:
            print(f"  {len(t)} line{'s' if len(t) > 1 else ' '} last {t[-1][4] / colw:4.0%}  {col_name(t[0][:2])}  "
                  f"{t[0][5][:45]}")
wrapped_q = [q for q in qlines if len(q) > 1]
if qlines:
    print(f"{len(wrapped_q)} of {len(qlines)} Q lines wrap onto a second line" + (" (last line's fill):" if wrapped_q else ""))
    for q in wrapped_q:
        print(f"  {q[-1][4] / colw:.2f}  {col_name(q[0][:2])}  {q[0][5][:45]} … {q[-1][5][-25:]}")

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
    return starts_point(p[0])


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
            # the rest of a hit that wraps onto the next line, or that goes on in another font on the same line
            # (e.g. "Costs → ⑦": the circled number is a second box right after the first), is not a new place
            wrapped = prev is not None and prev[0] == c and (0 <= r.y0 - prev[1] < line_h
                                                             or (r.y0 < prev[1] and abs(r.x0 - prev[2]) < 1))
            prev = (c, r.y1, r.x1)
            if not wrapped:
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

if a.update:                                # rewrite "card name ②（A2 35%）" tags in other documents
    where = {}                              # card name (title without stars and 〔topic〕) -> (side, column, % down)
    for (kind, title), j in zip(blocks, starts):
        if j is not None:
            row = flat[j][0]
            name = re.sub(r"^〔[^〕]*〕\s*", "", title.replace("`", "")).strip()
            where[name] = (SIDES[row[0]], row[1] + 1, int(f"{max(0, row[2] - a.font - m) / colh:.0%}"[:-1]))   # as --cards prints it
    # (A2 35%) · （B 面第 2 栏 84%） · (B2, 50% down): side, column and % are replaced, the rest is kept
    POS_RE = re.compile(r"[（(]\s*([A-G])\s*(?:面\s*第\s*)?([1-5])\s*(?:栏)?\s*[,，]?\s*(\d{1,3})\s*%[^）)\n]{0,8}[）)]")
    TAIL_RE = re.compile(r"[\s" + CIRCLED + r"–—\-~～、,，*]+$")

    def card_at(before):
        """The card whose name ends the text just before a position bracket; the longest name that fits wins."""
        seg = re.split(r"[|｜＋+：:；;。>「“\"（(\[\]]", before)[-1]
        seg = TAIL_RE.sub("", seg).strip()
        for i in range(len(seg)):
            cand = seg[i:].strip()
            if not cand or (i and seg[i - 1].isascii() and seg[i - 1].isalnum() and cand[0].isascii()):
                continue                    # do not start inside an English word
            hits = [n for n in where if n == cand or n.startswith(cand + " ")]
            exact = [n for n in hits if n == cand]
            if len(hits) == 1 or exact:
                return (exact or hits)[0]
            if hits:
                return None                 # several cards start with these words: cite more of the name
        return None

    for path in a.update:
        raw = open(path, "rb").read()
        bom = raw.startswith(b"\xef\xbb\xbf")
        text = raw.decode("utf-8-sig")
        out, last, changed, same, unknown = [], 0, 0, 0, []
        for pm in POS_RE.finditer(text):
            line_start = text.rfind("\n", 0, pm.start()) + 1
            name = card_at(text[line_start:pm.start()])
            if name is None:
                unknown.append(f"line {text.count(chr(10), 0, pm.start()) + 1}: "
                               f"…{text[max(line_start, pm.start() - 24):pm.end()]}")
                continue
            side, col, pct = where[name]
            tag, s0 = pm.group(0), pm.start()
            new = (tag[:pm.start(1) - s0] + side + tag[pm.end(1) - s0:pm.start(2) - s0] + str(col)
                   + tag[pm.end(2) - s0:pm.start(3) - s0] + str(pct) + tag[pm.end(3) - s0:])
            if new == tag:
                same += 1
                continue
            out.append(text[last:pm.start()] + new)
            last = pm.end()
            changed += 1
        if changed:
            with open(path, "wb") as f:     # keep the file's own line endings and BOM
                f.write((b"\xef\xbb\xbf" if bom else b"") + ("".join(out) + text[last:]).encode("utf-8"))
        print(f"{path}: {changed} positions updated, {same} already current, {len(unknown)} not matched to a card")
        for u in unknown[:20]:
            print(f"  {u}")
        if len(unknown) > 20:
            print(f"  … and {len(unknown) - 20} more")
