#!/usr/bin/env python3
"""從各景點頁的「## 查證狀態」彙整出 wiki/待查證清單.md。

用法：python3 scripts/build_todo.py
規則：
  - 每個 type: spot／restaurant／cafe 的頁面都要有「## 查證狀態」，缺少就報錯（退出碼 1）。
  - 官網狀態只能是：已有官網資料／已知官網，尚未取得／尚未找到官網。
  - 證據狀態開頭只能是：官方已核對／旅遊專門網站查證／Google 地圖實測／多來源一致／單一來源／無來源；可加「；有矛盾」。
"""
import os, re, sys, glob, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OFFICIAL = ["已有官網資料", "已知官網，尚未取得", "尚未找到官網"]
EVIDENCE = ["官方已核對", "旅遊專門網站查證", "Google 地圖實測", "多來源一致", "單一來源", "無來源"]
problems, spots = [], []

for f in sorted(glob.glob(os.path.join(ROOT, "wiki", "**", "*.md"), recursive=True)):
    t = open(f, encoding="utf-8").read()
    fm = re.match(r"---\n(.*?)\n---", t, re.S)
    tm = re.search(r"^type: (spot|restaurant|cafe)$", fm.group(1), re.M) if fm else None
    if not tm:
        continue
    ptype = tm.group(1)
    name = os.path.basename(f)[:-3]
    m = re.search(r"^## 查證狀態\n(.*?)(?=\n## |\Z)", t, re.S | re.M)
    if not m:
        problems.append(f"{name}：缺少「## 查證狀態」")
        continue
    sec = m.group(1)
    def get(label):
        x = re.search(r"^- " + label + r"：(.*)$", sec, re.M)
        return x.group(1).strip() if x else None
    official, url, todo = get("官網狀態"), get("官網網址"), get("待辦")
    if official not in OFFICIAL:
        problems.append(f"{name}：官網狀態不合法：{official}")
    rows = []
    for line in sec.splitlines():
        if line.startswith("|") and not line.startswith("| 欄位") and not line.startswith("|---"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if len(cells) != 4:
                problems.append(f"{name}：表格列欄數不是 4：{line[:30]}"); continue
            if not any(cells[3].startswith(e) for e in EVIDENCE):
                problems.append(f"{name}：證據狀態不合法：{cells[3]}")
            rows.append(cells)
    status = re.search(r"^status: (.*)$", fm.group(1), re.M).group(1)
    spots.append(dict(ptype=ptype, name=name, official=official, url=url, todo=todo, rows=rows, status=status))

if problems:
    print("發現問題：")
    for p in problems: print("-", p)
    sys.exit(1)

GROUPS = [("spot", "景點"), ("restaurant", "餐廳"), ("cafe", "咖啡廳甜點")]
need = [s for s in spots if s["official"] != "已有官網資料" or (s["todo"] and s["todo"] != "無")]
done = [s for s in spots if s not in need]
CORE_KEYS = ("營業", "開放", "公休", "休業", "交通時間", "地址", "座標", "最後點餐", "拝觀時間")
is_core = lambda r: any(k in r[0] for k in CORE_KEYS)
weak = lambda r: r[3].startswith(("單一來源", "無來源")) and "可接受" not in r[3]   # 有矛盾不算（使用者決定：不一致沒關係）
eligible = lambda s: not any(weak(r) for r in s["rows"] if is_core(r))

out = ["---", "type: checklist", "id: checklist-verify", "name: 待查證清單",
       f"updated: {datetime.date.today().isoformat()}", "---", "",
       "# 待查證清單", "",
       "> 由 `scripts/build_todo.py` 從各頁的「查證狀態」自動產生，請不要手動修改這頁；要改請改該頁。景點、餐廳、咖啡廳甜點分開列。", "",
       "## 需要你動手"]
for key, label in GROUPS:
    grp = [s for s in need if s["ptype"] == key]
    if not grp:
        continue
    out += ["", f"### {label}", "", "| 名稱 | 官網狀態 | 官網網址 | 待辦 |", "|---|---|---|---|"]
    for s in grp:
        out.append(f"| [[{s['name']}]] | {s['official']} | {s['url']} | {s['todo']} |")
out += ["", "## 符合「已確認」資格（只看時間與地點，見 CLAUDE.md 4.8.1）", ""]
for key, label in GROUPS:
    ok = [s for s in spots if s["ptype"] == key and eligible(s) and s["status"] == "待確認"]
    if ok:
        out.append(f"**{label}**：" + "、".join(f"[[{s['name']}]]" for s in ok))
        out.append("")
out += ["", "## 核心欄位待查證（時間或地點，影響已確認）"]
for key, label in GROUPS:
    grp = [s for s in spots if s["ptype"] == key and any(weak(r) for r in s["rows"] if is_core(r))]
    if not grp:
        continue
    out += ["", f"### {label}", "", "| 名稱 | 欄位 | 目前的值 | 證據狀態 |", "|---|---|---|---|"]
    for s in grp:
        for r in s["rows"]:
            if is_core(r) and weak(r):
                out.append(f"| [[{s['name']}]] | {r[0]} | {r[1]} | {r[3]} |")
out += ["", "## 行前自行確認（非核心欄位，沒有官方資料，不影響已確認）"]
for key, label in GROUPS:
    grp = [s for s in spots if s["ptype"] == key and any(weak(r) for r in s["rows"] if not is_core(r))]
    if not grp:
        continue
    out += ["", f"### {label}", "", "| 名稱 | 欄位 | 目前的值 | 證據狀態 |", "|---|---|---|---|"]
    for s in grp:
        for r in s["rows"]:
            if not is_core(r) and weak(r):
                out.append(f"| [[{s['name']}]] | {r[0]} | {r[1]} | {r[3]} |")
out += ["", "## 已完成（官網資料已齊）", ""]
for key, label in GROUPS:
    grp = [s for s in done if s["ptype"] == key]
    if grp:
        out.append(f"**{label}**：" + "、".join(f"[[{s['name']}]]" for s in grp))
        out.append("")
out += ["", "## 證據狀態說明", "",
        "- **官方已核對**：有官網或店家官方的資料，由你提供剪藏。",
        "- **旅遊專門網站查證**：gltjp 這類旅遊專門網站的頁面，頁面自己標示經官方確認或有監製單位；是網站的標示，我們無法獨立驗證。",
        "- **Google 地圖實測**：路線時間與座標，我用瀏覽器實際查詢。",
        "- **多來源一致**：沒有官方資料，但有兩個以上來源說法一致。",
        "- **單一來源**：只有一個第二手來源，沒有佐證。",
        "- **無來源**：沒查到。",
        "- **有矛盾**：來源之間不一致，兩者都留在頁面備註；使用者決定不一致沒關係，不影響已確認。",
        "- 官網狀態「尚未找到官網」是指我沒找到，不代表沒有。", ""]
open(os.path.join(ROOT, "wiki", "待查證清單.md"), "w", encoding="utf-8").write("\n".join(out))
print(f"已產生 wiki/待查證清單.md：{len(spots)} 頁（景點 {sum(x["ptype"]=="spot" for x in spots)}、餐廳 {sum(x["ptype"]=="restaurant" for x in spots)}、咖啡廳甜點 {sum(x["ptype"]=="cafe" for x in spots)}），需要你動手 {len(need)} 頁")
