# -*- coding: utf-8 -*-
"""端到端验证答疑链路：检索 + 组 prompt + 调模型，与网页逻辑一致"""
import os
import json
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
KB = json.load(open(os.path.join(HERE, "data", "knowledge.json"), encoding="utf-8"))
KEY = os.environ.get("OPENROUTER_API_KEY", "")
URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-chat"


def retrieve(query, topk=3):
    """复刻网页里的检索打分逻辑"""
    q = query.lower()
    tokens = set()
    import re
    for w in re.findall(r"[a-z0-9_]+", q):
        if len(w) > 1:
            tokens.add(w)
    zh = re.sub(r"[^\u4e00-\u9fa5]", "", q)
    for i in range(len(zh) - 1):
        tokens.add(zh[i:i + 2])
    for i in range(len(zh) - 2):
        tokens.add(zh[i:i + 3])

    out = []
    for c in KB["chapters"]:
        hay_title = (c["title"] + " " + c["part"]).lower()
        hay_terms = " ".join(c["key_terms"]).lower()
        hay_sym = " ".join(c["code_symbols"]).lower()
        hay_out = " ".join(s["title"] + " " + " ".join(s["points"]) for s in c["outline"]).lower()
        hay_intro = c["intro"].lower()
        sc = 0
        for t in tokens:
            if not t:
                continue
            if t in hay_title:
                sc += 12
            if t in hay_terms:
                sc += 7
            if t in hay_sym:
                sc += 5
            if t in hay_out:
                sc += 3
            if t in hay_intro:
                sc += 1
        if sc:
            out.append((sc, c))
    out.sort(key=lambda x: -x[0])
    return out[:topk]


def build_ctx(hits):
    if not hits:
        return "（未匹配到特定章节）"
    parts = []
    for _, c in hits:
        s = f"### 《{c['title']}》（{c['part']}）\n"
        if c["intro"]:
            s += f"章节概要：{c['intro']}\n"
        for o in c["outline"]:
            s += f"- {o['num']} {o['title']}"
            if o["points"]:
                s += f"\n  要点：{o['points'][0]}"
            s += "\n"
        if c["key_terms"]:
            s += "关键术语：" + "、".join(c["key_terms"][:25]) + "\n"
        if c["code_symbols"]:
            s += "代码符号：" + "、".join(c["code_symbols"][:25]) + "\n"
        parts.append(s)
    return "\n---\n".join(parts)


SYS = """你是一位专门讲授《从零开始构建智能体》(Hello-Agents) 的资深 Agent 答疑老师。

## 硬性规则
1. 涉及教程内容时严格以【教程知识库片段】为准，不编造。
2. 引用具体章节时标注 [第X章]。
3. 代码问题给 Python 示例，简洁可读。
4. 不要说"作为一个AI"，你就是在扮演答疑老师。
5. 概念题 200-400 字，实现题可到 600 字。

## 教程知识库片段
{ctx}

请以答疑老师身份作答。"""


def ask(query):
    hits = retrieve(query)
    ctx = build_ctx(hits)
    print(f"\n{'='*68}")
    print(f"学生提问：{query}")
    print(f"命中章节：{[c['n'] for _, c in hits]}")
    print(f"{'='*68}")
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYS.format(ctx=ctx)},
            {"role": "user", "content": query},
        ],
        "temperature": 0.6,
    }
    req = urllib.request.Request(
        URL, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {KEY}"},
    )
    with urllib.request.urlopen(req, timeout=90) as r:
        d = json.load(r)
    ans = d["choices"][0]["message"]["content"]
    print(f"\n🎓 答疑老师：\n{ans}")
    u = d.get("usage", {})
    print(f"\n[tokens] prompt={u.get('prompt_tokens')} completion={u.get('completion_tokens')}")


if __name__ == "__main__":
    for q in [
        "ReAct 和 Plan-and-Solve 有什么区别？",
        "什么是 MCP 协议？",
    ]:
        try:
            ask(q)
        except Exception as e:
            print(f"[ERROR] {q} -> {e}")
