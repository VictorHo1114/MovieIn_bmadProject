#  深度研究：訊息後端效能優化策略

## 研究目標

針對 MovieIn 專案的 WebSocket 訊息系統，進行全面的效能瓶頸分析與優化策略研究，目標是將訊息發送延遲從 80ms 降低至 20ms（提升 75%）。

---

## 背景上下文

### 當前架構現況

**已實作內容：**
-  WebSocket 雙向通訊（FastAPI WebSocket）
-  連線管理器（ConnectionManager）
-  JWT Token 驗證
-  心跳檢測機制（ping/pong）
-  多裝置連線支援（Set[WebSocket]）
-  上線/離線廣播通知

**檔案路徑：**
- Backend: ackend/app/routers/websocket.py
- Frontend: rontend/hooks/useWebSocket.tsx
- Messages API: ackend/app/routers/messages.py

### 已識別的效能瓶頸

####  瓶頸 1：重複 Schema 檢查（每次訊息發送）
`python
# 當前實作（websocket.py Line 204-209）
cols_result = db.execute(text('''
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'messages'
'''))
cols = {row[0] for row in cols_result.fetchall()}
`

**問題分析：**
- 每次發送訊息都查詢 information_schema（~10ms）
- Schema 不會在運行時改變，但每次都檢查
- 這個查詢佔總延遲的 **12.5%**（10ms / 80ms）

**影響範圍：**
- 發送訊息：每次觸發
- 未讀數查詢：每次觸發（messages.py）
- 對話列表載入：每次觸發（messages.py）

####  瓶頸 2：缺少快取層

**當前行為：**
- 未讀數每次都查詢 DB（COUNT(*) on messages table）
- 對話列表每次都 JOIN profiles 表
- 沒有任何 in-memory cache

**預期查詢頻率：**
- 未讀數：平均每 30 秒/用戶（WebSocket 心跳時順便查）
- 對話列表：每次切換對話觸發
- 100 個活躍用戶 = 200 次/分鐘 無意義查詢

####  瓶頸 3：缺少連線池配置

**當前狀況：**
`python
# database.py
engine = create_engine(
    DATABASE_URL,
    #  沒有配置連線池參數
)
`

**問題：**
- 預設連線池大小：5
- 預設最大 overflow：10
- WebSocket 長連線 + 頻繁查詢 = 容易耗盡連線池

####  瓶頸 4：無訊息批次處理

**當前流程：**
`
用戶 A 發送訊息  DB INSERT  發送給 B
用戶 C 發送訊息  DB INSERT  發送給 D
用戶 E 發送訊息  DB INSERT  發送給 F
`

**問題：**
- 每條訊息一次 DB 寫入（無批次）
- 高流量時會產生大量小型事務

---

## 研究問題

### 主要研究問題（Must Answer）

1. **Redis 快取策略設計**
   - 哪些數據應該快取？（未讀數、在線狀態、對話列表）
   - TTL 設定策略？（考慮即時性 vs 資源消耗）
   - Cache invalidation 機制？（何時清除快取）
   - Redis Pub/Sub vs WebSocket 的取捨？

2. **Schema 檢查優化方案比較**
   - 方案 A：啟動時檢查一次 + 全域快取
   - 方案 B：LRU Cache 裝飾器（functools.lru_cache）
   - 方案 C：環境變數配置（手動指定 schema）
   - 哪個方案最適合 MovieIn 的場景？

3. **連線池最佳實踐**
   - 針對 WebSocket 長連線的 pool_size 建議值？
   - max_overflow 應該設定多少？
   - pool_pre_ping 是否必要？（檢測死連線）
   - pool_recycle 時間設定？（避免 MySQL 8h timeout）

4. **訊息批次處理可行性**
   - 批次窗口多長合適？（延遲 vs 吞吐量權衡）
   - 批次大小上限？（避免單次事務過大）
   - 實作複雜度 vs 效能提升是否值得？
   - 對用戶體驗的影響？（會增加延遲嗎？）

### 次要研究問題（Nice to Have）

5. **訊息佇列引入必要性**
   - RabbitMQ vs Redis Pub/Sub vs 不使用？
   - 當前用戶規模（<1000）是否需要？
   - 未來擴展性考量（10k+ 用戶時）

6. **資料庫索引優化**
   - messages 表的查詢熱點？
   - 是否需要複合索引？（sender_id + created_at）
   - EXPLAIN ANALYZE 的實際執行計劃分析

7. **WebSocket 連線管理優化**
   - ConnectionManager 的記憶體佔用？
   - 是否需要連線數限制？（Rate Limiting）
   - 斷線重連的指數退避策略？

8. **監控與可觀測性**
   - 關鍵效能指標（KPIs）定義？
   - Prometheus + Grafana 整合方案？
   - 告警閾值設定建議？

---

## 研究方法

### 資訊來源

**技術文檔：**
- FastAPI WebSocket 官方文檔
- SQLAlchemy Connection Pooling Guide
- Redis Caching Patterns (Redis.io)
- PostgreSQL Performance Tuning

**開源專案參考：**
- Discord.py（WebSocket 訊息系統）
- Slack API（訊息批次處理）
- Rocket.Chat（開源聊天系統架構）

**效能測試工具：**
- wrk - HTTP benchmarking
- ws - WebSocket load testing
- pg_stat_statements - PostgreSQL 查詢分析

### 分析框架

**成本效益矩陣：**
`
            低實作成本  高實作成本

高效能提升    P0        P1

低效能提升    P2          不做
`

**優化決策樹：**
`
1. 效能提升幅度 > 30%？
    是  2. 實作時間 < 2 天？
             是  立即執行（P0）
             否  3. 未來擴展必要？
                      是  排程執行（P1）
                      否  暫緩（P2）
    否  暫不考慮
`

---

## 預期交付成果

### 執行摘要

- 關鍵發現與洞察（3-5 點）
- 效能提升潛力估算（具體數字）
- 建議行動方案（按優先級排序）

### 詳細分析

#### 1. Redis 快取架構設計
`python
# 範例：快取策略 Pseudocode
class MessageCacheStrategy:
    # 未讀數快取
    key_pattern: "user:{user_id}:unread_count"
    ttl: 60 seconds
    invalidation: on_new_message, on_mark_read
    
    # 在線狀態快取
    key_pattern: "user:{user_id}:online"
    ttl: 30 seconds
    invalidation: on_disconnect
    
    # 對話列表快取
    key_pattern: "user:{user_id}:conversations"
    ttl: 120 seconds
    invalidation: on_new_message
`

#### 2. 優化方案比較表
| 方案 | 效能提升 | 實作成本 | 維護成本 | 推薦度 |
|------|---------|---------|---------|--------|
| 移除重複 Schema 檢查 | 12%  | 30min | 低 |  |
| Redis 快取（未讀數） | 35%  | 2h | 中 |  |
| 連線池配置優化 | 8%  | 10min | 低 |  |
| 訊息批次處理 | 15%  | 1天 | 中 |  |

#### 3. 實作程式碼範例

**Redis 快取整合：**
`python
import redis
from functools import wraps

redis_client = redis.Redis(
    host='localhost',
    port=6379,
    decode_responses=True
)

def cache_unread_count(user_id: str, ttl: int = 60):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"user:{user_id}:unread"
            cached = redis_client.get(cache_key)
            
            if cached is not None:
                return int(cached)
            
            result = await func(*args, **kwargs)
            redis_client.setex(cache_key, ttl, result)
            return result
        return wrapper
    return decorator
`

**連線池優化：**
`python
from sqlalchemy import create_engine

engine = create_engine(
    DATABASE_URL,
    pool_size=20,           # 增加連線池大小
    max_overflow=40,        # 允許臨時超載
    pool_pre_ping=True,     # 檢測死連線
    pool_recycle=3600,      # 1小時回收連線
    echo_pool=True          # 日誌記錄（開發用）
)
`

#### 4. 風險與挑戰

**技術風險：**
- Redis 單點故障（SPOF） 建議：Redis Sentinel
- 快取一致性問題  建議：寫穿策略（Write-through）
- 連線池耗盡  建議：監控 + 自動擴展

**營運風險：**
- Redis 記憶體成本  估算：100 活躍用戶 ~5MB
- 額外維護負擔  建議：Docker Compose 簡化部署

#### 5. 部署與監控指南

**部署步驟：**
`ash
# 1. 啟動 Redis
docker run -d -p 6379:6379 redis:alpine

# 2. 安裝 Python 依賴
pip install redis

# 3. 套用程式碼變更
# ... (詳細步驟)

# 4. 驗證效能提升
wrk -t4 -c100 -d30s http://localhost:8000/api/v1/messages/unread_count
`

**監控指標：**
`python
# Prometheus metrics
message_send_latency = Histogram(
    'message_send_latency_seconds',
    'Time to send a message'
)
redis_cache_hit_rate = Counter(
    'redis_cache_hits_total',
    'Redis cache hit count'
)
`

---

## 成功標準

### 量化指標

-  訊息發送延遲 < 25ms（P95）
-  Redis 快取命中率 > 80%
-  資料庫連線池使用率 < 70%
-  未讀數查詢延遲 < 5ms

### 質化指標

-  程式碼可讀性維持（無過度複雜化）
-  向後相容性（不破壞現有 API）
-  部署流程簡化（Docker Compose 一鍵啟動）

---

## 時間規劃

### Phase 1（立即執行 - 1天）
- [ ] 移除重複 Schema 檢查
- [ ] 連線池配置優化
- [ ] 基礎效能監控

### Phase 2（短期 - 1週）
- [ ] Redis 快取整合
- [ ] 未讀數快取
- [ ] 對話列表快取

### Phase 3（中期 - 2週）
- [ ] 訊息批次處理（可選）
- [ ] 完整監控儀表板
- [ ] 負載測試驗證

---

**研究負責人：** Winston (Architect)  
**預期完成時間：** 3-5 工作天  
**更新頻率：** 每日進度更新

---

**下一步行動：**
1. 開始 Phase 1 實作（移除 Schema 檢查）
2. 建立 Redis 整合 POC（Proof of Concept）
3. 進行基準測試（Baseline Benchmarking）

---

*此研究文檔將持續更新，直到所有優化方案完成驗證。*
