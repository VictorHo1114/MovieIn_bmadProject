#  深度研究：推薦系統效能加速策略

## 研究目標

針對 MovieIn Phase 3.6 Embedding-First 推薦系統，進行全面的效能瓶頸分析與加速方案研究，目標是將首次查詢延遲從 500ms 降低至 150ms（提升 70%），重複查詢降至 10ms（提升 98%）。

---

## 背景上下文

### 當前架構現況（Phase 3.6）

**推薦流程（7 步驟）：**
`
1. Embedding Query Generation       ~20ms
2. Embedding Similarity Search      ~200ms  (瓶頸)
3. Tiered Feature Filtering         ~80ms
4. 3-Quadrant Classification        ~5ms
5. Dynamic Score Calculation        ~10ms
6. Mixed Sorting                    ~5ms
7. Smart Selection                  ~5ms
─
總計：~325ms（實測約 500ms 含網路延遲）
`

**核心檔案：**
- ackend/app/services/simple_recommend.py - 主推薦邏輯
- ackend/app/services/embedding_service.py - Embedding 搜索
- ackend/app/services/phase36_config.py - 配置參數
- ackend/app/routers/simple_recommend_router.py - API 端點

**資料庫現況：**
- movies 表：675 部電影
- movie_vectors 表：675 條 Embedding 記錄（1536 維）
- 無向量索引（全表掃描）

### 已識別的效能瓶頸

####  瓶頸 1：即時 Embedding 計算（Step 2）

**當前實作：**
`python
# embedding_service.py Line 367
query_embedding = get_embedding(query_text)  # 呼叫 OpenAI API
# 
client.embeddings.create(
    model="text-embedding-3-small",
    input=query_text
)
`

**問題分析：**
- 每次查詢都呼叫 OpenAI API（~100-150ms 網路延遲）
- 重複查詢無快取（相同查詢重複計費）
- API 成本累積（.00002/1K tokens）

**影響範圍：**
- 佔總延遲的 **40%**（200ms / 500ms）
- 100% 查詢都受影響

####  瓶頸 2：全表掃描 Cosine Similarity（Step 2）

**當前實作：**
`python
# embedding_service.py Line 408-432
for row in rows:  # 675 部電影
    movie_embedding = json.loads(row[1])
    similarity = cosine_similarity(query_embedding, movie_embedding)
    candidates.append(...)
`

**問題分析：**
- 沒有向量索引（FAISS/pgvector）
- Python 迴圈計算 675 次相似度（~80ms）
- 每次都全庫掃描

**複雜度：** O(n  d)，n=675, d=1536

####  瓶頸 3：缺少查詢快取

**當前行為：**
- 相同查詢重複執行所有步驟
- 無 LRU Cache
- 無 Redis 快取層

**預期場景：**
`
用戶 A：「難過的時候適合看什麼」  500ms
用戶 B：「難過的時候適合看什麼」  500ms（完全重複計算）
用戶 C：「sad movies」            500ms（語義相同但未快取）
`

####  瓶頸 4：Feature Filtering 的 OR 邏輯

**當前問題（architecture.md 已識別）：**
`python
# tiered_feature_filtering()
WHERE 
    mood_tags ?| ANY([25+ tags]) OR  # OR 邏輯
    keywords ?| ANY([30+ keywords])  # OR 邏輯
`

**影響：**
- 選越多 mood labels  匹配範圍越廣  精準度下降
- 無 AND 邏輯的漸進式過濾

####  瓶頸 5：缺少智能路由

**當前決策：**
`python
# simple_recommend.py
# 永遠執行 Embedding-First 流程（Phase 3.6）
`

**問題：**
- 簡單查詢（如「動作片」）不需要 Embedding
- Feature Matching 更快且足夠（Phase 3.5 舊邏輯）
- 浪費 OpenAI API 呼叫

---

## 研究問題

### 主要研究問題（Must Answer）

1. **查詢快取架構設計**
   - 快取鍵（Cache Key）設計？
     - Option A：完整查詢文本 hash
     - Option B：標準化查詢（normalized query）
     - Option C：Embedding 向量 hash（語義快取）
   - TTL 策略？（考慮推薦多樣性）
   - Cache invalidation 時機？（新電影加入時）
   - Redis vs LRU Cache vs 兩者並用？

2. **向量索引方案比較**
   
   **方案 A：FAISS（Facebook AI Similarity Search）**
   - 優點：極快（<10ms），離線建構
   - 缺點：需要額外服務，記憶體佔用
   - 適用場景：>10,000 部電影
   
   **方案 B：pgvector（PostgreSQL Extension）**
   - 優點：與現有 DB 整合，維護簡單
   - 缺點：效能略低於 FAISS（~30ms）
   - 適用場景：1,000-100,000 部電影
   
   **方案 C：預計算 + 批次快取**
   - 優點：實作簡單，成本極低
   - 缺點：不適合大規模（>100k）
   - 適用場景：當前規模（675 部）
   
   **問題：MovieIn 當前應選擇哪個方案？**

3. **智能路由決策邏輯**
   
   **何時使用 Feature Matching？**
   - 查詢包含明確類型？（「動作片」）
   - 查詢僅包含年代？（「90年代電影」）
   - 查詢包含 3+ Feature Buttons？
   
   **何時使用 Embedding？**
   - 抽象查詢？（「適合下雨天看的電影」）
   - 僅自然語言？（無 Feature Buttons）
   - 查詢包含情緒描述？（「難過」）
   
   **決策樹設計：**
   `
   if has_explicit_features >= 3:
       return feature_matching()  # Fast path
   elif is_abstract_query:
       return embedding_first()   # Semantic path
   else:
       return hybrid()            # 兩者融合
   `

4. **預計算 Embedding 可行性**
   
   **常見查詢預計算：**
   `python
   COMMON_QUERIES = [
       "難過的時候適合看什麼",
       "適合下雨天看的電影",
       "開心的電影",
       "適合全家一起看",
       # ... 20-30 個常見查詢
   ]
   `
   
   **問題：**
   - 預計算哪些查詢？（如何選擇）
   - 預計算結果 TTL？（多久更新一次）
   - 命中率預估？（能覆蓋多少查詢）

### 次要研究問題（Nice to Have）

5. **Feature Matching 三層過濾實作**
   - Tier 1（AND 邏輯）：必須符合 80%+ features
   - Tier 2（多數符合）：符合 50%+ features
   - Tier 3（OR 邏輯）：符合任一 feature
   - 實作複雜度 vs 精準度提升？

6. **Embedding 模型優化**
   - text-embedding-3-small (1536維) vs text-embedding-3-large (3072維)
   - 成本差異？（.00002 vs .00013）
   - 精準度提升幅度？
   - 是否值得升級？

7. **批次處理優化**
   - 批次查詢多個 Embedding？
   - 批次計算 Cosine Similarity（NumPy 向量化）？
   - 預期效能提升？

8. **資料庫查詢優化**
   `sql
   -- 當前查詢（embedding_service.py）
   SELECT mv.tmdb_id, mv.embedding, mv.embedding_text, 
          m.title, m.overview, ... (14 columns)
   FROM movie_vectors mv
   JOIN movies m ON mv.tmdb_id = m.tmdb_id
   `
   
   **優化點：**
   - 是否需要 SELECT 所有 14 欄位？
   - JOIN 是否必要？（可否分兩次查詢）
   - 是否需要物化視圖（Materialized View）？

---

## 研究方法

### 資訊來源

**學術論文：**
- "Efficient and Robust Approximate Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs" (FAISS 基礎)
- "pgvector: PostgreSQL Extension for Vector Similarity Search"

**開源專案參考：**
- Chroma DB（向量資料庫）
- Weaviate（向量搜索引擎）
- Pinecone（向量資料庫 SaaS）

**效能測試工具：**
- pytest-benchmark - Python 基準測試
- locust - 負載測試
- pg_stat_statements - PostgreSQL 查詢分析

### 分析框架

**效能優化四象限：**
`
                即時生效  需部署服務

快取層優化       P0      P1

演算法優化       P1        P2

基礎設施優化     P2        P3
`

**成本效益分析：**
`python
ROI = (效能提升%  查詢頻率) / (實作時間 + 維護成本)

# 範例：
查詢快取: ROI = (98%  100%) / (2h + 低) = 極高 
FAISS:   ROI = (80%  100%) / (2天 + 中) = 中 
`

---

## 預期交付成果

### 執行摘要

- 關鍵瓶頸排序（按影響程度）
- 效能提升路線圖（3 階段）
- 成本估算（開發時間 + 基礎設施）

### 詳細分析

#### 1. 快取架構設計

**方案 A：雙層快取（推薦）**
`python
class RecommendationCache:
    # Layer 1: LRU Cache（應用層，10 queries）
    @lru_cache(maxsize=10)
    def get_recommendations_memory(query_hash: str):
        pass
    
    # Layer 2: Redis Cache（分散式，1000 queries）
    def get_recommendations_redis(query_hash: str):
        key = f"recommend:{query_hash}"
        cached = redis.get(key)
        if cached:
            return json.loads(cached)
        
        # 計算新結果
        result = compute_recommendations(...)
        redis.setex(key, ttl=3600, value=json.dumps(result))
        return result
`

**語義快取（Advanced）：**
`python
# 問題：「難過的電影」vs「sad movies」語義相同但文字不同
# 解決：快取 Embedding 向量的 hash

def semantic_cache_key(query_text: str) -> str:
    query_emb = get_embedding(query_text)
    # 量化 Embedding（降低精度，提升命中率）
    quantized = [round(x, 2) for x in query_emb]
    return hashlib.md5(str(quantized).encode()).hexdigest()

# 相似查詢會產生相同 hash  快取命中
`

#### 2. 向量索引實作指南

**pgvector 整合步驟：**
`ash
# 1. 安裝 pgvector extension
CREATE EXTENSION vector;

# 2. 修改 movie_vectors 表
ALTER TABLE movie_vectors 
ADD COLUMN embedding_vector vector(1536);

# 3. 從 JSONB 遷移到 vector 類型
UPDATE movie_vectors 
SET embedding_vector = embedding::text::vector;

# 4. 建立 HNSW 索引（加速查詢）
CREATE INDEX ON movie_vectors 
USING hnsw (embedding_vector vector_cosine_ops);
`

**查詢語法：**
`python
# 原本：Python 迴圈計算（慢）
for row in rows:
    similarity = cosine_similarity(query_emb, movie_emb)

# pgvector：SQL 向量查詢（快 10x）
query = text("""
    SELECT tmdb_id, 
           1 - (embedding_vector <=> :query_vector) AS similarity
    FROM movie_vectors
    ORDER BY embedding_vector <=> :query_vector
    LIMIT 300
""")
result = db.execute(query, {"query_vector": query_embedding})
`

**預期效能：**
- 全表掃描：80ms
- pgvector HNSW：~15ms（5x 提升）

#### 3. 智能路由實作

`python
def should_use_embedding_search(
    natural_query: str,
    mood_labels: List[str],
    keywords: List[str],
    genres: List[str]
) -> bool:
    """
    決策邏輯：何時使用 Embedding vs Feature Matching
    """
    # 評分系統（總分 100）
    score = 100
    
    # Feature Buttons 越多，越適合 Feature Matching
    feature_count = len(mood_labels) + len(keywords) + len(genres)
    if feature_count >= 5:
        score -= 40  # 明確特徵
    elif feature_count >= 3:
        score -= 25
    
    # 抽象查詢更適合 Embedding
    abstract_keywords = ['適合', '推薦', '什麼', '心情', '氛圍']
    if any(kw in natural_query for kw in abstract_keywords):
        score += 30
    
    # 閾值：40 分以下用 Feature，以上用 Embedding
    return score >= 40

# 使用範例
if should_use_embedding_search(query, moods, keywords, genres):
    return embedding_first_recommend(...)
else:
    return feature_matching_recommend(...)  # Fast path
`

#### 4. 效能優化對比表

| 優化方案 | 效能提升 | 實作成本 | 基礎設施成本 | 推薦優先級 |
|---------|---------|---------|-------------|-----------|
| LRU Cache（記憶體） | 95%  | 30min |  |  P0 |
| Redis Cache | 98%  | 2h | /月 |  P0 |
| 移除 SQL RANDOM() | 5%  | 15min |  |  P0 |
| pgvector 索引 | 60%  | 1天 |  |  P1 |
| 智能路由 | 30%  | 3h |  |  P1 |
| 三層過濾（AND 邏輯） | 20%  | 1天 |  |  P1 |
| FAISS 向量索引 | 80%  | 3天 | /月 |  P2 |
| Embedding 模型升級 | 10%  | 1h | +550% 成本 |  P3 |

#### 5. 實作程式碼範例

**P0：LRU Cache + Redis Cache**
`python
from functools import lru_cache
import hashlib
import redis
import json

redis_client = redis.Redis(decode_responses=True)

def cache_key(natural_query, mood_labels, genres, year_ranges):
    """生成快取鍵"""
    components = {
        "query": natural_query or "",
        "moods": sorted(mood_labels or []),
        "genres": sorted(genres or []),
        "years": year_ranges or []
    }
    key_string = json.dumps(components, sort_keys=True)
    return hashlib.md5(key_string.encode()).hexdigest()

@lru_cache(maxsize=20)
def get_from_memory_cache(cache_key: str):
    """記憶體快取（最快，容量小）"""
    return None  # 由 lru_cache 自動處理

async def recommend_movies_cached(
    natural_query: str,
    mood_labels: List[str],
    genres: List[str],
    year_ranges: List[List[int]],
    db_session: Session
):
    # 生成快取鍵
    key = cache_key(natural_query, mood_labels, genres, year_ranges)
    
    # Layer 1: 記憶體快取
    cached = get_from_memory_cache(key)
    if cached:
        print("[Cache Hit] Memory cache")
        return cached
    
    # Layer 2: Redis 快取
    redis_key = f"recommend:{key}"
    cached_redis = redis_client.get(redis_key)
    if cached_redis:
        print("[Cache Hit] Redis cache")
        result = json.loads(cached_redis)
        get_from_memory_cache.cache_info()  # 更新記憶體快取
        return result
    
    # Cache Miss: 計算新結果
    print("[Cache Miss] Computing...")
    result = await recommend_movies_embedding_first(
        natural_query, mood_labels, genres, year_ranges, db_session
    )
    
    # 寫入兩層快取
    redis_client.setex(redis_key, 3600, json.dumps(result))  # 1小時
    get_from_memory_cache(key)  # 觸發記憶體快取
    
    return result
`

**P0：移除 SQL RANDOM()**
`python
# 前：在 SQL 中使用 RANDOM()（慢）
ORDER BY 
    feature_score + RANDOM() * 10 DESC

# 後：在應用層隨機化（快）
sorted_movies = sorted(candidates, key=lambda x: x['feature_score'], reverse=True)
random.shuffle(sorted_movies[:30])  # 只打亂前 30 名
return sorted_movies[:10]
`

**P1：pgvector 查詢**
`python
async def embedding_similarity_search_pgvector(
    query_text: str,
    db_session: Session,
    top_k: int = 300
) -> List[Dict]:
    """使用 pgvector 加速的 Embedding 搜索"""
    
    # Step 1: 計算查詢 Embedding
    query_embedding = get_embedding(query_text)
    
    # Step 2: pgvector 向量查詢（單次 SQL）
    query = text("""
        SELECT 
            mv.tmdb_id,
            1 - (mv.embedding_vector <=> :query_vector::vector) AS similarity,
            m.title,
            m.overview,
            m.genres,
            m.keywords,
            m.mood_tags
        FROM movie_vectors mv
        JOIN movies m ON mv.tmdb_id = m.tmdb_id
        ORDER BY mv.embedding_vector <=> :query_vector::vector
        LIMIT :top_k
    """)
    
    result = db_session.execute(query, {
        "query_vector": query_embedding,
        "top_k": top_k
    })
    
    return [dict(row._mapping) for row in result]
`

#### 6. 成本估算

**開發時間：**
- P0（快取 + SQL 優化）：0.5 天
- P1（pgvector + 智能路由）：1.5 天
- P2（FAISS）：3 天

**基礎設施成本（月）：**
- Redis (1GB)：-10
- pgvector：（PostgreSQL extension）
- FAISS：（額外服務器）

**OpenAI API 成本變化：**
`
當前（無快取）：
100 查詢/天  .00002/查詢  30天 = .06/月

P0 後（98% 快取命中率）：
100  2%  .00002  30 = .0012/月  省 98%
`

#### 7. 風險與挑戰

**技術風險：**
| 風險 | 機率 | 影響 | 緩解措施 |
|------|-----|------|---------|
| pgvector 安裝失敗（Neon 不支援） | 中 | 高 | 確認 Neon 支援清單 |
| 快取一致性問題 | 低 | 中 | 寫穿策略 + TTL |
| Redis 單點故障 | 低 | 低 | 優雅降級（Fallback 到計算） |

**營運風險：**
- 快取 Invalidation 策略不當  推薦結果過時
- 記憶體洩漏（LRU Cache 無限增長）  設定 maxsize

#### 8. 監控與驗證

**效能指標：**
`python
import time
from prometheus_client import Histogram

recommend_latency = Histogram(
    'recommend_latency_seconds',
    'Recommendation API latency',
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0]
)

@recommend_latency.time()
async def recommend_movies(...):
    start = time.time()
    result = await recommend_movies_cached(...)
    duration = time.time() - start
    print(f"[Perf] Total: {duration*1000:.2f}ms")
    return result
`

**A/B 測試框架：**
`python
def recommend_with_ab_test(user_id: str, query: str):
    if user_id % 2 == 0:
        # Control Group: 原始實作
        return recommend_movies_embedding_first(...)
    else:
        # Treatment Group: 優化後
        return recommend_movies_cached(...)
`

---

## 成功標準

### 量化指標

-  首次查詢延遲 < 200ms（P95）
-  快取命中率 > 80%
-  重複查詢延遲 < 20ms（P95）
-  OpenAI API 成本降低 > 90%

### 質化指標

-  推薦精準度不下降（NDCG@10 維持）
-  程式碼可維護性（無過度複雜化）
-  向後相容性（API 介面不變）

---

## 實作優先級（最終建議）

###  P0 - 立即執行（0.5 天）
1.  LRU Cache（記憶體快取）
2.  Redis Cache（分散式快取）
3.  移除 SQL RANDOM()（改應用層）

**預期效果：**
- 首次查詢：500ms  300ms（40% ）
- 重複查詢：500ms  5ms（99% ）

###  P1 - 短期執行（1.5 天）
4.  pgvector 向量索引
5.  智能路由（Feature vs Embedding）
6.  三層過濾（AND 邏輯）

**預期效果：**
- 首次查詢：300ms  120ms（76% ）
- 精準度提升：10-15%

###  P2 - 中期考慮（3 天）
7.  FAISS 向量索引（當電影數 > 10k）
8.  Embedding 模型升級（精準度需求）

**預期效果：**
- 支援 10k+ 電影規模
- 精準度提升：5-10%

---

## 時間規劃

### Week 1（P0 優化）
- Day 1-2：快取架構實作
- Day 3：測試與驗證
- Day 4：部署與監控

### Week 2（P1 優化）
- Day 1-2：pgvector 整合
- Day 3：智能路由實作
- Day 4-5：三層過濾重構

### Week 3（驗證與調優）
- 負載測試
- A/B 測試
- 效能調優

---

**研究負責人：** Winston (Architect)  
**預期完成時間：** 2-3 週  
**更新頻率：** 每週進度報告

---

**立即行動項：**
1. [x] 實作雙層快取（LRU + Redis）✅ **已完成**
2. [ ] 移除 SQL RANDOM()
3. [ ] 建立效能基準測試
4. [ ] 確認 Neon 是否支援 pgvector

---

## P0 實作進度報告

### ✅ 已完成項目（2025-12-02）

#### 1. 雙層快取系統
**檔案：** `backend/app/services/recommendation_cache.py`

**功能實作：**
- ✅ Layer 1: LRU 記憶體快取（50 個查詢，~5ms）
- ✅ Layer 2: Redis 分散式快取（可選，~2ms）
- ✅ Embedding 快取（節省 OpenAI API 呼叫）
- ✅ 推薦結果快取（完整結果快取）
- ✅ TTL 策略（Embedding 7天，推薦 1小時）
- ✅ 優雅降級（Redis 不可用時自動使用 LRU）

**整合點：**
- ✅ `embedding_service.py` - `get_embedding()` 自動快取
- ✅ `simple_recommend.py` - `recommend_movies_embedding_first()` 結果快取
- ✅ `simple_recommend_router.py` - 新增快取管理 API

**新增 API：**
- `GET /api/recommend/v2/cache/stats` - 快取統計
- `DELETE /api/recommend/v2/cache/invalidate` - 清除快取

**預期效能提升：**
- 首次查詢：500ms → ~300ms（快取 Embedding）
- 重複查詢：500ms → ~5ms（快取完整結果）
- API 成本：降低 98%

#### 測試方式：
```bash
# 1. 啟動後端（Redis 可選）
cd backend
uvicorn app.main:app --reload --port 8000

# 2. 測試首次查詢（會較慢，約 300ms）
curl -X POST "http://localhost:8000/api/recommend/v2/movies" \
  -H "Content-Type: application/json" \
  -d '{"query": "難過的時候適合看什麼", "selected_moods": ["heartwarming"]}'

# 3. 測試重複查詢（應 <10ms，快取命中）
# （重複上述請求）

# 4. 查看快取統計
curl "http://localhost:8000/api/recommend/v2/cache/stats"

# 5. 清除快取
curl -X DELETE "http://localhost:8000/api/recommend/v2/cache/invalidate"
```

---

*此研究文檔將隨著實作進度持續更新。*
