"""检查「答题卡式」cheatsheet 的 Markdown 母版（排版之前跑一次）。

用法：
    python check_master.py 你的cheatsheet.md [--font 5] [--gap-cm 0.05] [--similar [0.35]]
--font 是打算排的字号（默认 4.5），--gap-cm 是栏间距（默认 0.1），用来算图片占几行、图里的字要多大。
--similar 列出用词接近的两句（默认 0.35：两句合起来的实词里，两句都有的占三分之一以上），挤版时找可以删、
          可以合并的句子。
「错误」是排出来会出问题的地方（颜色错位、颜色键原样印出、Q 行指向不存在的要点……），必须改；
「提醒」是 references/format.md 里的写法规则（缺 Q 行、Q 行没有指到的要点、标签不会着色、英文句子里混了中文、
以 It/This 开头、写了出处、槽外有过去时、写了答题技巧的话、[ ] 槽太长、太长……），答题卡要点、精简卡和
二星单句都查，看情况改。
「图片」列出每张图按栏宽缩放后大约占几行，以及图里的字至少要多大（按页边距 0 估算）。
最后一行统计有几句带 [ ] 换词槽、几句可以原样抄。
有错误时退出码为 1。
"""
import argparse
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
ap = argparse.ArgumentParser(description="检查答题卡式 cheatsheet 的 Markdown 母版")
ap.add_argument("master", help="Markdown 母版")
ap.add_argument("--font", type=float, default=4.5, help="打算排的字号（pt），默认 4.5")
ap.add_argument("--gap-cm", type=float, default=0.1, help="栏间距（cm），默认 0.1，和 build_cheatsheet.py 的第 5 个参数一致")
ap.add_argument("--similar", type=float, nargs="?", const=0.35, default=None, metavar="SHARE",
                help="列出实词重合到这个比例的两句（默认 0.35），挤版时找可删可并的句子")
args = ap.parse_args()
FONT = args.font

# 下面这些规则和 build_cheatsheet.py 保持一致
CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"
COLOR_RE = re.compile(r"^\{(EXAM|DESIGN|W1[0-2]|W[1-9])\}\s*")
CARD_RE = re.compile(r"^(\*\*)?(★★★★|★★★ |★★ )")
TAG_RE = re.compile(r"^([" + CIRCLED + r"]\s*(?:[^\sA-Za-z(\[`]+|[A-Z][A-Za-z]*(?: [A-Za-z]+){0,2}:)\s)")
MAP_RE = re.compile(r"^>?\s*(?:配色|colou?rs?)\s*[:：]\s*(.+)$", re.I)
MAP_PAIR_RE = re.compile(r"(\w+)\s*=\s*(EXAM|DESIGN|W1[0-2]|W[1-9])\b")
TOPICS = {"A": "EXAM", "1": "W2", "2": "W3", "3": "W4", "4": "W5", "5": "W6",
          "6": "W7", "7": "W8", "8": "W9", "9": "W10", "10": "W12"}
CJK = re.compile(r"[㐀-鿿豈-﫿]")
RANGE_RE = re.compile(r"([" + CIRCLED + r"])\s*[–—\-~～]\s*([" + CIRCLED + r"])")
IMG_RE = re.compile(r"!\[([^\]]*)\]\(\s*<?([^)>\s]+)>?(?:\s+\"[^\"]*\")?\s*\)")

COL_CM = (29.7 - 4 * args.gap_cm) / 5       # 页边距 0 时的一栏宽
LIMITS = {"q_words": 25, "point_words": 40, "card_chars": 1600, "mini_chars": 290, "oneliner_chars": 400,
          "slot_words": 5}
# 出处：考场上抄进答案会很怪（"the lecture's …"、"Week 3"、"slide 12"、"p. 4"、"Quiz 2"）
SOURCE_RE = re.compile(r"\b(lectures?|slides?|tutorials?|textbook|quiz(?:zes)?|week\s*\d+|W\d{1,2}|pp?\.\s*\d+|"
                       r"pages?\s+\d+)\b", re.I)
# 槽外的过去时：句子像在讲某一个案例发生过的事（"[the system] went live"、"factors included"），换了题目就不能
# 照抄。was / were / had / did / happened 不查：被动语态、从句和 "records what happened" 里太常见
PAST_RE = re.compile(r"\b(went|became|contributed|included)\b", re.I)
# 答题技巧的话：写的是怎么答题，不是答案本身
EXAM_RE = re.compile(r"\b(the answer|this answer|the question|this question|examiners?|full marks|marking guide|"
                     r"answer guide|model answer)\b", re.I)
slots = {"with": 0, "without": 0}
sentences = []       # [(行号, 开头, 英文句子)]，--similar 用

src = Path(args.master)
text = "\n" + src.read_text(encoding="utf-8").replace("\r\n", "\n")
errors, notes, infos = [], [], []
offset = 0
if "\n## 答题卡\n" in text:
    header, text = text.split("\n## 答题卡\n", 1)
    offset = header.count("\n") + 2
    for hl in header.split("\n"):
        hm = MAP_RE.match(hl.strip())
        if hm:
            TOPICS.update(dict(MAP_PAIR_RE.findall(hm.group(1))))
else:
    notes.append((0, '没有 "## 答题卡" 这一行：整个文件都会被排进去，包括说明文字'))


def topic_color(topic):
    if topic in TOPICS:
        return TOPICS[topic]
    if topic.isdigit() and int(topic) > 0:
        return f"W{(int(topic) - 1) % 12 + 1}"
    return None


def plain(s):
    """去掉 Markdown 加粗和行内代码，只留要读的文字。"""
    return re.sub(r"`[^`]*`", " ", s).replace("**", "")


def words(s):
    """英文词数：不算圈号、箭头、中文和（）里的注释。"""
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.\-]*", re.sub(r"（[^）]*）", " ", plain(s))))


def image_size(path):
    """图片的像素宽高；读不出来就返回 None（需要 PyMuPDF 或 Pillow）。"""
    try:
        import fitz
        pix = fitz.Pixmap(str(path))
        return pix.width, pix.height
    except Exception:
        pass
    try:
        from PIL import Image
        with Image.open(path) as im:
            return im.size
    except Exception:
        return None


def check_image(ln, im):
    alt, ref = im.group(1), im.group(2)
    if re.match(r"^[a-z][a-z0-9+.\-]*://", ref, re.I):
        errors.append((ln, f"只支持本地图片文件：{ref}"))
        return
    path = src.resolve().parent / ref
    if not path.is_file():
        errors.append((ln, f"找不到图片 {ref}（路径相对于 .md 所在的文件夹）"))
        return
    if path.suffix.lower() not in (".png", ".jpg", ".jpeg"):
        notes.append((ln, f"图片最好用 PNG 或 JPG：{ref}"))
    pm = re.match(r"\s*(\d{1,3})\s*%", alt)
    pct = int(pm.group(1)) if pm else 100
    if not 10 <= pct <= 100:
        notes.append((ln, f"图片宽度 {pct}% 不在 10%–100% 之间，会按 {min(100, max(10, pct))}% 排：{ref}"))
        pct = min(100, max(10, pct))
    size = image_size(path)
    if not size:
        infos.append((ln, f"{ref}：占栏宽 {pct}%（读不出像素尺寸，没法估算高度）"))
        return
    w, h = size
    h_cm = COL_CM * pct / 100 * h / w
    min_px = FONT * w / (COL_CM * pct / 100 / 2.54 * 72)
    infos.append((ln, f"{ref}：占栏宽 {pct}%，约 {h_cm:.1f} cm 高 ≈ {h_cm * 28.35 / (FONT * 1.18):.0f} 行（{FONT:g} pt）；"
                      f"图里文字的字号至少 {min_px:.0f} 像素（绘图软件里按这张图的像素设的字号）才不比 {FONT:g} pt 正文小"))


def nonspace(s):
    return len(re.sub(r"\s", "", s.replace("**", "").replace("`", "")))


def check_sentence(ln, sentence, what, head):
    """要点、精简卡、二星单句共用：sentence 是考场上要抄的英文部分（标签或加粗标题后面的文字）。"""
    text = re.sub(r"（[^）]*）", " ", plain(sentence))          # （中文注）不抄，不查
    if CJK.search(re.sub(r"\[[^\]]*\]", " ", text)):
        notes.append((ln, f"{what}的英文句子里有中文（考场上不能照抄）：{head}"))
    if re.match(r"(It|This|These|They)\b", sentence.strip()):
        notes.append((ln, f"{what}以 It/This/They 开头，单独抄出来看不懂指的是什么：{head}"))
    sm = SOURCE_RE.search(text)
    if sm:
        notes.append((ln, f"{what}里有出处词「{sm.group(0)}」，抄进答案会很怪：{head}"))
    outside = re.sub(r"\[[^\]]*\]", " ", text)
    pm = PAST_RE.search(outside)
    if pm:
        notes.append((ln, f"{what}的 [ ] 外有过去时「{pm.group(0)}」，像在讲某个案例：改成一般现在时，"
                          f"或把案例的部分放进 [ ]：{head}"))
    em = EXAM_RE.search(outside)
    if em:
        notes.append((ln, f"{what}里有答题技巧的话「{em.group(0)}」，抄进答案会很怪：直接写内容本身：{head}"))
    owner = ""
    if what == "要点" and card is not None:            # 答题卡名：〔主题〕后面到第一个小写英文词为止
        owner = re.split(r"\s+(?=[a-z·])", re.sub(r"^★+\s*(〔[^〕]*〕\s*)?", "", card["title"]), 1)[0] + " "
    sentences.append((ln, owner + head, text))
    found = re.findall(r"\[([^\]]*)\]", text)
    slots["with" if found else "without"] += 1
    for s in found:
        if len(s.split()) > LIMITS["slot_words"]:
            notes.append((ln, f"{what}的 [ ] 槽有 {len(s.split())} 个词（目标 1–3 个），槽越长考场上要自己写的越多："
                              f"[{s[:30]}]"))


counts = {"★★★★": 0, "★★★ ": 0, "★★ ": 0}
card = None          # 当前答题卡：{"line", "title", "q", "qline", "points": [(行号, 序号)], "chars"}


def close_card():
    if card is None:
        return
    nums = [n for _, n in card["points"]]
    if not card["q"]:
        notes.append((card["line"], f"答题卡标题下面没有 Q 行：{card['title']}"))
    if not nums:
        errors.append((card["line"], f"答题卡没有要点：{card['title']}"))
    elif nums != list(range(1, len(nums) + 1)):
        errors.append((card["line"], f"要点编号不连续（{''.join(CIRCLED[n - 1] for n in nums)}）：{card['title']}"))
    if card["q"]:
        refs = set()
        q = card["q"]
        for a, b in RANGE_RE.findall(q):
            refs.update(range(CIRCLED.index(a) + 1, CIRCLED.index(b) + 2))
        q = RANGE_RE.sub(" ", q)
        refs.update(CIRCLED.index(c) + 1 for c in q if c in CIRCLED)
        missing = sorted(refs - set(nums))
        if missing:
            errors.append((card["qline"], "Q 行指向不存在的要点 " + "".join(CIRCLED[n - 1] for n in missing)
                           + f"：{card['title']}"))
        unrouted = sorted(set(nums) - refs)
        if unrouted and card["q"].startswith("Q:"):
            notes.append((card["qline"], "Q 行没有指到 " + "".join(CIRCLED[n - 1] for n in unrouted)
                          + f"（从题目找不到这几条：加进 Q 行，或确认只是备用句）：{card['title']}"))
        n = words(card["q"][2:])
        if n > LIMITS["q_words"]:
            notes.append((card["qline"], f"Q 行 {n} 个英文词，超过 {LIMITS['q_words']}：{card['title']}"))
    if card["chars"] > LIMITS["card_chars"]:
        notes.append((card["line"], f"答题卡 {card['chars']} 个非空白字符，超过 {LIMITS['card_chars']}：{card['title']}"))


fence = False
for ln, raw in enumerate(text.split("\n"), start=offset):
    if raw.startswith("```"):
        fence = not fence
        continue
    if fence or raw.startswith("|") or not raw.strip():
        if card is not None and raw.strip():
            card["chars"] += nonspace(raw)
        if raw.startswith("|") and IMG_RE.search(raw):
            notes.append((ln, "表格里的图片不会缩放，固定行距还会把图裁掉；把图单独放一行"))
        continue
    imgs = list(IMG_RE.finditer(raw))
    for im in imgs:
        check_image(ln, im)
    if imgs and not IMG_RE.sub("", raw).strip():
        continue
    if imgs:
        notes.append((ln, "图片最好单独占一行（和文字写在一起，整段都会变成单倍行距）"))
    line, key = raw, None
    m = COLOR_RE.match(line)
    if m:
        key, line = m.group(1), line[m.end():]
    elif re.match(r"^\{[^}]*\}", line):
        errors.append((ln, f"不认识的颜色键 {line.split('}')[0]}}}，会原样印出来"
                           "（可用 {EXAM} {DESIGN} {W1}…{W12}）"))
    if line.count("**") % 2:
        errors.append((ln, f"加粗符号 ** 没有成对，会原样印出来：{line[:30]}"))

    cm = CARD_RE.match(line)
    if cm:
        close_card()
        card = None
        kind = cm.group(2)
        counts[kind] += 1
        title = re.sub(r"\*\*", "", line).strip()
        short_title = title[:40]
        if not cm.group(1):
            errors.append((ln, f"卡片标题没有用 ** 加粗，标题不会着色：{short_title}"))
        if kind == "★★★★":
            if key is None:
                tm = re.search(r"〔(\w+)", line)
                if not tm:
                    errors.append((ln, f"答题卡标题里没有〔主题〕，会用灰色：{short_title}"))
                elif topic_color(tm.group(1)) is None:
                    errors.append((ln, f"〔{tm.group(1)}〕配不上颜色，会用灰色（在说明里写 \"配色: {tm.group(1)}=W3\"）"
                                       f"：{short_title}"))
            card = {"line": ln, "title": short_title, "q": None, "qline": ln, "points": [], "chars": nonspace(line)}
        else:
            if key is None:
                notes.append((ln, f"{'精简卡' if kind == '★★★ ' else '二星单句'}行首没有颜色键（如 {{W3}}），"
                                  f"标题不会着色：{short_title}"))
            what = "精简卡" if kind == "★★★ " else "二星单句"
            limit = LIMITS["mini_chars"] if kind == "★★★ " else LIMITS["oneliner_chars"]
            if nonspace(line) > limit:
                notes.append((ln, f"{what} {nonspace(line)} 个非空白字符，超过 {limit}：{short_title}"))
            bm = re.match(r"\*\*[^*]*\*\*\s*(.*)", line)
            if bm and bm.group(1).strip():
                check_sentence(ln, bm.group(1), what, short_title)
        continue

    if line.startswith(("Q:", "用法")):
        if card is None:
            notes.append((ln, f"Q 行不在答题卡里：{line[:30]}"))
        else:
            if card["q"] is None and not card["points"]:
                card["q"], card["qline"] = line, ln
            card["chars"] += nonspace(line)
        continue

    if line[0] in CIRCLED:
        if card is None:
            errors.append((ln, f"要点不在任何答题卡里（前面是精简卡或单句？）：{line[:30]}"))
            continue
        card["points"].append((ln, CIRCLED.index(line[0]) + 1))
        card["chars"] += nonspace(line)
        tm = TAG_RE.match(line)
        if not tm:
            notes.append((ln, f"要点标签认不出来，不会加粗着色（标签用中文，或英文小标题加冒号）：{line[:30]}"))
            sentence = line[1:].strip().split(" ", 1)[-1]
        else:
            sentence = line[tm.end():].strip()
        check_sentence(ln, sentence, "要点", line[:30])
        n = words(sentence)
        if n > LIMITS["point_words"]:
            notes.append((ln, f"要点 {n} 个英文词，超过 {LIMITS['point_words']}（约一分一句）：{line[:30]}"))
        continue

    if card is not None:
        card["chars"] += nonspace(line)
close_card()

print(f"答题卡 {counts['★★★★']} 张，精简卡 {counts['★★★ ']} 张，二星单句 {counts['★★ ']} 条；"
      f"图片 {len(infos)} 张；错误 {len(errors)} 条，提醒 {len(notes)} 条")
for label, items in (("错误", errors), ("提醒", notes), ("图片", infos)):
    for ln, msg in sorted(items):
        print(f"  [{label}] 第 {ln} 行：{msg}" if ln else f"  [{label}] {msg}")
n_sent = slots["with"] + slots["without"]
if n_sent:
    print(f"可抄的句子 {n_sent} 句：{slots['without']} 句原样抄，{slots['with']} 句带 [ ] 换词槽（考场上只换槽里的词）")

if args.similar is not None:         # 用词接近的两句：同一个意思写了两遍，挤版时先看能不能删一句
    STOP = set("""the a an and or of to for in on by with as is are be been being that which so such from at it its
    their this these those than not can should must may each into when where while whereas who what how why also
    only more most other any all both before after through about over under between because if then there was were
    has have had do does did will would could""".split())

    def content(t):
        t = re.sub(r"\[[^\]]*\]", " ", t.lower())
        return {w for w in re.findall(r"[a-z][a-z'\-]*", t) if w not in STOP and len(w) > 2}
    sets = [(ln, head, content(t)) for ln, head, t in sentences]
    pairs = []
    for i, (l1, h1, w1) in enumerate(sets):
        for l2, h2, w2 in sets[i + 1:]:
            if len(w1) >= 4 and len(w2) >= 4:
                share = len(w1 & w2) / len(w1 | w2)
                if share >= args.similar:
                    pairs.append((share, l1, h1, l2, h2))
    pairs.sort(reverse=True)
    print(f"用词接近的句子 {len(pairs)} 对（实词重合 ≥ {args.similar:.0%}；同一个意思写了两遍时，留 Q 行指到的那句）：")
    for share, l1, h1, l2, h2 in pairs[:30]:
        print(f"  {share:.0%}  第 {l1} 行 {h1[:28]}  ↔  第 {l2} 行 {h2[:28]}")
    if len(pairs) > 30:
        print(f"  … 还有 {len(pairs) - 30} 对（把比例调高再看）")
sys.exit(1 if errors else 0)
