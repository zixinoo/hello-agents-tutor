# -*- coding: utf-8 -*-
"""
云服务免密钥链路验证（对照 SDK 实际协议，已跑通）

协议要点（从 SDK 逆向确认）：
  鉴权头  x-wb-webapp-access-key: <publishableKey>   ← 不是 Authorization: Bearer
  前缀    /.cloud
  模型    GET  /.cloud/llm/models
  对话    POST /.cloud/llm/chat/completions   (stream 必须 true)
"""
import json
import urllib.request
import urllib.error

ENDPOINT = "https://agent-tutor.app.workbuddy.host"
PUB_KEY = "wbpk_u4Sl3bASY6xTnLP0rl8M6T_BJG1uy2J7UkLZdc4XeGee0XMMxgsv6jZ"


def call(path, body=None, method="GET", accept="application/json", timeout=100):
    r = urllib.request.Request(ENDPOINT + path,
                               data=json.dumps(body).encode() if body else None,
                               method=method)
    r.add_header("Content-Type", "application/json")
    r.add_header("Accept", accept)
    r.add_header("x-wb-webapp-access-key", PUB_KEY)
    r.add_header("Origin", ENDPOINT)
    return urllib.request.urlopen(r, timeout=timeout)


print("=" * 72)
print("1) 模型列表  GET /.cloud/llm/models")
print("=" * 72)
models = []
try:
    with call("/.cloud/llm/models") as r:
        d = json.loads(r.read().decode())
        models = d if isinstance(d, list) else (d.get("data") or [])
        print(f"HTTP 200 — 共 {len(models)} 个免密钥模型")
        for m in models:
            if isinstance(m, dict):
                caps = []
                if m.get("supportsReasoning") is True:
                    caps.append("推理")
                if m.get("supportsImages") is True:
                    caps.append("读图")
                flag = f"  [{','.join(caps)}]" if caps else ""
                print(f"  {m.get('name','?'):24} {m.get('id','?'):28}{flag}")
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:300])
except Exception as e:
    print("ERR", type(e).__name__, e)

print()
print("=" * 72)
print("2) 流式问答  POST /.cloud/llm/chat/completions")
print("=" * 72)
if not models:
    print("模型列表为空，跳过")
    raise SystemExit(0)

mid = next((m["id"] for m in models if isinstance(m, dict) and m.get("disabled") is not True),
           models[0].get("id") if isinstance(models[0], dict) else models[0])
print("模型:", mid)
print("--- 输出 ---")
body = {
    "model": mid,
    "messages": [
        {"role": "system", "content": "你是《从零开始构建智能体》的答疑老师，回答简洁并标注章节。"},
        {"role": "user", "content": "ReAct 范式的核心循环是什么？"},
    ],
    "stream": True,
}
content, n = "", 0
try:
    with call("/.cloud/llm/chat/completions", body, "POST", "text/event-stream") as r:
        for raw in r:
            line = raw.decode("utf-8", "ignore").strip()
            if not line.startswith("data:"):
                continue
            p = line[5:].strip()
            if p == "[DONE]":
                print("\n[DONE]")
                break
            try:
                j = json.loads(p)
                d = (j.get("choices") or [{}])[0].get("delta") or {}
                if d.get("content"):
                    content += d["content"]
                    n += 1
                    print(d["content"], end="", flush=True)
            except Exception:
                pass
except urllib.error.HTTPError as e:
    print("HTTP", e.code, e.read().decode()[:400])
except Exception as e:
    print("ERR", type(e).__name__, e)

print()
print("=" * 72)
print(f"{'✅ 免密钥链路验证通过' if content else '❌ 无内容'}  ({n} 分片 / {len(content)} 字)")
