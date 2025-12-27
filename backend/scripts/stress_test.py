# backend/scripts/stress_test.py
"""
MovieIn 壓力測試工具

模擬真實用戶查詢，逐步提高負載，監控系統效能指標。

測試階段：
1. 初始 (4 RPS) - 建立基準線
2. 穩定攀升 (6 RPS) - 觀察是否出現排隊
3. 性能臨界點 (8 RPS) - 找出系統瓶頸
4. 負載尖峰 (10 RPS) - 測試超時情況
5. 全面壓力 (15 RPS) - 推到極限
6. 極限測試 (20 RPS) - 找出崩潰點
7. 目標驗證 (50 RPS) - 驗證 Priority 1 修復效果
"""
import asyncio
import aiohttp
import time
import statistics
from typing import List, Dict, Any
from datetime import datetime
import json

# 配置
API_BASE_URL = "http://127.0.0.1:8000"
API_ENDPOINT = "/api/v1/recommend/v2/movies"

# 測試查詢樣本
TEST_QUERIES = [
    {
        "query": "難過的時候適合看什麼電影",
        "selected_moods": ["heartwarming", "uplifting"],
        "selected_genres": ["劇情"],
        "selected_eras": ["90s", "00s"]
    },
    {
        "query": "週末和朋友一起看的輕鬆電影",
        "selected_moods": ["fun", "lighthearted"],
        "selected_genres": ["喜劇"],
        "selected_eras": ["10s", "20s"]
    },
    {
        "query": "深夜一個人看的懸疑片",
        "selected_moods": ["tense", "mysterious"],
        "selected_genres": ["懸疑", "驚悚"],
        "selected_eras": ["00s", "10s"]
    }
]

# 測試階段配置
STRESS_TEST_PHASES = [
    {"name": "初始", "rps": 4, "duration": 30},
    {"name": "穩定攀升", "rps": 10, "duration": 30},
    {"name": "性能臨界", "rps": 20, "duration": 30},
    {"name": "負載尖峰", "rps": 50, "duration": 30},
    {"name": "全面壓力", "rps": 100, "duration": 30},
    {"name": "極限測試", "rps": 200, "duration": 30},
    {"name": "目標驗證", "rps": 300, "duration": 30},
]

async def make_request(session, query):
    """執行單次推薦請求"""
    start_time = time.time()
    try:
        async with session.post(
            f"{API_BASE_URL}{API_ENDPOINT}",
            json=query,
            timeout=aiohttp.ClientTimeout(total=30)
        ) as response:
            latency_ms = (time.time() - start_time) * 1000
            if response.status == 200:
                data = await response.json()
                return {
                    "success": True,
                    "status": response.status,
                    "latency_ms": latency_ms,
                    "error": None
                }
            else:
                text = await response.text()
                return {
                    "success": False,
                    "status": response.status,
                    "latency_ms": latency_ms,
                    "error": f"HTTP {response.status}"
                }
    except asyncio.TimeoutError:
        return {
            "success": False,
            "status": 0,
            "latency_ms": 30000,
            "error": "Timeout"
        }
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"❌ Request error: {error_msg}")
        return {
            "success": False,
            "status": 0,
            "latency_ms": latency_ms,
            "error": error_msg
        }

async def run_phase(phase):
    """執行單一測試階段"""
    print(f"\n{'='*70}")
    print(f"階段: {phase['name']} | {phase['rps']} RPS | {phase['duration']}s")
    print(f"{'='*70}")
    
    rps = phase["rps"]
    duration = phase["duration"]
    interval = 1.0 / rps
    
    results = []
    start_time = time.time()
    
    connector = aiohttp.TCPConnector(limit=rps * 2)
    async with aiohttp.ClientSession(connector=connector) as session:
        request_count = 0
        while time.time() - start_time < duration:
            query = TEST_QUERIES[request_count % len(TEST_QUERIES)]
            task = asyncio.create_task(make_request(session, query))
            results.append(task)
            request_count += 1
            await asyncio.sleep(interval)
        
        print(f" 等待 {len(results)} 個請求完成...")
        completed = await asyncio.gather(*results, return_exceptions=True)
    
    # 統計
    successful = [r for r in completed if isinstance(r, dict) and r.get("success")]
    failed = [r for r in completed if isinstance(r, dict) and not r.get("success")]
    latencies = [r["latency_ms"] for r in successful]
    
    if latencies:
        avg_latency = statistics.mean(latencies)
        p99_latency = statistics.quantiles(latencies, n=100)[98] if len(latencies) > 100 else max(latencies)
    else:
        avg_latency = p99_latency = 0
    
    total = len(completed)
    success_rate = (len(successful) / total * 100) if total > 0 else 0
    
    # 健康狀態
    if success_rate >= 99 and p99_latency < 1000:
        health = "健康 "
    elif success_rate >= 95:
        health = "警告 "
    elif success_rate >= 80:
        health = "阻塞 "
    else:
        health = "崩潰 "
    
    print(f"\n 結果:")
    print(f"   總請求: {total}")
    print(f"   成功: {len(successful)} ({success_rate:.1f}%)")
    print(f"   失敗: {len(failed)}")
    print(f"   平均延遲: {avg_latency:.0f}ms")
    print(f"   P99延遲: {p99_latency:.0f}ms")
    print(f"   健康狀態: {health}")
    
    return {
        "phase": phase["name"],
        "rps": rps,
        "success_rate": success_rate,
        "avg_latency": avg_latency,
        "p99_latency": p99_latency,
        "health": health
    }

async def run_stress_test():
    """執行完整壓力測試"""
    print("\n MovieIn 壓力測試 - Priority 1 驗證\n")
    
    # 預熱
    print(" 預熱中...")
    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[make_request(session, TEST_QUERIES[0]) for _ in range(5)])
    
    all_results = []
    for i, phase in enumerate(STRESS_TEST_PHASES, 1):
        print(f"\n 階段 {i}/{len(STRESS_TEST_PHASES)}")
        result = await run_phase(phase)
        all_results.append(result)
        if i < len(STRESS_TEST_PHASES):
            await asyncio.sleep(10)
    
    # 總結
    print(f"\n{'='*70}")
    print("總結報告")
    print(f"{'='*70}")
    print(f"{'階段':<12} {'RPS':<6} {'平均延遲':<12} {'P99延遲':<12} {'成功率':<10} {'狀態':<10}")
    print("-" * 70)
    for r in all_results:
        print(f"{r['phase']:<12} {r['rps']:<6} {r['avg_latency']:>8.0f}ms  {r['p99_latency']:>8.0f}ms  {r['success_rate']:>6.1f}%   {r['health']:<10}")
    
    # 驗證目標
    target = next((r for r in all_results if r['rps'] == 300), None)
    print(f"\n🎯 高並發目標 (300 RPS):")
    if target and target['success_rate'] >= 95 and target['p99_latency'] < 1000:
        print("   ✅ 達成！生產級別性能")
    else:
        print("    未達成")

async def run_quick_test():
    """快速測試"""
    phases = [
        {"name": "基準", "rps": 6, "duration": 20},
        {"name": "負載", "rps": 10, "duration": 20},
        {"name": "目標", "rps": 50, "duration": 20},
    ]
    for phase in phases:
        await run_phase(phase)
        await asyncio.sleep(5)

def main():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "quick":
        asyncio.run(run_quick_test())
    else:
        asyncio.run(run_stress_test())

if __name__ == "__main__":
    main()
