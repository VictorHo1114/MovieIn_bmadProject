# backend/app/services/simple_recommend.py
"""
Phase 3.6: Embedding-First 推薦服務

架構：
1. Embedding Query Generation (智能查詢生成)
2. Embedding Similarity Search (全庫語義搜索，300 候選)
3. Tiered Feature Filtering (三層漸進式過濾，150 候選)
4. 3-Quadrant Classification (Q1 完美 / Q2 語義發現 / Q4 候補)
5. Dynamic Score Calculation (動態權重評分)
6. Mixed Sorting (象限優先 + 分數排序)
7. Smart Selection (Top N 保證 + 隨機池多樣性)

參考文檔：
- docs/phase36-decisions.md
- docs/phase36-implementation-guide.md
- app/services/phase36_config.py
"""
import os
import random
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

# ============================================
# Phase 3.6: Embedding-First 推薦系統
# 配置檔案: phase36_config.py
# ============================================

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# 英文类型到简体中文的映射（匹配数据库中的 genres）
GENRE_EN_TO_ZH = {
    "Action": "动作",
    "Adventure": "冒险",
    "Animation": "动画",
    "Comedy": "喜剧",
    "Crime": "犯罪",
    "Documentary": "纪录",
    "Drama": "剧情",
    "Family": "家庭",
    "Fantasy": "奇幻",
    "History": "历史",
    "Horror": "恐怖",
    "Music": "音乐",
    "Mystery": "悬疑",
    "Romance": "爱情",
    "Science Fiction": "科幻",
    "Thriller": "惊悚",
    "War": "战争",
    "Western": "西部"
}

# ============================================
# 基礎工具函數
# ============================================ 
# 新系統優勢：
# 1. 精確匹配：直接從 DB 提取 keywords，不需要中英映射
# 2. Mood 映射：MOOD_LABEL_TO_DB_TAGS 提供精準的 mood → tags/keywords 映射
# 3. 規則推斷：自動推斷年份、語言等參數
# ============================================

# ============================================================================
# Phase 3.6: 核心工具函數
# ============================================================================

def calculate_match_ratio(
    movie: Dict,
    keywords: List[str],
    mood_tags: List[str],
    genres: List[str]
) -> float:
    """
    計算電影符合用戶要求的比例（0.0-1.0）
    
    Match Ratio = (matched_features / total_required_features)
    
    例子：
    - 用戶要求: 5 個 moods, 3 個 genres → total = 8
    - 電影符合: 4 個 moods, 2 個 genres → matched = 6
    - Match Ratio = 6/8 = 0.75 (75%)
    """
    total_required = 0
    matched = 0
    
    # Keywords 匹配
    if keywords:
        total_required += len(keywords)
        movie_keywords = movie.get('keywords', []) or []
        movie_keywords_lower = [k.lower() for k in movie_keywords] if isinstance(movie_keywords, list) else []
        for kw in keywords:
            if kw.lower() in movie_keywords_lower:
                matched += 1
    
    # Mood Tags 匹配
    if mood_tags:
        total_required += len(mood_tags)
        movie_moods = movie.get('mood_tags', []) or []
        movie_moods_lower = [m.lower() for m in movie_moods] if isinstance(movie_moods, list) else []
        for mood in mood_tags:
            if mood.lower() in movie_moods_lower:
                matched += 1
    
    # Genres 匹配
    if genres:
        total_required += len(genres)
        movie_genres = movie.get('genres', []) or []
        genres_zh = [GENRE_EN_TO_ZH.get(g, g) for g in genres]
        for genre in genres_zh:
            if genre in movie_genres:
                matched += 1
    
    if total_required == 0:
        return 1.0  # 沒有要求時，全部符合
    
    return matched / total_required


async def tiered_feature_filtering(
    embedding_candidates: List[Dict],
    keywords: List[str],
    mood_tags: List[str],
    genres: List[str],
    exclude_genres: List[str] = None,
    year_range: tuple = None,
    year_ranges: List[List[int]] = None,
    min_rating: float = None,
    target_count: int = 150,
    randomness: float = 0.3
) -> List[Dict]:
    """
    Phase 3.6: Tiered Feature Filtering
    
    🔄 角色轉變：從候選生成 → 候選過濾
    
    Phase 2/3.5 (舊角色):
        - Input: 用戶特徵（keywords, moods, genres）
        - Output: 從 DB 生成候選電影
        - 引擎: SQL Feature Matching (Primary)
    
    Phase 3.6 (新角色):
        - Input: Embedding 搜索結果（300 candidates）+ 用戶特徵
        - Output: 過濾後的候選電影（150 candidates）
        - 引擎: Feature Filtering (Secondary)
    
    📊 過濾策略（三層漸進）:
        - Tier 1 (嚴格): Match Ratio >= 80%
        - Tier 2 (平衡): Match Ratio >= 50%
        - Tier 3 (寬鬆): Match Ratio >= 0% (保底)
    
    🎯 過濾條件:
        - Hard Filters: exclude_genres, year_range, min_rating（強制過濾）
        - Soft Filters: keywords, mood_tags, genres（計算 match_ratio）
    
    Args:
        embedding_candidates: Embedding 搜索結果（300 部，已有 embedding_score）
        keywords: 用戶選擇的 keywords
        mood_tags: 用戶選擇的 mood tags
        genres: 用戶選擇的 genres
        exclude_genres: 排除的類型
        year_range: 年份範圍
        year_ranges: 多個年份範圍
        min_rating: 最低評分
        target_count: 目標返回數量（預設 150）
        randomness: 隨機性參數
    
    Returns:
        List[Dict]: 過濾後的候選電影，包含：
            - 原有的 embedding_score
            - 新增的 match_ratio, feature_score
    
    Example:
        >>> embedding_results = await embedding_similarity_search(...)  # 300 candidates
        >>> filtered = await tiered_feature_filtering(
        ...     embedding_candidates=embedding_results,
        ...     keywords=["love", "family"],
        ...     mood_tags=["heartwarming", "emotional"],
        ...     genres=["Drama"],
        ...     target_count=150
        ... )
        >>> len(filtered)  # 150
        >>> filtered[0]["match_ratio"]  # 0.85
        >>> filtered[0]["embedding_score"]  # 0.82 (preserved)
    """
    print(f"\n🔧 [Phase 3.6 Feature Filtering] 過濾 Embedding 候選")
    print(f"   - Input: {len(embedding_candidates)} candidates (from Embedding Search)")
    print(f"   - Features: {len(keywords)} keywords, {len(mood_tags)} moods, {len(genres)} genres")
    print(f"   - Target: {target_count} candidates")
    print(f"{'-'*70}")
    
    # Step 1: Hard Filters（強制過濾）
    print(f"\n[1/3] 應用 Hard Filters...")
    filtered_candidates = embedding_candidates.copy()
    
    # 過濾：genres（用戶選擇的類型，必須符合）
    if genres:
        before_count = len(filtered_candidates)
        # 支援繁體/簡體中文
        from app.services.enhanced_feature_extraction import GENRE_TRADITIONAL_TO_SIMPLIFIED
        
        # 將繁體轉簡體（如果需要）
        genres_simplified = []
        for g in genres:
            simplified = GENRE_TRADITIONAL_TO_SIMPLIFIED.get(g, g)
            genres_simplified.append(simplified)
        
        filtered_candidates = [
            m for m in filtered_candidates
            if any(g in m.get("genres", []) for g in genres_simplified)
        ]
        print(f"   - Genres Filter {genres} → {genres_simplified}: {before_count} → {len(filtered_candidates)} (-{before_count - len(filtered_candidates)})")
    
    # 過濾：exclude_genres
    if exclude_genres:
        before_count = len(filtered_candidates)
        filtered_candidates = [
            m for m in filtered_candidates
            if not any(g in m.get("genres", []) for g in exclude_genres)
        ]
        print(f"   - Exclude Genres: {before_count} → {len(filtered_candidates)} (-{before_count - len(filtered_candidates)})")
    
    # 過濾：year_range
    if year_range:
        before_count = len(filtered_candidates)
        min_year, max_year = year_range
        filtered_candidates = [
            m for m in filtered_candidates
            if _check_year_in_range(m.get("release_date"), min_year, max_year)
        ]
        print(f"   - Year Range [{min_year}, {max_year}]: {before_count} → {len(filtered_candidates)} (-{before_count - len(filtered_candidates)})")
    
    # 過濾：year_ranges（多個年份範圍）
    if year_ranges:
        before_count = len(filtered_candidates)
        filtered_candidates = [
            m for m in filtered_candidates
            if any(_check_year_in_range(m.get("release_date"), yr[0], yr[1]) for yr in year_ranges)
        ]
        print(f"   - Year Ranges: {before_count} → {len(filtered_candidates)} (-{before_count - len(filtered_candidates)})")
    
    # 過濾：min_rating
    if min_rating is not None:
        before_count = len(filtered_candidates)
        filtered_candidates = [
            m for m in filtered_candidates
            if m.get("vote_average", 0) >= min_rating
        ]
        print(f"   - Min Rating >= {min_rating}: {before_count} → {len(filtered_candidates)} (-{before_count - len(filtered_candidates)})")
    
    print(f"   ✓ Hard Filters 完成: {len(embedding_candidates)} → {len(filtered_candidates)}")
    
    if not filtered_candidates:
        print(f"   ⚠️  Hard Filters 過濾後無候選，返回空列表")
        return []
    
    # Step 2: 計算 Match Ratio（Soft Filters）
    print(f"\n[2/3] 計算 Match Ratio...")
    
    for movie in filtered_candidates:
        # 計算 match_ratio（與原 tiered_feature_matching 相同邏輯）
        movie['match_ratio'] = calculate_match_ratio(
            movie, keywords, mood_tags, genres
        )
        movie['match_count'] = int(movie['match_ratio'] * (len(keywords) + len(mood_tags) + len(genres)))
        movie['total_features'] = len(keywords) + len(mood_tags) + len(genres)
    
    # Step 3: 三層漸進過濾
    print(f"\n[3/3] 三層漸進過濾...")
    
    # Tier 1: Match Ratio >= 80%
    tier1_results = [m for m in filtered_candidates if m['match_ratio'] >= 0.8]
    tier1_results.sort(key=lambda x: (x['match_ratio'], x['embedding_score']), reverse=True)
    
    print(f"   📍 Tier 1 (>=80%): {len(tier1_results)} candidates")
    if tier1_results:
        top = tier1_results[0]
        print(f"      - Top: {top['title'][:40]:40s} - MR:{top['match_ratio']:.2f}, ES:{top['embedding_score']:.3f}")
    
    if len(tier1_results) >= target_count:
        results = tier1_results[:target_count]
        print(f"   🎉 Tier 1 已足夠，返回 {len(results)} candidates")
        return results
    
    # Tier 2: Match Ratio >= 50%
    tier2_results = [m for m in filtered_candidates if 0.5 <= m['match_ratio'] < 0.8]
    tier2_results.sort(key=lambda x: (x['match_ratio'], x['embedding_score']), reverse=True)
    
    print(f"   📍 Tier 2 (50-79%): {len(tier2_results)} candidates")
    
    combined = tier1_results + tier2_results
    combined.sort(key=lambda x: (x['match_ratio'], x['embedding_score']), reverse=True)
    
    if len(combined) >= target_count:
        results = combined[:target_count]
        print(f"   🎉 Tier 1+2 已足夠，返回 {len(results)} candidates")
        print(f"      (Tier 1: {len(tier1_results)}, Tier 2: {len(results) - len(tier1_results)})")
        return results
    
    # Tier 3: Match Ratio >= 0% (保底)
    tier3_results = [m for m in filtered_candidates if m['match_ratio'] < 0.5]
    tier3_results.sort(key=lambda x: x['embedding_score'], reverse=True)
    
    print(f"   📍 Tier 3 (<50%): {len(tier3_results)} candidates")
    
    final_results = tier1_results + tier2_results + tier3_results
    final_results = final_results[:target_count]
    
    print(f"\n   🎉 返回 {len(final_results)} candidates")
    print(f"      (Tier 1: {len(tier1_results)}, Tier 2: {len(tier2_results)}, Tier 3: {len(final_results) - len(tier1_results) - len(tier2_results)})")
    print(f"{'-'*70}\n")
    
    return final_results


def _check_year_in_range(release_date, min_year: int, max_year: int) -> bool:
    """檢查 release_date 是否在年份範圍內"""
    if not release_date:
        return False
    
    # 處理 datetime.date 或 string
    if hasattr(release_date, 'year'):
        year = release_date.year
    elif isinstance(release_date, str) and len(release_date) >= 4:
        try:
            year = int(release_date[:4])
        except:
            return False
    else:
        return False
    
    return min_year <= year <= max_year


# ============================================================================
# Phase 3.6: 三象限分類與評分
# ============================================================================

def classify_to_3quadrant(
    movie: Dict,
    embedding_score: float,
    config: Dict = None
) -> str:
    """
    Phase 3.6: 將電影分類到三個象限
    
    與 Phase 3.5 的差異：
    - Phase 3.5: 4 quadrants (Q1/Q2/Q3/Q4)
    - Phase 3.6: 3 quadrants (Q1/Q2/Q4) - 合併 Q2 和 Q3
    
    三象限定義：
    - Q1 (Perfect Match): High Embedding (>=0.60) AND High Match (>=0.40)
    - Q2 (Semantic Discovery): High Embedding (>=0.60) AND Low Match (<0.40)
    - Q4 (Fallback): Low Embedding (<0.60) - 不論 Match Ratio
    
    Args:
        movie: 電影資料（必須包含 match_ratio）
        embedding_score: Embedding 相似度分數 (0-1)
        config: Phase 3.6 配置參數
    
    Returns:
        quadrant: 'q1_perfect_match' | 'q2_semantic_discovery' | 'q4_fallback'
    
    Example:
        >>> movie = {"match_ratio": 0.75}
        >>> classify_to_3quadrant(movie, embedding_score=0.65)
        'q1_perfect_match'  # High E (0.65>=0.60) AND High M (0.75>=0.40)
        
        >>> classify_to_3quadrant(movie, embedding_score=0.65)
        'q2_semantic_discovery'  # High E (0.65>=0.60) AND Low M (0.30<0.40)
        
        >>> classify_to_3quadrant(movie, embedding_score=0.50)
        'q4_fallback'  # Low E (0.50<0.60)
    """
    # Phase 3.6 預設閾值（與 Phase 3.5 不同）
    default_thresholds = {
        "high_embedding": 0.60,  # ↑ from 0.45 (Phase 3.5)
        "high_match": 0.40       # ↓ from 0.50 (Phase 3.5)
    }
    
    cfg = config or {}
    thresholds = cfg.get("quadrant_thresholds", default_thresholds)
    
    match_ratio = movie.get('match_ratio', 0)
    
    high_embedding = embedding_score >= thresholds["high_embedding"]
    high_match = match_ratio >= thresholds["high_match"]
    
    # 三象限分類邏輯
    if high_embedding and high_match:
        return 'q1_perfect_match'
    elif high_embedding and not high_match:
        return 'q2_semantic_discovery'
    else:
        # Low Embedding → 直接歸類到 Q4（不論 Match Ratio）
        return 'q4_fallback'


def calculate_3quadrant_score(
    movie: Dict,
    embedding_score: float,
    quadrant: str,
    config: Dict = None
) -> float:
    """
    Phase 3.6: 根據三象限計算最終分數（動態權重）
    
    與 Phase 3.5 的差異：
    - Phase 3.5: feature_score 為主（40-50%）
    - Phase 3.6: embedding_score 為主（30-70%）
    
    三象限權重配置：
    - Q1 (Perfect Match): E:50%, F:30%, M:20% (平衡)
    - Q2 (Semantic Discovery): E:70%, F:10%, M:20% (Embedding 優先)
    - Q4 (Fallback): E:30%, F:40%, M:30% (Feature 優先)
    
    Args:
        movie: 電影資料（包含 match_ratio）
        embedding_score: Embedding 相似度分數 (0-1)
        quadrant: 象限類型
        config: Phase 3.6 配置參數
    
    Returns:
        final_score: 最終融合分數 (0-100)
    
    Example:
        >>> movie = {"match_ratio": 0.75}
        >>> calculate_3quadrant_score(
        ...     movie, 
        ...     embedding_score=0.65, 
        ...     quadrant='q1_perfect_match'
        ... )
        65.0  # = 0.65*100*0.50 + 0.75*100*0.20 + 0*0.30
    """
    # Phase 3.6 預設權重
    default_weights = {
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
    }
    
    cfg = config or {}
    all_weights = cfg.get("quadrant_weights", default_weights)
    weights = all_weights.get(quadrant, default_weights.get(quadrant, {
        "embedding": 0.50,
        "feature": 0.30,
        "match_ratio": 0.20
    }))
    
    match_ratio = movie.get('match_ratio', 0)
    
    # Phase 3.6: 不使用 feature_score（已移除）
    # 只使用 embedding_score 和 match_ratio
    final_score = (
        embedding_score * 100 * weights.get('embedding', 0.50) +
        match_ratio * 100 * weights.get('match_ratio', 0.20)
        # feature 權重保留但設為 0（未來可擴展）
    )
    
    return final_score


def sort_by_quadrant_and_embedding(
    movies: List[Dict],
    config: Dict = None
) -> List[Dict]:
    """
    Phase 3.6: 混合排序策略（象限優先 + Embedding 次要）
    
    排序規則：
    1. Primary: Quadrant 優先級 (Q1 > Q2 > Q4)
    2. Secondary: final_score 降序（同象限內）
    
    與 Phase 3.5 的差異：
    - Phase 3.5: 可能使用 feature_score 或 match_ratio 排序
    - Phase 3.6: 統一使用 final_score（已融合 embedding + match）
    
    Args:
        movies: 電影列表（必須包含 quadrant, final_score）
        config: Phase 3.6 配置參數
    
    Returns:
        sorted_movies: 排序後的電影列表
    
    Example:
        >>> movies = [
        ...     {"quadrant": "q4_fallback", "final_score": 50},
        ...     {"quadrant": "q1_perfect_match", "final_score": 80},
        ...     {"quadrant": "q2_semantic_discovery", "final_score": 70},
        ...     {"quadrant": "q1_perfect_match", "final_score": 85}
        ... ]
        >>> sorted_movies = sort_by_quadrant_and_embedding(movies)
        >>> [m["quadrant"] for m in sorted_movies]
        ['q1_perfect_match', 'q1_perfect_match', 'q2_semantic_discovery', 'q4_fallback']
        >>> [m["final_score"] for m in sorted_movies]
        [85, 80, 70, 50]
    """
    # 定義象限優先級
    quadrant_priority = {
        'q1_perfect_match': 1,
        'q2_semantic_discovery': 2,
        'q4_fallback': 3
    }
    
    # 排序：先按象限優先級，再按 final_score 降序
    sorted_movies = sorted(
        movies,
        key=lambda m: (
            quadrant_priority.get(m.get('quadrant', 'q4_fallback'), 999),
            -m.get('final_score', 0)  # 負號表示降序
        )
    )
    
    return sorted_movies


# ============================================
# Phase 3.5: 四象限混合推薦
# ============================================

async def recommend_movies_embedding_first(
    natural_query: str = None,
    mood_labels: List[str] = None,
    keywords: List[str] = None,
    genres: List[str] = None,
    exclude_genres: List[str] = None,
    year_range: tuple = None,
    year_ranges: List[List[int]] = None,
    min_rating: float = None,
    db_session: Session = None,
    count: int = 10,
    config: Dict = None
) -> List[Dict[str, Any]]:
    """
    Phase 3.6: Embedding-First 推薦系統（完整流程）
    
    架構流程：
    1. Query Generation: 生成最佳 Embedding 查詢文本
       - 情境 1 (NL only): 直接使用自然語言
       - 情境 2 (Mood only): Relationship-aware Template
       - 情境 3 (Both): NL 優先，衝突檢測
    2. Embedding Search: 全庫語義搜索（300 candidates）
       - 查詢 668 部電影的 embeddings
       - 計算 Cosine Similarity
       - 返回 Top 300
    3. Feature Filtering: 特徵過濾（150 candidates）
       - Tier 1: Match Ratio >= 80%
       - Tier 2: Match Ratio 50-79%
       - Tier 3: Match Ratio < 50%
    4. 3-Quadrant Classification: 三象限分類
       - Q1: High Embedding (>=0.60) + High Match (>=0.40) → 完美匹配
       - Q2: High Embedding (>=0.60) + Low Match (<0.40) → 語義發現
       - Q4: Low Embedding (<0.60) → 候補
    5. Score Calculation: 動態權重評分
       - Q1: E:50% M:20% F:30%
       - Q2: E:70% M:20% F:10%
       - Q4: E:30% M:30% F:40%
    6. Mixed Sorting: 象限優先 + 分數次要排序
       - Primary: Q1 > Q2 > Q4
       - Secondary: final_score desc
    7. Return Top K: 返回前 10 部推薦
    
    與 Phase 3.5 的差異：
    - Primary Engine: Feature Matching → Embedding Search
    - Secondary Engine: Embedding Reranking → Feature Filtering
    - Candidates: 150 (Feature) → 300 (Embedding) → 150 (Filtered)
    - Quadrants: 4 (Q1/Q2/Q3/Q4) → 3 (Q1/Q2/Q4)
    - Axes: Match Ratio (Y) × Embedding (X) → Embedding (Y) × Match Ratio (X)
    - Thresholds: 0.50/0.45 → 0.40/0.60
    
    Args:
        natural_query: 自然語言查詢 (例: "難過的時候適合看什麼電影")
        mood_labels: Mood 標籤列表 (英文，例: ["heartwarming", "uplifting"])
        keywords: 關鍵詞列表 (英文)
        genres: 類型列表 (簡體中文，例: ["劇情"])
        exclude_genres: 排除類型列表
        year_range: 單一年份範圍 (min, max)
        year_ranges: 多個年份範圍 [[1990, 1999], [2000, 2009]]
        min_rating: 最低評分
        db_session: 資料庫 Session
        count: 返回數量 (預設 10)
        config: 自定義配置 (可選，預設使用 phase36_config.PHASE36_CONFIG)
    
    Returns:
        List[Dict]: 推薦電影列表，每部電影包含：
        - tmdb_id: TMDB ID
        - title: 電影名稱
        - overview: 簡介
        - embedding_score: Embedding 相似度 (0.0-1.0)
        - match_ratio: Feature 匹配率 (0.0-1.0)
        - final_score: 綜合評分
        - quadrant: 象限 (q1_perfect_match | q2_semantic_discovery | q4_fallback)
        - ... (其他電影資訊)
    
    Example:
        >>> results = await recommend_movies_embedding_first(
        ...     natural_query="難過的時候適合看什麼電影",
        ...     mood_labels=["heartwarming", "uplifting"],
        ...     genres=["劇情"],
        ...     db_session=session,
        ...     count=10
        ... )
        >>> print(results[0])
        {
            "title": "風雲人物",
            "embedding_score": 0.482,
            "match_ratio": 0.67,
            "final_score": 34.45,
            "quadrant": "q4_fallback"
        }
    
    References:
        - 決策文檔: docs/phase36-decisions.md
        - 實現指南: docs/phase36-implementation-guide.md
        - 配置檔: app/services/phase36_config.py
    """
    # 導入依賴
    from app.services.embedding_query_generator import generate_embedding_query
    from app.services.embedding_service import embedding_similarity_search
    from app.services.phase36_config import PHASE36_CONFIG
    
    # 使用配置
    cfg = config or PHASE36_CONFIG
    verbose = cfg.get("debug", {}).get("verbose", True)
    
    if verbose:
        print("\n" + "🎬"*35)
        print("Phase 3.6: Embedding-First Recommendation System")
        print("🎬"*35)
    
    # ========================================================================
    # Step 1: Query Generation
    # ========================================================================
    if verbose:
        print(f"\n[Step 1/7] Embedding Query Generation")
        print(f"   - Natural Query: {natural_query or 'None'}")
        print(f"   - Mood Labels: {mood_labels or []}")
    
    query_result = generate_embedding_query(
        natural_query=natural_query,
        mood_labels=mood_labels or []
    )
    
    embedding_query_text = query_result["query"]
    has_conflict = query_result.get("conflict", False)
    
    if verbose:
        print(f"   ✓ Generated Query: '{embedding_query_text[:80]}...'")
        if has_conflict:
            print(f"   ⚠️  Conflict Detected: NL vs Mood sentiment mismatch")
    
    # ========================================================================
    # Step 2: Embedding Similarity Search (全庫搜索)
    # ========================================================================
    if verbose:
        print(f"\n[Step 2/7] Embedding Similarity Search")
    
    embedding_top_k = cfg.get("candidate_counts", {}).get("embedding_top_k", 300)
    min_similarity = cfg.get("embedding_search", {}).get("min_similarity", 0.0)
    
    embedding_candidates = await embedding_similarity_search(
        query_text=embedding_query_text,
        db_session=db_session,
        top_k=embedding_top_k,
        min_similarity=min_similarity
    )
    
    if verbose:
        print(f"   ✓ Retrieved {len(embedding_candidates)} candidates")
    
    if not embedding_candidates:
        if verbose:
            print(f"   ⚠️  No candidates found, returning empty list")
        return []
    
    # ========================================================================
    # Step 3: Feature Filtering (漸進式過濾)
    # ========================================================================
    if verbose:
        print(f"\n[Step 3/7] Tiered Feature Filtering")
    
    feature_filter_k = cfg.get("candidate_counts", {}).get("feature_filter_k", 150)
    randomness = cfg.get("feature_filtering", {}).get("randomness", 0.3)
    
    filtered_candidates = await tiered_feature_filtering(
        embedding_candidates=embedding_candidates,
        keywords=keywords or [],
        mood_tags=mood_labels or [],
        genres=genres or [],
        exclude_genres=exclude_genres,
        year_range=year_range,
        year_ranges=year_ranges,
        min_rating=min_rating,
        target_count=feature_filter_k,
        randomness=randomness
    )
    
    if verbose:
        print(f"   ✓ Filtered to {len(filtered_candidates)} candidates")
    
    if not filtered_candidates:
        if verbose:
            print(f"   ⚠️  All candidates filtered out, returning empty list")
        return []
    
    # ========================================================================
    # Step 4: 3-Quadrant Classification
    # ========================================================================
    if verbose:
        print(f"\n[Step 4/7] 3-Quadrant Classification")
    
    for movie in filtered_candidates:
        quadrant = classify_to_3quadrant(
            movie=movie,
            embedding_score=movie["embedding_score"],
            config=cfg
        )
        movie["quadrant"] = quadrant
    
    # 統計象限分佈
    if verbose and cfg.get("debug", {}).get("print_quadrant_stats", True):
        quadrant_counts = {
            "q1_perfect_match": 0,
            "q2_semantic_discovery": 0,
            "q4_fallback": 0
        }
        for movie in filtered_candidates:
            quadrant_counts[movie["quadrant"]] += 1
        
        print(f"   ✓ Quadrant Distribution:")
        print(f"      - Q1 (Perfect Match): {quadrant_counts['q1_perfect_match']}")
        print(f"      - Q2 (Semantic Discovery): {quadrant_counts['q2_semantic_discovery']}")
        print(f"      - Q4 (Fallback): {quadrant_counts['q4_fallback']}")
    
    # ========================================================================
    # Step 5: Score Calculation (動態權重)
    # ========================================================================
    if verbose:
        print(f"\n[Step 5/7] Dynamic Score Calculation")
    
    for movie in filtered_candidates:
        final_score = calculate_3quadrant_score(
            movie=movie,
            embedding_score=movie["embedding_score"],
            quadrant=movie["quadrant"],
            config=cfg
        )
        movie["final_score"] = final_score
    
    if verbose:
        print(f"   ✓ Calculated final scores for all candidates")
    
    # ========================================================================
    # Step 6: Mixed Sorting (象限優先 + 分數次要)
    # ========================================================================
    if verbose:
        print(f"\n[Step 6/7] Mixed Sorting (Quadrant + Score)")
    
    sorted_movies = sort_by_quadrant_and_embedding(
        movies=filtered_candidates,
        config=cfg
    )
    
    if verbose:
        print(f"   ✓ Sorted {len(sorted_movies)} movies")
    
    # ========================================================================
    # Step 7: Return Top K (混合策略：Top 3 固定 + 隨機選取)
    # ========================================================================
    # 🎲 新策略：增加重複查詢時的多樣性
    # - Top N: 固定返回最佳推薦（保證質量）
    # - 其他: 從剩餘候選中隨機選取（增加驚喜感）
    
    if verbose:
        print(f"\n[Step 7/7] Smart Selection Strategy")
    
    import random
    
    # 從配置獲取參數
    guaranteed_top = cfg.get("candidate_counts", {}).get("guaranteed_top", 3)
    random_pool_size = cfg.get("candidate_counts", {}).get("random_pool_size", 30)
    
    # 確保 Top N
    top_guaranteed = sorted_movies[:guaranteed_top] if len(sorted_movies) >= guaranteed_top else sorted_movies
    
    # 從排名 (N+1) - pool_size 中隨機選取
    remaining_pool = sorted_movies[guaranteed_top:min(random_pool_size, len(sorted_movies))]
    random_count = count - len(top_guaranteed)
    random_picks = random.sample(remaining_pool, min(random_count, len(remaining_pool))) if remaining_pool else []
    
    final_recommendations = top_guaranteed + random_picks
    
    if verbose:
        print(f"   ✓ Guaranteed Top {len(top_guaranteed)}: {[m['title'][:30] for m in top_guaranteed]}")
        if random_picks:
            print(f"   ✓ Random {len(random_picks)} (from rank {guaranteed_top+1}-{random_pool_size}): {[m['title'][:25] for m in random_picks[:3]]}...")
    
    # 格式化電影數據，確保前端所需欄位都存在
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    formatted_results = []
    
    for movie in final_recommendations:
        # 處理 release_date → release_year
        release_date = movie.get("release_date")
        release_year = None
        if release_date:
            if hasattr(release_date, 'year'):
                release_year = release_date.year
            elif isinstance(release_date, str) and len(release_date) >= 4:
                release_year = int(release_date[:4])
        
        # 構建前端格式
        formatted_movie = {
            "id": str(movie.get("id", movie.get("tmdb_id", ""))),
            "title": movie.get("title", "Unknown"),
            "overview": movie.get("overview", ""),
            "poster_url": f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
            "vote_average": float(movie.get("vote_average", 0.0)),
            "release_year": release_year,
            "release_date": str(release_date) if release_date else None,
            # Phase 3.6 特有欄位
            "embedding_score": movie.get("embedding_score", 0.0),
            "match_ratio": movie.get("match_ratio", 0.0),
            "final_score": movie.get("final_score", 0.0),
            "quadrant": movie.get("quadrant", "unknown"),
            # 其他可選欄位
            "genres": movie.get("genres", []),
            "runtime": movie.get("runtime"),
            "actors": movie.get("actors", [])
        }
        formatted_results.append(formatted_movie)
    
    if verbose:
        print(f"\n[Step 7/7] Returning Top {count} Recommendations")
        print(f"\n   📊 Top {min(5, len(formatted_results))} Results:")
        for i, movie in enumerate(formatted_results[:5]):
            print(f"      {i+1}. {movie['title'][:40]:40s}")
            print(f"         - Quadrant: {movie['quadrant']}")
            print(f"         - Final Score: {movie['final_score']:.2f}")
            print(f"         - Embedding: {movie['embedding_score']:.3f}, Match: {movie['match_ratio']:.2f}")
        
        print("\n" + "🎬"*35)
        print(f"Phase 3.6 Recommendation Complete: {len(formatted_results)} movies")
        print("🎬"*35 + "\n")
    
    return formatted_results

