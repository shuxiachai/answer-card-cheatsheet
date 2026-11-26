"""出处核对：列出 cheatsheet 上哪些句子用了课程文件里一次都没出现过的词。

用法：
    python source_audit.py 你的cheatsheet.md 课程文件或文件夹 [更多文件或文件夹 ...] [--exclude 文字 ...] [--find 词 ...]
课程文件：.pdf、.pptx、.docx、.txt、.md，文件夹会往下找所有子文件夹。只给课程自己的材料（课件、tutorial、
阅读、官方模拟卷和答案），不要把自己写的笔记、讲义放进去，否则什么都能"找到"。母版本身会自动跳过。
--exclude  文件名里含这段文字（不分大小写）就跳过，例如与本次考试无关的题库。
--find     列出每个词或短语出现在哪些文件的第几页（PPT 是第几张），用来回答"这个课本里有没有、在哪"。

查的是答题卡要点、精简卡和二星单句（考场上要抄的句子）：去掉中文标签、（中文注）、[ ] 换词槽里的词和
`行内代码` 之后，每个英文词连同它的变形（复数、-ed、-ing、-ly、-er、-ation，英式和美式拼写）在课程文件里找。
找不到的词不一定是错：可能是同义改写、常用词，或者课程用了别的说法。它只是把要人工看的句子挑出来，
按找不到的词数从多到少排，最后列出出现最多的生词。用 --find 查具体出处。
需要：PyMuPDF（pip install pymupdf，读 PDF 用）；.pptx 和 .docx 直接解压读文字，不需要别的库。
"""
import argparse
import re
import sys
import zipfile
from collections import Counter, defaultdict
from html import unescape
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser(description="列出 cheatsheet 上课程文件里找不到的词")
ap.add_argument("master", help="Markdown 母版")
ap.add_argument("sources", nargs="+", help="课程文件或文件夹")
ap.add_argument("--exclude", nargs="*", default=[], help="跳过文件名里含这段文字的文件")
ap.add_argument("--find", nargs="*", default=[], help="列出这些词或短语出现在哪些文件的第几页")
args = ap.parse_args()

# 和 check_master.py 一致
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
CARD_RE = re.compile(r"^(?:\{[^}]*\}\s*)?\*\*(★★★★|★★★ |★★ )")
TAG_RE = re.compile(r"^([" + CIRCLED + r"]\s*(?:[^\sA-Za-z(\[`]+|[A-Z][A-Za-z]*(?: [A-Za-z]+){0,2}:)\s)")
EXTS = {".pdf", ".pptx", ".docx", ".txt", ".md"}
STOP = set("""a about above after again against all also although am an and any are as at be because been before
being below between both but by can could did do does doing done down during each either else enough even every
for from further had has have having he her here hers him his how however i if in into is it its itself just
least less let like may might more most much must my no nor not now of off often on once one only or other our
ours out over own per rather same she should since so some such than that the their theirs them then there these
they this those though through thus to too two under until up upon us very via was we were what when where whether
which while who whom whose why will with within without would yet you your whereas whilst hence therefore thereby
instead unless besides toward towards across along around among amongst behind beyond onto inside outside already
still never always""".split())


SPELLING = {"licence": "license", "licences": "licenses", "defence": "defense", "offence": "offense",
            "practise": "practice", "programme": "program", "programmes": "programs"}
SUFFIXES = (("ies", "y"), ("ied", "y"), ("ily", "y"), ("es", ""), ("s", ""), ("ed", ""), ("ed", "e"), ("ing", ""),
            ("ing", "e"), ("ly", ""), ("er", ""), ("er", "e"), ("est", ""), ("est", "e"), ("ations", ""),
            ("ations", "e"), ("ation", ""), ("ation", "e"), ("ment", ""), ("ments", ""), ("ness", ""))


def forms(w):
    """一个词可能的原形（去掉复数、-ed、-ing、-ly、-er、-ation 等，英式拼写改成美式）。课程文件里的词和表上的词
    都展开成这些形式，有一个对上就算出现过：只求两边一致，不求语言学上准确。"""
    w = w.lower().strip("-'")
    if w.endswith("'s"):
        w = w[:-2]
    w = SPELLING.get(w, w)
    w = re.sub(r"is(e|es|ed|ing|ation|ations|er|ers)$", r"iz\1", w)    # organise → organize
    if len(w) >= 6:
        w = re.sub(r"our(s|ed|ing|al)?$", r"or\1", w)                   # behaviour → behavior
    out = {w}
    for suf, add in SUFFIXES:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            b = w[:-len(suf)] + add
            out.add(b)
            if len(b) >= 4 and b[-1] == b[-2] and b[-1] not in "aeiouls":   # stopped → stop
                out.add(b[:-1])
    return out


def tokens(text):
    return re.findall(r"[A-Za-z][A-Za-z'\-]*[A-Za-z]|[A-Za-z]", text)


# ---- 1. 读课程文件：每个文件按页（PPT 按张）存文字 -------------------------------------------------------------
def xml_text(data, tag):
    return unescape(" ".join(re.findall(r"<" + tag + r"(?: [^>]*)?>([^<]*)</" + tag + ">", data)))


def read_file(path):
    """[(页码或 None, 文字)]"""
    ext = path.suffix.lower()
    if ext == ".pdf":
        try:
            import fitz  # PyMuPDF
        except ImportError:
            sys.exit("读 PDF 需要 PyMuPDF：pip install pymupdf")
        with fitz.open(path) as doc:
            return [(i + 1, page.get_text()) for i, page in enumerate(doc)]
    if ext == ".pptx":
        with zipfile.ZipFile(path) as z:
            names = [n for n in z.namelist() if re.match(r"ppt/(slides/slide|notesSlides/notesSlide)\d+\.xml$", n)]
            pages = defaultdict(str)
            for n in names:
                pages[int(re.search(r"(\d+)\.xml$", n).group(1))] += " " + xml_text(z.read(n).decode("utf-8", "ignore"), "a:t")
            return sorted(pages.items())
    if ext == ".docx":
        with zipfile.ZipFile(path) as z:
            return [(None, xml_text(z.read("word/document.xml").decode("utf-8", "ignore"), "w:t"))]
    return [(None, path.read_text(encoding="utf-8", errors="ignore"))]


master = Path(args.master).resolve()
files = []
for s in args.sources:
    p = Path(s)
    if not p.exists():
        sys.exit(f"找不到：{s}")
    for f in ([p] if p.is_file() else sorted(p.rglob("*"))):
        if f.is_file() and f.suffix.lower() in EXTS and f.resolve() != master and not f.name.startswith("~$"):
            files.append(f)
skipped = [f for f in files if any(x.lower() in f.name.lower() for x in args.exclude)]
files = [f for f in files if f not in skipped]
if not files:
    sys.exit("没有可读的课程文件（.pdf .pptx .docx .txt .md）")

pages, unreadable = [], []          # [(文件名, 页码, 文字)]
for f in files:
    try:
        pages += [(f.name, n, t) for n, t in read_file(f)]
    except Exception as e:          # 加密、损坏的文件：记下来，接着读别的
        unreadable.append(f"{f.name}（{type(e).__name__}）")
words_seen = set()
for _, _, t in pages:
    words_seen.update(tokens(t))
known = set()
for w in words_seen:
    known |= forms(w)
kinds = Counter(f.suffix.lower() for f in files)
print(f"读了 {len(files)} 个课程文件（" + "，".join(f"{k} {n}" for k, n in sorted(kinds.items()))
      + f"），{len({w.lower() for w in words_seen})} 个不同的词")
if skipped:
    print("按 --exclude 跳过：" + "；".join(f.name for f in skipped))
if unreadable:
    print("读不了：" + "；".join(unreadable))

# ---- 2. --find：每个词或短语在哪些文件的第几页 -------------------------------------------------------------------
for term in args.find:                      # 整词匹配（RTO 不算 portion 里的 rto），词之间的空格、换行、连字符都算
    want = re.compile(r"(?<![A-Za-z])" + r"[\s\-]+".join(map(re.escape, term.split())) + r"(?![A-Za-z])", re.I)
    hits = defaultdict(list)
    for name, n, t in pages:
        if want.search(t):
            hits[name].append(n)
    if not hits:
        print(f"  '{term}'：课程文件里没有")
        continue
    where = []
    for name, ns in hits.items():
        ns = [n for n in ns if n is not None]
        where.append(name + (f" p{','.join(map(str, ns[:8]))}{'…' if len(ns) > 8 else ''}" if ns else ""))
    print(f"  '{term}'：{len(hits)} 个文件 — " + "；".join(where))
if args.find:
    sys.exit(0)

# ---- 3. 母版里要抄的句子 -------------------------------------------------------------------------------------
text = "\n" + master.read_text(encoding="utf-8").replace("\r\n", "\n")
offset = 0
if "\n## 答题卡\n" in text:
    header, text = text.split("\n## 答题卡\n", 1)
    offset = header.count("\n") + 2
items, title, fence = [], "", False      # [(行号, 卡片, 序号, 句子)]
for ln, line in enumerate(text.split("\n"), start=offset):
    if line.startswith("```"):
        fence = not fence
        continue
    if fence or line.startswith("|") or not line.strip():
        continue
    cm = CARD_RE.match(line)
    if cm:
        title = re.sub(r"\*\*|\{[^}]*\}|★", "", line).strip()
        if cm.group(1) != "★★★★":         # 精简卡、二星单句：加粗标题后面的句子
            bm = re.match(r"^(?:\{[^}]*\}\s*)?\*\*[^*]*\*\*\s*(.*)", line)
            if bm and bm.group(1).strip():
                items.append((ln, title, "", bm.group(1)))
        continue
    if line[0] in CIRCLED:
        tm = TAG_RE.match(line)
        items.append((ln, title, line[0], line[tm.end():] if tm else line[1:]))


def clean(s):
    s = re.sub(r"`[^`]*`", " ", s)                  # 行内代码：名字多是自己起的
    s = re.sub(r"\[[^\]]*\]", " ", s)               # 换词槽：考场上换成题目里的词
    s = re.sub(r"（[^）]*）", " ", s)                 # 中文注
    return re.sub(r"\*\*|\{[^}]*\}", "", s)


rows, freq = [], Counter()
for ln, card, num, sentence in items:
    unknown = []
    for w in tokens(clean(sentence)):
        low = w.lower()
        if low in STOP or (len(w) < 3 and not w.isupper()):
            continue
        parts = [x for x in low.split("-") if x]
        if forms(low) & known or (len(parts) > 1 and all(forms(x) & known or x in STOP for x in parts)):
            continue
        if w not in unknown:
            unknown.append(w)
    if unknown:
        rows.append((ln, card, num, sentence, unknown))
        freq.update(w.lower() for w in unknown)

print(f"要抄的句子 {len(items)} 句：{len(items) - len(rows)} 句的词都在课程文件里出现过，"
      f"{len(rows)} 句有课程文件里找不到的词（按找不到的词数排；常用词和同义改写也会列出来，逐条人工看）：")
for ln, card, num, sentence, unknown in sorted(rows, key=lambda r: (-len(r[4]), r[0])):
    print(f"  第 {ln} 行 {card[:24]} {num}  找不到：{', '.join(unknown)}")
    print(f"      {sentence[:110]}{'…' if len(sentence) > 110 else ''}")
if freq:
    print("出现最多的生词：" + "，".join(f"{w} ×{n}" if n > 1 else w for w, n in freq.most_common(30)))
print("用 --find 查一个词在哪个文件第几页，例如：python source_audit.py 母版.md 课程文件夹 --find \"defence in depth\"")
