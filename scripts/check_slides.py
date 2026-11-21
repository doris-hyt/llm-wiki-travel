#!/usr/bin/env python3
"""簡報檢查腳本（CLAUDE.md 5.7 的第 4 步）。

用法：python3 scripts/check_slides.py slides/src.html
檢查項目：
  a. 每張投影片的 data-src 都能對到 wiki 頁面
  b. 投影片上的數字能在被引用的頁面裡找到
  c. 引用核心資料（時間、地點）尚未確認的頁面，投影片必須標示「待確認」
  d. 只出現在「待查證／估計」行的數字，投影片必須同時標示待查證或「行前自行確認」
  e. 禁用詞（wiki 沒有來源的說法）
  f. 圖片檔存在
  g. 每個景點、餐廳、咖啡廳甜點頁與概念頁至少被引用一次
  h. 每張（meta 除外）下方的來源列（class="src"）要寫出「來源：」或「圖片：」
退出碼：0 = 全部通過，1 = 有問題
"""
import os, re, sys, glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
html_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "slides", "src.html")
html = open(html_path, encoding="utf-8").read()

# ---- 載入 wiki 頁面（以檔名與 id 兩種方式索引）----
pages = {}      # key -> (path, text, frontmatter dict)
for f in glob.glob(os.path.join(ROOT, "wiki", "**", "*.md"), recursive=True):
    text = open(f, encoding="utf-8").read()
    stem = os.path.basename(f)[:-3]
    fm = {}
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if m:
        for line in m.group(1).splitlines():
            if re.match(r"^[A-Za-z_]+:", line):
                k, v = line.split(":", 1)
                fm[k.strip()] = v.strip()
    pages[stem] = (f, text, fm)
    if "id" in fm:
        pages[fm["id"]] = (f, text, fm)

CORE_KEYS = ("營業", "開放", "公休", "休業", "交通時間", "地址", "座標", "最後點餐", "拝觀時間")
def core_verified(text):
    """依 4.8.1：核心欄位（時間、地點）證據都不是『單一來源／無來源』（標『可接受』者除外）。"""
    m = re.search(r"## 查證狀態(.*)", text, re.S)
    if not m:
        return False
    for line in m.group(1).splitlines():
        if line.startswith("|") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) == 4 and cells[0] != "欄位" and any(k in cells[0] for k in CORE_KEYS):
                if cells[3].startswith(("單一來源", "無來源")) and "可接受" not in cells[3]:
                    return False
    return True

BANNED = ["トンビ", "老鷹", "鳶", "必去", "最好吃", "全球第一", "保證"]
NUM = re.compile(r"\d[\d,]*(?::\d\d)?")

issues = []
cited = set()
slides = re.findall(r'<section class="slide[^"]*" data-src="([^"]*)">(.*?)</section>', html, re.S)
total_sections = len(re.findall(r'<section class="slide', html))
if len(slides) != total_sections:
    # 自我檢查：腳本抓到的張數必須等於實際張數，否則有投影片被悄悄略過
    print(f"[腳本錯誤] 抓到 {len(slides)} 張，但實際有 {total_sections} 張")
    sys.exit(2)

def norm(s):
    return s.replace(",", "")

for idx, (srcs, body) in enumerate(slides, 1):
    srcs = [s.strip() for s in srcs.split(",") if s.strip()]
    if not srcs:
        issues.append((idx, "a", "沒有 data-src"))
        continue
    if srcs == ["meta"]:
        continue
    texts, spot_pending = [], False
    for s in srcs:
        if s == "index":
            p = os.path.join(ROOT, "wiki", "index.md")
            texts.append(open(p, encoding="utf-8").read())
            continue
        if s not in pages:
            issues.append((idx, "a", f"data-src 找不到頁面：{s}"))
            continue
        cited.add(s if s in pages else s)
        path, text, fm = pages[s]
        cited.add(os.path.basename(path)[:-3])
        texts.append(text)
        if fm.get("type") in ("spot", "restaurant", "cafe") and not core_verified(text):
            spot_pending = True
    corpus = norm("\n".join(texts))
    lines = corpus.splitlines()

    plain = re.sub(r'<div class="(eyebrow|src)">.*?</div>', " ", body, flags=re.S)
    plain = re.sub(r"<[^>]+>", " ", plain)
    plain = re.sub(r"\s+", " ", plain)

    # b. 數字
    for tok in sorted(set(NUM.findall(norm(plain)))):
        if not re.search(r"(?<![\d.])" + re.escape(tok) + r"(?!\d)", corpus):
            issues.append((idx, "b", f"數字「{tok}」在被引用的頁面裡找不到"))
            continue
        # d. 只出現在待查證／估計行
        hits = [l for l in lines if re.search(r"(?<![\d.])" + re.escape(tok) + r"(?!\d)", l)]
        if hits and all(re.search(r"待查證|估計", l) for l in hits):
            if not re.search(r"待查證|估計|行前自行確認", plain):
                issues.append((idx, "d", f"數字「{tok}」只出現在待查證／估計的內容，投影片沒有標示"))

    # c. 待確認
    if spot_pending and "待確認" not in body:
        issues.append((idx, "c", "引用核心資料尚未確認的頁面，但投影片沒有標示「待確認」"))

    # h. 來源列
    foot = " ".join(re.findall(r'<div class="src">(.*?)</div>', body, re.S))
    if not re.search(r"來源：|圖片：", foot):
        issues.append((idx, "h", "下方沒有來源列（來源：／圖片：）"))

    # e. 禁用詞
    for w in BANNED:
        if w in plain:
            issues.append((idx, "e", f"出現沒有來源的說法：{w}"))

    # f. 圖片
    for img in re.findall(r'<img[^>]+src="([^"]+)"', body):
        if img.startswith("data:"):
            continue   # 已嵌入的圖片
        p = os.path.normpath(os.path.join(os.path.dirname(html_path), img))
        if not os.path.exists(p):
            issues.append((idx, "f", f"圖片不存在：{img}"))

# g. 覆蓋率（以唯一檔案計，stem 與 id 指向同一頁只算一次）
seen = set()
for key, (f, text, fm) in pages.items():
    if f in seen:
        continue
    seen.add(f)
    stem = os.path.basename(f)[:-3]
    if fm.get("type") in ("spot", "restaurant", "cafe", "concept") and stem not in cited:
        issues.append((0, "g", f"頁面沒有被任何投影片引用：{stem}"))

print(f"檢查 {len(slides)} 張投影片，來源頁面 {len([1 for k,v in pages.items() if v[2].get('type')=='source'])} 個")
if not issues:
    print("全部通過")
    sys.exit(0)
for n, code, msg in issues:
    print(f"- 第 {n} 張 [{code}] {msg}" if n else f"- [{code}] {msg}")
print(f"共 {len(issues)} 個問題")
sys.exit(1)
