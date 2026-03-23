# MovieIn | AI-Powered Social Movie Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.119.1-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16.0.0-000000?logo=next.js)](https://nextjs.org)
[![Neon](https://img.shields.io/badge/Database-Neon_PostgreSQL-00E699?logo=postgresql&logoColor=white)](https://neon.tech)

MovieIn 是一個結合大語言模型（LLM）語義檢索與社交元素的現代化電影推薦平台。

## Key Engineering Highlights

* **Hybrid Recommendation Engine (雙引擎混合推薦系統)**: 獨立設計並實作基於 `Feature Matching` 與 `Embedding Vector` 的智能決策路由。系統能動態判斷使用者 Query 的特徵豐富度，自動切換精確條件過濾或 RAG 概念的語義相似度搜尋。
* **High-Performance Vector Search**: 整合 OpenAI `text-embedding-3-small` 將電影特徵轉換為 1536 維向量，並利用 **Neon PostgreSQL + pgvector (HNSW 索引)** 達成針對 30,000+ 筆資料小於 50ms 的超低延遲餘弦相似度 (Cosine Similarity) 檢索。
* **Modern Full-Stack Architecture**: 後端採用 FastAPI 處理高併發非同步請求，前端以 Next.js (App Router) 搭配 Zustand 進行狀態管理，確保流暢的 SPA 體驗。
* **Agentic Agile Development**: 導入 BMAD Method，透過 AI Agent 協作完成從架構設計 (Brownfield Architecture)、API 規格制定到自動化測試的全生命週期開發。


## System Architecture

### 混合推薦引擎架構

為解決自然語言中模糊的觀影意圖，系統實作了智能決策層：

```text
┌────────────────────────────────────────────────────────┐
│               Smart Routing Controller                 │
│  (Evaluates input feature richness & intent clarity)   │
└────────┬───────────────────────────────────────┬───────┘
         │ [Clear Features]                      │ [Vague/Contextual Input]
         ▼                                       ▼
┌──────────────────┐                   ┌───────────────────┐
│ Feature Matching │                   │ Embedding Vector  │
│ Engine (SQL)     │                   │ Engine (pgvector) │
│ • Genres         │      RESULTS      │ • OpenAI Embed API│
│ • Keyword Tags   │ ────────────────► │ • Semantic Search │
│ • Mood Mapping   │                   │ • Context Analysis│
└──────────────────┘                   └───────────────────┘
```
### 核心實作細節 (Smart Routing):
```text
def decide_recommendation_engine(user_input: str, mood_labels: list, genres: list):
    # 動態評估特徵權重，決定檢索策略
    feature_score = calculate_feature_richness(mood_labels, genres, extract_keywords(user_input))
    
    if feature_score >= FEATURE_THRESHOLD:
        return feature_matching_engine(mood_labels, genres)
    return embedding_vector_engine(user_input)
```
## Tech Stack
### Backend & Database
* **Framework**: FastAPI, Uvicorn (Asynchronous RESTful APIs)
* **Database**: Neon Serverless PostgreSQL, SQLAlchemy 2.0 (ORM), Alembic (Migration)
* **AI / Search**: OpenAI API (Embeddings), pgvector (Vector Database extension)
* **Caching & Auth**: Redis 5.0, JWT, PassLib<br>

### Frontend
* **Framework**: Next.js 16 (React 19), TypeScript
* **State Management & Data Fetching**: Zustand, ky
* **Styling**: Tailwind CSS 4.x

## Core Features
* **AI Semantic Search (語義檢索)**: 支援如「週末想和家人看點溫馨感人的電影」等自然語言輸入，系統透過 70+ 種情緒標籤映射表（SSOT）與語義向量空間，精準捕捉隱含的電影類型與避雷點。
* **Social Watchlists (片單社交)**: 實作高效能的關聯資料庫庫結構，支援建立、分享與公開使用者的 Top 10 片單與 Watchlist，並內建好友系統與品味匹配演算法。
* **Gamified Assessment (互動式品味分析)**: 設計多維度問卷系統，收集並分析使用者的觀影偏好，產生個人化報表並作為推薦引擎的冷啟動權重參考。


## Quick Start
### 1. Clone Repository & Setup Environment
```text
git clone [https://github.com/VictorHo1114/MovieIn_bmadProject.git](https://github.com/VictorHo1114/MovieIn_bmadProject.git)
cd MovieIn_bmadProject/backend

# Initialize virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```
### 2. Configure Environment Variables (.env)
```text
DATABASE_URL=postgresql://user:password@localhost/moviein
SECRET_KEY=your_secret_key
OPENAI_API_KEY=your_openai_api_key
```
### 3. Run Migrations & Start Services
```text
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```
## Documentation
Check out formalDocs for more details. 
## Contact
**Victor Ho**<br>
**Email**: victort509dm@gmail.com<br>
**GitHub**: @VictorHo1114<br>
