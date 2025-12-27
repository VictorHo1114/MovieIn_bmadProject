# backend/scripts/diagnose_performance.py
"""
Priority 1: 效能診斷工具

檢查項目：
1. 資料庫連線池狀態
2. pgvector 索引是否存在
3. Embedding 資料填充率
4. 快取系統狀態
5. 當前資料庫連線數
"""
import os
import sys
from pathlib import Path

# 加入 backend 到路徑
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from db.database import engine, SessionLocal
from dotenv import load_dotenv

load_dotenv()

def check_connection_pool():
    """檢查連線池配置"""
    print("\n" + "="*70)
    print("1  連線池配置檢查")
    print("="*70)
    
    pool = engine.pool
    print(f" Pool Size: {pool.size()}")
    print(f" Pool Timeout: {engine.pool._timeout}s")
    print(f" Pool Pre-Ping: {engine.pool._pre_ping}")
    print(f" Pool Recycle: {engine.pool._recycle}s" if hasattr(engine.pool, '_recycle') else " Pool Recycle: Not set")
    print(f" Current Checked Out: {pool.checkedout()}")
    print(f" Current Overflow: {pool.overflow()}")
    
    # 計算理論最大連線數
    max_connections = pool.size() + (pool._max_overflow if hasattr(pool, '_max_overflow') else 0)
    print(f"\n 理論最大連線數: {max_connections}")

def check_pgvector_status():
    """檢查 pgvector 狀態"""
    print("\n" + "="*70)
    print("2  pgvector 索引檢查")
    print("="*70)
    
    with engine.connect() as conn:
        # 檢查擴展
        result = conn.execute(text("SELECT * FROM pg_extension WHERE extname = 'vector'"))
        extensions = result.fetchall()
        
        if extensions:
            print(" pgvector 擴展已安裝")
        else:
            print(" pgvector 擴展未安裝！")
            return
        
        # 檢查索引
        result = conn.execute(text("""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'movie_vectors' 
              AND indexdef LIKE '%hnsw%'
        """))
        indexes = result.fetchall()
        
        if indexes:
            print(f" HNSW 索引已建立: {indexes[0][0]}")
            print(f"  索引定義: {indexes[0][1][:100]}...")
        else:
            print(" HNSW 索引未建立！")
            print("\n  需要執行以下 SQL 建立索引：")
            print("""
CREATE INDEX movie_vectors_embedding_vector_hnsw_idx
ON movie_vectors
USING hnsw (embedding_vector vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
            """)

def check_embedding_coverage():
    """檢查 Embedding 資料覆蓋率"""
    print("\n" + "="*70)
    print("3  Embedding 資料檢查")
    print("="*70)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                COUNT(*) as total_movies,
                COUNT(embedding_vector) as has_embedding_vector,
                COUNT(embedding) as has_embedding_jsonb,
                ROUND(COUNT(embedding_vector)::numeric / COUNT(*)::numeric * 100, 2) as fill_rate_pct
            FROM movie_vectors
        """))
        stats = result.fetchone()
        
        if stats:
            print(f" 總電影數: {stats[0]}")
            print(f" 已有 embedding_vector: {stats[1]} ({stats[3]}%)")
            print(f" 已有 embedding_jsonb: {stats[2]}")
            
            if stats[3] < 100:
                print(f"\n  資料填充率不足 100%，建議執行：")
                print("python backend/tools/batch_populate_enhanced_embeddings.py")
        else:
            print(" movie_vectors 表不存在或無資料")

def check_cache_system():
    """檢查快取系統狀態"""
    print("\n" + "="*70)
    print("4  快取系統檢查")
    print("="*70)
    
    try:
        from app.services.recommendation_cache import REDIS_AVAILABLE, get_cache_stats
        
        if REDIS_AVAILABLE:
            print(" Redis 快取可用")
            stats = get_cache_stats()
            print(f"  - Embedding 快取: {stats.get('embedding_cache_size', 0)} 項")
            print(f"  - 推薦快取: {stats.get('recommendation_cache_size', 0)} 項")
        else:
            print("  Redis 不可用，僅使用 LRU Cache")
            print("   建議安裝 Redis 以獲得更好的效能")
    except Exception as e:
        print(f" 快取系統檢查失敗: {e}")

def check_current_connections():
    """檢查當前連線數"""
    print("\n" + "="*70)
    print("5  資料庫連線數檢查")
    print("="*70)
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT 
                count(*) as current_connections,
                max_conn.setting as max_connections,
                ROUND((count(*)::numeric / max_conn.setting::numeric) * 100, 2) as usage_pct
            FROM pg_stat_activity,
                 (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_conn
            WHERE datname = current_database()
            GROUP BY max_conn.setting
        """))
        stats = result.fetchone()
        
        if stats:
            print(f" 當前連線數: {stats[0]} / {stats[1]} ({stats[2]}%)")
            
            if stats[2] > 80:
                print(f"\n  連線使用率超過 80%，系統可能即將崩潰！")
            elif stats[2] > 60:
                print(f"\n  連線使用率超過 60%，需要注意")

def main():
    print("\n" + ""*35)
    print("Priority 1: MovieIn 效能診斷")
    print(""*35)
    
    try:
        check_connection_pool()
        check_pgvector_status()
        check_embedding_coverage()
        check_cache_system()
        check_current_connections()
        
        print("\n" + "="*70)
        print(" 診斷完成")
        print("="*70)
        
    except Exception as e:
        print(f"\n 診斷失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
