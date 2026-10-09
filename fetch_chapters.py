# -*- coding: utf-8 -*-
"""下载 hello-agents 教程 16 章正文，统一存为 chN.md"""
import urllib.request
import urllib.parse
import os
import time

BASE = "https://raw.githubusercontent.com/datawhalechina/hello-agents/main/docs"

CHAPTERS = {
    1: "第一章 初识智能体.md",
    2: "第二章 智能体发展史.md",
    3: "第三章 大语言模型基础.md",
    4: "第四章 智能体经典范式构建.md",
    5: "第五章 基于低代码平台的智能体搭建.md",
    6: "第六章 框架开发实践.md",
    7: "第七章 构建你的Agent框架.md",
    8: "第八章 记忆与检索.md",
    9: "第九章 上下文工程.md",
    10: "第十章 智能体通信协议.md",
    11: "第十一章 Agentic-RL.md",
    12: "第十二章 智能体性能评估.md",
    13: "第十三章 智能旅行助手.md",
    14: "第十四章 自动化深度研究智能体.md",
    15: "第十五章 构建赛博小镇.md",
    16: "第十六章 毕业设计.md",
}

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)

ok, fail = [], []
for n, name in CHAPTERS.items():
    quoted = urllib.parse.quote(name)
    url = f"{BASE}/chapter{n}/{quoted}"
    dest = os.path.join(OUT, f"ch{n}.md")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read()
        text = raw.decode("utf-8")
        if len(text) < 500:
            raise ValueError(f"内容过短({len(text)}字符)，可能 404")
        with open(dest, "w", encoding="utf-8") as f:
            f.write(text)
        ok.append((n, name, len(text)))
        print(f"[OK] ch{n}.md  {name}  {len(text)} 字符")
    except Exception as e:
        fail.append((n, name, str(e)))
        print(f"[FAIL] ch{n}  {name}  -> {e}")
    time.sleep(0.3)

print(f"\n成功 {len(ok)} / 失败 {len(fail)}")
if fail:
    for n, name, err in fail:
        print(f"  失败: ch{n} {name}: {err}")
