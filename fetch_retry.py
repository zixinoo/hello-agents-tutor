# -*- coding: utf-8 -*-
"""重试下载失败的章节，走 GitHub API（base64 解码）作为备选通道"""
import urllib.request
import json
import base64
import os
import time

API = "https://api.github.com/repos/datawhalechina/hello-agents/contents/docs"

CHAPTERS = {
    2: "第二章 智能体发展史.md",
    3: "第三章 大语言模型基础.md",
    12: "第十二章 智能体性能评估.md",
}

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)

for n, name in CHAPTERS.items():
    dest = os.path.join(OUT, f"ch{n}.md")
    done = False
    for attempt in range(1, 4):
        try:
            import urllib.parse
            quoted = urllib.parse.quote(name)
            url = f"{API}/chapter{n}/{quoted}"
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/vnd.github.v3+json",
            })
            with urllib.request.urlopen(req, timeout=45) as r:
                d = json.load(r)
            text = base64.b64decode(d["content"]).decode("utf-8")
            if len(text) < 500:
                raise ValueError(f"内容过短: {len(text)}")
            with open(dest, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"[OK] ch{n}.md  {name}  {len(text)} 字符 (第{attempt}次尝试)")
            done = True
            break
        except Exception as e:
            print(f"  ch{n} 第{attempt}次失败: {e}")
            time.sleep(2)
    if not done:
        print(f"[FAIL] ch{n} {name} 三次均失败")

print("\n--- 当前 data 目录 ---")
for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    print(f"  {f}: {os.path.getsize(p)} bytes")
