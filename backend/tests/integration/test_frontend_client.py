"""系统测试前端链路: REST API + WebSocket + 数据格式验证

模拟前端浏览器行为，验证:
1. 12 个 REST 端点
2. WebSocket 事件流
3. snake_case/camelCase 数据转换
"""

import asyncio
import json
import httpx
import websockets

BASE = "http://localhost:8000/api"
WS_BASE = "ws://localhost:8000/ws/discussions"
SESSION = "frontend-test-client"

PASS = 0
FAIL = 0


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name}  -- {detail}")
    return condition


async def test_rest_endpoints():
    """1. 测试全部 REST 端点"""
    global PASS, FAIL
    H = {"Content-Type": "application/json;charset=utf-8", "X-Session-Id": SESSION}

    print("\n" + "=" * 60)
    print("1. REST API 端点测试")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=120) as c:
        # 创建
        r = await c.post(
            f"{BASE}/discussions",
            json={"topic": "前端链路测试", "expert_count": 3, "max_rounds": 3},
            headers=H,
        )
        check("POST /discussions 返回 201", r.status_code == 201, f"got {r.status_code}")
        check("响应有 code/data/message", all(k in r.json() for k in ["code", "data", "message"]))
        check("status=pending", r.json()["data"]["status"] == "pending")
        d_id = r.json()["data"]["id"]
        print(f"    discussion_id = {d_id[:8]}...")

        # 生成嘉宾
        r = await c.post(
            f"{BASE}/discussions/{d_id}/panel/generate",
            json={"regenerate_member_id": None},
            headers=H,
        )
        check("POST /panel/generate 返回 200", r.status_code == 200, f"got {r.status_code}")
        panel = r.json()["data"]
        check("host 有完整字段", all(k in panel["host"] for k in ["name", "title", "stance", "color"]))
        check("experts 数量=3", len(panel["experts"]) == 3)
        print(f"    host={panel['host']['name']}")

        # 确认
        confirm = {"host": panel["host"], "experts": panel["experts"]}
        r = await c.put(f"{BASE}/discussions/{d_id}/panel", json=confirm, headers=H)
        check("PUT /panel 返回 200", r.status_code == 200)
        check("panel_confirmed=true", r.json()["data"]["panel_confirmed"] is True)

        # 开始
        r = await c.post(f"{BASE}/discussions/{d_id}/start", headers=H)
        check("POST /start 返回 200", r.status_code == 200)
        check("status=live", r.json()["data"]["status"] == "live")

        # 列表
        r = await c.get(f"{BASE}/discussions?status=live")
        check("GET /discussions 列表非空", len(r.json()["data"]["items"]) > 0)

        # 详情 (等 2s)
        await asyncio.sleep(2)
        r = await c.get(f"{BASE}/discussions/{d_id}")
        check("GET /discussions/{id} 返回 200", r.status_code == 200)
        detail = r.json()["data"]
        check("panel 有嘉宾", len(detail["panel"]) >= 3)
        print(f"    transcript={len(detail['transcript'])} 条")

        # 暂停
        r = await c.post(f"{BASE}/discussions/{d_id}/pause", headers=H)
        check("POST /pause 返回 200", r.status_code == 200)

        # 继续
        r = await c.post(f"{BASE}/discussions/{d_id}/resume", headers=H)
        check("POST /resume 返回 200", r.status_code == 200)

        # 手动推进
        r = await c.post(f"{BASE}/discussions/{d_id}/next", headers=H)
        check("POST /next 返回 200", r.status_code == 200)

        # 结束
        r = await c.post(f"{BASE}/discussions/{d_id}/end", headers=H)
        check("POST /end 返回 200", r.status_code == 200)
        check("status=ended", r.json()["data"]["status"] == "ended")

        # 报告
        r = await c.get(f"{BASE}/discussions/{d_id}/report")
        check("GET /report 返回 200", r.status_code == 200)
        check("report 有 transcript", "transcript" in r.json()["data"])

        # 权限
        r2 = await c.post(f"{BASE}/discussions", json={"topic": "权限测试", "expert_count": 2}, headers=H)
        priv_id = r2.json()["data"]["id"]
        r2 = await c.post(
            f"{BASE}/discussions/{priv_id}/end",
            headers={"Content-Type": "application/json", "X-Session-Id": "OTHER-SESSION"},
        )
        check("非创建者返回 40301", r2.json()["code"] == 40301, f"got {r2.json()['code']}")


async def test_websocket_events():
    """2. 测试 WebSocket 事件推送"""
    global PASS, FAIL
    H = {"Content-Type": "application/json;charset=utf-8", "X-Session-Id": SESSION}

    print("\n" + "=" * 60)
    print("2. WebSocket 事件测试")
    print("=" * 60)

    # 创建+生成+确认
    async with httpx.AsyncClient(timeout=120) as c:
        r = await c.post(f"{BASE}/discussions", json={"topic": "WS测试", "expert_count": 2, "max_rounds": 2}, headers=H)
        ws_id = r.json()["data"]["id"]
        r = await c.post(f"{BASE}/discussions/{ws_id}/panel/generate", json={"regenerate_member_id": None}, headers=H)
        panel = r.json()["data"]
        await c.put(f"{BASE}/discussions/{ws_id}/panel", json={"host": panel["host"], "experts": panel["experts"]}, headers=H)

    # 连接 WS 先，再开始讨论 (确保 WS 在线接收全部事件)
    events = []
    async with websockets.connect(f"{WS_BASE}/{ws_id}?session_id={SESSION}") as ws:
        # 先连上 WS，再通过 REST 开始讨论
        async with httpx.AsyncClient(timeout=120) as c:
            await c.post(f"{BASE}/discussions/{ws_id}/start", headers=H)

        # 接收事件 30 个或 40s
        for _ in range(80):
            try:
                msg = await asyncio.wait_for(ws.recv(), timeout=8)
                events.append(json.loads(msg))
            except asyncio.TimeoutError:
                break

    types = set(e["type"] for e in events)
    counts = {}
    for e in events:
        counts[e["type"]] = counts.get(e["type"], 0) + 1
    print(f"    收到 {len(events)} 个事件, 分布: {counts}")

    check("收到 initial_snapshot", "initial_snapshot" in types)
    check("收到 utterance_token", "utterance_token" in types)
    check("收到 utterance_complete", "utterance_complete" in types)
    check("收到 expert_status", "expert_status" in types)

    # 验证字段名 (snake_case)
    for e in events:
        d = e.get("data", {})
        if e["type"] == "expert_status":
            expected = ["member_id", "member_name", "member_color", "status", "focus_summary", "desire_value", "timestamp"]
            check("expert_status 字段对齐 API 契约", all(k in d for k in expected))
            break

    for e in events:
        d = e.get("data", {})
        if e["type"] == "utterance_complete":
            expected = ["utterance_id", "member_id", "member_name", "member_title", "member_color", "content", "utterance_type"]
            check("utterance_complete 字段对齐 API 契约", all(k in d for k in expected))
            break

    # 验证 initial_snapshot 包含 transcript
    for e in events:
        if e["type"] == "initial_snapshot":
            snap = e["data"]
            check("snapshot 有 transcript", "transcript" in snap)
            check("snapshot 有 consensus", "consensus" in snap)
            break


async def test_data_format():
    """3. 数据格式往返测试"""
    global PASS, FAIL

    print("\n" + "=" * 60)
    print("3. Data Format (snake_case <-> camelCase)")
    print("=" * 60)

    H = {"Content-Type": "application/json;charset=utf-8", "X-Session-Id": SESSION}

    async with httpx.AsyncClient(timeout=30) as c:
        # 前端 keysToSnake: {expertCount:4} → {expert_count:4}
        # 后端接收 snake_case
        r = await c.post(f"{BASE}/discussions", json={"topic": "格式测试", "expert_count": 4, "max_rounds": 5}, headers=H)
        check("snake_case 请求被接受", r.status_code == 201, f"got {r.status_code}")

        raw = r.json()["data"]
        check("响应 expert_count=snake_case", "expert_count" in raw)
        check("响应 creator_session_id=snake_case", "creator_session_id" in raw)
        check("响应 current_round=snake_case", "current_round" in raw)
        check("响应 created_at=snake_case", "created_at" in raw)

        # 前端收到后 keysToCamel: {expert_count:4} → {expertCount:4}
        def to_camel(s):
            return "".join(w if i == 0 else w.capitalize() for i, w in enumerate(s.split("_")))

        sample = {"expert_count": 4, "creator_session_id": "s", "current_round": 0, "created_at": "2026"}
        camel = {to_camel(k): v for k, v in sample.items()}
        check("keysToCamel: expert_count→expertCount", camel.get("expertCount") == 4)
        check("keysToCamel: creator_session_id→creatorSessionId", camel.get("creatorSessionId") == "s")
        check("keysToCamel: current_round→currentRound", camel.get("currentRound") == 0)
        check("keysToCamel: created_at→createdAt", camel.get("createdAt") == "2026")


async def main():
    global PASS, FAIL
    await test_rest_endpoints()
    await test_websocket_events()
    await test_data_format()

    print(f"\n{'=' * 60}")
    print(f"结果: {PASS} PASSED / {PASS + FAIL} TOTAL")
    if FAIL == 0:
        print("前端链路全部通过: REST 请求 + WS 事件 + 数据格式")
    else:
        print(f"{FAIL} 项失败，需要修复")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
