#!/usr/bin/env python3
"""把 slides/src.html 的圖片嵌入，輸出單一檔案 slides/enoshima-guide.html。"""
import base64, io, os, re
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
src = os.path.join(ROOT, "slides", "src.html")
out = os.path.join(ROOT, "slides", "enoshima-guide.html")
html = open(src, encoding="utf-8").read()
def embed(m):
    path = os.path.normpath(os.path.join(os.path.dirname(src), m.group(1)))
    im = Image.open(path).convert("RGB")
    im.thumbnail((1400, 1400))
    buf = io.BytesIO(); im.save(buf, "JPEG", quality=82)
    return 'src="data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode() + '"'
html = re.sub(r'src="(\.\./assets/[^"]+)"', embed, html)
open(out, "w", encoding="utf-8").write(html)
print("built", out, round(os.path.getsize(out)/1024), "KB")
