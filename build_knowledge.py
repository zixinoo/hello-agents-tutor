# -*- coding: utf-8 -*-
"""
把 16 章正文压缩成结构化知识库 knowledge.json

策略：分层抽取，保留可答疑的信息密度
- 章引言（首段）：定位与核心问题
- 一二级标题：知识骨架
- 每个二级小节下的首个实质段落（截断到 300 字）：概念要点
- 代码块签名（class/def 行）：可回答"怎么实现"
- 加粗术语：关键概念词表
"""
import os
import re
import json

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "knowledge.json")

TITLES = {
    1: ("第一章 初识智能体", "智能体与语言模型基础"),
    2: ("第二章 智能体发展史", "智能体与语言模型基础"),
    3: ("第三章 大语言模型基础", "智能体与语言模型基础"),
    4: ("第四章 智能体经典范式构建", "构建你的大语言模型智能体"),
    5: ("第五章 基于低代码平台的智能体搭建", "构建你的大语言模型智能体"),
    6: ("第六章 框架开发实践", "构建你的大语言模型智能体"),
    7: ("第七章 构建你的Agent框架", "构建你的大语言模型智能体"),
    8: ("第八章 记忆与检索", "高级知识扩展"),
    9: ("第九章 上下文工程", "高级知识扩展"),
    10: ("第十章 智能体通信协议", "高级知识扩展"),
    11: ("第十一章 Agentic-RL", "高级知识扩展"),
    12: ("第十二章 智能体性能评估", "高级知识扩展"),
    13: ("第十三章 智能旅行助手", "综合案例进阶"),
    14: ("第十四章 自动化深度研究智能体", "综合案例进阶"),
    15: ("第十五章 构建赛博小镇", "综合案例进阶"),
    16: ("第十六章 毕业设计", "毕业设计及未来展望"),
}


def clean(text):
    """剥离 markdown 装饰，保留可读文本"""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"<strong>(.+?)</strong>", r"\1", text)
    text = re.sub(r"`(.+?)`", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"&emsp;|&nbsp;", " ", text)
    text = re.sub(r"\[(.+?)\]\(.+?\)", r"\1", text)   # 链接保留文字
    return text.strip()


def extract(path):
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")

    intro, sections, codes, terms = [], [], [], []
    cur_h1, cur_h2 = None, None
    cur_body = []
    started = False

    def flush():
        """把当前收集的正文挂到对应的 h2"""
        nonlocal cur_body
        if cur_h2 and cur_body:
            joined = " ".join(cur_body)
            joined = re.sub(r"\s+", " ", joined).strip()
            if len(joined) > 30:
                # 取第一个实质句群，最多 300 字
                sections[-1]["points"].append(joined[:300])
        cur_body = []

    for raw in lines:
        line = raw.rstrip()
        if not line:
            continue

        m_h1 = re.match(r"^##\s+(\d+\.\d+)\s+(.+)$", line)      # ## 4.1 xxx
        m_h2 = re.match(r"^###\s+(\d+\.\d+\.\d+)\s+(.+)$", line) # ### 4.1.1 xxx

        if line.startswith("# "):
            continue
        if line.startswith("## ") and not re.match(r"^##\s+\d", line):
            continue

        if m_h1:
            flush()
            cur_h1, cur_h2 = m_h1.group(2).strip(), None
            sections.append({"num": m_h1.group(1), "title": cur_h1, "points": []})
            started = True
            continue

        if m_h2:
            flush()
            cur_h2 = m_h2.group(2).strip()
            sections[-1]["sub"] = sections[-1].get("sub", [])
            sections[-1]["sub"].append(cur_h2)
            continue

        # 代码块：提取签名
        if line.startswith("```"):
            continue
        m_code = re.match(r"^\s*(class|def|async def)\s+(\w+)", line)
        if m_code:
            codes.append(m_code.group(2))
            continue

        # 加粗术语
        for t in re.findall(r"\*\*(.+?)\*\*", line):
            t = clean(t)
            if 1 < len(t) < 30 and not t.endswith(("：", ":")):
                terms.append(t)

        body = clean(line)
        if not started:
            if len(body) > 40:
                intro.append(body)
            continue
        if len(body) > 25 and not body.startswith(("|", "-", "*", "1.")):
            cur_body.append(body)

    flush()

    # 收尾：最后一节可能没被 flush 到
    return intro, sections, codes, terms


kb = {"source": {}, "chapters": []}
for n in sorted(TITLES):
    path = os.path.join(DATA, f"ch{n}.md")
    if not os.path.exists(path):
        print(f"[跳过] ch{n} 不存在")
        continue
    title, part = TITLES[n]
    intro, sections, codes, terms = extract(path)

    # 术语去重保序
    seen, uniq_terms = set(), []
    for t in terms:
        if t not in seen:
            seen.add(t)
            uniq_terms.append(t)

    # 代码签名去重
    seen_c, uniq_codes = set(), []
    for c in codes:
        if c not in seen_c:
            seen_c.add(c)
            uniq_codes.append(c)

    chap = {
        "n": n,
        "title": title,
        "part": part,
        "intro": " ".join(intro)[:600],
        "outline": [
            {
                "num": s["num"],
                "title": s["title"],
                "points": s["points"][:3],
            }
            for s in sections
        ],
        "key_terms": uniq_terms[:40],
        "code_symbols": uniq_codes[:40],
    }
    kb["chapters"].append(chap)
    print(f"[OK] ch{n:>2} {title}  小节 {len(sections)}  术语 {len(uniq_terms)}  符号 {len(uniq_codes)}")

kb["source"] = {
    "repo": "datawhalechina/hello-agents",
    "title": "《从零开始构建智能体》Hello-Agents",
    "url": "https://github.com/datawhalechina/hello-agents",
    "online": "https://hello-agents.datawhale.cc",
    "total_chapters": len(kb["chapters"]),
    "note": "本地化整理的精简知识库，用于离线答疑检索。完整内容请访问原仓库。",
}

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(kb, f, ensure_ascii=False, indent=1)

size = os.path.getsize(OUT)
print(f"\n知识库已生成: {OUT}")
print(f"体积: {size/1024:.1f} KB")
print(f"章节数: {len(kb['chapters'])}")
