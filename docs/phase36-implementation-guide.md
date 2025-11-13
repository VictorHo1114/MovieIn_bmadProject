# Phase 3.6: Embedding-First 實現指南

## 快速導航

📋 **決策文檔**：[phase36-decisions.md](./phase36-decisions.md)  
📚 **完整架構**：[recommendation-system-architecture.md](./recommendation-system-architecture.md)  
🎯 **本文目的**：實現步驟清單與代碼框架

---

## 實現順序

### 🚀 Priority 0: 基礎函數（1-2 天）

#### 1.1 `generate_embedding_query()`

**位置**：`backend/app/services/embedding_query_generator.py` (新建)

```python
"""
Embedding Query 生成器 - Phase 3.6
處理三種輸入情境，生成最佳 Embedding 查詢文本
"""

from typing import List, Optional, Dict

def generate_embedding_query(
    natural_query: str,
    mood_labels: List[str],
    mood_relationship: Optional[Dict] = None
) -> str:
    """
    三情境處理：
    1. 僅 NL → 直接使用
    2. 僅 Mood → 關係感知模板
    3. NL + Mood → 分離處理（NL 優先）
    
    Args:
        natural_query: 用戶輸入的自然語言
        mood_labels: 英文 Mood Labels 列表
        mood_relationship: analyze_mood_combination() 的結果
    
    Returns:
        用於 Embedding 的查詢文本
    """
    has_nl = bool(natural_query.strip())
    has_moods = bool(mood_labels)
    
    # 情境 1: 僅自然語言
    if has_nl and not has_moods:
        return natural_query
    
    # 情境 3: 兩者皆有（分離處理）
    if has_nl and has_moods:
        # TODO: 實現衝突檢測
        # 目前策略：NL 優先
        return natural_query
    
    # 情境 2: 僅 Mood Labels
    if not has_nl and has_moods:
        if mood_relationship is None:
            mood_relationship = analyze_mood_combination(mood_labels)
        
        return generate_mood_template(mood_labels, mood_relationship)
    
    # Fallback
    return "popular movies"


def generate_mood_template(
    mood_labels: List[str],
    relationship: Dict
) -> str:
    """
    根據 Mood 關係生成模板
    
    Args:
        mood_labels: ["sad", "healing"]
        relationship: {"type": "journey", "template": "..."}
    
    Returns:
        生成的查詢文本
    """
    rel_type = relationship.get("type", "simple")
    
    if rel_type == "journey":
        # 轉變關係
        # TODO: 從 MOOD_RELATIONSHIP_MATRIX 取得模板
        return f"A story about transformation from {mood_labels[0]} to {mood_labels[1]}"
    
    elif rel_type == "paradox":
        # 矛盾關係
        return f"A movie that blends {mood_labels[0]} with {mood_labels[1]}"
    
    elif rel_type == "intensification":
        # 強化關係
        return f"A deeply {mood_labels[0]} and {mood_labels[1]} story"
    
    else:
        # Fallback: 簡單拼接
        return f"A {' and '.join(mood_labels)} movie"


# TODO: 實現衝突檢測
def detect_sentiment_conflict(
    natural_query: str,
    mood_labels: List[str]
) -> bool:
    """
    檢測 NL 與 Mood 是否衝突
    
    簡單版本：基於關鍵詞
    未來版本：基於 Embedding 語義距離
    """
    pass
```

**測試案例**：
```python
# test_embedding_query_generator.py

def test_scenario_1_nl_only():
    result = generate_embedding_query(
        natural_query="難過的時候適合看什麼",
        mood_labels=[]
    )
    assert result == "難過的時候適合看什麼"

def test_scenario_2_mood_only():
    result = generate_embedding_query(
        natural_query="",
        mood_labels=["sad", "healing"]
    )
    assert "transformation" in result.lower()
    assert "sad" in result.lower()
    assert "healing" in result.lower()

def test_scenario_3_both():
    result = generate_embedding_query(
        natural_query="溫暖治癒的故事",
        mood_labels=["sad", "dark"]
    )
    # NL 優先
    assert result == "溫暖治癒的故事"
```

---

#### 1.2 `analyze_mood_combination()`

**位置**：`backend/app/services/mood_analyzer.py` (新建)

```python
"""
Mood 組合分析器 - Phase 3.6
識別 Mood Labels 之間的語義關係
"""

from typing import List, Dict, Optional

# TODO: 建立完整的 MOOD_RELATIONSHIP_MATRIX
MOOD_RELATIONSHIP_MATRIX = {
    # Journey (轉變)
    ("sad", "healing"): {
        "type": "journey",
        "description": "Emotional transformation",
        "template": "A story about transformation from sadness to healing, emotional journey of recovery and hope"
    },
    ("dark", "uplifting"): {
        "type": "journey",
        "description": "From darkness to light",
        "template": "A narrative that moves from dark themes towards uplifting moments"
    },
    
    # Paradox (矛盾)
    ("dark", "lighthearted"): {
        "type": "paradox",
        "description": "Contrasting blend",
        "template": "A movie that blends dark themes with lighthearted moments"
    },
    
    # Intensification (強化)
    ("sad", "melancholy"): {
        "type": "intensification",
        "description": "Deep sadness",
        "template": "A deeply emotional and melancholic story"
    },
    
    # TODO: 新增 30+ 關係
}


def analyze_mood_combination(mood_labels: List[str]) -> Dict:
    """
    混合方法：Matrix 優先，Vector 補充
    
    Args:
        mood_labels: ["sad", "healing"]
    
    Returns:
        {
            "type": "journey" | "paradox" | "intensification" | "multi-faceted",
            "template": str,
            "confidence": "high" | "medium" | "low",
            "source": "matrix" | "vector" | "default"
        }
    """
    # 單一 Mood
    if len(mood_labels) <= 1:
        return {
            "type": "simple",
            "template": "simple",
            "confidence": "high",
            "source": "default"
        }
    
    # Phase 1: Matrix 查詢（優先）
    for (mood1, mood2), relationship in MOOD_RELATIONSHIP_MATRIX.items():
        if mood1 in mood_labels and mood2 in mood_labels:
            return {
                "type": relationship["type"],
                "template": relationship["template"],
                "confidence": "high",
                "source": "matrix"
            }
    
    # Phase 2: Vector 補充（TODO: 未來實現）
    # vector_result = analyze_by_semantic_vector(mood_labels)
    # if vector_result["confidence"] > 0.7:
    #     return vector_result
    
    # Fallback
    return {
        "type": "multi-faceted",
        "template": "complex",
        "confidence": "low",
        "source": "default"
    }


# TODO: 未來擴展
def analyze_by_semantic_vector(mood_labels: List[str]) -> Dict:
    """
    使用 Embedding 計算 Mood 之間的語義距離
    自動識別關係類型
    """
    pass
```

**數據建立任務**：
```python
# scripts/build_mood_relationship_matrix.py

"""
建立 MOOD_RELATIONSHIP_MATRIX
目標：50+ 對關係

優先級：
1. Journey: 10 對（sad→healing, dark→uplifting, etc.）
2. Paradox: 10 對（dark+lighthearted, sad+fun, etc.）
3. Intensification: 10 對（sad+melancholy, dark+gritty, etc.）
4. Multi-faceted: 20 對（複雜組合）
"""

PRIORITY_RELATIONSHIPS = [
    # Journey
    ("sad", "healing"),
    ("dark", "uplifting"),
    ("depressed", "hopeful"),
    ("lonely", "connected"),
    ("lost", "found"),
    # ... more
]
```

---

#### 1.3 `embedding_similarity_search()`

**位置**：`backend/app/services/embedding_service.py` (擴展現有)

```python
"""
Embedding 服務 - Phase 3.6 擴展
新增全庫語義搜索功能
"""

import json
from typing import List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text
import openai

async def embedding_similarity_search(
    query_text: str,
    db_session: Session,
    top_k: int = 300
) -> List[Dict]:
    """
    全庫 Embedding 語義搜索
    
    Args:
        query_text: "難過的時候適合看什麼" 或生成的模板
        db_session: Database session
        top_k: 返回前 K 個候選（預設 300）
    
    Returns:
        [
            {
                "tmdb_id": 668482,
                "embedding_score": 0.78,
                "embedding_text": "完美的日子..."
            },
            ...
        ]
    """
    # Step 1: 生成查詢 Embedding
    query_embedding = await generate_embedding(query_text)
    
    # Step 2: 從 DB 讀取所有電影 Embedding
    query_sql = text("""
        SELECT tmdb_id, embedding, embedding_text
        FROM movie_vectors
        WHERE embedding IS NOT NULL
    """)
    
    result = db_session.execute(query_sql)
    
    # Step 3: 計算相似度
    similarities = []
    for row in result:
        tmdb_id, movie_emb, emb_text = row
        
        # 處理 JSONB 格式
        if isinstance(movie_emb, str):
            movie_emb = json.loads(movie_emb)
        
        # Cosine Similarity
        sim_score = cosine_similarity(query_embedding, movie_emb)
        
        similarities.append({
            "tmdb_id": tmdb_id,
            "embedding_score": sim_score,
            "embedding_text": emb_text
        })
    
    # Step 4: 排序並返回 Top K
    similarities.sort(key=lambda x: x["embedding_score"], reverse=True)
    return similarities[:top_k]


async def generate_embedding(text: str) -> List[float]:
    """
    生成單個文本的 Embedding
    """
    response = await openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    計算 Cosine Similarity
    """
    from math import sqrt
    
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sqrt(sum(a * a for a in vec1))
    norm2 = sqrt(sum(b * b for b in vec2))
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)
```

**性能優化（未來）**：
```python
# 批次優化
async def embedding_similarity_search_batch(
    query_texts: List[str],
    db_session: Session,
    top_k: int = 300
) -> Dict[str, List[Dict]]:
    """
    批次查詢多個 Embedding
    減少 DB 連接次數
    """
    pass

# pgvector 優化（當電影數量 > 10,000 時）
async def embedding_similarity_search_pgvector(
    query_text: str,
    db_session: Session,
    top_k: int = 300
) -> List[Dict]:
    """
    使用 pgvector 擴展的近似最近鄰搜索（ANN）
    顯著提升大規模搜索性能
    """
    pass
```

---

### 🎯 Priority 1: 過濾與分類（2-3 天）

#### 2.1 `tiered_feature_filtering()` (重構)

**位置**：`backend/app/services/simple_recommend.py` (重構現有)

```python
def tiered_feature_filtering(
    embedding_candidates: List[Dict],  # 從 Embedding 來的 300 個
    extracted_features: Dict,          # Step 1 提取的 features
    db_session: Session,
    target_count: int = 150
) -> List[Dict]:
    """
    三層漸進式過濾 - Phase 3.6 重構版本
    
    角色變化：
    - Phase 3.5: 生成候選（主引擎）
    - Phase 3.6: 過濾候選（輔助驗證）
    
    Args:
        embedding_candidates: [{"tmdb_id": 668482, "embedding_score": 0.78}, ...]
        extracted_features: {
            "keywords": [...],
            "mood_tags": [...],
            "genres": [...],
            "year_ranges": [...]
        }
        target_count: 目標過濾後數量
    
    Returns:
        過濾後的電影列表，附加 match_ratio 和 feature_score
    """
    candidate_ids = [c["tmdb_id"] for c in embedding_candidates]
    
    # 從 DB 讀取候選電影的完整資訊
    movies = fetch_movies_by_ids(candidate_ids, db_session)
    
    # 計算每部電影的 Feature Match
    for movie in movies:
        match_info = calculate_feature_match(
            movie,
            extracted_features["keywords"],
            extracted_features["mood_tags"],
            extracted_features["genres"],
            extracted_features["year_ranges"]
        )
        movie["match_ratio"] = match_info["match_ratio"]
        movie["match_count"] = match_info["match_count"]
        movie["feature_score"] = match_info["feature_score"]
    
    # 三層過濾
    tier1 = [m for m in movies if m["match_ratio"] >= 0.8]
    if len(tier1) >= target_count:
        return tier1[:target_count]
    
    tier2 = [m for m in movies if 0.5 <= m["match_ratio"] < 0.8]
    if len(tier1) + len(tier2) >= target_count:
        return (tier1 + tier2)[:target_count]
    
    tier3 = [m for m in movies if m["match_ratio"] < 0.5]
    return (tier1 + tier2 + tier3)[:target_count]


def calculate_feature_match(
    movie: Dict,
    keywords: List[str],
    mood_tags: List[str],
    genres: List[str],
    year_ranges: List[tuple]
) -> Dict:
    """
    計算單部電影的 Feature Match
    
    Returns:
        {
            "match_ratio": 0.65,
            "match_count": 5,
            "total_features": 8,
            "feature_score": 45.2
        }
    """
    matched_count = 0
    total_features = len(keywords) + len(mood_tags) + len(genres)
    
    # Keyword 匹配
    movie_keywords = movie.get("keywords", [])
    keyword_matches = len(set(keywords) & set(movie_keywords))
    matched_count += keyword_matches
    
    # Mood Tag 匹配
    movie_moods = movie.get("mood_tags", [])
    mood_matches = len(set(mood_tags) & set(movie_moods))
    matched_count += mood_matches
    
    # Genre 匹配
    movie_genres = movie.get("genres", [])
    genre_matches = len(set(genres) & set(movie_genres))
    matched_count += genre_matches
    
    # Match Ratio
    match_ratio = matched_count / total_features if total_features > 0 else 0.0
    
    # Feature Score（簡化版）
    feature_score = (
        keyword_matches * 20 +
        mood_matches * 15 +
        genre_matches * 10 +
        (movie.get("vote_average", 5) - 5) * 3 +
        (movie.get("popularity", 0) / 1000) * 2
    )
    
    return {
        "match_ratio": match_ratio,
        "match_count": matched_count,
        "total_features": total_features,
        "feature_score": feature_score
    }
```

---

#### 2.2 `classify_to_3quadrant()`

**位置**：`backend/app/services/simple_recommend.py`

```python
def classify_to_3quadrant(
    embedding_score: float,
    match_ratio: float
) -> str:
    """
    三象限分類 - Phase 3.6
    
    閾值：
    - high_embedding = 0.60 (提高！)
    - high_match = 0.40 (降低！)
    
    Returns:
        "q1_perfect_match" | "q2_semantic_discovery" | "q4_fallback"
    """
    from backend.app.config import PHASE36_CONFIG
    
    high_emb_threshold = PHASE36_CONFIG["quadrant_thresholds"]["high_embedding"]
    high_match_threshold = PHASE36_CONFIG["quadrant_thresholds"]["high_match"]
    
    high_emb = embedding_score >= high_emb_threshold
    high_match = match_ratio >= high_match_threshold
    
    if high_emb and high_match:
        return "q1_perfect_match"
    elif high_emb and not high_match:
        return "q2_semantic_discovery"
    else:
        return "q4_fallback"


def calculate_3quadrant_score(
    quadrant: str,
    embedding_score: float,
    feature_score: float,
    match_ratio: float
) -> float:
    """
    計算三象限最終分數
    
    Args:
        quadrant: "q1_perfect_match" | "q2_semantic_discovery" | "q4_fallback"
        embedding_score: 0.78
        feature_score: 45.2
        match_ratio: 0.65
    
    Returns:
        final_score: 63.92
    """
    from backend.app.config import PHASE36_CONFIG
    
    weights = PHASE36_CONFIG["quadrant_weights"][quadrant]
    
    final_score = (
        embedding_score * 100 * weights["embedding"] +
        feature_score * weights["feature"] +
        match_ratio * 100 * weights["match_ratio"]
    )
    
    return final_score


def sort_by_quadrant_and_embedding(movies: List[Dict]) -> List[Dict]:
    """
    混合排序策略：
    1. 象限優先（Q1 > Q2 > Q4）
    2. 象限內按 Embedding Score 降序
    """
    quadrant_priority = {
        "q1_perfect_match": 1,
        "q2_semantic_discovery": 2,
        "q4_fallback": 3
    }
    
    return sorted(
        movies,
        key=lambda x: (
            quadrant_priority.get(x["quadrant"], 999),
            -x.get("embedding_score", 0)
        )
    )
```

---

### 🔧 Priority 2: 整合與配置（1 天）

#### 3.1 配置檔案

**位置**：`backend/app/config.py` (新增)

```python
"""
Phase 3.6 配置
"""

PHASE36_CONFIG = {
    # Embedding Query 生成
    "embedding_query": {
        "conflict_handling": "separate",
        "template_type": "relationship-aware"
    },
    
    # 三象限閾值
    "quadrant_thresholds": {
        "high_embedding": 0.60,
        "high_match": 0.40
    },
    
    # 三象限權重
    "quadrant_weights": {
        "q1_perfect_match": {
            "embedding": 0.50,
            "feature": 0.30,
            "match_ratio": 0.20
        },
        "q2_semantic_discovery": {
            "embedding": 0.70,
            "feature": 0.10,
            "match_ratio": 0.20
        },
        "q4_fallback": {
            "embedding": 0.30,
            "feature": 0.40,
            "match_ratio": 0.30
        }
    },
    
    # 候選數量
    "embedding_top_k": 300,
    "feature_filter_k": 150,
    "final_top_k": 10,
    
    # 功能開關
    "enable_3quadrant_logic": True,
    "enable_mood_relationship": True,
    "enable_diversity_filter": True
}
```

---

#### 3.2 主推薦函數

**位置**：`backend/app/services/simple_recommend.py`

```python
async def recommend_movies_embedding_first(
    natural_query: str,
    mood_buttons: List[str],
    genre_buttons: List[str],
    era_buttons: List[str],
    db_session: Session
) -> List[Dict]:
    """
    Phase 3.6: Embedding-First 完整推薦流程
    """
    from backend.app.services.enhanced_feature_extraction import enhanced_feature_extraction
    from backend.app.services.embedding_query_generator import generate_embedding_query
    from backend.app.services.mood_analyzer import analyze_mood_combination
    from backend.app.services.embedding_service import embedding_similarity_search
    
    # Step 1: 增強特徵提取
    extracted = enhanced_feature_extraction(
        natural_query, mood_buttons, genre_buttons, era_buttons, db_session
    )
    
    # Step 2: Embedding Query 生成
    mood_labels = extracted.get("mood_labels", [])
    has_nl = bool(natural_query.strip())
    has_moods = bool(mood_labels)
    
    # 生成查詢文本
    if has_moods:
        mood_relationship = analyze_mood_combination(mood_labels)
    else:
        mood_relationship = None
    
    query_text = generate_embedding_query(
        natural_query=natural_query,
        mood_labels=mood_labels,
        mood_relationship=mood_relationship
    )
    
    # Step 3: Embedding 全庫搜索
    embedding_candidates = await embedding_similarity_search(
        query_text=query_text,
        db_session=db_session,
        top_k=PHASE36_CONFIG["embedding_top_k"]
    )
    
    # Step 4: 三層漸進式過濾
    filtered_movies = tiered_feature_filtering(
        embedding_candidates=embedding_candidates,
        extracted_features=extracted,
        db_session=db_session,
        target_count=PHASE36_CONFIG["feature_filter_k"]
    )
    
    # Step 5: 合併 Embedding Score
    embedding_score_map = {
        c["tmdb_id"]: c["embedding_score"] for c in embedding_candidates
    }
    
    for movie in filtered_movies:
        movie["embedding_score"] = embedding_score_map.get(movie["tmdb_id"], 0.0)
    
    # Step 6: 三象限分類與評分
    for movie in filtered_movies:
        quadrant = classify_to_3quadrant(
            embedding_score=movie["embedding_score"],
            match_ratio=movie["match_ratio"]
        )
        movie["quadrant"] = quadrant
        
        movie["final_score"] = calculate_3quadrant_score(
            quadrant=quadrant,
            embedding_score=movie["embedding_score"],
            feature_score=movie["feature_score"],
            match_ratio=movie["match_ratio"]
        )
    
    # Step 7: 象限內 Embedding 排序
    sorted_movies = sort_by_quadrant_and_embedding(filtered_movies)
    
    # Step 8: 多樣性過濾（可選）
    if PHASE36_CONFIG.get("enable_diversity_filter"):
        # TODO: 實現多樣性過濾
        pass
    
    # 返回 Top 10
    return sorted_movies[:PHASE36_CONFIG["final_top_k"]]
```

---

### ✅ Priority 3: 測試（2-3 天）

#### 4.1 單元測試

**檔案結構**：
```
backend/tests/
├── test_embedding_query_generator.py    (情境 1/2/3)
├── test_mood_analyzer.py                 (Matrix + Vector)
├── test_embedding_similarity_search.py   (全庫搜索)
├── test_3quadrant_logic.py               (分類 + 評分 + 排序)
└── test_phase36_integration.py           (端到端)
```

**關鍵測試案例**：

```python
# test_phase36_integration.py

import pytest
from backend.app.services.simple_recommend import recommend_movies_embedding_first

@pytest.mark.asyncio
async def test_scenario_1_nl_only(db_session):
    """情境 1: 僅自然語言"""
    result = await recommend_movies_embedding_first(
        natural_query="難過的時候適合看什麼",
        mood_buttons=[],
        genre_buttons=[],
        era_buttons=[],
        db_session=db_session
    )
    
    assert len(result) == 10
    assert all("quadrant" in m for m in result)
    assert all("embedding_score" in m for m in result)
    # Q1 或 Q2 應該在前面
    assert result[0]["quadrant"] in ["q1_perfect_match", "q2_semantic_discovery"]
    assert result[0]["embedding_score"] >= 0.6


@pytest.mark.asyncio
async def test_scenario_2_mood_only(db_session):
    """情境 2: 僅 Mood Labels (Journey)"""
    result = await recommend_movies_embedding_first(
        natural_query="",
        mood_buttons=["sad", "healing"],
        genre_buttons=[],
        era_buttons=[],
        db_session=db_session
    )
    
    # 驗證使用了關係感知模板
    # 可通過 logging 或返回 metadata 驗證
    assert len(result) == 10


@pytest.mark.asyncio
async def test_scenario_3_conflict(db_session):
    """情境 3: NL + Mood 衝突"""
    result = await recommend_movies_embedding_first(
        natural_query="溫暖治癒的故事",
        mood_buttons=["sad", "dark"],
        genre_buttons=[],
        era_buttons=[],
        db_session=db_session
    )
    
    # NL 優先用於查詢
    # 推薦結果應偏向 "healing" 而非 "dark"
    assert len(result) == 10


def test_3quadrant_classification():
    """三象限分類邏輯"""
    assert classify_to_3quadrant(0.75, 0.65) == "q1_perfect_match"
    assert classify_to_3quadrant(0.70, 0.30) == "q2_semantic_discovery"
    assert classify_to_3quadrant(0.50, 0.70) == "q4_fallback"
    assert classify_to_3quadrant(0.30, 0.30) == "q4_fallback"


def test_quadrant_sorting():
    """象限排序測試"""
    movies = [
        {"quadrant": "q2_semantic_discovery", "embedding_score": 0.75},
        {"quadrant": "q1_perfect_match", "embedding_score": 0.80},
        {"quadrant": "q1_perfect_match", "embedding_score": 0.70},
        {"quadrant": "q4_fallback", "embedding_score": 0.55},
        {"quadrant": "q2_semantic_discovery", "embedding_score": 0.68},
    ]
    
    sorted_movies = sort_by_quadrant_and_embedding(movies)
    
    # 驗證排序
    assert sorted_movies[0]["quadrant"] == "q1_perfect_match"
    assert sorted_movies[0]["embedding_score"] == 0.80
    assert sorted_movies[1]["embedding_score"] == 0.70
    assert sorted_movies[2]["quadrant"] == "q2_semantic_discovery"
```

---

## 實現時間表

```
Week 1:
- Day 1-2: P0 基礎函數（generate_embedding_query, analyze_mood_combination）
- Day 3-4: P0 搜索與過濾（embedding_similarity_search, tiered_feature_filtering）
- Day 5: P1 分類系統（classify_to_3quadrant, calculate_3quadrant_score）

Week 2:
- Day 1: P2 配置與整合（config, recommend_movies_embedding_first）
- Day 2-4: P3 測試（單元測試 + 整合測試）
- Day 5: Bug 修復與優化

Week 3:
- Day 1-3: 數據建立（MOOD_RELATIONSHIP_MATRIX 50+ 對）
- Day 4-5: A/B 測試準備與灰度發布
```

---

## 檢查清單

### 開發檢查

- [ ] `generate_embedding_query()` 實現
- [ ] `analyze_mood_combination()` 實現
- [ ] `embedding_similarity_search()` 實現
- [ ] `tiered_feature_filtering()` 重構
- [ ] `classify_to_3quadrant()` 實現
- [ ] `calculate_3quadrant_score()` 實現
- [ ] `sort_by_quadrant_and_embedding()` 實現
- [ ] `recommend_movies_embedding_first()` 整合
- [ ] MOOD_RELATIONSHIP_MATRIX 建立（50+ 對）
- [ ] PHASE36_CONFIG 配置

### 測試檢查

- [ ] 情境 1 測試通過
- [ ] 情境 2 測試通過
- [ ] 情境 3 測試通過
- [ ] 三象限分類測試通過
- [ ] 排序邏輯測試通過
- [ ] 端到端測試通過
- [ ] 性能測試（延遲 < 300ms）
- [ ] 成本驗證（< $0.00003 per query）

### 文檔檢查

- [x] phase36-decisions.md 完成
- [x] recommendation-system-architecture.md 更新
- [x] phase36-implementation-guide.md 完成
- [ ] API 文檔更新
- [ ] 前端文檔更新

---

## 快速啟動

```bash
# 1. 創建新的 service 檔案
cd backend/app/services
touch embedding_query_generator.py
touch mood_analyzer.py

# 2. 執行測試
cd backend
pytest tests/test_phase36_integration.py -v

# 3. 運行開發伺服器
python -m uvicorn app.main:app --reload

# 4. 驗證 API
curl -X POST http://localhost:8000/api/recommend \
  -H "Content-Type: application/json" \
  -d '{
    "natural_query": "難過的時候適合看什麼",
    "mood_buttons": [],
    "genre_buttons": [],
    "era_buttons": []
  }'
```

---

**文檔版本**：1.0  
**最後更新**：2025-11-13  
**作者**：Winston  
**狀態**：✅ 實現指南完成