"""
MovieIn 壓力測試 - 最終測試腳本
使用 httpx + asyncio 進行並發壓力測試

測試項目：
1. 單一端點壓力測試
2. 混合場景壓力測試（Embedding + Feature 路徑）
3. 快取命中率測試
4. 峰值負載測試
5. 持續負載測試

使用方式：
    python test_stress_final.py --users 50 --duration 60
    python test_stress_final.py --scenario all --users 100
"""

import asyncio
import httpx
import time
import argparse
import statistics
from datetime import datetime
from collections import defaultdict
from typing import List, Dict, Tuple

# ============================================================================
# 配置
# ============================================================================

BASE_URL = "http://127.0.0.1:8000"
TIMEOUT = 30.0

# 測試查詢集合
TEST_QUERIES = {
    "embedding": [
        {
            "query": "難過的時候適合看什麼電影",
            "selected_moods": ["heartwarming"],
            "selected_genres": [],
        },
        {
            "query": "溫暖治癒的超級英雄電影",
            "selected_moods": [],
            "selected_genres": [],
        },
        {
            "query": "A heartwarming family movie with adventure",
            "selected_moods": [],
            "selected_genres": [],
        },
        {
            "query": "想看一些能讓我感動的電影",
            "selected_moods": ["emotional"],
            "selected_genres": [],
        },
    ],
    "feature": [
        {
            "query": "超級英雄動作片",
            "selected_moods": ["動作冒險", "視覺饗宴"],
            "selected_genres": ["Action"],
        },
        {
            "query": "",
            "selected_moods": ["動作冒險"],
            "selected_genres": ["Science Fiction", "Action"],
        },
        {
            "query": "搞笑喜劇",
            "selected_moods": ["feel-good", "輕鬆歡樂"],
            "selected_genres": ["Comedy"],
        },
    ],
    "mixed": [
        {
            "query": "難過的時候適合看什麼電影",
            "selected_moods": ["heartwarming"],
            "selected_genres": [],
        },
        {
            "query": "超級英雄動作片",
            "selected_moods": ["動作冒險"],
            "selected_genres": ["Action"],
        },
        {
            "query": "溫暖治癒的電影",
            "selected_moods": ["heartwarming", "feel-good"],
            "selected_genres": ["Drama"],
        },
        {
            "query": "",
            "selected_moods": ["動作冒險"],
            "selected_genres": ["Science Fiction"],
        },
    ],
}

# ============================================================================
# 統計類別
# ============================================================================

class StressTestStats:
    def __init__(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.response_times: List[float] = []
        self.errors: Dict[str, int] = defaultdict(int)
        self.strategies: Dict[str, int] = defaultdict(int)
        self.status_codes: Dict[int, int] = defaultdict(int)
        self.start_time = None
        self.end_time = None
    
    def add_result(self, success: bool, response_time: float, status_code: int, 
                   strategy: str = None, error: str = None):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
            self.response_times.append(response_time)
            if strategy:
                self.strategies[strategy] += 1
        else:
            self.failed_requests += 1
            if error:
                self.errors[error] += 1
        
        self.status_codes[status_code] += 1
    
    def get_summary(self) -> Dict:
        if not self.response_times:
            return {
                "total_requests": self.total_requests,
                "successful": self.successful_requests,
                "failed": self.failed_requests,
                "error": "No successful requests"
            }
        
        sorted_times = sorted(self.response_times)
        duration = (self.end_time - self.start_time) if self.start_time and self.end_time else 0
        
        return {
            "total_requests": self.total_requests,
            "successful": self.successful_requests,
            "failed": self.failed_requests,
            "success_rate": f"{(self.successful_requests / self.total_requests * 100):.2f}%",
            "duration_seconds": f"{duration:.2f}",
            "requests_per_second": f"{(self.total_requests / duration):.2f}" if duration > 0 else "N/A",
            "response_times": {
                "min": f"{min(sorted_times):.0f}ms",
                "max": f"{max(sorted_times):.0f}ms",
                "mean": f"{statistics.mean(sorted_times):.0f}ms",
                "median": f"{statistics.median(sorted_times):.0f}ms",
                "p95": f"{sorted_times[int(len(sorted_times) * 0.95)]:.0f}ms",
                "p99": f"{sorted_times[int(len(sorted_times) * 0.99)]:.0f}ms",
            },
            "strategies": dict(self.strategies),
            "status_codes": dict(self.status_codes),
            "errors": dict(self.errors) if self.errors else "None",
        }

# ============================================================================
# 測試函數
# ============================================================================

async def make_request(client: httpx.AsyncClient, payload: Dict) -> Tuple[bool, float, int, str, str]:
    """
    發送單一請求
    
    Returns:
        (success, response_time_ms, status_code, strategy, error_msg)
    """
    start = time.time()
    try:
        response = await client.post(
            f"{BASE_URL}/api/v1/recommend/v2/movies",
            json=payload,
            timeout=TIMEOUT
        )
        elapsed_ms = (time.time() - start) * 1000
        
        if response.status_code == 200:
            data = response.json()
            strategy = data.get("strategy", "unknown")
            return (True, elapsed_ms, 200, strategy, None)
        else:
            return (False, elapsed_ms, response.status_code, None, f"HTTP {response.status_code}")
    
    except httpx.TimeoutException:
        elapsed_ms = (time.time() - start) * 1000
        return (False, elapsed_ms, 0, None, "Timeout")
    except Exception as e:
        elapsed_ms = (time.time() - start) * 1000
        return (False, elapsed_ms, 0, None, str(type(e).__name__))


async def run_concurrent_requests(queries: List[Dict], num_users: int, stats: StressTestStats):
    """並發執行請求"""
    async with httpx.AsyncClient() as client:
        tasks = []
        for i in range(num_users):
            payload = queries[i % len(queries)]
            tasks.append(make_request(client, payload))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, Exception):
                stats.add_result(False, 0, 0, None, str(type(result).__name__))
            else:
                success, elapsed, status, strategy, error = result
                stats.add_result(success, elapsed, status, strategy, error)


async def run_sustained_load(queries: List[Dict], users_per_wave: int, duration_seconds: int, stats: StressTestStats):
    """持續負載測試"""
    end_time = time.time() + duration_seconds
    wave = 0
    
    while time.time() < end_time:
        wave += 1
        print(f"  Wave {wave}: {users_per_wave} concurrent users...")
        await run_concurrent_requests(queries, users_per_wave, stats)
        await asyncio.sleep(1)  # 每波之間休息 1 秒


# ============================================================================
# 測試場景
# ============================================================================

async def test_single_endpoint_burst(num_users: int = 50):
    """測試 1: 單一端點爆發測試"""
    print("\n" + "="*70)
    print(f"測試 1: 單一端點爆發測試 ({num_users} 並發用戶)")
    print("="*70)
    
    stats = StressTestStats()
    stats.start_time = time.time()
    
    print(f"▶ 發送 {num_users} 個並發請求...")
    await run_concurrent_requests(TEST_QUERIES["embedding"], num_users, stats)
    
    stats.end_time = time.time()
    print_summary(stats)


async def test_mixed_scenario(num_users: int = 100):
    """測試 2: 混合場景測試（Embedding + Feature）"""
    print("\n" + "="*70)
    print(f"測試 2: 混合場景測試 ({num_users} 並發用戶)")
    print("="*70)
    
    stats = StressTestStats()
    stats.start_time = time.time()
    
    print(f"▶ 混合 Embedding 和 Feature 查詢...")
    await run_concurrent_requests(TEST_QUERIES["mixed"], num_users, stats)
    
    stats.end_time = time.time()
    print_summary(stats)


async def test_cache_effectiveness(num_iterations: int = 3):
    """測試 3: 快取效果測試"""
    print("\n" + "="*70)
    print(f"測試 3: 快取效果測試 ({num_iterations} 輪)")
    print("="*70)
    
    # 使用相同查詢測試快取
    same_query = TEST_QUERIES["embedding"][0]
    
    for i in range(num_iterations):
        print(f"\n▶ 第 {i+1} 輪測試...")
        stats = StressTestStats()
        stats.start_time = time.time()
        
        await run_concurrent_requests([same_query], 20, stats)
        
        stats.end_time = time.time()
        
        summary = stats.get_summary()
        avg_time = summary["response_times"]["mean"]
        print(f"  平均響應時間: {avg_time}")
        print(f"  成功率: {summary['success_rate']}")
        
        if i < num_iterations - 1:
            print("  等待 2 秒...")
            await asyncio.sleep(2)


async def test_sustained_load_scenario(users_per_wave: int = 20, duration: int = 30):
    """測試 4: 持續負載測試"""
    print("\n" + "="*70)
    print(f"測試 4: 持續負載測試 ({users_per_wave} users/wave, {duration}秒)")
    print("="*70)
    
    stats = StressTestStats()
    stats.start_time = time.time()
    
    await run_sustained_load(TEST_QUERIES["mixed"], users_per_wave, duration, stats)
    
    stats.end_time = time.time()
    print_summary(stats)


async def test_peak_load(num_users: int = 200):
    """測試 5: 峰值負載測試"""
    print("\n" + "="*70)
    print(f"測試 5: 峰值負載測試 ({num_users} 並發用戶)")
    print("="*70)
    
    stats = StressTestStats()
    stats.start_time = time.time()
    
    print(f"▶ 發送 {num_users} 個並發請求（峰值測試）...")
    await run_concurrent_requests(TEST_QUERIES["mixed"], num_users, stats)
    
    stats.end_time = time.time()
    print_summary(stats)


# ============================================================================
# 輔助函數
# ============================================================================

def print_summary(stats: StressTestStats):
    """打印測試摘要"""
    summary = stats.get_summary()
    
    print("\n" + "-"*70)
    print("📊 測試結果摘要")
    print("-"*70)
    print(f"總請求數:     {summary['total_requests']}")
    print(f"成功:         {summary['successful']}")
    print(f"失敗:         {summary['failed']}")
    print(f"成功率:       {summary['success_rate']}")
    print(f"測試時長:     {summary['duration_seconds']}s")
    print(f"QPS:          {summary['requests_per_second']}")
    
    if "response_times" in summary and isinstance(summary["response_times"], dict):
        print("\n響應時間:")
        rt = summary["response_times"]
        print(f"  最小:       {rt['min']}")
        print(f"  最大:       {rt['max']}")
        print(f"  平均:       {rt['mean']}")
        print(f"  中位數:     {rt['median']}")
        print(f"  P95:        {rt['p95']}")
        print(f"  P99:        {rt['p99']}")
    
    if summary["strategies"]:
        print("\n推薦策略分佈:")
        for strategy, count in summary["strategies"].items():
            print(f"  {strategy}: {count}")
    
    if summary["errors"] != "None":
        print("\n錯誤:")
        for error, count in summary["errors"].items():
            print(f"  {error}: {count}")
    
    print("-"*70)


async def check_server():
    """檢查伺服器是否運行"""
    try:
        async with httpx.AsyncClient() as client:
            # 使用根路徑檢查
            response = await client.get(f"{BASE_URL}/", timeout=5.0)
            if response.status_code == 200:
                return True
    except:
        return False
    return False


# ============================================================================
# 主程序
# ============================================================================

async def main():
    parser = argparse.ArgumentParser(description="MovieIn 壓力測試")
    parser.add_argument("--scenario", choices=["burst", "mixed", "cache", "sustained", "peak", "all"], 
                       default="all", help="測試場景")
    parser.add_argument("--users", type=int, default=50, help="並發用戶數")
    parser.add_argument("--duration", type=int, default=30, help="持續時間（秒）")
    
    args = parser.parse_args()
    
    print("="*70)
    print("MovieIn 壓力測試")
    print(f"目標: {BASE_URL}")
    print(f"時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # 檢查伺服器
    print("\n🔍 檢查伺服器狀態...")
    if not await check_server():
        print("❌ 錯誤: 伺服器未運行或無法連接")
        print(f"   請確認 {BASE_URL} 可訪問")
        print("\n啟動方式:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000")
        return
    
    print("✅ 伺服器運行中\n")
    
    # 執行測試
    start_time = time.time()
    
    if args.scenario == "all":
        await test_single_endpoint_burst(args.users)
        await asyncio.sleep(2)
        
        await test_mixed_scenario(args.users)
        await asyncio.sleep(2)
        
        await test_cache_effectiveness(3)
        await asyncio.sleep(2)
        
        await test_sustained_load_scenario(20, 30)
        await asyncio.sleep(2)
        
        await test_peak_load(min(args.users * 2, 200))
    
    elif args.scenario == "burst":
        await test_single_endpoint_burst(args.users)
    
    elif args.scenario == "mixed":
        await test_mixed_scenario(args.users)
    
    elif args.scenario == "cache":
        await test_cache_effectiveness(5)
    
    elif args.scenario == "sustained":
        await test_sustained_load_scenario(args.users, args.duration)
    
    elif args.scenario == "peak":
        await test_peak_load(args.users)
    
    total_duration = time.time() - start_time
    
    print("\n" + "="*70)
    print("✅ 所有測試完成!")
    print(f"總耗時: {total_duration:.2f}秒")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
