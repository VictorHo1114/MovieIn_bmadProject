# backend/app/services/simple_recommend.py
"""
Phase 3.6: Embedding-First 推薦服務

完整推薦流程：
1. Embedding Query Generation - 智能查詢生成（處理 3 種輸入情境）
2. Embedding Similarity Search - 全庫語義搜索（返回 300 候選）
3. Tiered Feature Filtering - 三層漸進式過濾（篩選至 150 候選）
4. 3-Quadrant Classification - 三象限分類（Q1/Q2/Q4）
5. Dynamic Score Calculation - 動態權重評分
6. Mixed Sorting - 象限優先 + 分數次要排序
7. Smart Selection - Top 3 保證 + 隨機池多樣性

核心特色：
- 🎯 Embedding-First: 語義理解為主，特徵匹配為輔
- 📊 三象限加權: 根據品質自適應調整權重
- 🔮 Mood 關係分析: 支援 51 對情緒組合關係
- 💰 成本優化: 預計算 Embedding，查詢成本 ~$0.00002

參考文檔：
- docs/phase36-decisions.md (核心決策)
- docs/phase36-implementation-guide.md (實現指南)
- docs/PHASE36_PROGRESS.md (進度報告)
- app/services/phase36_config.py (配置參數)
"""
import os
import random
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# 類型映射：英文 → 簡體中文（匹配資料庫 genres 欄位）
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
    計算電影與用戶需求的匹配比例
    
    Match Ratio = matched_features / total_required_features
    
    Example:
        用戶要求: 5 moods + 3 genres = 8 features
        電影符合: 4 moods + 2 genres = 6 features
        Match Ratio = 6/8 = 0.75 (75%)
    
    Args:
        movie: 電影資料（包含 keywords, mood_tags, genres）
        keywords: 用戶要求的關鍵詞
        mood_tags: 用戶要求的情緒標籤
        genres: 用戶要求的類型
    
    Returns:
        float: 匹配比例 (0.0-1.0)
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
    Phase 3.6: 三層漸進式特徵過濾（輔助引擎）
    
    角色定位：
        - 輸入: Embedding 搜索結果（300 候選）+ 用戶特徵
        - 輸出: 過濾後的候選（150 候選）
        - 功能: 驗證語義候選是否符合用戶明確要求
    
    過濾策略：
        Tier 1 (嚴格): Match Ratio ≥ 80% - 高度符合
        Tier 2 (平衡): Match Ratio ≥ 50% - 中度符合
        Tier 3 (寬鬆): Match Ratio < 50%  - 保底候選
    
    過濾條件：
        Hard Filters（硬性過濾，必須符合）:
            - exclude_genres: 排除的類型
            - year_range: 年份範圍
            - min_rating: 最低評分
        
        Soft Filters（軟性過濾，計算 match_ratio）:
            - keywords: 關鍵詞匹配
            - mood_tags: 情緒標籤匹配
            - genres: 類型匹配
    
    Args:
        embedding_candidates: Embedding 搜索的 300 候選（含 embedding_score）
        keywords: 關鍵詞列表
        mood_tags: 情緒標籤列表
        genres: 類型列表
        exclude_genres: 排除類型
        year_range: 單一年份範圍 (min, max)
        year_ranges: 多個年份範圍 [[1990, 1999], [2000, 2009]]
        min_rating: 最低評分閾值
        target_count: 目標返回數量（預設 150）
        randomness: 隨機性參數（保留，未使用）
    
    Returns:
        List[Dict]: 過濾後的候選，每部包含：
            - embedding_score: 保留自 Embedding 搜索
            - match_ratio: 新增，特徵匹配率 (0.0-1.0)
            - match_count: 新增，符合的特徵數量
            - total_features: 新增，總特徵數量
    
    Example:
        >>> candidates = await embedding_similarity_search(query, top_k=300)
        >>> filtered = await tiered_feature_filtering(
        ...     embedding_candidates=candidates,
        ...     keywords=["love"],
        ...     mood_tags=["heartwarming"],
        ...     genres=["Drama"],
        ...     target_count=150
        ... )
        >>> len(filtered)
        150
        >>> filtered[0]
        {
            "title": "風雲人物",
            "embedding_score": 0.482,
            "match_ratio": 0.67,
            "match_count": 2,
            "total_features": 3
        }
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
        from app.services.mapping_tables import GENRE_TRADITIONAL_TO_SIMPLIFIED
        
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
    """
    檢查電影上映年份是否在指定範圍內
    
    Args:
        release_date: 上映日期（datetime.date 或 str 格式 "YYYY-MM-DD"）
        min_year: 最小年份
        max_year: 最大年份
    
    Returns:
        bool: 是否在範圍內
    """
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
# Phase 3.6: 三象限分類與動態加權
# ============================================================================

def classify_to_3quadrant(
    movie: Dict,
    embedding_score: float,
    config: Dict = None
) -> str:
    """
    三象限分類邏輯（Phase 3.6）
    
    象限定義：
        Q1 (Perfect Match): 高語義 (≥0.60) + 高匹配 (≥0.40)
            → 語義與特徵雙高，最佳推薦
        
        Q2 (Semantic Discovery): 高語義 (≥0.60) + 低匹配 (<0.40)
            → 語義相關但特徵不完全符合，發現型推薦
        
        Q4 (Fallback): 低語義 (<0.60)
            → 語義相似度不足，保底候選
    
    閾值設定：
        - high_embedding: 0.60 (Phase 3.6 提高標準)
        - high_match: 0.40 (Phase 3.6 降低要求)
    
    Args:
        movie: 電影資料，必須包含 match_ratio
        embedding_score: Embedding 相似度 (0.0-1.0)
        config: 自定義配置（可選）
    
    Returns:
        str: 象限標籤
            - "q1_perfect_match"
            - "q2_semantic_discovery"
            - "q4_fallback"
    
    Example:
        >>> movie = {"match_ratio": 0.75}
        >>> classify_to_3quadrant(movie, embedding_score=0.65)
        'q1_perfect_match'
        
        >>> movie = {"match_ratio": 0.30}
        >>> classify_to_3quadrant(movie, embedding_score=0.70)
        'q2_semantic_discovery'
        
        >>> classify_to_3quadrant(movie, embedding_score=0.50)
        'q4_fallback'
    """
    # Phase 3.6 預設閾值
    default_thresholds = {
        "high_embedding": 0.60,  # 提高語義閾值
        "high_match": 0.40       # 降低匹配閾值
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
    根據象限動態計算最終分數（Phase 3.6）
    
    權重策略：
        Q1 (Perfect Match): 平衡策略
            - Embedding: 50% (主導)
            - Match Ratio: 20% (輔助)
            - Feature: 30% (保留，當前未使用)
        
        Q2 (Semantic Discovery): Embedding 優先策略
            - Embedding: 70% (主導)
            - Match Ratio: 20% (輔助)
            - Feature: 10% (最小)
        
        Q4 (Fallback): Feature 優先策略
            - Embedding: 30% (降低)
            - Match Ratio: 30% (提高)
            - Feature: 40% (保留，當前未使用)
    
    評分公式：
        final_score = embedding_score × 100 × W_e + match_ratio × 100 × W_m
        (feature_score 權重保留但當前設為 0)
    
    Args:
        movie: 電影資料，包含 match_ratio
        embedding_score: Embedding 相似度 (0.0-1.0)
        quadrant: 象限標籤
        config: 自定義配置（可選）
    
    Returns:
        float: 最終分數 (0-100)
    
    Example:
        >>> movie = {"match_ratio": 0.75}
        >>> calculate_3quadrant_score(movie, 0.65, 'q1_perfect_match')
        47.5  # = 65*0.50 + 75*0.20 = 32.5 + 15.0
    """
    # Phase 3.6 預設權重配置
    default_weights = {
        "q1_perfect_match": {
            "embedding": 0.50,
            "feature": 0.30,      # 保留，當前未使用
            "match_ratio": 0.20
        },
        "q2_semantic_discovery": {
            "embedding": 0.70,
            "feature": 0.10,      # 保留，當前未使用
            "match_ratio": 0.20
        },
        "q4_fallback": {
            "embedding": 0.30,
            "feature": 0.40,      # 保留，當前未使用
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
    
    # 計算最終分數（當前僅使用 embedding 和 match_ratio）
    final_score = (
        embedding_score * 100 * weights.get('embedding', 0.50) +
        match_ratio * 100 * weights.get('match_ratio', 0.20)
    )
    
    return final_score


def sort_by_quadrant_and_embedding(
    movies: List[Dict],
    config: Dict = None
) -> List[Dict]:
    """
    混合排序策略（Phase 3.6）
    
    排序規則：
        1. 象限優先（Primary Sort）
           Q1 (完美匹配) > Q2 (語義發現) > Q4 (保底)
        
        2. 分數次要（Secondary Sort）
           同象限內按 final_score 降序排列
    
    Args:
        movies: 電影列表，必須包含 quadrant 和 final_score
        config: 自定義配置（可選，當前未使用）
    
    Returns:
        List[Dict]: 排序後的電影列表
    
    Example:
        >>> movies = [
        ...     {"title": "A", "quadrant": "q4_fallback", "final_score": 50},
        ...     {"title": "B", "quadrant": "q1_perfect_match", "final_score": 80},
        ...     {"title": "C", "quadrant": "q2_semantic_discovery", "final_score": 70},
        ...     {"title": "D", "quadrant": "q1_perfect_match", "final_score": 85}
        ... ]
        >>> sorted_movies = sort_by_quadrant_and_embedding(movies)
        >>> [m["title"] for m in sorted_movies]
        ['D', 'B', 'C', 'A']  # Q1(85) > Q1(80) > Q2(70) > Q4(50)
    """
    # 象限優先級映射
    quadrant_priority = {
        'q1_perfect_match': 1,
        'q2_semantic_discovery': 2,
        'q4_fallback': 3
    }
    
    # 兩級排序
    sorted_movies = sorted(
        movies,
        key=lambda m: (
            quadrant_priority.get(m.get('quadrant', 'q4_fallback'), 999),
            -m.get('final_score', 0)
        )
    )
    
    return sorted_movies


# ============================================================================
# Phase 3.6: 主推薦函數
# ============================================================================

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
    Phase 3.6: Embedding-First 主推薦函數
    
    完整推薦流程（7 步驟）：
    
    1. Query Generation（查詢生成）
       - 情境 1: 僅自然語言 → 直接使用
       - 情境 2: 僅 Mood → 關係感知模板生成
       - 情境 3: NL + Mood → 分離處理（NL 優先查詢，Mood 用於過濾）
    
    2. Embedding Search（全庫語義搜索）
       - 搜索 668 部電影的預計算 embeddings
       - 計算 Cosine Similarity
       - 返回 Top 300 語義相關候選
    
    3. Feature Filtering（三層漸進式過濾）
       - Tier 1: Match Ratio ≥ 80% (嚴格)
       - Tier 2: Match Ratio ≥ 50% (平衡)
       - Tier 3: Match Ratio < 50% (寬鬆保底)
       - 過濾至 150 候選
    
    4. 3-Quadrant Classification（三象限分類）
       - Q1: 高語義(≥0.60) + 高匹配(≥0.40) → 完美匹配
       - Q2: 高語義(≥0.60) + 低匹配(<0.40) → 語義發現
       - Q4: 低語義(<0.60) → 保底候選
    
    5. Score Calculation（動態權重評分）
       - Q1: Embedding 50%, Match 20%
       - Q2: Embedding 70%, Match 20%
       - Q4: Embedding 30%, Match 30%
    
    6. Mixed Sorting（混合排序）
       - 象限優先: Q1 > Q2 > Q4
       - 象限內: final_score 降序
    
    7. Smart Selection（智能選取）
       - Top 3: 固定返回（保證質量）
       - 4-10: 從排名 4-30 隨機選取（增加多樣性）
    
    Args:
        natural_query: 自然語言查詢（例: "難過的時候適合看什麼"）
        mood_labels: Mood 標籤（英文，例: ["heartwarming", "uplifting"]）
        keywords: 關鍵詞列表
        genres: 類型列表（簡體中文，例: ["劇情"]）
        exclude_genres: 排除類型
        year_range: 年份範圍 (min, max)
        year_ranges: 多個年份範圍 [[1990, 1999], [2000, 2009]]
        min_rating: 最低評分
        db_session: 資料庫 Session
        count: 返回數量（預設 10）
        config: 自定義配置（可選，預設使用 PHASE36_CONFIG）
    
    Returns:
        List[Dict]: 推薦電影列表，每部包含：
            - id: 電影 ID
            - title: 電影名稱
            - overview: 簡介
            - poster_url: 海報圖片 URL
            - vote_average: TMDB 評分
            - release_year: 上映年份
            - embedding_score: 語義相似度 (0.0-1.0)
            - match_ratio: 特徵匹配率 (0.0-1.0)
            - final_score: 綜合評分 (0-100)
            - quadrant: 象限標籤
            - genres: 類型列表
    
    Example:
        >>> results = await recommend_movies_embedding_first(
        ...     natural_query="難過的時候適合看什麼",
        ...     mood_labels=["heartwarming"],
        ...     genres=["劇情"],
        ...     count=10
        ... )
        >>> results[0]
        {
            "title": "風雲人物",
            "embedding_score": 0.482,
            "match_ratio": 0.67,
            "final_score": 34.45,
            "quadrant": "q4_fallback"
        }
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
    # Step 7: Smart Selection（智能選取策略）
    # ========================================================================
    # 增加重複查詢時的多樣性：
    # - Top 3: 固定返回最佳推薦（保證質量）
    # - 4-10: 從排名 4-30 隨機選取（增加驚喜感，避免重複）
    
    if verbose:
        print(f"\n[Step 7/7] Smart Selection Strategy")
    
    import random
    
    # 智能選取參數
    guaranteed_top = cfg.get("candidate_counts", {}).get("guaranteed_top", 3)
    random_pool_size = cfg.get("candidate_counts", {}).get("random_pool_size", 30)
    
    # Top 3 固定返回
    top_guaranteed = sorted_movies[:guaranteed_top] if len(sorted_movies) >= guaranteed_top else sorted_movies
    
    # 從排名 4-30 隨機選取
    remaining_pool = sorted_movies[guaranteed_top:min(random_pool_size, len(sorted_movies))]
    random_count = count - len(top_guaranteed)
    random_picks = random.sample(remaining_pool, min(random_count, len(remaining_pool))) if remaining_pool else []
    
    final_recommendations = top_guaranteed + random_picks
    
    if verbose:
        print(f"   ✓ Guaranteed Top {len(top_guaranteed)}: {[m['title'][:30] for m in top_guaranteed]}")
        if random_picks:
            print(f"   ✓ Random {len(random_picks)} (from rank {guaranteed_top+1}-{random_pool_size}): {[m['title'][:25] for m in random_picks[:3]]}...")
    
    # ========================================================================
    # 格式化返回數據（確保前端所需欄位完整）
    # ========================================================================
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    formatted_results = []
    
    for movie in final_recommendations:
        # 處理日期格式
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

