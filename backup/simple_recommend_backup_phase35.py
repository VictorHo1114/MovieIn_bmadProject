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
        # 修復：genres 可能是 list of dicts 或 list of strings
        if genres and isinstance(genres[0], dict):
            main_genre = genres[0].get("name", "Unknown")
        elif genres and isinstance(genres[0], str):
            main_genre = genres[0]
        else:
            main_genre = "Unknown"
        
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
    
    # === Step 2: 三層漸進式 Feature Matching (Phase 2 ⭐) ===
    print(f"📍 [Step 2] 三層漸進式 Feature Matching (Phase 2)")
    print(f"{'-'*70}")
    
    # 使用新的三層漸進式匹配替代原本的 sql_feature_matching
    candidates = await tiered_feature_matching(
        keywords=user_keywords,
        mood_tags=user_mood_tags,
        genres=intent.get("genres", []),
        exclude_genres=intent.get("exclude_genres", []),
        year_range=intent.get("year_range"),  # 舊版單一範圍
        year_ranges=features.get("year_ranges"),  # 新版多個範圍 ⭐
        min_rating=intent.get("min_rating"),
        db_session=db_session,
        target_count=count * 15,  # 目標候選數量
        randomness=randomness  # 傳遞隨機性參數
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
            movie['match_ratio'] = 1.0  # 精確匹配視為 100%
            merged_candidates.append(movie)
            seen_ids.add(movie['id'])
    
    # 2. 精確關鍵詞匹配（次高優先級）
    for movie in exact_keyword_matches:
        if movie['id'] not in seen_ids:
            movie['is_exact_keyword_match'] = True
            movie['feature_score'] = movie.get('feature_score', 0) + 30  # Boost
            movie['match_ratio'] = movie.get('match_ratio', 0.9)  # 高匹配度
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
    
    # === Step 3: 智能判斷（Phase 3: 雙引擎模式判定）===
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
    
    # Phase 3 ⭐ 雙引擎並行模式
    enable_dual_engine = HYBRID_CONFIG.get("enable_dual_engine", False)
    
    if enable_dual_engine:
        decision_icon = "� Dual-Engine (並行融合)"
        print(f"🎯 決策: {decision_icon}")
        print(f"   評分: {score}/100, 閾值: {HYBRID_CONFIG['decision_threshold']}")
        print(f"   策略: Feature + Embedding 並行執行，加權融合")
    else:
        decision_icon = "�🔮 Embedding" if use_embedding else "⚡ Feature"
        print(f"🎯 決策: {decision_icon} (評分: {score}/100, 閾值: {HYBRID_CONFIG['decision_threshold']})")
    
    print(f"\n📋 評分細節:")
    print(f"    {reason_details}")
    print(f"{'-'*70}\n")
    
    # === Step 4: 路徑選擇（Phase 3: 雙引擎並行 or 單一路徑）===
    if enable_dual_engine:
        # ========================================
        # Phase 3 ⭐ 雙引擎並行 + 加權融合
        # ========================================
        print(f"📍 [Step 4] 🔥 雙引擎並行推薦")
        print(f"{'-'*70}")
        print(f"🚀 並行執行 Feature Matching + Embedding Reranking...")
        
        # 初始化 embedding_scores 字典
        embedding_scores = {}
        
        # 只有在有用戶輸入時才執行 Embedding
        if user_input and len(user_input.strip()) > 0:
            print(f"   🔮 Embedding 路徑: 調用語義匹配...")
            try:
                from app.services.embedding_service import rerank_by_semantic_similarity
                
                diversity_weight = 0.3 + (randomness * 0.4)
                
                reranked = await rerank_by_semantic_similarity(
                    query_text=user_input,
                    candidate_movies=candidates,
                    db_session=db_session,
                    top_k=len(candidates),  # 獲取所有候選的分數
                    diversity_weight=diversity_weight,
                    boost_exact_matches=True
                )
                
                # 建立 movie_id → embedding_score 映射
                for movie in reranked:
                    embedding_scores[movie['id']] = movie.get('similarity_score', 0)
                
                print(f"   ✓ Embedding 完成: {len(embedding_scores)} 部電影獲得語義分數")
            except Exception as e:
                print(f"   ⚠ Embedding 失敗: {e}，將只使用 Feature 分數")
        else:
            print(f"   ⚠ 無用戶輸入，跳過 Embedding 路徑")
        
        # === Phase 3.5 核心：四象限邏輯 ===
        enable_quadrant = HYBRID_CONFIG.get("enable_quadrant_logic", False)
        
        if enable_quadrant:
            print(f"\n   🎯 四象限分類與加權融合...")
            
            # 統計各象限電影數量
            quadrant_stats = {
                'q1_perfect': 0,
                'q2_feature_trust': 0,
                'q3_semantic_discovery': 0,
                'q4_filtered': 0
            }
            
            for movie in candidates:
                embedding_score = embedding_scores.get(movie["id"], 0)
                
                # 分類到象限
                quadrant = classify_to_quadrant(movie, embedding_score, HYBRID_CONFIG)
                movie['quadrant'] = quadrant
                quadrant_stats[quadrant] += 1
                
                # 計算象限專屬分數
                final_score = calculate_quadrant_score(
                    movie, embedding_score, quadrant, HYBRID_CONFIG
                )
                movie["final_score"] = final_score
                movie["embedding_score"] = embedding_score * 100  # 歸一化顯示
            
            # 顯示象限統計
            print(f"   📊 象限分佈:")
            print(f"      Q1 完美匹配: {quadrant_stats['q1_perfect']} 部 (高Match + 高Embedding)")
            print(f"      Q2 Feature可信: {quadrant_stats['q2_feature_trust']} 部 (高Match + 低Embedding)")
            print(f"      Q3 語義發現: {quadrant_stats['q3_semantic_discovery']} 部 (低Match + 高Embedding)")
            print(f"      Q4 過濾: {quadrant_stats['q4_filtered']} 部 (低Match + 低Embedding)")
            
            # 按象限優先級 + final_score 排序
            quadrant_priority = {
                'q1_perfect': 1,
                'q2_feature_trust': 2,
                'q3_semantic_discovery': 3,
                'q4_filtered': 4
            }
            candidates.sort(
                key=lambda x: (quadrant_priority[x['quadrant']], -x.get("final_score", 0))
            )
            
            print(f"   ✓ 四象限排序完成")
            
        else:
            # === Phase 3 原版：統一加權融合 ===
            print(f"\n   🎯 統一加權融合三個分數...")
            weights = HYBRID_CONFIG.get("fusion_weights", {
                "feature_score": 0.4,
                "embedding_score": 0.3,
                "match_ratio": 0.3
            })
            
            for movie in candidates:
                feature_score = movie.get("feature_score", 0)
                embedding_score = embedding_scores.get(movie["id"], 0) * 100  # 歸一化到 0-100
                match_ratio = movie.get("match_ratio", 0)
                
                # 融合公式
                final_score = (
                    feature_score * weights["feature_score"] +
                    embedding_score * weights["embedding_score"] +
                    match_ratio * 100 * weights["match_ratio"]
                )
                
                movie["final_score"] = final_score
                movie["embedding_score"] = embedding_score  # 保存以供前端顯示
                movie['quadrant'] = 'legacy'  # 標記為舊版
            
            # 按 final_score 排序
            candidates.sort(key=lambda x: x.get("final_score", 0), reverse=True)
            
            print(f"   ✓ 融合權重: Feature {weights['feature_score']*100:.0f}% + " +
                  f"Embedding {weights['embedding_score']*100:.0f}% + " +
                  f"Match {weights['match_ratio']*100:.0f}%")
        
        # 多樣性過濾
        results = diversity_filter(
            candidates=candidates,
            top_k=count,
            randomness=randomness
        )
        
        print(f"   ✓ 雙引擎完成，返回 {len(results)} 部電影")
        print(f"{'-'*70}\n")
        
    elif use_embedding:
        # ========================================
        # 原有的 Embedding-only 路徑
        # ========================================
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
            "feature_score": movie.get("feature_score", 0.0),
            "match_ratio": movie.get("match_ratio", 0.0),      # Phase 2 ⭐
            "match_count": movie.get("match_count", 0),         # Phase 2 ⭐
            "total_features": movie.get("total_features", 0),   # Phase 2 ⭐
            "final_score": movie.get("final_score", 0.0),       # Phase 3 ⭐
            "embedding_score": movie.get("embedding_score", 0.0), # Phase 3 ⭐
            "quadrant": movie.get("quadrant", "unknown")         # Phase 3.5 ⭐
        })
        print(f"   {i}. {movie.get('title')} ({display_year}) - ⭐{movie.get('vote_average', 0):.1f}")
    
    print(f"\n{'='*70}")
    print(f"✨ [Complete] 推薦完成！策略: {decision_icon}")
    print(f"{'='*70}\n")
    
    return formatted_results


# ============================================
# Phase 2: 三層漸進式 Feature Matching
# ============================================

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


async def tiered_feature_matching(
    keywords: List[str],
    mood_tags: List[str],
    genres: List[str],
    exclude_genres: List[str] = None,
    year_range: tuple = None,
    year_ranges: List[List[int]] = None,
    min_rating: float = None,
    db_session: Session = None,
    target_count: int = 10,
    randomness: float = 0.3
) -> List[Dict]:
    """
    三層漸進式 Feature Matching (Phase 2 核心功能)
    
    🎯 解決問題：選越多 mood labels 越不準
    
    📊 三層策略：
    - Tier 1 (嚴格): Match Ratio >= 80% (必須符合 80%+ 特徵)
    - Tier 2 (平衡): Match Ratio >= 50% (必須符合 50%+ 特徵)
    - Tier 3 (寬鬆): Match Ratio >= 0% (任一符合即可，原本的 OR 邏輯)
    
    📈 漸進執行：
    1. 先嘗試 Tier 1，如果 >= target_count → 返回
    2. 不夠則嘗試 Tier 2，合併結果，如果 >= target_count → 返回
    3. 還不夠則執行 Tier 3 (保底)
    
    ✅ 優點：
    - 選越多 labels → Tier 1 返回越精準的結果
    - 選少量 labels → 也能保證有結果 (降級到 Tier 2/3)
    - 保留原有的多樣性和隨機性
    """
    print(f"\n🎯 [Tiered Matching] 三層漸進式匹配開始")
    print(f"   - Target Count: {target_count}")
    print(f"   - Features: {len(keywords)} keywords, {len(mood_tags)} moods, {len(genres)} genres")
    print(f"{'-'*70}")
    
    # === Tier 1: 嚴格模式 (80%+ 符合) ===
    print(f"\n📍 Tier 1: 嚴格模式 (Match Ratio >= 80%)")
    
    # 先獲取較大的候選集 (Tier 3 的結果)
    all_candidates = await sql_feature_matching(
        keywords=keywords,
        mood_tags=mood_tags,
        genres=genres,
        exclude_genres=exclude_genres,
        year_range=year_range,
        year_ranges=year_ranges,
        min_rating=min_rating,
        db_session=db_session,
        limit=target_count * 20,  # 獲取足夠大的候選池
        randomness=randomness
    )
    
    # 計算每部電影的 match_ratio
    for movie in all_candidates:
        movie['match_ratio'] = calculate_match_ratio(
            movie, keywords, mood_tags, genres
        )
        movie['match_count'] = int(movie['match_ratio'] * (len(keywords) + len(mood_tags) + len(genres)))
        movie['total_features'] = len(keywords) + len(mood_tags) + len(genres)
    
    # Tier 1 篩選 (>= 80%)
    tier1_results = [m for m in all_candidates if m['match_ratio'] >= 0.8]
    tier1_results.sort(key=lambda x: (x['match_ratio'], x.get('feature_score', 0)), reverse=True)
    
    print(f"   ✓ 找到 {len(tier1_results)} 部電影符合 >=80%")
    if tier1_results:
        top = tier1_results[0]
        print(f"   - Top: {top['title']} (符合 {top['match_ratio']*100:.0f}% = {top['match_count']}/{top['total_features']})")
    
    if len(tier1_results) >= target_count:
        results = tier1_results[:target_count]
        print(f"   🎉 Tier 1 已足夠，返回 {len(results)} 部電影")
        return results
    
    # === Tier 2: 平衡模式 (50%+ 符合) ===
    print(f"\n📍 Tier 2: 平衡模式 (Match Ratio >= 50%)")
    
    tier2_results = [m for m in all_candidates if 0.5 <= m['match_ratio'] < 0.8]
    tier2_results.sort(key=lambda x: (x['match_ratio'], x.get('feature_score', 0)), reverse=True)
    
    print(f"   ✓ 找到 {len(tier2_results)} 部電影符合 50%-79%")
    if tier2_results:
        top = tier2_results[0]
        print(f"   - Top: {top['title']} (符合 {top['match_ratio']*100:.0f}% = {top['match_count']}/{top['total_features']})")
    
    # 合併 Tier 1 + Tier 2
    combined = tier1_results + tier2_results
    combined.sort(key=lambda x: (x['match_ratio'], x.get('feature_score', 0)), reverse=True)
    
    if len(combined) >= target_count:
        results = combined[:target_count]
        print(f"   🎉 Tier 1+2 已足夠，返回 {len(results)} 部電影")
        print(f"      (Tier 1: {len(tier1_results)}, Tier 2: {len(results) - len(tier1_results)})")
        return results
    
    # === Tier 3: 寬鬆模式 (任一符合) ===
    print(f"\n📍 Tier 3: 寬鬆模式 (Match Ratio >= 0%, 保底)")
    
    tier3_results = [m for m in all_candidates if m['match_ratio'] < 0.5]
    tier3_results.sort(key=lambda x: x.get('feature_score', 0), reverse=True)
    
    print(f"   ✓ 找到 {len(tier3_results)} 部電影符合 <50%")
    
    # 合併所有層級
    final_results = tier1_results + tier2_results + tier3_results
    final_results = final_results[:target_count]
    
    print(f"\n   🎉 返回 {len(final_results)} 部電影")
    print(f"      (Tier 1: {len(tier1_results)}, Tier 2: {len(tier2_results)}, Tier 3: {len(final_results) - len(tier1_results) - len(tier2_results)})")
    print(f"{'-'*70}\n")
    
    return final_results


# ============================================================================
# Phase 3.6: Embedding 候選過濾
# ============================================================================

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

def classify_to_quadrant(
    movie: Dict,
    embedding_score: float,
    config: Dict = None
) -> str:
    """
    將電影分類到四個象限
    
    Args:
        movie: 電影資料（必須包含 match_ratio）
        embedding_score: Embedding 相似度分數 (0-1)
        config: 配置參數
    
    Returns:
        quadrant: 'q1_perfect', 'q2_feature_trust', 'q3_semantic_discovery', 'q4_filtered'
    """
    cfg = config or HYBRID_CONFIG
    thresholds = cfg.get("quadrant_thresholds", {
        "high_match": 0.6,
        "high_embedding": 0.5
    })
    
    match_ratio = movie.get('match_ratio', 0)
    
    high_match = match_ratio >= thresholds["high_match"]
    high_embedding = embedding_score >= thresholds["high_embedding"]
    
    if high_match and high_embedding:
        return 'q1_perfect'
    elif high_match and not high_embedding:
        return 'q2_feature_trust'
    elif not high_match and high_embedding:
        return 'q3_semantic_discovery'
    else:
        return 'q4_filtered'


def calculate_quadrant_score(
    movie: Dict,
    embedding_score: float,
    quadrant: str,
    config: Dict = None
) -> float:
    """
    根據象限計算最終分數
    
    Args:
        movie: 電影資料（包含 feature_score, match_ratio）
        embedding_score: Embedding 相似度分數 (0-1)
        quadrant: 象限類型
        config: 配置參數
    
    Returns:
        final_score: 最終融合分數
    """
    cfg = config or HYBRID_CONFIG
    weights = cfg.get("quadrant_weights", {}).get(quadrant, {
        "feature": 0.4,
        "embedding": 0.3,
        "match": 0.3
    })
    
    feature_score = movie.get('feature_score', 0)
    match_ratio = movie.get('match_ratio', 0)
    
    final_score = (
        feature_score * weights.get('feature', 0.4) +
        embedding_score * 100 * weights.get('embedding', 0.3) +
        match_ratio * 100 * weights.get('match', 0.3)
    )
    
    return final_score


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


# ============================================================================
# ============================================================================
# Phase 3.6: Embedding-First 主推薦函數 ⭐ 最新架構
# ============================================================================
# 
# 架構變化：
# - Primary Engine: Embedding Similarity Search (300 候選)
# - Secondary Engine: Feature-based Filtering (300→150)
# - 三象限分類: Q1 完美 / Q2 語義發現 / Q4 候補
# - 混合排序: Quadrant 優先 + Embedding Score 排序
# 
# 與 Phase 3.5 的差異：
# - 3.5: Feature → Embedding (Feature 主導，Embedding 輔助)
# - 3.6: Embedding → Feature (Embedding 主導，Feature 驗證)
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

