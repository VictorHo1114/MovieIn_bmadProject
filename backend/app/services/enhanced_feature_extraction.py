# backend/app/services/enhanced_feature_extraction.py
"""
增強版 Feature Extraction - 解決語意斷層問題

"""
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

# 從映射表模組導入所有映射字典
from app.services.mapping_tables import (
    ZH_TO_EN_MOOD,
    ZH_TO_EN_KEYWORDS,
    MOOD_LABEL_TO_DB_TAGS
)

# ============================================================================
# 年代與類型常量定義
# ============================================================================

# 年代映射表 (前端顯示 ID → 年份範圍)
ERA_RANGE_MAP = {
    "60s": (1960, 1969),
    "70s": (1970, 1979),
    "80s": (1980, 1989),
    "90s": (1990, 1999),
    "00s": (2000, 2009),
    "10s": (2010, 2019),
    "20s": (2020, 2029),
}

# 簡體中文 → 繁體中文映射表 (DB 使用簡體，UI 顯示繁體)
GENRE_SIMPLIFIED_TO_TRADITIONAL = {
    "冒险": "冒險",
    "剧情": "劇情",
    "动作": "動作",
    "动画": "動畫",
    "历史": "歷史",
    "喜剧": "喜劇",
    "奇幻": "奇幻",
    "家庭": "家庭",
    "恐怖": "恐怖",
    "悬疑": "懸疑",
    "惊悚": "驚悚",
    "战争": "戰爭",
    "爱情": "愛情",
    "犯罪": "犯罪",
    "电视电影": "電視電影",
    "科幻": "科幻",
    "纪录": "紀錄",
    "西部": "西部",
    "音乐": "音樂",
}

# 繁體中文 → 簡體中文映射表 (前端傳繁體，後端轉簡體查詢)
GENRE_TRADITIONAL_TO_SIMPLIFIED = {v: k for k, v in GENRE_SIMPLIFIED_TO_TRADITIONAL.items()}

# ============================================================================
# 精確 Keyword 匹配器 (解決 "empire" 問題)
# ============================================================================

async def extract_exact_keyword_movies_from_db(
    user_input: str,
    db_session: Session
) -> List[Dict[str, Any]]:
    """
    從用戶輸入中提取包含精確 Keywords 的電影（完整電影資料）
    
    解決問題: 用戶輸入 "empire"  匹配包含 "empire" keyword 的電影
    """
    if not user_input or len(user_input.strip()) < 3:
        return []
    
    # 分詞（簡單版）
    words = [w.lower() for w in user_input.split() if len(w) >= 3]
    
    if not words:
        return []
    
    # 構建查詢（匹配 keywords 陣列）
    keyword_conditions = []
    params = {}
    
    for i, word in enumerate(words[:5]):  # 限制最多 5 個詞
        keyword_conditions.append(f"""
            EXISTS (
                SELECT 1 
                FROM jsonb_array_elements_text(keywords) AS kw
                WHERE LOWER(kw) LIKE :word{i}
            )
        """)
        params[f"word{i}"] = f"%{word}%"
    
    where_clause = " OR ".join(keyword_conditions)
    
    query = text(f"""
        SELECT 
            tmdb_id as id, title, overview, poster_path, release_date,
            vote_average, vote_count, popularity, genres, keywords, mood_tags,
            80 as feature_score
        FROM movies
        WHERE {where_clause}
        ORDER BY popularity DESC
        LIMIT 10
    """)
    
    result = db_session.execute(query, params)
    return [dict(row._mapping) for row in result]

async def extract_exact_keywords_from_db(
    user_input: str,
    db_session: Session
) -> List[str]:
    """
    從用戶輸入中提取資料庫中存在的 keywords（關鍵詞列表）
    
    支援中英雙語輸入：
    - 英文: "time travel" → ["time travel", "time-manipulation", ...]
    - 中文: "時間旅行" → ["time travel", "time-manipulation", ...] (先查映射表)
    
    用於後續的 SQL Feature Matching
    """
    if not user_input or len(user_input.strip()) == 0:
        return []
    
    matched = []
    
    # ========================================
    # Step 1: 中文 → 英文映射表查詢 (優先)
    # ========================================
    for zh_term, en_keyword in ZH_TO_EN_KEYWORDS.items():
        if zh_term in user_input:
            matched.append(en_keyword)
    
    # ========================================
    # Step 2: 英文分詞 + DB 匹配
    # ========================================
    words = [w.lower() for w in user_input.split() if len(w) >= 3]
    
    if words:
        # 查詢 DB 中所有 keywords
        query = text("""
            SELECT DISTINCT jsonb_array_elements_text(keywords) as keyword
            FROM movies
            WHERE keywords IS NOT NULL
            LIMIT 1000
        """)
        
        result = db_session.execute(query)
        db_keywords = {row[0].lower() for row in result}
        
        # 精確匹配
        for word in words:
            if word in db_keywords and word not in matched:
                matched.append(word)
        
        # 部分匹配（例如 "empire" 匹配 "galactic empire"）
        for db_keyword in db_keywords:
            for word in words:
                if word in db_keyword and word not in matched and db_keyword not in matched:
                    matched.append(db_keyword)
                    if len(matched) >= 15:
                        break
            if len(matched) >= 15:
                break
    
    # ========================================
    # Step 3: 中文字符級匹配 (Fallback)
    # ========================================
    # 如果中文輸入沒有在映射表中找到，嘗試字符級匹配
    # 例如: "機器" 可能匹配 "robot", "android"
    if not matched and any('\u4e00' <= c <= '\u9fff' for c in user_input):
        # 查詢 DB 中所有 keywords
        query = text("""
            SELECT DISTINCT jsonb_array_elements_text(keywords) as keyword
            FROM movies
            WHERE keywords IS NOT NULL
            LIMIT 1000
        """)
        
        result = db_session.execute(query)
        db_keywords = list({row[0].lower() for row in result})
        
        # 嘗試翻譯常見詞（簡單版）
        zh_chars = {
            "機": ["robot", "machine", "android"],
            "愛": ["love", "romance"],
            "戰": ["war", "battle", "fight"],
            "魔": ["magic", "demon"],
            "時": ["time"],
            "空": ["space"],
            "未": ["future"],
            "來": ["future"],
        }
        
        for char, potential_keywords in zh_chars.items():
            if char in user_input:
                for kw in potential_keywords:
                    if kw in db_keywords and kw not in matched:
                        matched.append(kw)
    
    return matched[:15]  # 限制數量

# ============================================================================
# 精確片名匹配器
# ============================================================================

async def extract_exact_titles_from_db(
    user_input: str,
    db_session: Session
) -> List[Dict[str, Any]]:
    """
    從用戶輸入中提取資料庫中的片名（完整電影資料）
    
    解決問題: 用戶輸入 "007"  匹配 "007: No Time to Die" 並返回完整資料
    """
    if not user_input or len(user_input.strip()) < 2:
        return []
    
    query = text("""
        SELECT 
            tmdb_id as id, title, overview, poster_path, release_date,
            vote_average, vote_count, popularity, genres, keywords, mood_tags,
            100 as feature_score
        FROM movies
        WHERE LOWER(title) LIKE :pattern
        ORDER BY popularity DESC
        LIMIT 5
    """)
    
    pattern = f"%{user_input.lower()}%"
    result = db_session.execute(query, {"pattern": pattern})
    
    return [dict(row._mapping) for row in result]

# ============================================================================
# 增強版 Feature Extraction（整合以上功能）
# ============================================================================

async def enhanced_feature_extraction(
    user_input: str,
    selected_moods: List[str],
    selected_genres: List[str],
    selected_eras: List[str],  # 新增: 年代篩選 ⭐
    db_session: Session
) -> Dict[str, Any]:
    """
    增強版特徵提取
    
    參數:
    - user_input: 用戶輸入的自然語言
    - selected_moods: 心情標籤 (如 ["輕鬆", "緊張"])
    - selected_genres: 類型標籤 (繁體中文，如 ["喜劇", "動作"])
    - selected_eras: 年代標籤 (如 ["90s", "00s"])
    
    返回:
    {
        "keywords": [...],          # 精確 + 映射 + GPT 提取
        "mood_tags": [...],         # 映射表精準匹配
        "genres": [...],            # 類型標籤 (簡體，供 DB 查詢)
        "year_ranges": [...],       # 年份範圍列表 (供 DB 查詢) ⭐
        "exact_matches": {
            "titles": [...],        # 片名精確匹配
            "keywords": [...]       # Keyword 精確匹配
        }
    }
    """
    # 轉換繁體類型為簡體 (供 DB 查詢)
    db_genres = []
    if selected_genres:
        for genre in selected_genres:
            simplified = GENRE_TRADITIONAL_TO_SIMPLIFIED.get(genre, genre)
            db_genres.append(simplified)
    
    result = {
        "keywords": [],
        "mood_tags": [],
        "genres": db_genres,  # 使用簡體中文供 DB 查詢
        "year_ranges": [],    # 新增: 年份範圍列表 ⭐
        "exact_matches": {
            "titles": [],
            "keywords": []
        },
        "exclude_genres": [],
        "year_range": None,   # 保留舊版 (單一範圍)
        "min_rating": None
    }
    
    # ========================================
    # 0. 年代篩選 → 年份範圍轉換 ⭐
    # ========================================
    
    if selected_eras:
        for era in selected_eras:
            if era in ERA_RANGE_MAP:
                result["year_ranges"].append(list(ERA_RANGE_MAP[era]))
    
    # 如果沒有選擇年代，year_ranges 保持為空 []
    
    # ========================================
    # 1. 精確匹配（優先級最高）
    # ========================================
    
    # 1a. 片名精確匹配（返回完整電影資料）
    if user_input:
        exact_title_movies = await extract_exact_titles_from_db(user_input, db_session)
        result["exact_matches"]["titles"] = exact_title_movies
    
    # 1b. Keyword 精確匹配（返回包含該 keyword 的電影）
    if user_input:
        exact_keyword_movies = await extract_exact_keyword_movies_from_db(user_input, db_session)
        result["exact_matches"]["keywords"] = exact_keyword_movies
        
        # 同時提取 keyword 列表供後續 SQL 使用
        exact_keywords = await extract_exact_keywords_from_db(user_input, db_session)
        result["keywords"].extend(exact_keywords)
    
    # ========================================
    # 2. Mood Label 映射表（精準匹配）
    # ========================================
    # 注意: Mood Label 不再包含 genres/year_range，這些由 Hard Filter 處理
    
    if selected_moods:
        for mood_label in selected_moods:
            if mood_label in MOOD_LABEL_TO_DB_TAGS:
                mapping = MOOD_LABEL_TO_DB_TAGS[mood_label]
                
                # 添加映射的 DB Mood Tags
                result["mood_tags"].extend(mapping.get("db_mood_tags", []))
                
                # 添加映射的 Keywords
                result["keywords"].extend(mapping.get("db_keywords", []))
                
                # 評分限制（僅保留 min_rating，不包含 genres/year_range）
                if "min_rating" in mapping:
                    if result["min_rating"] is None:
                        result["min_rating"] = mapping["min_rating"]
                    else:
                        result["min_rating"] = max(result["min_rating"], mapping["min_rating"])
    
    # ========================================
    # 2.5. 中文自然語言 → Mood Tags 映射
    # ========================================
    # 從用戶輸入的中文文字中提取 mood tags
    if user_input:
        for zh_mood, en_mood in ZH_TO_EN_MOOD.items():
            if zh_mood in user_input and en_mood not in result["mood_tags"]:
                result["mood_tags"].append(en_mood)
    
    # ========================================
    # 3. 自然語言簡單推斷（年份、語言）
    # ========================================
    
    if user_input:
        user_lower = user_input.lower()
        
        # 年份推斷（規則式）
        if not result["year_range"]:  # 只在 Mood 沒有設定時才推斷
            if any(word in user_input for word in ["近期", "最近", "新", "最新", "2024", "2025"]):
                result["year_range"] = [2020, 2025]
            elif any(word in user_input for word in ["經典", "老片", "復古", "懷舊"]):
                result["year_range"] = [1980, 2010]
            elif "90年代" in user_input or "九零年代" in user_input:
                result["year_range"] = [1990, 1999]
            elif "2000年代" in user_input or "零零年代" in user_input:
                result["year_range"] = [2000, 2009]
            elif "2010" in user_input:
                if "後" in user_input or "以後" in user_input:
                    result["year_range"] = [2010, 2025]
                else:
                    result["year_range"] = [2010, 2019]
        
        # 語言推斷（規則式）
        if any(word in user_input for word in ["日本", "日劇", "日影", "日系", "動畫"]):
            result["original_language"] = "ja"
        elif any(word in user_input for word in ["韓國", "韓劇", "韓影", "韓系"]):
            result["original_language"] = "ko"
        elif any(word in user_input for word in ["中文", "華語", "台灣", "香港"]):
            result["original_language"] = "zh"
        elif any(word in user_input for word in ["好萊塢", "美國", "歐美"]):
            result["original_language"] = "en"
    
    # ========================================
    # 4. 去重
    # ========================================
    
    result["keywords"] = list(set(result["keywords"]))[:15]
    result["mood_tags"] = list(set(result["mood_tags"]))[:10]
    result["genres"] = list(set(result["genres"]))
    result["exclude_genres"] = list(set(result["exclude_genres"]))
    
    return result

# ============================================================================
# 使用範例
# ============================================================================

if __name__ == "__main__":
    print(" Mood Label  DB Mood Tags 映射表")
    print("=" * 80)
    
    for mood_label, mapping in MOOD_LABEL_TO_DB_TAGS.items():
        print(f"\n【{mood_label}】")
        print(f"  DB Mood Tags: {mapping['db_mood_tags']}")
        print(f"  DB Keywords:  {mapping['db_keywords']}")
        print(f"  Genres:       {mapping['genres']}")
