# -*- coding: utf-8 -*-
"""
验证云端额度 RPC（bump / refund / get）在真实 HTTP 链路上的行为。
走的是浏览器同一条链路：POST /.cloud/database/rest/rpc/<fn>，头 x-wb-webapp-access-key。
"""
import json
import urllib.request
import urllib.error

ENDPOINT = "https://agent-tutor.app.workbuddy.host"
KEY = "wbpk_u4Sl3bASY6xTnLP0rl8M6T_BJG1uy2J7UkLZdc4XeGee0XMMxgsv6jZ"
DEVICE = "verify_quota_dev_001"


def rpc(fn, payload):
    url = f"{ENDPOINT}/.cloud/database/rest/rpc/{fn}"
    body = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-wb-webapp-access-key", KEY)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()


def main():
    print("=" * 60)
    print("云端额度 RPC 验证（真实 HTTP）")
    print("=" * 60)

    # 0. 先清干净（用 get 看初始值）
    st, d = rpc("get_paid_usage", {"p_device": DEVICE})
    print(f"\n[0] get_paid_usage  -> HTTP {st}  {d}")

    # 1. 第 1 次
    st, d = rpc("bump_paid_usage", {"p_device": DEVICE, "p_limit": 2})
    print(f"[1] bump（第1次）   -> HTTP {st}  {d}")

    # 2. 第 2 次
    st, d = rpc("bump_paid_usage", {"p_device": DEVICE, "p_limit": 2})
    print(f"[2] bump（第2次）   -> HTTP {st}  {d}")

    # 3. 第 3 次（应被拒）
    st, d = rpc("bump_paid_usage", {"p_device": DEVICE, "p_limit": 2})
    print(f"[3] bump（第3次）   -> HTTP {st}  {d}   <- 期望 allowed=false")

    # 4. 退还 1 次
    st, d = rpc("refund_paid_usage", {"p_device": DEVICE})
    print(f"[4] refund          -> HTTP {st}  {d}   <- 期望 used_count=1")

    # 5. 再 bump 一次（退还后应又能用）
    st, d = rpc("bump_paid_usage", {"p_device": DEVICE, "p_limit": 2})
    print(f"[5] bump（退还后）  -> HTTP {st}  {d}   <- 期望 allowed=true, used=2")

    # 6. 最终值
    st, d = rpc("get_paid_usage", {"p_device": DEVICE})
    print(f"[6] get_paid_usage  -> HTTP {st}  {d}   <- 期望 2")
    print("\n提示：测试数据已写入 device_key =", DEVICE, "（真实用户不受影响）")


if __name__ == "__main__":
    main()
