# MovieIn 專案 - Brownfield 架構文件

## 文件資訊

### 文件範圍
完整記錄 MovieIn 專案的現有架構、技術棧、資料流、整合點與已知技術債務。

### 變更記錄

| 日期 | 版本 | 描述 | 作者 |
|------|------|------|------|
| 2025-11-06 | 1.0 | 初始 brownfield 架構分析 | Winston (Architect) |

---

## 專案概述

**MovieIn** 是一個基於 AI 的電影推薦平台，結合自然語言處理和 TMDB（The Movie Database）API，為使用者提供個性化的電影推薦。

### 核心特色
-  **智能混合推薦系統**：Feature Matching + Embedding 雙引擎自動切換
-  **增強特徵提取**：Mood Label 映射表 + 精確 Keyword 匹配 + 自然語言推斷
-  **本地資料庫**：PostgreSQL 儲存完整電影資料（genres, keywords, mood_tags）
-  **動態隨機性控制**：可調整推薦的多樣性與探索性
-  **現代化 UI**：Next.js 16 + React 19 + Tailwind CSS 4

---

## 快速參考 - 關鍵檔案與進入點

### 關鍵檔案清單

#### 後端核心檔案
- **主進入點**：`backend/app/main.py`
- **推薦引擎**：`backend/app/services/simple_recommend.py` - 🔥 智能混合推薦系統
- **特徵提取**：`backend/app/services/enhanced_feature_extraction.py` - Mood/Keyword 映射
- **映射表定義**：`backend/app/services/mapping_tables.py` - MOOD_LABEL_TO_DB_TAGS (SSOT)
- **語義重排序**：`backend/app/services/embedding_service.py` - Embedding 匹配
- **資料庫連線**：`backend/db/database.py`
- **使用者模型**：`backend/app/models/user.py`
- **棄用**：`backend/app/routers/intent_parse.py` (舊版 LLM 意圖解析)

#### 前端核心檔案
- **主進入點**：`frontend/app/page.tsx`  重定向至 `/home`
- **首頁客戶端**：`frontend/features/home/HomeClient.tsx` - 核心 UI 邏輯
- **API 層**：`frontend/lib/api.ts`, `frontend/lib/http.ts`
- **類型定義**：`frontend/lib/types/index.ts`
- **全域佈局**：`frontend/app/layout.tsx`

#### Schema 與規格檔案
- **意圖 Schema**：`backend/app/schemas/intent.py`
- **電影結果 Schema**：`backend/app/schemas/movie_result.py`
- **標籤定義（SSOT）**：`backend/app/schemas/specs/intent_labels.py`
- **JSON Schema**：`backend/app/schemas/specs/movie_intent.schema.json`

---

## 高階架構

### 技術摘要

MovieIn 採用**現代化全端架構**，前後端分離，透過 RESTful API 通訊。後端使用 FastAPI 提供高效能 API 服務，前端使用 Next.js 16 的 App Router 架構。

### 技術棧明細

| 類別 | 技術 | 版本 | 備註 |
|------|------|------|------|
| **後端框架** | FastAPI | 0.119.1 | 非同步 Python Web 框架 |
| **Python** | Python | 3.x | 建議 3.10+ |
| **資料庫** | PostgreSQL (Neon) | 13+ | 雲端託管，儲存完整電影資料 |
| **ORM** | SQLAlchemy | Latest | 使用 declarative_base |
| **遷移工具** | Alembic | 1.14.0 | 資料庫版本控制 |
| **AI/Embedding** | OpenAI Embedding | text-embedding-3-small | 語義匹配（可選路徑） |
| **外部 API** | ~~TMDB API~~ | ~~v3~~ | ⚠️ 已棄用，使用本地 DB |
| **前端框架** | Next.js | 16.0.0 | App Router 架構 |
| **UI 函式庫** | React | 19.2.0 | 最新版本 |
| **狀態管理** | Zustand | 5.0.8 | 輕量級狀態管理 |
| **HTTP 客戶端** | ky | 1.13.0 | 現代化 fetch wrapper |
| **樣式** | Tailwind CSS | 4.x | Utility-first CSS |
| **TypeScript** | TypeScript | 5.x | 型別安全 |

### 系統架構圖

```

                        使用者介面層                                
  Next.js 16 (React 19) + Tailwind CSS 4 + Zustand              
                                                                  
   首頁 (HomeClient) - 自然語言輸入 + 標籤選擇                    
   搜尋頁面 - 電影搜尋功能                                        
   個人資料頁 - 使用者資訊與觀看清單                               

                  HTTP/JSON (ky client)
                  http://127.0.0.1:8000
                 

                        API 閘道層                                 
              FastAPI (CORS enabled, *允許所有來源)                
                                                                  
  路由掛載點:                                                      
   /home - 首頁動態                                              
   /profile - 使用者資料                                         
   /search - 搜尋功能                                            
   /api/intent/parse - 意圖解析                                
   /api/recommend/movies - 電影推薦                            

                           
                            OpenAI API
                            GPT-4o-mini
                                        (意圖解析 LLM)
     
      TMDB API (v3)
                                        (電影資料、圖片)
     
      PostgreSQL (Neon)
                                         (使用者、觀看清單)

```

### 資料流說明

#### 核心推薦流程（最重要）

```
1. 使用者輸入（前端）
   
   自然語言: "難過的時候適合看什麼"
   + Mood Buttons: ["難過", "治癒"]
   + Genre Buttons: ["劇情"]
   + Era Buttons: ["90s", "00s"]
   
2. POST /api/recommend/movies
   
   [智能混合推薦流程]
   
   階段 1: Enhanced Feature Extraction
    🔍 中文 Mood → 英文 Mood Tags (ZH_TO_EN_MOOD 映射表)
      "難過" → "sad", "melancholy"
      "治癒" → "healing", "heartwarming"
    
    🔍 Mood Label → DB Tags/Keywords (MOOD_LABEL_TO_DB_TAGS 映射表)
      "sad" → mood_tags: ["sad", "melancholy", "emotional"]
            → keywords: ["loss", "grief", "depression"]
      "healing" → mood_tags: ["healing", "uplifting"]
                → keywords: ["hope", "recovery", "redemption"]
    
    🔍 自然語言 Keyword 提取 (extract_exact_keywords_from_db)
      "難過" → 查詢映射表 → "sadness", "sorrow"
      直接從 DB 提取存在的 keywords
    
    🔍 年代轉換 (ERA_RANGE_MAP)
      "90s" → [1990, 1999]
      "00s" → [2000, 2009]
    
    📦 輸出:
      {
        "keywords": ["loss", "grief", "hope", "recovery", ...],
        "mood_tags": ["sad", "melancholy", "healing", "uplifting", ...],
        "genres": ["剧情"],  // 簡體中文（DB 格式）
        "year_ranges": [[1990, 1999], [2000, 2009]]  // 多個範圍 OR 邏輯
      }
   
   階段 2: SQL Feature Matching (⚠️ **完全 OR 邏輯**)
    
    📊 評分公式:
      feature_score = 
        (keyword_matches × 20) +      // 任一 keyword 符合就加分
        (mood_tag_matches × 15) +     // 任一 mood_tag 符合就加分
        (genre_matches × 10) +        // 任一 genre 符合就加分
        (vote_average - 5) × 3 +
        (popularity / 1000) × 2 +
        RANDOM() × (5-50)             // 隨機性權重
    
    🔍 硬性過濾（AND 邏輯）:
      WHERE 
        (release_year BETWEEN 1990 AND 1999 OR   // 年代 OR 邏輯
         release_year BETWEEN 2000 AND 2009)
        AND genres @> ["剧情"]                    // 類型必須包含
    
    ⚠️ **問題**: 
      - 選 10 個 mood labels → 映射出 50+ tags/keywords → 任一符合就得分
      - 選 1 個 mood label → 映射出 5 個 tags/keywords → 任一符合就得分
      - **結果**: 選越多 labels，匹配範圍越廣，越不精準
      - **缺少**: 沒有「先找全部符合，再找部分符合」的漸進邏輯
    
    📤 返回: 150 部候選電影（按 feature_score 排序）
   
   階段 3: 智能決策 (should_use_embedding)
    
    🤖 評分系統（總分 100，閾值 40）:
      - 有明確 keywords (3+): -30 分
      - 有明確 mood_tags (2+): -20 分
      - 有 Feature Buttons (3+): -25 分
      - 無抽象詞: -20 分
      - Feature 分數高: -15 分
      - 候選數量足夠: -15 分
    
    🎯 決策:
      - 分數 < 40 → Feature 路徑（規則式多樣性過濾）
      - 分數 >= 40 → Embedding 路徑（語義匹配重排序）
    
    📊 當前案例:
      keywords: 8 個 (-30), mood_tags: 4 個 (-30),
      buttons: 3 個 (-25), 無抽象詞 (-20)
      → 總分 = 100 - 30 - 30 - 25 - 20 = -5
      → **使用 Feature 路徑**
   
   階段 4: 路徑執行
    
    ⚡ Feature 路徑: diversity_filter()
      - 規則式多樣性過濾
      - 避免同類型/同年代電影重複
      - 隨機性加權（randomness 參數控制）
    
    🔮 Embedding 路徑: rerank_by_semantic_similarity()
      - 使用 OpenAI Embedding API
      - 計算語義相似度
      - MMR 多樣性重排序
   
   階段 5: 返回結果
    
    📤 格式化為 FrontendMovie[]
      {
        "id": 123,
        "title": "完美的日子",
        "overview": "...",
        "poster_url": "https://image.tmdb.org/t/p/w500/...",
        "release_year": 2023,
        "vote_average": 7.8,
        "feature_score": 45.2,
        "similarity_score": 0.85  // 僅 Embedding 路徑
      }

3. 前端顯示結果
   
   HomeClient.tsx 渲染電影卡片
```

---

## 原始碼樹狀結構與模組組織

### 專案結構（實際）

```
MovieIn_bmadProject/
 backend/                     # Python FastAPI 後端
    alembic.ini             # Alembic 設定檔
    requirements.txt        # Python 依賴
    test_db.py              # 資料庫連線測試
   
    api/                    # 外部 API 整合層
       tmdb_client.py      #  TMDB API 客戶端（含 Fallback 邏輯）
       tmdb_mapper.py      # Intent  TMDB 參數映射
   
    app/                    # 應用程式核心
       main.py             #  FastAPI 應用主進入點
      
       models/             # SQLAlchemy 資料模型
          base.py         # declarative_base()
          user.py         # User 模型（UUID, email, password_hash）
      
       routers/            # API 路由層
          home.py         # 首頁動態（Mock 資料）
          profile.py      # 使用者資料（Mock 資料）
          search.py       # 搜尋功能（Mock 資料）
          intent_parse.py #  核心：混合式意圖解析引擎
          recommend_router.py #  推薦端點（串接 TMDB）
      
       schemas/            # Pydantic 資料驗證
           __init__.py     # Barrel export
           intent.py       #  MovieIntent, IntentConstraints
           movie_result.py # FrontendMovie
           movie.py        # MovieCard
           feed.py         # HomeFeed
           profile.py      # Profile
           search.py       # SearchResult
          
           specs/          # 規格定義（SSOT）
               intent_labels.py        #  FEATURE_LABELS, MUST_NOT_LABELS
               movie_intent.schema.json # JSON Schema for LLM
   
    db/                     # 資料庫層
        database.py         #  SQLAlchemy engine, SessionLocal
        env.py              # Alembic 環境設定
        script.py.mako      # Alembic 遷移模板
       
        versions/           # 資料庫遷移檔案
            0e2a35aaaaaf_init_users.py
            342292faab66_init_users_fixed.py
            7d8fb740c1e7_init_users.py

 frontend/                   # Next.js 16 前端
    package.json            # npm 依賴
    next.config.ts          # Next.js 設定
    tsconfig.json           # TypeScript 設定
    postcss.config.mjs      # PostCSS 設定（Tailwind）
    eslint.config.mjs       # ESLint 設定
   
    app/                    # App Router 結構
       layout.tsx          #  根佈局（NavBar, globals.css）
       page.tsx            # 根頁面（重定向至 /home）
       globals.css         # 全域樣式
      
       home/               # 首頁路由
          page.tsx        #  Server Component，載入 HomeClient
      
       profile/            # 個人資料路由
          page.tsx
      
       search/             # 搜尋路由
           page.tsx
   
    components/             # UI 元件
       NavBar.tsx          # 導航列
      
       figmaAi_ui/         # shadcn/ui 元件庫
           button.tsx
           textarea.tsx
           card.tsx
           ... (其他 UI 元件)
   
    features/               # 功能模組（業務邏輯）
       home/               # 首頁功能
          HomeClient.tsx  #  核心：意圖解析 UI
          services.ts     # parseMovieIntent() API 呼叫
          index.ts
          css/
              homeclient.css # 自訂按鈕樣式
      
       profile/            # 個人資料功能
          services.ts
      
       search/             # 搜尋功能
           services.ts
   
    lib/                    # 共用函式庫
       api.ts              #  API 客戶端（統一介面）
       http.ts             # HTTP 工具函式（getJSON）
       config.ts           # API_BASE, USE_MOCKS
      
       types/              # TypeScript 型別定義
           index.ts        # Barrel export
           movie.ts        # MovieCard
           profile.ts      # Profile
           search.ts       # SearchResult
   
    public/                 # 靜態資源
        favicon.ico

 bmad-core/                  # BMAD 方法框架（開發輔助）
     core-config.yaml        # 專案設定
```

### 關鍵模組說明

#### 後端核心模組

**1. `simple_recommend.py` - 智能混合推薦引擎** ⭐
- **職責**：核心推薦邏輯，智能選擇 Feature 或 Embedding 路徑
- **架構**：
  - `recommend_movies_hybrid()` - 主推薦函數
  - `should_use_embedding()` - 智能決策引擎（100 分評分系統）
  - `sql_feature_matching()` - SQL 多維特徵匹配
  - `diversity_filter()` - 規則式多樣性過濾
- **評分公式**：`keywords×20 + mood_tags×15 + genres×10 + rating×3 + popularity×2 + RANDOM()×(5-50)`
- **特色**：
  - 動態決策閾值（預設 40）
  - 可調整隨機性（0.0-1.0）
  - 詳細日誌輸出
- **⚠️ 已知問題**：
  - **完全 OR 邏輯**：所有 features 都是任一符合就加分
  - **缺少 AND 邏輯**：沒有「必須全部符合」的選項
  - **選越多越不準**：大量 mood labels → 映射出大量 tags → 匹配範圍過廣

**2. `enhanced_feature_extraction.py` - 增強特徵提取** ⭐
- **職責**：將用戶輸入轉換為 DB 可查詢的特徵
- **架構**：
  - `enhanced_feature_extraction()` - 主提取函數
  - `extract_exact_keywords_from_db()` - 從 DB 提取精確 keywords
  - `extract_exact_titles_from_db()` - 片名精確匹配
  - Mood Label 映射表（MOOD_LABEL_TO_DB_TAGS）
  - 中英文映射（ZH_TO_EN_MOOD, ZH_TO_EN_KEYWORDS）
- **特色**：
  - 三層匹配：精確匹配 → 映射表 → 自然語言推斷
  - 支援多年代篩選（OR 邏輯）
  - 繁簡轉換（UI 繁體 → DB 簡體）
- **輸出**：`{keywords, mood_tags, genres, year_ranges, exact_matches}`

**3. `mapping_tables.py` - 映射表定義（SSOT）**
- **職責**：Mood Label → DB Tags/Keywords 的唯一真相來源
- **核心映射表**：
  - `MOOD_LABEL_TO_DB_TAGS` - 200+ mood labels 映射
  - `ZH_TO_EN_MOOD` - 中文情緒 → 英文 mood tags
  - `ZH_TO_EN_KEYWORDS` - 中文關鍵詞 → 英文 keywords
- **範例**：
  ```python
  "sad": {
    "db_mood_tags": ["sad", "melancholy", "emotional"],
    "db_keywords": ["loss", "grief", "depression"]
  }
  ```

**4. `embedding_service.py` - 語義匹配服務**
- **職責**：使用 OpenAI Embedding 進行語義重排序
- **架構**：
  - `rerank_by_semantic_similarity()` - 主重排序函數
  - MMR (Maximal Marginal Relevance) 多樣性算法
- **特色**：
  - 僅在高抽象查詢時觸發（由 `should_use_embedding()` 決定）
  - 支援多樣性權重調整
  - Boost 精確匹配電影

**5. `database.py` - 資料庫連線**
- **職責**：建立 SQLAlchemy engine 和 session
- **Schema**：
  - `movies` 表：包含 genres (JSONB), keywords (JSONB), mood_tags (JSONB)
  - `users` 表：UUID, email, password_hash
- **技術債務**：⚠️ 若 `DATABASE_URL` 未設定會直接拋出 RuntimeError

#### 前端核心模組

**1. `HomeClient.tsx` - 首頁客戶端元件**
- **職責**：意圖解析 UI（自然語言輸入 + 標籤選擇）
- **狀態管理**：
  - `text`：自然語言查詢
  - `selectedLabels`：Feature 標籤（Set<string>）
  - `selectedMustNots`：Must Not 標籤（Set<string>）
  - `intentResult`：解析結果
- **特色**：
  - 不規則按鈕佈局（flex-wrap）
  - 自訂按鈕樣式（.btn-5, .btn-5-selected）
  - Debug 區域顯示 API 回應
- **SSOT**：從 `intent_labels.py` 同步標籤定義

**2. `api.ts` - API 客戶端**
- **職責**：統一前端 API 呼叫介面
- **當前端點**：
  - `home()`：取得首頁動態
  - `profile.me()`：取得使用者資料
  - `search(q)`：搜尋電影
- **技術債務**： 缺少 `parseIntent()` 和 `recommendMovies()` 方法

**3. `http.ts` - HTTP 工具函式**
- **職責**：封裝 `fetch` API
- **特色**：
  - 自動拼接 `API_BASE`
  - 錯誤處理（拋出含狀態碼的 Error）
  - `cache: "no-store"` 避免快取

---

## 資料模型與 API

### 資料模型

#### 後端 Schema（Pydantic）

**1. MovieIntent**（`backend/app/schemas/intent.py`）

```python
class IntentConstraints(BaseModel):
    year_range: Optional[Tuple[int,int]] = None
    languages: Optional[List[str]] = None
    genres: Optional[List[str]] = None
    country: Optional[str] = None
    must_have_providers: Optional[List[str]] = None
    runtime_range: Optional[Tuple[int,int]] = None
    vote_average_min: Optional[float] = None
    vote_count_min: Optional[int] = None
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None

class MovieIntent(BaseModel):
    feature_labels: List[str]
    must_not_labels: Optional[List[str]] = []
    natural_query: Optional[str] = None
    constraints: Optional[IntentConstraints] = None
    locale: Optional[str] = "zh-TW"
```

**2. FrontendMovie**（`backend/app/schemas/movie_result.py`）

```python
class FrontendMovie(BaseModel):
    id: int
    title: str
    overview: str
    poster_url: Optional[str] = None
    release_year: Optional[int] = None
    vote_average: float = Field(0.0)
```

**3. User**（`backend/app/models/user.py`）

```python
class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    username = Column(String, unique=True)
    created_at = Column(TIMESTAMP(timezone=True))
```

#### 前端 Types（TypeScript）

**1. MovieCard**（`frontend/lib/types/movie.ts`）
**2. Profile**（`frontend/lib/types/profile.ts`）
**3. SearchResult**（`frontend/lib/types/search.ts`）

> **注意**：前端 Types 與後端 Schema 應保持一致，但目前缺少 `MovieIntent` 和 `FrontendMovie` 的 TypeScript 定義。

### API 規格

#### 後端 API 端點

| 端點 | 方法 | 描述 | 請求體 | 回應體 |
|------|------|------|--------|--------|
| `/home` | GET | 取得首頁動態（Mock） | - | `HomeFeed` |
| `/profile/me` | GET | 取得使用者資料（Mock） | - | `Profile` |
| `/search` | GET | 搜尋電影（Mock） | `?q={query}` | `SearchResult` |
| `/api/intent/parse` | POST |  解析意圖 | `ParseReq` | `MovieIntent` |
| `/api/intent/validate` | POST | 驗證 Intent | `MovieIntent` | `MovieIntent` |
| `/api/recommend/movies` | POST |  取得推薦 | `MovieIntent` | `List[FrontendMovie]` |
| `/db-test` | GET | 測試資料庫連線 | - | `{"status": "..."}` |

#### API 請求/回應範例

**POST /api/intent/parse**

請求：
```json
{
  "text": "想看溫暖又真實的日韓電影，不要太血腥",
  "preselected_labels": [
    "comforting",
    "based_on_true_story", 
    "asian_cinema",
    "must_not:gore",
    "must_not:graphic_violence"
  ]
}
```

回應：
```json
{
  "feature_labels": ["comforting", "based_on_true_story", "asian_cinema"],
  "must_not_labels": ["gore", "graphic_violence"],
  "natural_query": "想看溫暖又真實的日韓電影，不要太血腥",
  "constraints": {
    "year_range": [2015, 2025],
    "languages": ["ja", "ko", "zh"],
    "genres": ["Drama", "Romance", "Family", "Comedy"],
    "runtime_range": [80, 250],
    "vote_average_min": 6.5,
    "vote_count_min": 200,
    "include_keywords": ["based on true story", "heartwarming", "healing"],
    "exclude_keywords": ["gore", "violence"],
    "sort_by": "vote_average.desc"
  },
  "locale": "zh-TW"
}
```

**POST /api/recommend/movies**

請求：
```json
{
  "feature_labels": ["comforting", "asian_cinema"],
  "must_not_labels": ["gore"],
  "natural_query": "溫暖的亞洲電影",
  "constraints": {
    "year_range": [2015, 2025],
    "languages": ["ja", "ko", "zh"],
    "genres": ["Drama", "Family"],
    "vote_count_min": 200
  }
}
```

回應：
```json
[
  {
    "id": 668482,
    "title": "完美的日子",
    "overview": "一位東京清潔工的平靜生活...",
    "poster_url": "https://image.tmdb.org/t/p/w500/...",
    "release_year": 2023,
    "vote_average": 7.8
  },
  ...
]
```

---

## 技術債務與已知問題

### 關鍵技術債務

#### 1. ⚠️ **推薦系統缺少 AND 邏輯（最嚴重）**
**問題**：Feature Matching 完全使用 OR 邏輯，無漸進式篩選

**影響**：
- 選擇 10 個 mood labels → 映射出 50+ tags/keywords → 任一符合就得分
- 選擇 1 個 mood label → 映射出 5 個 tags/keywords → 任一符合就得分
- **結果**：選越多 labels，匹配範圍越廣，反而越不精準

**當前評分公式**（`sql_feature_matching()`）：
```python
feature_score = 
    (keyword_matches × 20) +      # OR 邏輯：任一 keyword 符合就加分
    (mood_tag_matches × 15) +     # OR 邏輯：任一 mood_tag 符合就加分
    (genre_matches × 10) +        # OR 邏輯：任一 genre 符合就加分
    (vote_average - 5) × 3 +
    (popularity / 1000) × 2 +
    RANDOM() × (5-50)
```

**建議解決方案**：
```python
# 方案 A: 分層查詢（Tiered Matching）
# Tier 1: 嚴格模式 - 必須符合所有選擇的 features
WHERE 
    genres @> ALL(selected_genres) AND
    mood_tags ?& ALL(selected_moods) AND
    keywords ?& ALL(selected_keywords)
LIMIT 10

# Tier 2: 如果結果 < 10，降級到多數符合（70%）
WHERE 
    (matched_count >= total_required * 0.7)
LIMIT 10

# Tier 3: 如果還是不夠，降級到任一符合（現狀）
WHERE 
    genres ?| ANY(selected_genres) OR
    mood_tags ?| ANY(selected_moods)

# 方案 B: 加權必要性（Match Ratio）
match_ratio = matched_features / total_required_features

ORDER BY 
    match_ratio DESC,          # 符合比例優先
    feature_score DESC         # 同比例再看總分

# 方案 C: 用戶選擇匹配模式
// 前端新增選項
matchMode: "strict" | "balanced" | "loose"
// strict: 必須符合 80%+ features
// balanced: 符合 50%+ features（建議預設）
// loose: 符合任一 feature（目前）
```

**優先級**：🔥 **P0 - 影響核心推薦品質**

---

#### 2. 環境變數依賴 
**問題**：多個關鍵功能依賴環境變數，未設定會導致應用無法啟動。

**影響檔案**：
- `backend/db/database.py`：`DATABASE_URL` 未設定  RuntimeError
- `backend/app/routers/intent_parse.py`：`OPENAI_API_KEY` 未設定  意圖解析失敗
- `backend/api/tmdb_client.py`：`TMDB_API_KEY` 未設定  推薦功能失敗

**解決方案**：
- 建立 `.env.example` 檔案提供範本
- 在 README 中明確說明必要環境變數
- 考慮在啟動時檢查必要環境變數並提供友善錯誤訊息

#### 2. 環境變數依賴
**問題**：多個關鍵功能依賴環境變數，未設定會導致應用無法啟動。

**影響檔案**：
- `backend/db/database.py`：`DATABASE_URL` 未設定 → RuntimeError
- `backend/app/services/embedding_service.py`：`OPENAI_API_KEY` 未設定 → Embedding 失敗（可降級）
- ~~`backend/api/tmdb_client.py`~~：⚠️ 已棄用 TMDB API

**解決方案**：
- 建立 `.env.example` 檔案提供範本
- 在 README 中明確說明必要環境變數
- 考慮在啟動時檢查必要環境變數並提供友善錯誤訊息

#### 3. Mock 資料端點 
**問題**：`/home`, `/profile/me`, `/search` 端點回傳硬編碼的 Mock 資料。

**影響**：
- 無法反映真實使用者資料
- 搜尋功能實際上不會查詢任何資料庫

**待辦**：
- 實作真實的資料庫查詢
- 連接 User 模型與 Profile 端點
- 整合 TMDB 搜尋 API 至 `/search` 端點

#### 3. 前端 API 客戶端不完整 
**問題**：`frontend/lib/api.ts` 缺少關鍵方法。

**缺少的方法**：
```typescript
// 需要新增：
parseIntent: (payload: ParseReq) => Promise<MovieIntent>
recommendMovies: (intent: MovieIntent) => Promise<FrontendMovie[]>
```

**現狀**：`HomeClient.tsx` 直接呼叫 `features/home/services.ts` 的 `parseMovieIntent()`，繞過了統一的 API 層。

**建議**：統一所有 API 呼叫至 `lib/api.ts`。

#### 4. 資料庫遷移管理 
**問題**：`backend/db/versions/` 有三個遷移檔案（看起來有重複/修正）。

**檔案**：
- `0e2a35aaaaaf_init_users.py`
- `7d8fb740c1e7_init_users.py`
- `342292faab66_init_users_fixed.py`  "fixed" 暗示前面有問題

**風險**：
- 不清楚目前資料庫狀態對應哪個遷移
- 可能導致新環境部署時遷移失敗

**建議**：
- 清理遷移歷史，保留正確的版本
- 文件化資料庫 schema 版本

#### 5. CORS 設定過於寬鬆 
**問題**：`backend/app/main.py` 允許所有來源 (`allow_origins=["*"]`)。

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  #  生產環境風險
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**風險**：生產環境會允許任何網站呼叫您的 API。

**建議**：使用環境變數設定允許的來源：
```python
allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
```

### 已知的工作方式（Workarounds）

#### 1. Page 隨機化（intentional）
**檔案**：`backend/api/tmdb_mapper.py`

```python
params: Dict[str, Any] = {
    "page": random.randint(1, 5),  # 刻意隨機化頁數
    ...
}
```

**原因**：避免每次推薦都回傳相同結果，增加推薦多樣性。

**注意**：這是設計決策，非 Bug。

#### 2. Frontend 直接使用 `fetch` 而非 `Api` 客戶端
**檔案**：`frontend/features/home/services.ts`

```typescript
export async function parseMovieIntent(payload: ParseReq) {
  const res = await fetch(`${API_BASE}/api/intent/parse`, {
    method: "POST",
    ...
  });
  ...
}
```

**原因**：`lib/api.ts` 尚未實作 `parseIntent()` 方法。

**影響**：繞過了統一的錯誤處理和快取策略。

---

## 整合點與外部依賴

### 外部服務

| 服務 | 用途 | 整合方式 | 關鍵檔案 |
|------|------|----------|----------|
| **OpenAI GPT-4** | 意圖解析 LLM | REST API (openai Python SDK) | `intent_parse.py` |
| **TMDB API** | 電影資料與圖片 | REST API (httpx) | `tmdb_client.py` |
| **Neon PostgreSQL** | 使用者資料持久化 | SQLAlchemy ORM | `database.py` |

### 外部服務詳細說明

#### 1. OpenAI GPT-4o-mini
**用途**：將自然語言  結構化 JSON

**設定**：
- API Key：`OPENAI_API_KEY` 環境變數
- 模型：`gpt-4o-mini`
- Temperature：0.0（完全確定性）
- Response Format：`json_object`

**呼叫範例**（`intent_parse.py`）：
```python
resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT + schema},
        {"role": "user", "content": user_prompt}
    ],
    response_format={"type": "json_object"},
    temperature=0.0,
    max_completion_tokens=500,
)
```

**錯誤處理**：若 LLM 失敗，回退至僅使用 `preselected_labels` 的基礎 Intent。

#### 2. TMDB API v3
**用途**：取得電影資料、圖片、評分等

**設定**：
- API Key：`TMDB_API_KEY` 環境變數
- Base URL：`https://api.themoviedb.org/3`
- Image Base URL：`https://image.tmdb.org/t/p/w500`

**使用的端點**：
- `GET /discover/movie`：根據條件探索電影

**參數範例**：
```python
{
    "api_key": "...",
    "language": "en-US",
    "with_genres": "18|10749",  # Drama | Romance
    "with_keywords": "9672|208889",  # based on true story | heartwarming
    "with_original_language": "ja,ko,zh",
    "primary_release_date.gte": "2015-01-01",
    "primary_release_date.lte": "2025-12-31",
    "vote_count.gte": 200,
    "sort_by": "vote_average.desc",
    "page": 3  # 隨機
}
```

**Fallback 策略**：四層（如前述「資料流」章節）

#### 3. Neon PostgreSQL
**用途**：使用者資料、觀看清單（未來）

**連線設定**：
- 連線字串：`DATABASE_URL` 環境變數
- 格式：`postgresql://user:pass@host/dbname`

**當前 Schema**：
- `users` 表（UUID, email, password_hash, username, created_at）

**遷移工具**：Alembic

**注意事項**：
-  目前 API 端點尚未真正使用資料庫（回傳 Mock 資料）
-  `/db-test` 端點可驗證連線

### 內部整合點

#### 前後端通訊
- **協定**：HTTP/JSON
- **Base URL**：`http://127.0.0.1:8000`（可透過 `NEXT_PUBLIC_API_BASE` 設定）
- **認證**： 尚未實作（無 JWT/Session）
- **錯誤格式**：FastAPI 預設格式

#### 前端狀態管理
- **工具**：Zustand
- **當前狀態**： 尚未實際使用（保留給未來功能）

---

## 開發與部署

### 本地開發設定

#### 前置需求
1. **Python 3.10+**（推薦 3.11）
2. **Node.js 20+**
3. **PostgreSQL**（或 Neon 雲端帳號）
4. **OpenAI API Key**
5. **TMDB API Key**

#### 後端啟動步驟

1. **安裝依賴**：
```bash
cd backend
pip install -r requirements.txt
```

2. **設定環境變數**（建立 `backend/.env`）：
```bash
DATABASE_URL=postgresql://user:pass@host/dbname
OPENAI_API_KEY=sk-...
TMDB_API_KEY=...
```

3. **執行資料庫遷移**：
```bash
alembic upgrade head
```

4. **啟動開發伺服器**：
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

5. **驗證**：
- 訪問 http://127.0.0.1:8000/docs（Swagger UI）
- 測試 http://127.0.0.1:8000/db-test

#### 前端啟動步驟

1. **安裝依賴**：
```bash
cd frontend
npm install
```

2. **設定環境變數**（建立 `frontend/.env.local`）：
```bash
NEXT_PUBLIC_API_BASE=http://127.0.0.1:8000
NEXT_PUBLIC_USE_MOCKS=false
```

3. **啟動開發伺服器**：
```bash
npm run dev
```

4. **訪問**：http://localhost:3000

### 建置與部署流程

#### 後端建置
```bash
# 無需特別建置，直接部署 Python 代碼
# 確保生產環境安裝依賴：
pip install -r requirements.txt --no-cache-dir
```

#### 前端建置
```bash
cd frontend
npm run build   # 建置至 .next/ 目錄
npm run start   # 生產模式啟動
```

#### 部署注意事項

**環境變數（生產環境）**：
- 後端：
  - `DATABASE_URL`（Neon 或其他 PostgreSQL）
  - `OPENAI_API_KEY`
  - `TMDB_API_KEY`
  - `CORS_ORIGINS`（ 需要修改 main.py 以支援）
  
- 前端：
  - `NEXT_PUBLIC_API_BASE`（後端 API URL）

**CORS 設定**：
 **必須修改** `backend/app/main.py` 中的 CORS 設定：
```python
# 生產環境不可使用 "*"
allow_origins=[
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com"
]
```

**資料庫遷移**：
部署新版本前，執行：
```bash
alembic upgrade head
```

### 測試現況

#### 後端測試
- **單元測試**： 尚未建立
- **整合測試**： 尚未建立
- **手動測試**： 可透過 Swagger UI（`/docs`）

#### 前端測試
- **單元測試**： 尚未建立
- **E2E 測試**： 尚未建立
- **手動測試**： 主要測試方式

#### 執行測試指令（未來）
```bash
# 後端（建議使用 pytest）
cd backend
pytest

# 前端（建議使用 Jest + React Testing Library）
cd frontend
npm test
```

---

## 附錄 - 常用命令與腳本

### 後端常用命令

```bash
# 啟動開發伺服器（熱重載）
uvicorn app.main:app --reload

# 建立新的資料庫遷移
alembic revision --autogenerate -m "description"

# 套用遷移
alembic upgrade head

# 回退遷移
alembic downgrade -1

# 查看遷移歷史
alembic history

# 測試資料庫連線
python test_db.py
```

### 前端常用命令

```bash
# 啟動開發伺服器
npm run dev

# 建置生產版本
npm run build

# 執行生產伺服器
npm run start

# Lint 檢查
npm run lint
```

### 除錯與疑難排解

#### 常見問題

**1. 後端啟動失敗：`RuntimeError: DATABASE_URL is not set`**
- **原因**：未設定環境變數
- **解決**：建立 `backend/.env` 檔案並設定 `DATABASE_URL`

**2. 意圖解析失敗：`LLM 解析失敗`**
- **原因**：OpenAI API Key 無效或未設定
- **解決**：檢查 `OPENAI_API_KEY` 環境變數

**3. 推薦功能回傳空陣列**
- **原因**：TMDB API Key 無效或查詢條件過於嚴格
- **除錯**：檢查後端日誌中的 `[DEBUG]` 訊息，查看 TMDB API 參數

**4. CORS 錯誤**
- **原因**：前端網域未在 CORS 白名單中
- **解決**：確認 `main.py` 的 `allow_origins` 包含前端網域

**5. 前端無法連接後端**
- **原因**：`NEXT_PUBLIC_API_BASE` 設定錯誤
- **解決**：檢查 `.env.local` 檔案

#### 日誌位置

- **後端日誌**：輸出至 stdout（開發模式）
- **前端日誌**：瀏覽器 Console
- **資料庫日誌**：Neon 控制台

#### 效能監控

 目前尚無監控工具整合

**建議工具**：
- 後端：Sentry, Datadog
- 前端：Vercel Analytics, Google Analytics
- 資料庫：Neon 內建監控

---

## ⚠️ 關鍵問題與改進建議

### 🔥 診斷結果: Embedding 使用率低且不準的原因

#### 根本原因分析

**1. 語言匹配問題**：
```
✅ 已確認: DB 電影 overview 全部為中文
✅ 用戶輸入: 中文（"難過的時候適合看什麼"）
→ 理論上應該可以匹配，但...
```

**2. Embedding 基礎設施缺失**：
```
❌ movie_vectors 表不存在
❌ 沒有預先計算的 embedding
❌ 每次都要即時呼叫 OpenAI API（慢且貴）
```

**3. 觸發閾值過高**：
```python
# 用戶選擇 3 個 mood buttons + 1 個 genre
→ 評分: 100 - 25(buttons) - 30(mood_tags) - 30(keywords) = 15
→ 閾值: 40
→ 結果: 15 < 40，不觸發 Embedding ❌
```

**4. Embedding 內容單一**：
```python
# 當前實作（embedding_service.py）
movie_text = f"{title}. {overview or ''}"  # 只用 title + overview

# 問題: 缺少關鍵特徵
❌ 沒有 genres（類型）
❌ 沒有 keywords（關鍵詞）
❌ 沒有 mood_tags（情緒標籤）
```

#### 建議改進方案

**【方案 A+】雙引擎並行 + 加權融合** ⭐⭐⭐ （推薦）

```python
async def hybrid_dual_engine_recommend(
    user_input: str,
    features: Dict,
    db_session: Session,
    top_k: int = 10
):
    # Step 1: Feature Matching（三層漸進式）
    tier1_results = await strict_feature_matching(features, threshold=0.8)  # AND 邏輯
    tier2_results = await balanced_feature_matching(features, threshold=0.5) if len(tier1_results) < 50 else []
    tier3_results = await loose_feature_matching(features) if len(tier1_results + tier2_results) < 100 else []
    
    feature_candidates = tier1_results + tier2_results + tier3_results
    
    # Step 2: Embedding Reranking（並行執行，不替代）
    if user_input and len(user_input.strip()) > 0:
        # 使用增強版 embedding（包含 genres + keywords + mood_tags）
        embedding_scores = await enhanced_embedding_rerank(
            query=user_input,
            candidates=feature_candidates,
            db_session=db_session
        )
    else:
        embedding_scores = {}
    
    # Step 3: 加權融合
    for movie in feature_candidates:
        feature_score = movie.get("feature_score", 0)
        embedding_score = embedding_scores.get(movie["id"], 0) * 100  # 歸一化到 0-100
        match_ratio = movie.get("match_ratio", 0)  # 符合比例（0-1）
        
        # 融合公式（可調整權重）
        final_score = (
            feature_score * 0.4 +          # Feature 匹配 40%
            embedding_score * 0.3 +        # 語義匹配 30%
            match_ratio * 100 * 0.3        # 符合比例 30%
        )
        movie["final_score"] = final_score
    
    # Step 4: 排序 + 多樣性過濾
    feature_candidates.sort(key=lambda x: x["final_score"], reverse=True)
    results = diversity_filter(feature_candidates, top_k=top_k)
    
    return results
```

**優點**：
- ✅ 保留 Feature Matching 的精準度（三層漸進式）
- ✅ 加入 Embedding 的語義理解（補足 Feature 盲點）
- ✅ 兩者互補，不再二選一
- ✅ 權重可調整（A/B 測試友善）

**【方案 B】增強 Embedding 內容**

```python
# 修改 batch_populate_embeddings.py
def generate_enhanced_embedding_text(movie: Dict) -> str:
    """
    生成包含所有特徵的 embedding 文本
    """
    parts = []
    
    # 1. 標題
    parts.append(f"Title: {movie['title']}")
    
    # 2. 類型
    if movie.get('genres'):
        genres_str = ", ".join(movie['genres'])
        parts.append(f"Genres: {genres_str}")
    
    # 3. 情緒標籤
    if movie.get('mood_tags'):
        moods_str = ", ".join(movie['mood_tags'])
        parts.append(f"Mood: {moods_str}")
    
    # 4. 關鍵詞
    if movie.get('keywords'):
        keywords_str = ", ".join(movie['keywords'][:10])  # 限制數量
        parts.append(f"Keywords: {keywords_str}")
    
    # 5. 簡介
    if movie.get('overview'):
        parts.append(f"Overview: {movie['overview']}")
    
    return " | ".join(parts)

# 範例輸出:
# "Title: 完美的日子 | Genres: 劇情 | Mood: peaceful, contemplative, healing | 
#  Keywords: slice-of-life, minimalism, daily-routine | 
#  Overview: 一位東京清潔工的平靜生活..."
```

**優點**：
- ✅ Embedding 包含完整特徵（genres + moods + keywords）
- ✅ 語義匹配更準確
- ✅ 適合抽象查詢（"適合下雨天看的電影"）

**【方案 C】建立 movie_vectors 表 + 預計算**

```sql
-- 創建 Embedding 向量表
CREATE TABLE IF NOT EXISTS movie_vectors (
    tmdb_id INTEGER PRIMARY KEY REFERENCES movies(tmdb_id),
    embedding_text TEXT,              -- 用於生成 embedding 的完整文本
    embedding JSONB,                  -- embedding 向量（1536 維）
    embedding_version VARCHAR(20),    -- embedding 模型版本
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_movie_vectors_tmdb_id ON movie_vectors(tmdb_id);
```

```python
# 批次預計算（執行一次）
python tools/batch_populate_enhanced_embeddings.py

# 預估成本:
# 675 部電影 × $0.00002/1K tokens × 平均 300 tokens 
# = 675 × 0.00002 × 0.3 = $0.00405 ≈ $0.004
# （超便宜！）
```

**優點**：
- ✅ 預先計算，查詢時超快
- ✅ 成本極低（一次性）
- ✅ 可離線更新

---

### 問題 1: Feature Matching 完全 OR 邏輯

**現況**：
- 所有 features（keywords, mood_tags, genres）都是 **OR 匹配**
- 只要符合**任意一個** feature 就會獲得分數並被選中
- 沒有「必須全部符合」或「漸進式比較」的機制

**影響範例**：
```
用戶選擇: ["sad", "healing", "uplifting", "emotional", "heartwarming"]
↓
映射後: 25+ mood_tags + 30+ keywords
↓
SQL 查詢: WHERE mood_tags ?| ANY([25個tags]) OR keywords ?| ANY([30個keywords])
↓
結果: 只要電影包含「sad」或「healing」其中一個就會被選中
→ 匹配範圍過廣，精準度降低
```

**建議改進方案**：

#### 方案 A: 三層漸進式查詢（推薦）⭐
```python
async def tiered_feature_matching(features, db_session):
    # Tier 1: 嚴格模式（AND 邏輯）- 優先嘗試
    strict_results = await query_with_all_features(features, threshold=0.8)
    if len(strict_results) >= 10:
        return strict_results[:10]
    
    # Tier 2: 平衡模式（多數符合）- 降級
    balanced_results = await query_with_most_features(features, threshold=0.5)
    if len(balanced_results) >= 10:
        return balanced_results[:10]
    
    # Tier 3: 寬鬆模式（OR 邏輯）- 保底
    loose_results = await query_with_any_features(features)
    return loose_results[:10]
```

**優點**：
- 保持精準度（先嚴格，後寬鬆）
- 保證有結果（三層 fallback）
- 用戶體驗好（選越多越精準）

#### 方案 B: Match Ratio 排序
```python
# 計算符合比例
match_ratio = matched_features / total_required_features

# 優先顯示高符合比例的電影
ORDER BY 
    match_ratio DESC,          # 100% 符合優先
    feature_score DESC         # 同比例再看總分
```

**優點**：
- 實作簡單（單一查詢）
- 符合比例清楚（可顯示給用戶）
- 保留現有評分邏輯

#### 方案 C: 用戶自選匹配模式
```typescript
// 前端新增選項
<select name="matchMode">
  <option value="strict">嚴格（必須全部符合）</option>
  <option value="balanced">平衡（符合 50%+）</option>
  <option value="loose">寬鬆（符合任一）</option>
</select>
```

**優點**：
- 彈性最高
- 滿足不同用戶需求
- 教育用戶理解推薦邏輯

---

### 問題 2: Mood Label 數量影響推薦精準度

**現況**：
```
選 1 個 mood → 映射 5 個 tags → OR 匹配 → 範圍適中
選 5 個 moods → 映射 25 個 tags → OR 匹配 → 範圍過廣
選 10 個 moods → 映射 50 個 tags → OR 匹配 → 範圍極廣，幾乎所有電影都符合
```

**建議改進**：
1. **限制 Mood 選擇數量**（3-5 個）
2. **實作方案 A 的三層查詢**
3. **顯示匹配度指標**（符合 8/10 個條件）

---

### 問題 3: 缺少用戶反饋機制

**現況**：
- 沒有「喜歡/不喜歡」按鈕
- 無法學習用戶偏好
- 推薦結果無法改進

**建議改進**：
1. 新增評分/反饋 API
2. 儲存用戶互動記錄
3. 調整 feature_score 權重
4. 實作協同過濾

---

## 總結與建議

### 專案優勢 

1. **創新的混合式架構**：LLM + 規則系統確保意圖解析的準確性與可靠性
2. **強大的 Fallback 機制**：四層策略確保推薦功能高可用性
3. **現代化技術棧**：使用最新版本的 FastAPI, Next.js, React
4. **清晰的模組化設計**：前後端職責分明，易於擴展
5. **SSOT 原則**：標籤定義單一真相來源（`intent_labels.py`）

### 關鍵改進建議 

#### 短期（1-2 週）
1. **補充環境變數範本**：建立 `.env.example` 檔案
2. **統一 API 客戶端**：將所有 API 呼叫移至 `lib/api.ts`
3. **修正 CORS 設定**：使用環境變數控制允許的來源
4. **清理資料庫遷移**：移除重複的遷移檔案

#### 中期（1 個月）
1. **實作真實資料端點**：連接 `/home`, `/profile`, `/search` 至資料庫
2. **新增 TypeScript 型別**：為 `MovieIntent`, `FrontendMovie` 建立前端型別
3. **實作認證系統**：JWT 或 Session-based 認證
4. **新增基礎測試**：至少為核心功能（intent_parse, tmdb_client）編寫測試

#### 長期（3 個月）
1. **使用者功能**：註冊、登入、觀看清單、評分
2. **推薦個性化**：基於使用者歷史的推薦
3. **效能優化**：快取策略、CDN 整合
4. **監控與日誌**：整合 Sentry, 結構化日誌

### 架構演進方向 

```
當前架構 (MVP)

階段 1: 完善基礎功能
 真實資料端點
 認證系統
 基礎測試

階段 2: 個性化推薦
 使用者行為追蹤
 協同過濾
 A/B 測試框架

階段 3: 規模化
 快取層（Redis）
 佇列系統（Celery）
 微服務拆分

階段 4: 智能化
 深度學習推薦
 即時推薦
 多模態搜尋（圖片、影片）
```

---

## 文件維護

### 更新頻率
- **重大架構變更**：立即更新
- **新增功能模組**：功能完成後更新
- **定期審查**：每季度檢視一次

### 文件擁有者
- **主要維護者**：技術主管/架構師
- **貢獻者**：所有開發團隊成員

### 相關文件
- **API 文件**：http://127.0.0.1:8000/docs（Swagger UI）
- **README**：專案根目錄
- **PRD**：（尚未建立）
- **UX 設計**：（尚未建立）

---

**文件版本**：1.0  
**最後更新**：2025-11-06  
**作者**：Winston (Architect Agent)  
**狀態**： 已完成初版

 **此文件反映了 MovieIn 專案的真實現況，包含所有技術債務與設計決策。**
