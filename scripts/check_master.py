"""检查「答题卡式」cheatsheet 的 Markdown 母版（排版之前跑一次）。

用法：
    python check_master.py 你的cheatsheet.md
「错误」是排出来会出问题的地方（颜色错位、颜色键原样印出、Q 行指向不存在的要点……），必须改；
「提醒」是 references/format.md 里的写法规则（缺 Q 行、标签不会着色、英文句子里混了中文、太长……），看情况改。
有错误时退出码为 1。
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
if len(sys.argv) != 2:
    sys.exit(__doc__)

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

LIMITS = {"q_words": 25, "point_words": 40, "card_chars": 1400, "mini_chars": 290, "oneliner_chars": 400}

text = "\n" + Path(sys.argv[1]).read_text(encoding="utf-8").replace("\r\n", "\n")
errors, notes = [], []
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


def nonspace(s):
    return len(re.sub(r"\s", "", s.replace("**", "").replace("`", "")))


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
        continue
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
            limit = LIMITS["mini_chars"] if kind == "★★★ " else LIMITS["oneliner_chars"]
            if nonspace(line) > limit:
                notes.append((ln, f"{'精简卡' if kind == '★★★ ' else '二星单句'} {nonspace(line)} 个非空白字符，"
                                  f"超过 {limit}：{short_title}"))
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
        body = re.sub(r"（[^）]*）|\[[^\]]*\]", " ", plain(sentence))
        if CJK.search(body):
            notes.append((ln, f"要点的英文句子里有中文（考场上不能照抄）：{line[:30]}"))
        if re.match(r"(It|This|These|They)\b", sentence):
            notes.append((ln, f"要点以 It/This/They 开头，单独抄出来看不懂指的是什么：{line[:30]}"))
        n = words(sentence)
        if n > LIMITS["point_words"]:
            notes.append((ln, f"要点 {n} 个英文词，超过 {LIMITS['point_words']}（约一分一句）：{line[:30]}"))
        continue

    if card is not None:
        card["chars"] += nonspace(line)
close_card()

print(f"答题卡 {counts['★★★★']} 张，精简卡 {counts['★★★ ']} 张，二星单句 {counts['★★ ']} 条；"
      f"错误 {len(errors)} 条，提醒 {len(notes)} 条")
for label, items in (("错误", errors), ("提醒", notes)):
    for ln, msg in sorted(items):
        print(f"  [{label}] 第 {ln} 行：{msg}" if ln else f"  [{label}] {msg}")
sys.exit(1 if errors else 0)
