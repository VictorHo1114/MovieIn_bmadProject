-- ============================================================================
-- Priority 1: Neon 資料庫診斷腳本
-- ============================================================================

-- 1. 檢查 pgvector 擴展是否已安裝
SELECT * FROM pg_extension WHERE extname = 'vector';

-- 2. 檢查 movie_vectors 表結構
SELECT 
    column_name, 
    data_type, 
    udt_name
FROM information_schema.columns 
WHERE table_name = 'movie_vectors'
ORDER BY ordinal_position;

-- 3. 檢查 HNSW 索引是否存在
SELECT 
    indexname, 
    indexdef 
FROM pg_indexes 
WHERE tablename = 'movie_vectors' 
  AND indexdef LIKE '%hnsw%';

-- 4. 檢查 embedding_vector 資料是否已填充
SELECT 
    COUNT(*) as total_movies,
    COUNT(embedding_vector) as has_embedding_vector,
    COUNT(embedding) as has_embedding_jsonb,
    ROUND(COUNT(embedding_vector)::numeric / COUNT(*)::numeric * 100, 2) as fill_rate_pct
FROM movie_vectors;

-- 5. 檢查當前資料庫連線數
SELECT 
    count(*) as current_connections,
    max_conn.setting as max_connections,
    ROUND((count(*)::numeric / max_conn.setting::numeric) * 100, 2) as usage_pct
FROM pg_stat_activity,
     (SELECT setting FROM pg_settings WHERE name = 'max_connections') as max_conn
WHERE datname = current_database()
GROUP BY max_conn.setting;

-- 6. 檢查 movies 表數量
SELECT COUNT(*) as total_movies FROM movies;
