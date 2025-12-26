# 🎬 MovieIn - 趣味化電影社交娛樂平台

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.1-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.0.0-000000?logo=next.js)](https://nextjs.org)
[![React](https://img.shields.io/badge/React-19.2.0-61dafb?logo=react)](https://react.dev)
[![Neon](https://img.shields.io/badge/Database-Neon_PostgreSQL-00E699?logo=postgresql&logoColor=white)](https://neon.tech)
[![Built with BMAD](https://img.shields.io/badge/Built%20with-BMAD%20Method-purple?logo=github)](https://github.com/bmadcode/BMAD-METHOD)


>**使用 [BMAD Method™](https://github.com/bmadcode/BMAD-METHOD) 打造** - 革命性的 Agentic Agile 開發方法，由 AI 代理團隊（分析師、架構師、產品經理、Scrum Master、開發者、QA）協作設計並實現這個全端平台。

---

## MovieIn 核心價值

### 為電影愛好者打造的社交娛樂平台

**MovieIn 的使命：** 讓喜愛電影的人不再孤單觀影，透過共同的觀影品味建立真實連結。

#### 三大核心體驗

1. **趣味化推薦** 
   - 用自然語言表達心情：「今天想看點輕鬆搞笑的」
   - AI 秒懂你的需求，推薦最合適的電影
   - 不只是冰冷的演算法，而是懂你的觀影夥伴

2. **片單社交** 
   - 分享你的觀影清單(Watchlist/Top10 List)，展現獨特品味
   - 找到和你口味相似的影友
   - 透過電影開啟話題，建立深度連結

3. **娛樂互動** 
   - 趣味測驗：探索你的電影人格
   - 排行榜：發現社群熱門電影
   - 評分分享：影響彼此的觀影選擇

### 解決的核心痛點

 傳統困境 vs MovieIn 創新解決方案 

一、
- **選擇疲勞、缺乏智慧推薦**：平台有數千部電影卻不知看什麼
- **AI 智能推薦** Phase 3.6 混合推薦引擎，精準理解需求 
二、
- **孤單觀影**：市面上鮮少有電影為主題的交友社群Application 
- **片單交友**透過觀影品味 (Top10 List 與Watchlist 的交換與共享)找到知音影友 


## 核心功能特色

### Phase 3.6 智能混合推薦系統

**突破性的雙引擎推薦架構：**

```
┌─────────────────────────────────────────────────────┐
│          Phase 3.6 混合推薦引擎                      │
│                                                     │
│  ┌──────────────────┐      ┌───────────────────┐    │
│  │ Feature Matching │      │ Embedding Vector  │    │
│  │ Engine (Phase 1) │      │ Engine (Phase 3.6)│    │
│  │                  │      │                   │    │
│  │ • 類型匹配        │      │ • OpenAI Embedding│    │
│  │ • 關鍵字匹配      │      │ • 語義相似度      │     │
│  │ • 心情標籤匹配    │      │ • 深度理解語境    │     │
│  └────────┬─────────┘      └─────────┬─────────┘    │
│           │                          │              │
│           └──────────┬───────────────┘              │
│                      ▼                              │
│           ┌──────────────────────┐                  │
│           │   智能決策邏輯        │                  │
│           │  (自動選擇最佳引擎)   │                  │
│           └──────────────────────┘                 │ 
└─────────────────────────────────────────────────────┘
```

#### Feature Matching Engine
- **精準特徵匹配**：基於電影的結構化資料（genres, keywords, mood_tags）
- **確定性推薦**：當使用者需求明確時，提供最相關的結果
- **高效能查詢**：直接從 Neon PostgreSQL 進行索引查詢

#### Embedding Vector Engine（Phase 3.6 核心創新）
- **OpenAI text-embedding-3-small**：將電影描述轉換為 1536 維語義向量
- **深度語義理解**：理解「輕鬆愉快的科幻喜劇」背後的真實含義
- **相似度計算**：使用餘弦相似度找出語義最接近的電影
- **情境感知**：捕捉當下心情與觀影需求的細微差異

#### 智能決策邏輯
```python
# 系統自動判斷最佳推薦策略
if user_input.has_clear_features:
    # 明確需求 → Feature Matching
    return feature_matching_engine(genres, keywords, moods)
else:
    # 模糊描述 → Embedding Vector
    return embedding_engine(natural_language_query)
```

### 自然語言對話式推薦

**真正理解你的話：**
```
使用者：「週末想和家人看點溫馨感人的電影」
      ↓
AI 解析：
  ✓ 情境：家庭觀影
  ✓ 心情：Heartwarming, Emotional
  ✓ 類型：Family, Drama
  ✓ 排除：暴力、恐怖內容
      ↓
推薦：《可可夜總會》、《心靈奇旅》、《腦筋急轉彎》
```

### 片單社交 - 用電影交朋友

#### 觀影清單分享
- **個人化片單**：建立專屬的「想看清單」、「已看清單」
- **品味展示**：透過觀影紀錄展現你的電影品味
- **清單公開**：讓其他影友發現你的精選片單

#### 社交功能
- **好友系統**：加入志同道合的電影愛好者
- **品味匹配**：系統推薦口味相似的潛在影友
- **評論互動**：和朋友討論電影心得與感想
- **共同興趣**：發現你和好友都喜歡的電影類型

#### 社群互動
- **Top 10 排行榜**：看看社群都在追什麼片
- **熱門討論**：參與最火熱的電影話題
- **影友推薦**：接收來自好友的私人推薦

### 趣味化娛樂體驗

#### 智能測驗系統
- **電影人格測試**：透過問答了解你的觀影偏好
- **品味分析**：生成個人化的電影品味報告
- **推薦優化**：測驗結果強化推薦精準度

#### 遊戲化元素
- **觀影成就**：解鎖不同類型的電影徽章
- **探索挑戰**：嘗試新類型電影獲得獎勵
- **社群排名**：看看誰是最活躍的影評人

### 增強特徵提取系統
- **心情標籤映射表**：70+ 標籤（Romantic, Thrilling, Dark, Uplifting, Adventurous...）
- **關鍵字精準匹配**：30,000+ 電影關鍵字完整資料庫
- **多維度分析**：類型 × 心情 × 關鍵字三維交叉分析

---

## 技術架構

### 技術棧總覽

#### 後端技術

**FastAPI** | 0.119.1 | 高效能非同步 Python Web 框架 |
**Neon PostgreSQL** | Serverless | 
**雲端 Serverless 資料庫** 1000+ 部電影完整資料、自動擴展與休眠、超低延遲查詢 |
**SQLAlchemy** | 2.0.36 | ORM 資料庫抽象層 |
**OpenAI Embedding** | text-embedding-3-small | Phase 3.6 語義向量引擎 |
**Redis** | 5.0.1 | 推薦結果快取與 Session 管理 |
**Alembic** | 1.14.0 | 資料庫版本控制與遷移 |
**JWT + PassLib** | Latest | 使用者認證與授權 |

#### 前端技術
| 技術 | 版本 | 用途 |
|------|------|------|
| **Next.js** | 16.0.0 | React 框架（App Router） |
| **React** | 19.2.0 | UI 函式庫（最新版） |
| **Zustand** | 5.0.8 | 輕量級狀態管理 |
| **Tailwind CSS** | 4.x | Utility-first CSS 框架 |
| **ky** | 1.13.0 | 現代化 HTTP 客戶端 |
| **TypeScript** | 5.x | 完整型別安全 |

### 什麼是 BMAD Method？

**BMAD (Breakthrough Method of Agile AI-Driven Development)** 是一個革命性的 AI 代理協作開發框架，透過專業化的 AI 代理團隊進行全生命週期軟體開發。

### MovieIn 如何使用 BMAD

本專案完全採用 BMAD Method 進行開發，整個過程展示了 AI 代理團隊協作的強大能力：

#### 規劃階段（Planning Phase）

1. **分析師代理 (Analyst Agent)** 
   - 需求訪談與分析
   - 建立使用者故事
   - 定義核心痛點

2. **產品經理代理 (PM Agent)**
   - 撰寫產品需求文件 (PRD)
   - 定義功能優先級
   - 規劃產品路線圖

3. **架構師代理 (Architect Agent - Winston)**
   - 設計系統架構（brownfield architecture）
   - 技術選型與評估
   - 建立 `docs/architecture.md`

#### 開發階段（Development Phase）

4. **Scrum Master 代理**
   - 將 PRD 與架構文件拆分為開發故事
   - 管理 Sprint 進度
   - 協調代理團隊

5. **開發者代理 (Dev Agent)**
   - 實現每個故事的程式碼
   - 遵循架構設計原則
   - 建立測試與文件

6. **QA 代理**
   - 自動化測試
   - 整合測試
   - 效能與安全測試

### BMAD 帶來的優勢

| 傳統開發 | BMAD Method 開發 |
|---------|-----------------|
| 手動撰寫規格文件 | AI 代理協助建立詳細 PRD |
| 架構設計需要反覆討論 | Architect Agent 提供完整架構分析 |
| 開發與規格脫節 | Scrum Master 確保故事與規格一致 |
| 人工測試耗時 | QA Agent 自動化測試 |
| 文件常常過時 | 代理自動更新文件 |

### 專案結構（BMAD 組織）

```
bmad-method/
├── .bmad-core/              # BMAD 核心配置
│   ├── core-config.yaml     # 專案配置
│   └── agents/              # AI 代理定義
├── docs/
│   ├── architecture.md      # Winston 建立的架構文件
│   ├── QUICKSTART.md        # 快速開始指南
│   └── *.md                 # 其他規格文件
├── backend/                 # FastAPI 後端
│   ├── app/
│   │   ├── services/        # 核心服務（推薦引擎等）
│   │   ├── routers/         # API 路由
│   │   └── models/          # 資料模型
│   └── db/                  # 資料庫配置
├── frontend/                # Next.js 前端
│   ├── app/                 # App Router 頁面
│   ├── features/            # 功能模組
│   └── lib/                 # 工具函式庫
└── common/                  # 共用工具與任務
```

---

## 快速開始

### 環境需求

- **Node.js** 20+
- **Python** 3.10+
- **PostgreSQL** 13+
- **Redis** 5.0+（選用）

### 安裝步驟

#### 1. Clone 專案

```bash
git clone https://github.com/VictorHo1114/MovieIn_bmadProject.git
cd MovieIn_bmadProject
```

#### 2. 後端設定

```bash
cd backend

# 建立虛擬環境
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# 安裝依賴
pip install -r requirements.txt

# 設定環境變數（建立 .env 檔案）
DATABASE_URL=postgresql://user:password@localhost/moviein
SECRET_KEY=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key

# 執行資料庫遷移
alembic upgrade head

# 啟動後端服務
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

#### 3. 前端設定

```bash
cd frontend

# 安裝依賴
npm install

# 設定環境變數（建立 .env.local）
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000

# 啟動開發伺服器
npm run dev
```

#### 4. 存取應用

- **前端**：http://localhost:3000
- **後端 API**：http://127.0.0.1:8000
- **API 文件**：http://127.0.0.1:8000/docs

---

## 文件

- **[架構文件](docs/architecture.md)** - 完整的 brownfield 架構分析
- **[快速開始](docs/QUICKSTART.md)** - 詳細安裝與設定指南
- **[推薦系統架構](docs/recommendation-system-architecture.md)** - 混合推薦引擎說明
- **[測驗系統](docs/quiz-system-documentation.md)** - 智能測驗功能
- **[部署指南](docs/DEPLOYMENT.md)** - 生產環境部署

---

## 專案亮點與創新

### 核心技術創新

#### 1. Phase 3.6 智能決策邏輯

**自動判斷最佳推薦策略：**

```python
# simple_recommend.py - 核心智能決策
def decide_recommendation_engine(user_input, mood_labels, genres):
    """
    Phase 3.6 創新：智能選擇推薦引擎
    
    Feature Matching: 當特徵明確時使用
    Embedding Vector: 當需要深度語義理解時使用
    """
    
    # 分析輸入特徵豐富度
    feature_score = calculate_feature_richness(
        mood_labels=mood_labels,
        genres=genres,
        keywords=extract_keywords(user_input)
    )
    
    if feature_score >= FEATURE_THRESHOLD:
        # 特徵豐富 → 使用精準匹配
        logger.info("🎯 使用 Feature Matching Engine")
        return feature_matching_engine(mood_labels, genres)
    else:
        # 需要語義理解 → 使用 Embedding
        logger.info("🔮 使用 Embedding Vector Engine")
        return embedding_vector_engine(user_input)
```

#### 2. Neon PostgreSQL + pgvector 極速查詢

**毫秒級語義搜尋：**

```sql
-- Phase 3.6 核心查詢：使用 pgvector 進行向量相似度搜尋
SELECT 
    m.id,
    m.title,
    m.overview,
    m.genres,
    m.poster_path,
    m.vote_average,
    -- 計算餘弦相似度（值越接近 1 越相似）
    1 - (m.embedding_vector <=> :query_vector) AS similarity_score
FROM movies m
WHERE 
    -- 預先篩選以提升效能
    m.vote_count > 100
    AND m.vote_average > 6.0
    -- pgvector 的 <=> 運算子進行向量距離計算
ORDER BY m.embedding_vector <=> :query_vector
LIMIT 20;

-- 查詢時間：< 50ms（30,000+ 筆資料）
-- Neon 自動優化：使用 HNSW 索引加速向量搜尋
```

#### 3. 心情標籤映射表（SSOT）

**70+ 情緒標籤精準映射：**

```python
# mapping_tables.py - Single Source of Truth
MOOD_LABEL_TO_DB_TAGS = {
    # 正向情緒
    "Romantic": ["romance", "love", "relationship", "passion"],
    "Uplifting": ["inspiring", "hopeful", "feel-good", "optimistic"],
    "Heartwarming": ["touching", "emotional", "family", "friendship"],
    "Fun": ["entertaining", "enjoyable", "lighthearted", "playful"],
    
    # 刺激感受
    "Thrilling": ["suspense", "tension", "mystery", "edge-of-seat"],
    "Adventurous": ["epic", "journey", "exploration", "discovery"],
    "Intense": ["gripping", "powerful", "visceral", "raw"],
    
    # 深度情緒
    "Dark": ["noir", "gritty", "bleak", "haunting"],
    "Thought-Provoking": ["philosophical", "cerebral", "complex"],
    "Emotional": ["moving", "poignant", "tearjerker", "dramatic"],
    
    # ... 共 70+ 標籤映射
}
```




## 貢獻

歡迎貢獻！請查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解如何參與。

### 開發工作流程

1. Fork 本專案
2. 建立功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 開啟 Pull Request

---


## 完整文件

- **[架構文件](docs/architecture.md)** - 完整的 Brownfield 架構分析（Winston 架構師撰寫）
- **[快速開始指南](docs/QUICKSTART.md)** - 詳細安裝與設定教學
- **[推薦系統架構](docs/recommendation-system-architecture.md)** - Phase 3.6 混合推薦引擎深度解析
- **[測驗系統文件](docs/quiz-system-documentation.md)** - 智能電影人格測驗系統
- **[社交功能規格](docs/spec-social-features.md)** - 片單社交與好友系統
- **[遊戲化功能規格](docs/spec-gaming-features.md)** - 趣味化互動設計
- **[部署指南](docs/DEPLOYMENT.md)** - 生產環境部署完整流程

---

## 參與貢獻

歡迎所有形式的貢獻！無論是功能建議、Bug 回報、文件改進或程式碼貢獻。


## 授權

本專案採用 **MIT 授權** - 詳見 [LICENSE](LICENSE) 檔案

---

## 致謝

### 核心技術夥伴

- **[BMAD Method™](https://github.com/bmadcode/BMAD-METHOD)** - 革命性的 AI 代理開發框架
  - *感謝 BMAD 讓 AI 團隊協作成為可能*
  
- **[Neon](https://neon.tech)** - Serverless PostgreSQL 資料庫
  - *完美的 pgvector 支援，Phase 3.6 的基石*
  
- **[OpenAI](https://openai.com/)** - text-embedding-3-small API
  - *強大的語義理解能力*

### 開發框架與工具

- **[FastAPI](https://fastapi.tiangolo.com/)** - 現代化高效能 Python Web 框架
- **[Next.js](https://nextjs.org/)** - React 全端框架
- **[TMDB](https://www.themoviedb.org/)** - 電影資料來源
- **[Vercel](https://vercel.com/)** - 前端部署平台
- **[Render](https://render.com/)** - 後端託管服務

---

## 聯絡方式

**Victor Ho** - 專案創建者與維護者

- GitHub: [@VictorHo1114](https://github.com/VictorHo1114)
- 專案連結: [MovieIn_bmadProject](https://github.com/VictorHo1114/MovieIn_bmadProject)

有任何問題或建議，歡迎：
- 開啟 [Issue](https://github.com/VictorHo1114/MovieIn_bmadProject/issues)
- 發起 [Discussion](https://github.com/VictorHo1114/MovieIn_bmadProject/discussions)
- 給專案一個星星支持！

---

## 專案展望

### 已完成 

- ✅ Phase 3.6 混合推薦系統（Feature Matching + Embedding Vector）
- ✅ Neon PostgreSQL 整合與 pgvector 擴展
- ✅ 自然語言推薦功能
- ✅ 片單社交系統
- ✅ 好友關係管理
- ✅ 智能測驗系統
- ✅ 趣味化 UI/UX

### 規劃中 

- **個人化推薦演算法優化**
  - 基於使用者觀影歷史的協同過濾
  - 時間感知推薦（週末 vs 平日）
  
- **社群功能擴展**
  - 影評討論區
  - 主題片單（例如：「奧斯卡最佳影片」）
  - 觀影挑戰活動
  
- **AI 功能強化**
  - 電影劇情摘要生成
  - 個性化觀影報告
  - 智能觀影時間建議

---

### Built with 💜 using BMAD Method™

*展示 AI 代理團隊協作開發的無限可能*

---

[![Star History Chart](https://api.star-history.com/svg?repos=VictorHo1114/MovieIn_bmadProject&type=Date)](https://star-history.com/#VictorHo1114/MovieIn_bmadProject&Date)


