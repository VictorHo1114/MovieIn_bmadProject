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
-  **混合式意圖解析引擎**：LLM (GPT-4) + 規則系統雙重保障
-  **智能推薦系統**：多層 Fallback 機制確保推薦品質
-  **多語言支援**：支援中文自然語言查詢，整合 TMDB 國際資料
-  **現代化 UI**：Next.js 16 + React 19 + Tailwind CSS 4

---

## 快速參考 - 關鍵檔案與進入點

### 關鍵檔案清單

#### 後端核心檔案
- **主進入點**：`backend/app/main.py`
- **意圖解析**：`backend/app/routers/intent_parse.py` - 核心 AI 引擎
- **推薦引擎**：`backend/app/routers/recommend_router.py`
- **TMDB 客戶端**：`backend/api/tmdb_client.py` - 外部 API 整合
- **TMDB 映射器**：`backend/api/tmdb_mapper.py` - 參數轉換
- **資料庫連線**：`backend/db/database.py`
- **使用者模型**：`backend/app/models/user.py`

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
| **資料庫** | PostgreSQL (Neon) | 13+ | 雲端託管 |
| **ORM** | SQLAlchemy | Latest | 使用 declarative_base |
| **遷移工具** | Alembic | 1.14.0 | 資料庫版本控制 |
| **AI/LLM** | OpenAI GPT-4 | gpt-4o-mini | 意圖解析引擎 |
| **外部 API** | TMDB API | v3 | 電影資料來源 |
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
1. 使用者輸入
   
   "想看溫暖又真實的日韓電影，不要太血腥"
   + [comforting, based_on_true_story, asian_cinema]
   + [must_not: gore, graphic_violence]
   
2. POST /api/intent/parse
   
   [混合架構 - 三階段處理]
   
   階段 1: LLM 完整解析
    呼叫 GPT-4o-mini (temperature=0.0)
    解析年份、類型、情緒、關鍵字
    產生 llm_raw JSON
   
   階段 2: finalize_intent() 審計與補完
   a) 套用 Feature 規則 (apply_feature_rules)
      - "comforting"  genres: [Drama, Romance, Family, Comedy]
      - "comforting"  must_not: [thriller, horror, gore]
      - "based_on_true_story"  keywords: [9672, 9346]
   
   b) 套用語言規則 (apply_language_rules)
      - "asian_cinema"  languages: [ja, ko, zh]
   
   c) Regex 安全網 (apply_natural_language_hints)
      - "血腥"  exclude_keywords: [gore, violence]
      - "日韓"  確認 languages 包含 ja, ko
   
   d) 安全預設 (apply_safe_defaults)
      - year_range: [2015, 2025]
      - runtime_range: [80, 250]
      - vote_count_min: 200
      - sort_by: "vote_average.desc"
   
   階段 3: 回傳 MovieIntent
   
3. POST /api/recommend/movies (with MovieIntent)
   
   [多層 Fallback 策略]
   
   策略 1: 理想查詢 (Keywords + Genres)
    tmdb_mapper.to_tmdb_discover_params()
    genres: Drama, Romance, Family, Comedy
    keywords: "based on true story", "heartwarming"
    languages: ja, ko, zh
    若成功  回傳結果
   
   策略 2: 優先級 (僅 Keywords)
    移除 genres，保留 keywords
    若成功  回傳結果
   
   策略 3: 次要 (僅 Genres)
    移除 keywords，保留 genres
    若成功  回傳結果
   
   策略 4: 最終防呆 (僅 Genres + 熱門度)
    sort_by: "popularity.desc"
    若仍失敗  回傳空陣列 []
   
4. TMDB API 回應處理
   
   _format_tmdb_results()
    格式化為 FrontendMovie[]
    建構完整 poster URL
    解析 release_year
   
5. 回傳給前端
   
   HomeClient.tsx 顯示結果
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

**1. `intent_parse.py` - 混合式意圖解析引擎**
- **職責**：將自然語言 + 標籤  結構化 MovieIntent
- **架構**：LLM (GPT-4) + 規則系統（三階段處理）
- **特色**：
  - 完整解析年份、類型、情緒、關鍵字
  - Regex 安全網確保「動作片」不遺漏
  - 自動補充安全預設值
- **端點**：
  - `POST /api/intent/parse` - 解析意圖
  - `POST /api/intent/validate` - 驗證 Intent 結構
- **技術債務**： OpenAI API Key 必須設定在環境變數

**2. `tmdb_client.py` - TMDB API 整合層**
- **職責**：將 MovieIntent  TMDB API  FrontendMovie[]
- **特色**：四層 Fallback 策略確保推薦品質
  1. Keywords + Genres（理想）
  2. 僅 Keywords（優先）
  3. 僅 Genres（次要）
  4. 僅 Genres + 熱門度（保底）
- **注意事項**：
  -  使用 `httpx.AsyncClient` 非同步請求
  -  包含詳細 DEBUG 日誌
  -  TMDB API Key 必須設定在環境變數

**3. `tmdb_mapper.py` - 參數映射器**
- **職責**：MovieIntent  TMDB Discover API 參數
- **映射表**：
  - `GENRE_TO_TMDB`：類型名稱  TMDB ID（28=Action, 35=Comedy...）
  - `KEYWORD_TO_TMDB`：關鍵字  TMDB ID（9672=based on true story...）
- **注意**：使用 `set()` 確保 ID 唯一性

**4. `database.py` - 資料庫連線**
- **職責**：建立 SQLAlchemy engine 和 session
- **設定**：從 `.env` 讀取 `DATABASE_URL`
- **技術債務**： 若 `DATABASE_URL` 未設定會直接拋出 RuntimeError

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

#### 1. 環境變數依賴 
**問題**：多個關鍵功能依賴環境變數，未設定會導致應用無法啟動。

**影響檔案**：
- `backend/db/database.py`：`DATABASE_URL` 未設定  RuntimeError
- `backend/app/routers/intent_parse.py`：`OPENAI_API_KEY` 未設定  意圖解析失敗
- `backend/api/tmdb_client.py`：`TMDB_API_KEY` 未設定  推薦功能失敗

**解決方案**：
- 建立 `.env.example` 檔案提供範本
- 在 README 中明確說明必要環境變數
- 考慮在啟動時檢查必要環境變數並提供友善錯誤訊息

#### 2. Mock 資料端點 
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
