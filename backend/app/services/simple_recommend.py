# backend/app/services/simple_recommend.py
"""
智能混合推薦服務 - 方案 B
根據查詢類型智能選擇 Feature-Based 或 Embedding 策略
"""
import os
import random
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.services.embedding_service import rerank_by_semantic_similarity
from app.services.enhanced_feature_extraction import enhanced_feature_extraction

# ============================================
# 智能混合配置（可調整實驗參數）
# ============================================
HYBRID_CONFIG = {
    "decision_threshold": 40,        # 決策閾值（>= 40 使用 Embedding）
    "feature_score_threshold": 15.0, # Feature 匹配分數閾值
    "min_candidates": 20,            # 最小候選數量
    "enable_logging": True,          # 是否顯示詳細日誌
}

def update_hybrid_config(**kwargs):
    """動態更新混合配置（用於實驗）"""
    HYBRID_CONFIG.update(kwargs)
    print(f"[Config] 更新混合配置: {kwargs}")

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
# 棄用的舊函數（已由 enhanced_feature_extraction 取代）
# ============================================
# 說明：
# - KEYWORD_MAPPING (200+ 中英映射) → 已整合到 enhanced_feature_extraction.py 的 MOOD_LABEL_TO_DB_TAGS
# - extract_all_keywords() → 已由 enhanced_feature_extraction() 取代
# - extract_mood_tags() → 已由 MOOD_LABEL_TO_DB_TAGS 映射表取代
# 
# 新系統優勢：
# 1. 精確匹配：直接從 DB 提取 keywords，不需要中英映射
# 2. Mood 映射：MOOD_LABEL_TO_DB_TAGS 提供精準的 mood → tags/keywords 映射
# 3. 規則推斷：自動推斷年份、語言等參數
# ============================================

def should_use_embedding(
    user_input: str, 
    keywords: List[str], 
    mood_tags: List[str],
    candidates: List[Dict],
    config: Dict = None,
    selected_moods: List[str] = None,   # 新增：用戶選擇的 mood buttons
    selected_genres: List[str] = None   # 新增：用戶選擇的 genre buttons
) -> Tuple[bool, str, int]:
    """
    智能判斷是否需要 Embedding（方案 B - 智能混合）
    
    Args:
        user_input: 用戶輸入文字
        keywords: 提取的關鍵詞列表
        mood_tags: 提取的情緒標籤列表
        candidates: Feature 匹配的候選電影
        config: 配置參數（可選，用於實驗調整）
        selected_moods: 用戶選擇的 mood buttons（明確 feature）
        selected_genres: 用戶選擇的 genre buttons（明確 feature）
    
    Returns:
        Tuple[bool, str, int]: (是否使用 Embedding, 判斷原因, 評分)
    
    評分系統（總分 100，預設閾值 40）:
        - 有明確 keywords: -30 分（越少越需要 Embedding）
        - 有明確 mood_tags: -20 分
        - 有 Feature Buttons: -25 分（新增！用戶明確選擇）
        - 無抽象/情境詞: -20 分
        - Feature 匹配分數高: -15 分
        - 候選電影足夠: -15 分
    """
    # 使用配置或預設值
    cfg = config or HYBRID_CONFIG
    threshold = cfg.get("decision_threshold", 40)
    feature_threshold = cfg.get("feature_score_threshold", 15.0)
    min_cand = cfg.get("min_candidates", 20)
    
    score = 100  # 初始滿分（假設完全需要 Embedding）
    details = []  # 詳細評分項目
    
    # === 評估 1: Keywords 覆蓋度 (-30/-15/0) ===
    if len(keywords) >= 3:
        score -= 30
        details.append(("Keywords", f"{len(keywords)} 個", -30, "✅"))
    elif len(keywords) >= 1:
        score -= 15
        details.append(("Keywords", f"{len(keywords)} 個", -15, "⚠️"))
    else:
        details.append(("Keywords", "0 個", 0, "❌"))
    
    # === 評估 2: Mood Tags 覆蓋度 (-30/-20/-10/0) ===
    # 提高 Mood Tags 權重，因為它們是明確的 feature
    if len(mood_tags) >= 3:
        score -= 30
        details.append(("Mood Tags", f"{len(mood_tags)} 個", -30, "✅"))
    elif len(mood_tags) >= 2:
        score -= 20
        details.append(("Mood Tags", f"{len(mood_tags)} 個", -20, "✅"))
    elif len(mood_tags) >= 1:
        score -= 15
        details.append(("Mood Tags", f"{len(mood_tags)} 個", -15, "⚠️"))
    else:
        details.append(("Mood Tags", "0 個", 0, "❌"))
    
    # === 評估 2.5: Feature Buttons 明確度 (-25/-15/0) ===
    # 用戶點選 buttons 是明確的 feature 選擇，應該降低 Embedding 需求
    button_count = len(selected_moods or []) + len(selected_genres or [])
    if button_count >= 3:
        score -= 25
        details.append(("Feature Buttons", f"{button_count} 個 (Mood: {len(selected_moods or [])}, Genre: {len(selected_genres or [])})", -25, "✅"))
    elif button_count >= 1:
        score -= 15
        details.append(("Feature Buttons", f"{button_count} 個 (Mood: {len(selected_moods or [])}, Genre: {len(selected_genres or [])})", -15, "⚠️"))
    else:
        details.append(("Feature Buttons", "0 個", 0, "❌"))
    
    # === 評估 3: 抽象/情境詞檢測 (-20/-5/+10) ===
    # 只在有自然語言輸入時才檢測抽象詞
    # 注意：中文 mood 詞彙（如「難過」「搞笑」）已由 ZH_TO_EN_MOOD 映射處理，
    #      不應視為抽象詞，因為它們已成功提取為 mood_tags
    abstract_patterns = [
        # 情境詞 (14 個)
        "適合", "想看", "心情", "下雨", "晚上", "週末", "深夜", "假日",
        "一個人", "陪伴", "沙發", "被窩", "放鬆", "紓壓",
        
        # 相似性查詢 (8 個)
        "感覺像", "類似", "風格", "調性", "像是", "那種", "相似", "類型",
        
        # 主觀評價 (8 個)
        "好看", "推薦", "經典", "必看", "神作", "佳作", "名作", "傑作",
        
        # 模糊情感詞 (僅保留無法明確映射的)
        "共鳴", "氛圍", "治癒系", "哭", "笑", "爽", "過癮", "震撼", "平靜"
    ]
    
    # 只有在有自然語言輸入時才檢測抽象詞
    if user_input and user_input.strip():
        matched_abstract = [p for p in abstract_patterns if p in user_input]
        abstract_count = len(matched_abstract)
        
        # === 特殊檢測：純 Mood 文字輸入 ===
        # 如果用戶輸入非常短(<=5字)且成功提取了 mood_tags，
        # 說明這是明確的 feature 輸入，應該強制走 Feature 路徑
        is_pure_mood_input = (
            len(user_input.strip()) <= 5 and
            len(mood_tags) >= 1 and
            len(keywords) == 0 and
            abstract_count == 0
        )
        
        if is_pure_mood_input:
            score -= 25
            details.append(("純 Mood 輸入", f"'{user_input.strip()}'", -25, "✅"))
        elif abstract_count == 0:
            score -= 20
            details.append(("抽象詞", "無", -20, "✅"))
        elif abstract_count <= 2:
            score -= 5
            details.append(("抽象詞", f"{abstract_count} 個 ({', '.join(matched_abstract)})", -5, "⚠️"))
        else:
            score += 10
            details.append(("抽象詞", f"{abstract_count} 個 ({', '.join(matched_abstract[:3])}...)", +10, "❌"))
    else:
        # 沒有自然語言輸入（純 button 選擇）
        score -= 20
        details.append(("抽象詞", "僅 Button 選擇", -20, "✅"))
    
    # === 評估 4: Feature 匹配品質 (-15/-10/0) ===
    if candidates and len(candidates) > 0:
        top_score = candidates[0].get("feature_score", 0)
        if top_score >= feature_threshold * 1.5:
            score -= 15
            details.append(("Feature 分數", f"{top_score:.1f}", -15, "✅"))
        elif top_score >= feature_threshold:
            score -= 10
            details.append(("Feature 分數", f"{top_score:.1f}", -10, "⚠️"))
        else:
            details.append(("Feature 分數", f"{top_score:.1f}", 0, "❌"))
    else:
        details.append(("Feature 分數", "N/A", 0, "❌"))
    
    # === 評估 5: 候選電影數量 (-15/-10/0) ===
    candidate_count = len(candidates)
    if candidate_count >= min_cand * 2:
        score -= 15
        details.append(("候選數量", f"{candidate_count} 部", -15, "✅"))
    elif candidate_count >= min_cand:
        score -= 10
        details.append(("候選數量", f"{candidate_count} 部", -10, "⚠️"))
    else:
        details.append(("候選數量", f"{candidate_count} 部", 0, "❌"))
    
    # === 決策 ===
    use_embedding = score >= threshold
    
    # 格式化決策說明
    decision_icon = "🔮 Embedding" if use_embedding else "⚡ Feature"
    reason_parts = [f"{icon} {name}: {value} ({change:+d})" 
                    for name, value, change, icon in details]
    reason_str = "\n    ".join(reason_parts)
    
    return use_embedding, reason_str, score


def diversity_filter(candidates: List[Dict], top_k: int = 10, randomness: float = 0.3) -> List[Dict]:
    """
    規則式多樣性過濾（替代 MMR Embedding）
    確保推薦結果的類型、年份、導演多樣性
    
    隨機性參數 (0.0 - 1.0):
    - 0.0: 完全按分數排序（可能重複類型）
    - 0.3: 平衡多樣性與分數（預設）
    - 0.7: 高度隨機，探索性推薦
    - 1.0: 完全隨機洗牌
    """
    if len(candidates) <= top_k:
        return candidates
    
    # === 特殊處理：極高隨機性 (>= 0.8) ===
    if randomness >= 0.8:
        # 完全隨機洗牌（保留前 3 名高分電影）
        top_3 = candidates[:3]
        rest = candidates[3:]
        random.shuffle(rest)
        return top_3 + rest[:top_k - 3]
    
    selected = []
    genre_counts = {}
    decade_counts = {}
    
    # === 根據隨機性調整策略 ===
    # randomness 越高 → 懲罰越低、隨機波動越大、候選池越大
    genre_penalty_weight = 4.0 * (1 - randomness)      # 0.0-4.0
    decade_penalty_weight = 2.5 * (1 - randomness)     # 0.0-2.5
    random_amplitude = 10.0 * randomness               # 0.0-10.0
    candidate_pool_size = int(top_k * (2 + randomness * 3))  # 20-50
    
    # 為每部電影計算調整後的分數
    scored_candidates = []
    for movie in candidates:
        # 取得類型和年代
        genres = movie.get("genres", [])
        main_genre = genres[0] if genres else "Unknown"
        
        release_date = movie.get("release_date")
        if release_date:
            # 處理 datetime.date 對象或字串
            if hasattr(release_date, 'year'):
                decade = (release_date.year // 10) * 10
            elif isinstance(release_date, str) and len(release_date) >= 4:
                decade = (int(release_date[:4]) // 10) * 10
            else:
                decade = "Unknown"
        else:
            decade = "Unknown"
        
        # 計算多樣性懲罰
        genre_penalty = genre_counts.get(main_genre, 0) * genre_penalty_weight
        decade_penalty = decade_counts.get(decade, 0) * decade_penalty_weight
        
        # 調整分數
        base_score = movie.get("feature_score", 0)
        adjusted_score = base_score - genre_penalty - decade_penalty
        
        # === 加強隨機性 ===
        # randomness = 0.0 → random_bonus 範圍 = 0
        # randomness = 0.5 → random_bonus 範圍 = ±5
        # randomness = 1.0 → random_bonus 範圍 = ±10
        random_bonus = random.uniform(-random_amplitude, random_amplitude)
        adjusted_score += random_bonus
        
        # === 額外隨機機制：隨機跳躍 ===
        # 給低排名電影一定機會躍升（隨機性越高，機會越大）
        if randomness > 0.4 and random.random() < randomness * 0.3:
            jump_bonus = random.uniform(5, 15) * randomness
            adjusted_score += jump_bonus
        
        scored_candidates.append({
            "movie": movie,
            "adjusted_score": adjusted_score,
            "base_score": base_score,
            "main_genre": main_genre,
            "decade": decade
        })
    
    # 排序並選擇
    scored_candidates.sort(key=lambda x: x["adjusted_score"], reverse=True)
    
    # === 動態候選池大小 ===
    # randomness 越高 → 從更大的候選池中選擇
    pool_size = min(candidate_pool_size, len(scored_candidates))
    
    for item in scored_candidates[:pool_size]:
        if len(selected) >= top_k:
            break
        
        movie = item["movie"]
        main_genre = item["main_genre"]
        decade = item["decade"]
        
        selected.append(movie)
        genre_counts[main_genre] = genre_counts.get(main_genre, 0) + 1
        decade_counts[decade] = decade_counts.get(decade, 0) + 1
    
    # === 最終隨機洗牌（高隨機性時）===
    if randomness >= 0.6:
        # 保留前 2 名，其餘洗牌
        top_2 = selected[:2]
        rest = selected[2:]
        random.shuffle(rest)
        selected = top_2 + rest
    
    return selected


async def recommend_movies_hybrid(
    user_input: str,
    db_session: Session,
    count: int = 10,
    selected_genres: List[str] = None,
    selected_moods: List[str] = None,
    selected_eras: List[str] = None,  # 新增: 年代篩選 ⭐
    randomness: float = 0.3,
    decision_threshold: int = None  # 可選：自定義決策閾值（用於實驗）
) -> List[Dict[str, Any]]:
    """
    智能混合推薦流程（方案 B - 使用增強版 Feature Extraction）:
    1. Enhanced Feature Extraction (整合 Mood + GPT + Exact Match + Era)
    2. SQL Feature Matching (帶硬性年代/類型篩選)
    3. 智能判斷：Feature vs. Embedding
    4. 路徑選擇：
       - Feature 路徑：diversity_filter
       - Embedding 路徑：embedding_rerank
    5. 返回結果
    """
    # 更新配置（如果有自定義閾值）
    if decision_threshold is not None:
        HYBRID_CONFIG["decision_threshold"] = decision_threshold
    
    print(f"\n{'='*70}")
    print(f"🎬 [Hybrid Recommend] 智能混合推薦啟動 (Enhanced Feature Extraction)")
    print(f"{'='*70}")
    print(f"📝 用戶輸入: '{user_input}'")
    if selected_moods:
        print(f"💭 心情標籤: {selected_moods}")
    if selected_genres:
        print(f"🎭 類型標籤: {selected_genres}")
    if selected_eras:
        print(f"📅 年代標籤: {selected_eras}")  # 新增 ⭐
    print(f"⚙️  配置: 閾值={HYBRID_CONFIG['decision_threshold']}, 隨機性={randomness:.2f}")
    print(f"{'='*70}\n")
    
    # === Step 1: Enhanced Feature Extraction ===
    print(f"📍 [Step 1] Enhanced Feature Extraction")
    print(f"{'-'*70}")
    
    # 使用增強版特徵提取（整合 Mood Mapping + Exact Match + Era）
    features = await enhanced_feature_extraction(
        user_input=user_input,
        selected_moods=selected_moods or [],
        selected_genres=selected_genres or [],
        selected_eras=selected_eras or [],  # 新增 ⭐
        db_session=db_session
    )
    
    print(f"🔍 Enhanced Extraction 結果:")
    print(f"   - Keywords: {features['keywords'][:5] if features['keywords'] else '無'}")
    print(f"   - Mood Tags: {features['mood_tags'][:5] if features['mood_tags'] else '無'}")
    print(f"   - Genres: {features['genres']}")
    print(f"   - Year Ranges: {features['year_ranges']}")  # 新增 ⭐
    print(f"   - Exact Title Matches: {len(features['exact_matches']['titles'])} 部")
    print(f"   - Exact Keyword Matches: {len(features['exact_matches']['keywords'])} 部")
    
    # === 直接使用 Enhanced 結果（無需 GPT）===
    user_keywords = features['keywords']
    user_mood_tags = features['mood_tags']
    intent = {
        'genres': features['genres'],
        'exclude_genres': features.get('exclude_genres', []),
        'year_range': features.get('year_range'),
        'min_rating': features.get('min_rating'),
        'original_language': features.get('original_language')  # Enhanced 也可以提供語言過濾
    }
    
    if intent.get('year_range'):
        print(f"   - Year Range: {intent['year_range']}")
    if intent.get('min_rating'):
        print(f"   - Min Rating: {intent['min_rating']}")
    if intent.get('original_language'):
        print(f"   - Language: {intent['original_language']}")
    print(f"{'-'*70}\n")
    
    # === Step 2: SQL Feature Matching ===
    print(f"📍 [Step 2] SQL Feature Matching")
    print(f"{'-'*70}")
    
    candidates = await sql_feature_matching(
        keywords=user_keywords,
        mood_tags=user_mood_tags,
        genres=intent.get("genres", []),
        exclude_genres=intent.get("exclude_genres", []),
        year_range=intent.get("year_range"),  # 舊版單一範圍
        year_ranges=features.get("year_ranges"),  # 新版多個範圍 ⭐
        min_rating=intent.get("min_rating"),
        db_session=db_session,
        limit=count * 15,
        randomness=randomness  # 傳遞隨機性參數到 SQL 查詢
    )
    
    # 合併精確匹配的結果（優先置頂）
    exact_title_matches = features['exact_matches'].get('titles', [])
    exact_keyword_matches = features['exact_matches'].get('keywords', [])
    
    # 去重合併：精確匹配 + 一般候選
    seen_ids = set()
    merged_candidates = []
    
    # 1. 精確標題匹配（最高優先級）
    for movie in exact_title_matches:
        if movie['id'] not in seen_ids:
            movie['is_exact_title_match'] = True
            movie['feature_score'] = movie.get('feature_score', 0) + 50  # Boost
            merged_candidates.append(movie)
            seen_ids.add(movie['id'])
    
    # 2. 精確關鍵詞匹配（次高優先級）
    for movie in exact_keyword_matches:
        if movie['id'] not in seen_ids:
            movie['is_exact_keyword_match'] = True
            movie['feature_score'] = movie.get('feature_score', 0) + 30  # Boost
            merged_candidates.append(movie)
            seen_ids.add(movie['id'])
    
    # 3. 一般候選
    for movie in candidates:
        if movie['id'] not in seen_ids:
            merged_candidates.append(movie)
            seen_ids.add(movie['id'])
    
    candidates = merged_candidates
    
    print(f"📊 SQL 返回: {len(candidates)} 部候選電影")
    print(f"   - 精確標題匹配: {len(exact_title_matches)} 部")
    print(f"   - 精確關鍵詞匹配: {len(exact_keyword_matches)} 部")
    if candidates:
        top_score = candidates[0].get("feature_score", 0)
        print(f"   - Top 1: {candidates[0].get('title')} (分數: {top_score:.1f})")
        if len(candidates) > 1:
            print(f"   - Top 2: {candidates[1].get('title')} (分數: {candidates[1].get('feature_score', 0):.1f})")
    print(f"{'-'*70}\n")
    
    # === Step 3: 智能判斷 ===
    print(f"📍 [Step 3] 智能判斷路徑")
    print(f"{'-'*70}")
    
    use_embedding, reason_details, score = should_use_embedding(
        user_input=user_input,
        keywords=user_keywords,
        mood_tags=user_mood_tags,
        candidates=candidates,
        config=HYBRID_CONFIG,
        selected_moods=selected_moods,      # 傳遞 mood buttons
        selected_genres=selected_genres     # 傳遞 genre buttons
    )
    
    decision_icon = "🔮 Embedding" if use_embedding else "⚡ Feature"
    print(f"🎯 決策: {decision_icon} (評分: {score}/100, 閾值: {HYBRID_CONFIG['decision_threshold']})")
    print(f"\n📋 評分細節:")
    print(f"    {reason_details}")
    print(f"{'-'*70}\n")
    
    # === Step 4: 路徑選擇 ===
    if use_embedding:
        print(f"📍 [Step 4] 🔮 Embedding 語義匹配路徑")
        print(f"{'-'*70}")
        print(f"🌐 調用 Embedding API 進行語義重排序...")
        print(f"   隨機性設定: {randomness:.2f} (多樣性權重: {0.3 + (randomness * 0.4):.2f})")
        
        try:
            from app.services.embedding_service import rerank_by_semantic_similarity
            
            # randomness 越高 → diversity_weight 越高 (0.3-0.7)
            diversity_weight = 0.3 + (randomness * 0.4)
            
            reranked = await rerank_by_semantic_similarity(
                query_text=user_input,
                candidate_movies=candidates,
                db_session=db_session,
                top_k=count,
                diversity_weight=diversity_weight,
                boost_exact_matches=True
            )
            
            # === 額外隨機性處理（高隨機性時）===
            if randomness >= 0.7:
                # 保留前 3 名，其餘部分洗牌
                top_3 = reranked[:3]
                rest = reranked[3:count]
                random.shuffle(rest)
                results = top_3 + rest
                print(f"   🎲 高隨機性模式：保留 Top 3，其餘洗牌")
            else:
                results = reranked
            
            print(f"✅ Embedding 完成，返回 {len(results)} 部電影")
        except Exception as e:
            print(f"❌ Embedding 失敗: {e}")
            print(f"🔄 降級到 Feature 路徑")
            results = diversity_filter(candidates, top_k=count, randomness=randomness)
    else:
        print(f"📍 [Step 4] ⚡ Feature 匹配路徑")
        print(f"{'-'*70}")
        print(f"🎲 使用規則式多樣性過濾 (隨機性: {randomness:.2f})...")
        
        results = diversity_filter(
            candidates=candidates,
            top_k=count,
            randomness=randomness
        )
        print(f"✅ Feature 完成，返回 {len(results)} 部電影")
    
    print(f"{'-'*70}\n")
    
    # === Step 5: 格式化結果 ===
    TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"
    formatted_results = []
    for i, movie in enumerate(results[:count], 1):
        # 處理 release_date (可能是 datetime.date 或字串)
        release_date = movie.get("release_date")
        if release_date:
            if hasattr(release_date, 'year'):
                release_year = release_date.year
                display_year = str(release_year)
            elif isinstance(release_date, str) and len(release_date) >= 4:
                release_year = int(release_date[:4])
                display_year = release_date[:4]
            else:
                release_year = None
                display_year = 'N/A'
        else:
            release_year = None
            display_year = 'N/A'
        
        formatted_results.append({
            "id": movie["id"],
            "title": movie.get("title", ""),
            "overview": movie.get("overview", ""),
            "poster_url": f"{TMDB_IMAGE_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else None,
            "release_year": release_year,
            "vote_average": movie.get("vote_average", 0.0),
            "similarity_score": movie.get("similarity_score", 0.0),
            "feature_score": movie.get("feature_score", 0.0)
        })
        print(f"   {i}. {movie.get('title')} ({display_year}) - ⭐{movie.get('vote_average', 0):.1f}")
    
    print(f"\n{'='*70}")
    print(f"✨ [Complete] 推薦完成！策略: {decision_icon}")
    print(f"{'='*70}\n")
    
    return formatted_results


async def sql_feature_matching(
    keywords: List[str],
    mood_tags: List[str],
    genres: List[str],
    exclude_genres: List[str] = None,
    year_range: tuple = None,  # 保留舊版單一範圍
    year_ranges: List[List[int]] = None,  # 新增: 多個年份範圍 (OR 邏輯) ⭐
    min_rating: float = None,
    db_session: Session = None,
    limit: int = 150,
    randomness: float = 0.3  # 新增：隨機性參數
) -> List[Dict]:
    """
    SQL 多維 Feature 匹配
    排序公式: keywords * 20 + mood_tags * 15 + genres * 10 + rating * 3 + popularity * 2 + RANDOM() * (5-50)
    
    年份篩選 (硬性過濾):
    - year_ranges: [[1990, 1999], [2000, 2009]] → (90年代 OR 00年代)
    
    randomness 參數:
    - 0.0: RANDOM() * 5 (影響極小)
    - 0.3: RANDOM() * 20 (預設，中等影響)
    - 0.6: RANDOM() * 35 (高度隨機)
    - 1.0: RANDOM() * 50 (極度隨機，可能完全打亂排序)
    """
    sql_conditions = ["1=1"]
    sql_params = {}
    order_parts = []
    
    # === Keywords 匹配（最高權重 20）===
    if keywords:
        unique_keywords = list(set(keywords))[:10]
        keyword_array = ", ".join([f"'{k}'" for k in unique_keywords])
        
        keyword_match_sql = f"""
            (SELECT COUNT(*) 
             FROM jsonb_array_elements_text(COALESCE(keywords, '[]'::jsonb)) AS kw
             WHERE LOWER(kw) = ANY(ARRAY[{keyword_array}]))
        """
        order_parts.append(f"({keyword_match_sql}) * 20")
    
    # === Mood Tags 匹配（次高權重 15）===
    if mood_tags:
        unique_tags = list(set(mood_tags))[:10]
        tags_array = ", ".join([f"'{t}'" for t in unique_tags])
        
        mood_match_sql = f"""
            (SELECT COUNT(*) 
             FROM jsonb_array_elements_text(COALESCE(mood_tags, '[]'::jsonb)) AS mt
             WHERE LOWER(mt) = ANY(ARRAY[{tags_array}]))
        """
        order_parts.append(f"({mood_match_sql}) * 15")
    
    # === Genres 匹配（權重 10）===
    if genres:
        genres_zh = [GENRE_EN_TO_ZH.get(g, g) for g in genres]
        genres_placeholders = ", ".join([f":genre{i}" for i in range(len(genres_zh))])
        sql_conditions.append(f"genres ?| ARRAY[{genres_placeholders}]")
        for i, genre in enumerate(genres_zh):
            sql_params[f"genre{i}"] = genre
        
        genre_array = ", ".join([f"'{g}'" for g in genres_zh])
        genre_match_sql = f"""
            (SELECT COUNT(*) 
             FROM jsonb_array_elements_text(COALESCE(genres, '[]'::jsonb)) AS g
             WHERE g = ANY(ARRAY[{genre_array}]))
        """
        order_parts.append(f"({genre_match_sql}) * 10")
    
    # === 排除類型 ===
    if exclude_genres:
        exclude_zh = [GENRE_EN_TO_ZH.get(g, g) for g in exclude_genres]
        exclude_placeholders = ", ".join([f":exclude{i}" for i in range(len(exclude_zh))])
        sql_conditions.append(f"NOT (genres ?| ARRAY[{exclude_placeholders}])")
        for i, genre in enumerate(exclude_zh):
            sql_params[f"exclude{i}"] = genre
    
    # === 年份過濾 (硬性) - 支持多個範圍 (OR 邏輯) ⭐ ===
    if year_ranges and len(year_ranges) > 0:
        # 多個年份範圍 (OR 邏輯)
        # 例如: (year BETWEEN 1990 AND 1999) OR (year BETWEEN 2000 AND 2009)
        year_conditions = []
        for i, (y_min, y_max) in enumerate(year_ranges):
            year_conditions.append(
                f"EXTRACT(YEAR FROM release_date) BETWEEN :year{i}_min AND :year{i}_max"
            )
            sql_params[f"year{i}_min"] = y_min
            sql_params[f"year{i}_max"] = y_max
        
        sql_conditions.append(f"({' OR '.join(year_conditions)})")
    elif year_range:
        # 保留舊版單一範圍 (向下兼容)
        y_min, y_max = year_range
        sql_conditions.append("EXTRACT(YEAR FROM release_date) BETWEEN :year_min AND :year_max")
        sql_params["year_min"] = y_min
        sql_params["year_max"] = y_max
    
    # === 評分過濾 ===
    if min_rating:
        sql_conditions.append("vote_average >= :min_rating")
        sql_params["min_rating"] = min_rating
    
    # === 評分和人氣權重 ===
    order_parts.append("(vote_average - 5) * 3")
    order_parts.append("(popularity / 1000) * 2")
    
    # === 動態隨機權重（根據 randomness 參數）===
    # randomness = 0.0 → RANDOM() * 5 (幾乎不影響)
    # randomness = 0.3 → RANDOM() * 20 (中等影響)
    # randomness = 0.6 → RANDOM() * 35 (高度影響)
    # randomness = 1.0 → RANDOM() * 50 (可能完全打亂)
    random_weight = 5 + (randomness * 45)  # 5-50 範圍
    order_parts.append(f"RANDOM() * {random_weight:.1f}")
    
    # === 組合查詢 ===
    where_clause = " AND ".join(sql_conditions)
    order_clause = f"({' + '.join(order_parts)}) DESC"
    
    query = text(f"""
        SELECT 
            tmdb_id as id, title, overview, poster_path, release_date,
            vote_average, vote_count, popularity, genres, keywords, mood_tags,
            {' + '.join(order_parts)} as feature_score
        FROM movies
        WHERE {where_clause}
        ORDER BY {order_clause}
        LIMIT {limit}
    """)
    
    result = db_session.execute(query, sql_params)
    return [dict(row._mapping) for row in result]


async def recommend_movies_simple(
    user_input: str,
    db_session: Session,
    count: int = 10,
    selected_genres: List[str] = None,
    selected_moods: List[str] = None,
    randomness: float = 0.3
) -> List[Dict[str, Any]]:
    """
    簡化版推薦流程（已棄用 - 使用 recommend_movies_hybrid 替代）
    
    為了向後兼容保留，但直接調用新版 hybrid 推薦
    """
    print(f"\n⚠️ [Deprecated] recommend_movies_simple 已棄用，轉發到 recommend_movies_hybrid\n")
    
    return await recommend_movies_hybrid(
        user_input=user_input,
        db_session=db_session,
        count=count,
        selected_genres=selected_genres,
        selected_moods=selected_moods,
        randomness=randomness
    )
