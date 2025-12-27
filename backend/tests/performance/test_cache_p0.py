"""
P0 優化測試腳本：驗證雙層快取功能

測試項目：
1. Embedding 快取（記憶體 + Redis）
2. 推薦結果快取
3. 快取命中率
4. 效能對比（快取 vs 無快取）
"""
import asyncio
import time
import sys
import os

# 添加專案路徑
sys.path.insert(0, os.path.dirname(__file__))

from app.services.recommendation_cache import (
    get_cached_embedding,
    set_cached_embedding,
    generate_recommendation_cache_key,
    get_cached_recommendation,
    set_cached_recommendation,
    get_cache_stats,
    invalidate_recommendation_cache
)


def test_embedding_cache():
    """測試 Embedding 快取"""
    print("\n" + "="*70)
    print("測試 1: Embedding 快取")
    print("="*70)
    
    test_text = "A heartwarming story about family and love"
    test_embedding = [0.1] * 1536  # 模擬 embedding
    
    # 清除快取
    print("\n1. 清除舊快取...")
    invalidate_recommendation_cache()
    
    # 第一次查詢（應該未命中）
    print(f"\n2. 第一次查詢: '{test_text}'")
    cached = get_cached_embedding(test_text)
    print(f"   結果: {cached}")
    assert cached is None, "❌ 應該快取未命中"
    print("   ✅ 快取未命中（符合預期）")
    
    # 儲存到快取
    print(f"\n3. 儲存 Embedding 到快取...")
    set_cached_embedding(test_text, test_embedding)
    print("   ✅ 儲存成功")
    
    # 第二次查詢（應該命中）
    print(f"\n4. 第二次查詢（應該命中）...")
    cached = get_cached_embedding(test_text)
    print(f"   結果: {cached[:5]}... (showing first 5 dims)")
    assert cached is not None, "❌ 應該快取命中"
    assert len(cached) == 1536, "❌ Embedding 維度錯誤"
    print("   ✅ 快取命中！")
    
    print("\n✅ Embedding 快取測試通過")


def test_recommendation_cache():
    """測試推薦結果快取"""
    print("\n" + "="*70)
    print("測試 2: 推薦結果快取")
    print("="*70)
    
    # 模擬推薦結果
    test_query = "難過的時候適合看什麼"
    test_moods = ["heartwarming", "uplifting"]
    test_genres = ["劇情"]
    test_result = [
        {"id": "550", "title": "風雲人物", "embedding_score": 0.85},
        {"id": "551", "title": "完美的日子", "embedding_score": 0.82}
    ]
    
    # 清除快取
    print("\n1. 清除舊快取...")
    invalidate_recommendation_cache()
    
    # 第一次查詢（未命中）
    print(f"\n2. 第一次查詢: '{test_query}'")
    cached = get_cached_recommendation(
        natural_query=test_query,
        mood_labels=test_moods,
        genres=test_genres
    )
    print(f"   結果: {cached}")
    assert cached is None, "❌ 應該快取未命中"
    print("   ✅ 快取未命中（符合預期）")
    
    # 儲存到快取
    print(f"\n3. 儲存推薦結果到快取...")
    set_cached_recommendation(
        result=test_result,
        natural_query=test_query,
        mood_labels=test_moods,
        genres=test_genres
    )
    print("   ✅ 儲存成功")
    
    # 第二次查詢（命中）
    print(f"\n4. 第二次查詢（應該命中）...")
    cached = get_cached_recommendation(
        natural_query=test_query,
        mood_labels=test_moods,
        genres=test_genres
    )
    print(f"   結果: {cached}")
    assert cached is not None, "❌ 應該快取命中"
    assert len(cached) == 2, "❌ 結果數量錯誤"
    assert cached[0]["title"] == "風雲人物", "❌ 結果內容錯誤"
    print("   ✅ 快取命中！")
    
    # 測試查詢參數順序不影響快取
    print(f"\n5. 測試參數順序（mood 順序不同）...")
    cached = get_cached_recommendation(
        natural_query=test_query,
        mood_labels=["uplifting", "heartwarming"],  # 順序不同
        genres=test_genres
    )
    assert cached is not None, "❌ 參數順序不應影響快取"
    print("   ✅ 參數順序不影響快取（已自動排序）")
    
    print("\n✅ 推薦結果快取測試通過")


def test_cache_key_generation():
    """測試快取鍵生成"""
    print("\n" + "="*70)
    print("測試 3: 快取鍵生成")
    print("="*70)
    
    # 測試相同輸入產生相同鍵
    key1 = generate_recommendation_cache_key(
        natural_query="test",
        mood_labels=["a", "b"],
        genres=["drama"]
    )
    
    key2 = generate_recommendation_cache_key(
        natural_query="test",
        mood_labels=["b", "a"],  # 順序不同
        genres=["drama"]
    )
    
    print(f"\n1. Key 1: {key1}")
    print(f"   Key 2: {key2}")
    assert key1 == key2, "❌ 相同輸入應產生相同鍵"
    print("   ✅ 相同輸入產生相同鍵")
    
    # 測試不同輸入產生不同鍵
    key3 = generate_recommendation_cache_key(
        natural_query="different query",
        mood_labels=["a", "b"],
        genres=["drama"]
    )
    
    print(f"\n2. Key 3: {key3}")
    assert key1 != key3, "❌ 不同輸入應產生不同鍵"
    print("   ✅ 不同輸入產生不同鍵")
    
    print("\n✅ 快取鍵生成測試通過")


def test_cache_stats():
    """測試快取統計"""
    print("\n" + "="*70)
    print("測試 4: 快取統計")
    print("="*70)
    
    stats = get_cache_stats()
    print(f"\n快取統計：")
    import json
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    
    assert "memory_cache_size" in stats, "❌ 缺少記憶體快取統計"
    assert "redis_available" in stats, "❌ 缺少 Redis 狀態"
    print("\n✅ 快取統計測試通過")


async def test_performance_comparison():
    """測試效能對比（需要實際資料庫連線）"""
    print("\n" + "="*70)
    print("測試 5: 效能對比（可選）")
    print("="*70)
    print("\n⚠️  此測試需要資料庫連線，跳過")
    print("   請使用實際 API 測試：")
    print("   1. POST /api/recommend/v2/movies （首次查詢）")
    print("   2. POST /api/recommend/v2/movies （重複查詢）")
    print("   3. GET /api/recommend/v2/cache/stats （查看統計）")


def main():
    """執行所有測試"""
    print("\n🚀 P0 優化：雙層快取系統測試")
    print("="*70)
    
    try:
        # 基礎功能測試
        test_embedding_cache()
        test_recommendation_cache()
        test_cache_key_generation()
        test_cache_stats()
        
        # 效能測試（需要資料庫）
        asyncio.run(test_performance_comparison())
        
        print("\n" + "="*70)
        print("✅ 所有測試通過！")
        print("="*70)
        print("\n下一步：")
        print("1. 啟動後端： uvicorn app.main:app --reload --port 8000")
        print("2. 測試 API： curl -X POST http://localhost:8000/api/recommend/v2/movies ...")
        print("3. 查看快取統計： curl http://localhost:8000/api/recommend/v2/cache/stats")
        
    except AssertionError as e:
        print(f"\n❌ 測試失敗: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
