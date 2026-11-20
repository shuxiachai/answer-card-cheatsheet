"""把「答题卡式」cheatsheet 的 Markdown 排成 Word 版：
A4 横向、5 栏自动分栏、页边距 0、Segoe UI + 微软雅黑 5 pt、行距固定 5.9 pt、
★★★★ 标题彩色底白字、Q 行深灰、"① 标签" 加粗着色、精简卡悬挂缩进、紧凑表格、代码灰底。
为了省地方：行首的 ★★★★ / ★★★ / ★★ 只在 .md 里用来区分卡片类型，排版时删掉；
标题条、精简卡和二星单句的段前都是 0；关掉孤行控制，栏底不再空出几行；
栏间距 0.1 cm；正文用 Segoe UI、正常字距（比 Arial 收紧字距更清楚，所占宽度差不多）；行内代码用 Arial Narrow（代码块仍用等宽的 Consolas，DOM 树要靠等宽对齐）。

配色：每张卡按主题上色。标题条是深色底白字，
"① 标签"、精简卡 / 二星单句的加粗标题用同一种颜色，表格表头用同色浅底。
默认按 ★★★★ 标题里的〔主题〕配色：〔A〕EXAM、〔1〕W2、〔2〕W3、〔3〕W4、〔4〕W5、〔5〕W6、
〔6〕W7、〔7〕W8、〔8〕W9、〔9〕W10、〔10〕W12。要换颜色，或给没有〔主题〕的精简卡 / 二星单句上色，
就在那一行行首加 {W1}…{W12}、{EXAM} 或 {DESIGN}（排版时会删掉，不占版面）。

用法：
    python build_cheatsheet.py 你的cheatsheet.md [输出.docx] [字号，默认 5] [页边距 cm，默认 0]
（打印机印不到纸边的话，页边距写 0.5。）
需要：pandoc（命令行能运行 pandoc）和 python-docx（pip install python-docx）。
如果 .md 里有一行 "## 答题卡"，只排这一行之后的内容（前面可以放说明文字）。
排完用 Word 打开，导出 PDF，确认正好两页。
"""
import copy
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.run import Run

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) < 2:
    sys.exit(__doc__)
if shutil.which("pandoc") is None:
    sys.exit("找不到 pandoc：请先安装 pandoc（https://pandoc.org），再运行本脚本。")
src = Path(sys.argv[1])
out = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".docx")
FONT_PT = float(sys.argv[3]) if len(sys.argv) > 3 else 5.0
MARGIN_CM = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
HALF = str(int(round(FONT_PT * 2)))
LINE = Pt(FONT_PT * 1.18)         # 行距固定值（5 pt 字 → 5.9 pt）：否则含中文的行会比纯英文的行高
LATIN, EA, MONO, NARROW = "Segoe UI", "微软雅黑", "Consolas", "Arial Narrow"
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
GREY_TITLE, GREY_CODE = "E2E2E2", "F2F2F2"

# 配色：EXAM = 答题方法，DESIGN = 设计 / 场景题，W1–W12 = 第 1–12 周
PALETTE = {
    "EXAM": "1F3B57", "DESIGN": "8D6E00",
    "W1": "546E7A", "W2": "2E7D32", "W3": "1565C0", "W4": "D84315", "W5": "6A1B9A", "W6": "00838F",
    "W7": "AD1457", "W8": "6D4C41", "W9": "283593", "W10": "37474F", "W11": "558B2F", "W12": "C62828",
}
TOPIC_DEFAULT = {"A": "EXAM", "1": "W2", "2": "W3", "3": "W4", "4": "W5", "5": "W6",
                 "6": "W7", "7": "W8", "8": "W9", "9": "W10", "10": "W12"}
COLOR_RE = re.compile(r"^\{(EXAM|DESIGN|W1[0-2]|W[1-9])\}\s*")
WHITE = RGBColor(0xFF, 0xFF, 0xFF)


def tint(hexc, f=0.14):
    """浅色：主题色和白色按 14 : 86 混合。"""
    rgb = [int(hexc[k:k + 2], 16) for k in (0, 2, 4)]
    return "".join("%02X" % round(255 - (255 - c) * f) for c in rgb)


text = "\n" + src.read_text(encoding="utf-8")
if "\n## 答题卡\n" in text:
    text = text.split("\n## 答题卡\n", 1)[1]


def split_cells(row):
    return [c.strip() for c in re.split(r"(?<!\\)\|", row)[1:-1]]


def disp_width(s):
    s = re.sub(r"`|\*\*|\\\|", "", s)
    return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1 for c in s)


# ---- 1. 颜色标记：删掉行首的 {W9} 等，按卡片顺序记下每张卡的颜色 ------------------------------------
lines, card_colors, fence = [], [], False
for line in text.split("\n"):
    if line.startswith("```"):
        fence = not fence
    elif not fence:
        m = COLOR_RE.match(line)
        key = None
        if m:
            key, line = m.group(1), line[m.end():]
        if line.startswith(("**★★★★", "**★★★ ", "**★★ ")):
            if key is None and line.startswith("**★★★★"):
                tm = re.search(r"〔(\w+)", line)
                key = TOPIC_DEFAULT.get(tm.group(1)) if tm else None
            card_colors.append(key)
    lines.append(line)

# ---- 2. 每一行单独成段；表格分隔行按内容宽度分配列宽 ------------------------------------------
md, i, in_code = [], 0, False
while i < len(lines):
    line = lines[i]
    if line.startswith("```"):
        in_code = not in_code
        md.append(line)
        if not in_code:
            md.append("")
        i += 1
        continue
    if in_code:
        md.append(line)
        i += 1
        continue
    if (line.startswith("|") and i + 1 < len(lines)
            and re.fullmatch(r"\|(\s*:?-+:?\s*\|)+", lines[i + 1].strip())):
        j = i + 2
        while j < len(lines) and lines[j].startswith("|"):
            j += 1
        rows = [line] + lines[i + 2:j]
        ncol = len(split_cells(line))
        widths = [0.0] * ncol
        for r in rows:
            cells = split_cells(r)
            for k in range(min(ncol, len(cells))):
                widths[k] = max(widths[k], min(disp_width(cells[k]), 60))
        w = [max(3.0, x) ** 0.8 for x in widths]
        dashes = [max(3, round(100 * x / sum(w))) for x in w]
        if md and md[-1].strip():
            md.append("")
        md += [line, "|" + "|".join("-" * d for d in dashes) + "|"] + lines[i + 2:j] + [""]
        i = j
        continue
    md.append(line)
    if line.strip():
        md.append("")
    i += 1

with tempfile.TemporaryDirectory() as tmp:
    tmp_md, raw = Path(tmp) / "cards.md", Path(tmp) / "raw.docx"
    tmp_md.write_text("\n".join(md), encoding="utf-8", newline="\n")
    # ---- 3. pandoc --------------------------------------------------------------------------------
    subprocess.run(["pandoc", str(tmp_md), "-f", "gfm", "-t", "docx", "--columns=10", "-o", str(raw)], check=True)
    doc = Document(str(raw))

# ---- 4. 页面：A4 横向、页边距（默认 0）、5 栏 + 分隔线 ------------------------------------------------
sec = doc.sections[0]
sec.orientation = WD_ORIENT.LANDSCAPE
sec.page_width, sec.page_height = Cm(29.7), Cm(21.0)
for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
    setattr(sec, side, Cm(MARGIN_CM))
sec.header_distance = sec.footer_distance = Cm(0)
sectPr = sec._sectPr
for old in sectPr.findall(qn("w:cols")):
    sectPr.remove(old)
cols = OxmlElement("w:cols")
cols.set(qn("w:num"), "5")
cols.set(qn("w:space"), "57")       # 栏间距 0.1 cm
cols.set(qn("w:sep"), "1")          # 分隔线
sectPr.append(cols)


# ---- 5. 字体、字号、行距 -------------------------------------------------------------------------
def set_fonts(rpr, latin=LATIN):
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.insert(0, rf)
    for a in list(rf.attrib):
        del rf.attrib[a]
    rf.set(qn("w:ascii"), latin)
    rf.set(qn("w:hAnsi"), latin)
    rf.set(qn("w:eastAsia"), EA)
    rf.set(qn("w:cs"), LATIN)
    for tag in ("w:sz", "w:szCs"):
        el = rpr.find(qn(tag))
        if el is None:
            el = OxmlElement(tag)
            rpr.append(el)
        el.set(qn("w:val"), HALF)


rpr_default = doc.styles.element.find(qn("w:docDefaults")).find(qn("w:rPrDefault")).find(qn("w:rPr"))
set_fonts(rpr_default)
for st in doc.styles:
    el = st.element
    rpr = el.find(qn("w:rPr"))
    if rpr is None:
        rpr = OxmlElement("w:rPr")
        el.append(rpr)
    # 代码块用等宽字体（DOM 树靠等宽对齐）；行内代码用窄体，省地方
    set_fonts(rpr, MONO if st.name == "Source Code" else NARROW if st.name == "Verbatim Char" else LATIN)
    if st.type == 1:
        pf = st.paragraph_format
        pf.space_before = pf.space_after = Pt(0)
        pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
        pf.line_spacing = LINE
        pf.widow_control = False    # 关掉孤行控制：否则 Word 会把整段挪到下一栏，栏底空出几行


def shade(el_pr, fill):
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    el_pr.append(shd)


# ---- 6. 段落：标题、Q 行、要点、精简卡、代码（按卡片配色） --------------------------------------------
TAG_RE = re.compile(r"^([" + CIRCLED + r"]\s*(?:[^\sA-Za-z(\[`]+|[A-Z][A-Za-z]*(?: [A-Za-z]+){0,2}:)\s)")
state = {"hue": None}
card_iter = iter(card_colors)


def strip_stars(p):
    """删掉行首的 ★★★★ / ★★★ / ★★ 和后面的一个空格（pandoc 可能把它们拆在几个 run 里）。"""
    eat_space = False
    for r in p.runs:
        rt = r.text
        if eat_space:
            r.text = rt[1:] if rt.startswith(" ") else rt
            return
        rest = rt.lstrip("★")
        if rest == rt:
            return
        if rest:
            r.text = rest[1:] if rest.startswith(" ") else rest
            return
        r.text, eat_space = "", True


def format_paragraph(p):
    pf = p.paragraph_format
    pf.space_before = pf.space_after = Pt(0)
    pf.line_spacing_rule = WD_LINE_SPACING.EXACTLY
    pf.line_spacing = LINE
    pf.widow_control = False
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    t = p.text
    if t.startswith(("★★★★", "★★★ ", "★★ ")):     # 新的一张卡：换成它的颜色；行首星号不印
        state["hue"] = PALETTE.get(next(card_iter, None))
        strip_stars(p)
    hue = state["hue"]
    if t.startswith("★★★★"):                      # 答题卡标题：主题色底白字、与下段同页
        shade(p._p.get_or_add_pPr(), hue or GREY_TITLE)
        if hue:
            for r in p.runs:
                r.font.color.rgb = WHITE
        pf.keep_with_next = True                    # 段前 0：色条本身就能把卡片分开
    elif t.startswith(("★★★ ", "★★ ")):          # 精简卡 / 二星单句：悬挂缩进，加粗标题着色
        pf.left_indent = Pt(FONT_PT * 1.6)
        pf.first_line_indent = Pt(-FONT_PT * 1.6)
        if hue:
            for r in p.runs:
                if r.bold:
                    r.font.color.rgb = RGBColor.from_string(hue)
    elif t.startswith(("Q:", "用法")):             # Q 行 / 用法行：深灰
        pf.keep_with_next = True
        for r in p.runs:
            r.font.color.rgb = RGBColor(0x40, 0x40, 0x40)
    elif t and t[0] in CIRCLED:                     # 要点：悬挂缩进，"① 标签" 加粗着色
        pf.left_indent = Pt(FONT_PT * 1.05)
        pf.first_line_indent = Pt(-FONT_PT * 1.05)
        m = TAG_RE.match(t)
        remaining = len(m.group(1)) if m else 0
        for r in list(p.runs):                      # pandoc 会在中英文切换处拆 run，逐个处理
            if remaining <= 0:
                break
            rt = r.text
            if len(rt) <= remaining:
                tag_run = r
                remaining -= len(rt)
            else:
                head = copy.deepcopy(r._r)
                r._r.addprevious(head)
                tag_run = Run(head, p)
                tag_run.text = rt[:remaining]
                r.text = rt[remaining:]
                remaining = 0
            tag_run.font.bold = True
            if hue:
                tag_run.font.color.rgb = RGBColor.from_string(hue)
    if p.style is not None and p.style.name == "Source Code":
        shade(p._p.get_or_add_pPr(), GREY_CODE)
        pf.keep_together = True                     # 整个代码块放在同一栏，不拆开
        for r in p.runs:                            # pandoc 给代码块里的字也套了行内代码样式（窄体），改回等宽
            r.font.name = MONO


# ---- 7. 表格：100% 宽、细灰框、紧凑边距、表头用主题色浅底 + 主题色加粗字 -----------------------------------
def table_format(tbl):
    tblPr = tbl._tbl.tblPr
    for tag in ("w:tblBorders", "w:tblCellMar", "w:tblW", "w:tblInd"):
        old = tblPr.find(qn(tag))
        if old is not None:
            tblPr.remove(old)
    tw = OxmlElement("w:tblW")
    tw.set(qn("w:w"), "5000")
    tw.set(qn("w:type"), "pct")
    tblPr.append(tw)
    b = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "2")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "808080")
        b.append(e)
    tblPr.append(b)
    mar = OxmlElement("w:tblCellMar")
    for edge, v in (("left", "28"), ("right", "28"), ("top", "0"), ("bottom", "0")):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:w"), v)
        e.set(qn("w:type"), "dxa")
        mar.append(e)
    tblPr.append(mar)


def format_table(tbl):
    hue = state["hue"]
    table_format(tbl)
    for ri, row in enumerate(tbl.rows):
        for cell in row.cells:
            if ri == 0:
                shade(cell._tc.get_or_add_tcPr(), tint(hue) if hue else GREY_TITLE)
            for p in cell.paragraphs:
                p.paragraph_format.space_before = p.paragraph_format.space_after = Pt(0)
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.EXACTLY
                p.paragraph_format.line_spacing = LINE
                p.paragraph_format.widow_control = False
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    if ri == 0:
                        r.font.bold = True
                        if hue:
                            r.font.color.rgb = RGBColor.from_string(hue)


# 按文档顺序处理段落和表格，这样表格能用它所在卡片的颜色
paras = {p._p: p for p in doc.paragraphs}
tables = {t._tbl: t for t in doc.tables}
for el in list(doc.element.body.iterchildren()):
    if el in paras:
        format_paragraph(paras[el])
    elif el in tables:
        format_table(tables[el])

doc.save(str(out))
with zipfile.ZipFile(out) as z:                      # 去掉 ZIP 目录项（云盘协同编辑时 Word 可能拒绝打开）
    items = [(zi, z.read(zi.filename)) for zi in z.infolist() if not zi.filename.endswith("/")]
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for zi, data in items:
        z.writestr(zi, data)
print(f"已生成：{out}（{len(doc.paragraphs)} 段，{len(doc.tables)} 个表格）。用 Word 打开后导出 PDF，确认正好两页。")
