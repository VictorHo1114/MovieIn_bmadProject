# backend/app/services/embedding_query_generator.py
"""
Embedding Query 生成器 - Phase 3.6
處理三種輸入情境，生成最佳 Embedding 查詢文本

三種情境：
1. 僅自然語言 (NL only)
   - 策略：直接使用自然語言作為查詢
   - 範例："難過的時候適合看什麼電影" → 直接使用

2. 僅 Mood Labels (Mood only)
   - 策略：生成 Relationship-aware Template
   - 依賴：mood_analyzer.analyze_mood_combination()
   - 範例：["emotional", "heartwarming"] → "A heartwarming story about emotional healing..."

3. 自然語言 + Mood Labels (Both)
   - 策略：NL 優先用於 Embedding Query
   - 衝突檢測：檢查 NL 與 Mood 是否語義衝突
   - Mood 保留用於 Feature Filtering

返回格式：
{
    "query": str,              # 用於 Embedding 的查詢文本
    "scenario": str,           # "nl_only" | "mood_only" | "both" | "empty"
    "mood_relationship": Dict, # Mood 關係資訊
    "conflict_detected": bool  # 是否檢測到衝突
}

使用場景：
- Phase 3.6 Embedding-First 推薦系統
- Step 1: Query Generation
- 在 recommend_movies_embedding_first() 中調用
"""

from typing import List, Optional, Dict
from .mood_analyzer import analyze_mood_combination, MOOD_RELATIONSHIP_MATRIX


def generate_embedding_query(
    natural_query: Optional[str],
    mood_labels: List[str],
    mood_relationship: Optional[Dict] = None
) -> Dict:
    """
    三情境處理：
    1. 僅 NL → 直接使用
    2. 僅 Mood → 關係感知模板
    3. NL + Mood → 分離處理（NL 優先）
    
    Args:
        natural_query: 用戶輸入的自然語言 (can be None)
        mood_labels: 英文 Mood Labels 列表 (e.g., ["emotional", "heartwarming"])
        mood_relationship: analyze_mood_combination() 的結果（可選）
    
    Returns:
        {
            "query": str,                # 用於 Embedding 的查詢文本
            "scenario": "nl_only" | "mood_only" | "both",
            "mood_relationship": Dict,   # Mood 關係資訊
            "conflict_detected": bool    # 是否檢測到衝突
        }
    
    Example:
        >>> generate_embedding_query(
        ...     natural_query="難過的時候適合看什麼",
        ...     mood_labels=[]
        ... )
        {
            "query": "難過的時候適合看什麼",
            "scenario": "nl_only",
            "mood_relationship": None,
            "conflict_detected": False
        }
    """
    # Handle None
    if natural_query is None:
        natural_query = ""
    
    has_nl = bool(natural_query.strip())
    has_moods = bool(mood_labels)
    
    # 情境 1: 僅自然語言
    if has_nl and not has_moods:
        return {
            "query": natural_query,
            "scenario": "nl_only",
            "mood_relationship": None,
            "conflict_detected": False
        }
    
    # 情境 3: 兩者皆有（分離處理）
    if has_nl and has_moods:
        # 檢測衝突
        conflict = detect_sentiment_conflict(natural_query, mood_labels)
        
        # 策略：NL 優先用於 Embedding Query
        # Mood 保留用於 Feature Filtering（在主推薦流程中處理）
        return {
            "query": natural_query,  # NL 優先
            "scenario": "both",
            "mood_relationship": mood_relationship or analyze_mood_combination(mood_labels),
            "conflict_detected": conflict
        }
    
    # 情境 2: 僅 Mood Labels
    if not has_nl and has_moods:
        # 分析 Mood 關係
        if mood_relationship is None:
            mood_relationship = analyze_mood_combination(mood_labels)
        
        # 生成模板
        template_text = generate_mood_template(mood_labels, mood_relationship)
        
        return {
            "query": template_text,
            "scenario": "mood_only",
            "mood_relationship": mood_relationship,
            "conflict_detected": False
        }
    
    # Fallback（無輸入）
    return {
        "query": "popular and highly rated movies",
        "scenario": "empty",
        "mood_relationship": None,
        "conflict_detected": False
    }


def generate_mood_template(
    mood_labels: List[str],
    relationship: Dict
) -> str:
    """
    根據 Mood 關係生成模板
    
    Args:
        mood_labels: ["emotional", "heartwarming"]
        relationship: {
            "type": "journey",
            "template": "A heartwarming story...",
            ...
        }
    
    Returns:
        生成的查詢文本
    
    Example:
        >>> generate_mood_template(
        ...     ["emotional", "heartwarming"],
        ...     {"type": "journey", "template": "A heartwarming story..."}
        ... )
        "A heartwarming story about emotional healing..."
    """
    rel_type = relationship.get("type", "simple")
    
    # 優先使用 Matrix 中的模板
    if "template" in relationship and relationship["template"] != "simple":
        return relationship["template"]
    
    # Fallback: 根據類型生成
    if rel_type == "journey":
        # 轉變關係
        if len(mood_labels) >= 2:
            return f"A story about transformation from {mood_labels[0]} to {mood_labels[1]}, emotional journey and character development"
        return f"A {mood_labels[0]} story about personal growth and transformation"
    
    elif rel_type == "paradox":
        # 矛盾關係
        if len(mood_labels) >= 2:
            return f"A movie that blends {mood_labels[0]} with {mood_labels[1]}, contrasting yet harmonious"
        return f"A {mood_labels[0]} film with unexpected contrasts"
    
    elif rel_type == "intensification":
        # 強化關係
        if len(mood_labels) >= 2:
            return f"A deeply {mood_labels[0]} and {mood_labels[1]} story, intensely emotional and atmospheric"
        return f"An intensely {mood_labels[0]} film"
    
    elif rel_type == "multi-faceted":
        # 多面向
        return f"A complex {' and '.join(mood_labels[:3])} film with layered storytelling"
    
    else:
        # Simple 或其他
        return f"A {' and '.join(mood_labels)} movie"


def detect_sentiment_conflict(
    natural_query: str,
    mood_labels: List[str]
) -> bool:
    """
    檢測 NL 與 Mood 是否衝突
    
    簡單版本：基於關鍵詞
    未來版本：基於 Embedding 語義距離
    
    Args:
        natural_query: "溫暖治癒的故事"
        mood_labels: ["dark", "gritty"]
    
    Returns:
        True if conflict detected, False otherwise
    
    Example:
        >>> detect_sentiment_conflict("溫暖治癒的故事", ["dark", "gritty"])
        True  # 溫暖 vs 黑暗 = 衝突
    """
    # 定義正面/負面關鍵詞
    POSITIVE_KEYWORDS = {
        # 中文
        "溫暖", "治癒", "療癒", "開心", "快樂", "歡樂", "振奮", "激勵",
        "正能量", "希望", "光明", "美好", "幸福", "甜蜜", "浪漫",
        # 英文
        "warm", "healing", "happy", "cheerful", "uplifting", "inspiring",
        "hopeful", "positive", "bright", "beautiful", "sweet", "romantic"
    }
    
    NEGATIVE_KEYWORDS = {
        # 中文
        "黑暗", "陰暗", "沉重", "悲傷", "難過", "憂鬱", "絕望", "痛苦",
        "殘酷", "恐怖", "驚悚", "壓抑", "灰暗", "冷酷",
        # 英文
        "dark", "gritty", "sad", "melancholic", "depressing", "disturbing",
        "harsh", "bleak", "grim", "tragic", "painful"
    }
    
    # 定義情緒分組
    POSITIVE_MOODS = {
        "cheerful", "lighthearted", "feel-good", "funny", "uplifting",
        "heartwarming", "comforting", "cozy", "inspiring", "hopeful",
        "romantic", "whimsical", "playful"
    }
    
    NEGATIVE_MOODS = {
        "dark", "gritty", "disturbing", "melancholic", "bittersweet",
        "heartbreaking", "intense", "suspenseful", "creepy", "eerie"
    }
    
    # 檢測 NL 中的情感傾向
    query_lower = natural_query.lower()
    nl_is_positive = any(keyword in query_lower for keyword in POSITIVE_KEYWORDS)
    nl_is_negative = any(keyword in query_lower for keyword in NEGATIVE_KEYWORDS)
    
    # 檢測 Mood Labels 中的情感傾向
    mood_set = set(mood_labels)
    moods_are_positive = bool(mood_set & POSITIVE_MOODS)
    moods_are_negative = bool(mood_set & NEGATIVE_MOODS)
    
    # 判斷衝突
    conflict = (
        (nl_is_positive and moods_are_negative) or
        (nl_is_negative and moods_are_positive)
    )
    
    return conflict


# ============================================================================
# 測試與範例
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Embedding Query Generator - 測試案例")
    print("=" * 60)
    
    # 測試案例 1: 僅自然語言
    print("\n【情境 1: 僅自然語言】")
    result1 = generate_embedding_query(
        natural_query="難過的時候適合看什麼",
        mood_labels=[]
    )
    print(f"輸入: NL='難過的時候適合看什麼', Moods=[]")
    print(f"情境: {result1['scenario']}")
    print(f"查詢文本: {result1['query']}")
    print(f"衝突: {result1['conflict_detected']}")
    
    # 測試案例 2: 僅 Mood Labels (Journey)
    print("\n【情境 2: 僅 Mood Labels - Journey】")
    result2 = generate_embedding_query(
        natural_query="",
        mood_labels=["emotional", "heartwarming"]
    )
    print(f"輸入: NL='', Moods=['emotional', 'heartwarming']")
    print(f"情境: {result2['scenario']}")
    print(f"查詢文本: {result2['query']}")
    print(f"Mood 關係: {result2['mood_relationship']['type']}")
    print(f"中文描述: {result2['mood_relationship'].get('zh_description', 'N/A')}")
    
    # 測試案例 3: 僅 Mood Labels (Paradox)
    print("\n【情境 2: 僅 Mood Labels - Paradox】")
    result3 = generate_embedding_query(
        natural_query="",
        mood_labels=["dark", "lighthearted"]
    )
    print(f"輸入: NL='', Moods=['dark', 'lighthearted']")
    print(f"情境: {result3['scenario']}")
    print(f"查詢文本: {result3['query']}")
    print(f"Mood 關係: {result3['mood_relationship']['type']}")
    
    # 測試案例 4: 僅 Mood Labels (Intensification)
    print("\n【情境 2: 僅 Mood Labels - Intensification】")
    result4 = generate_embedding_query(
        natural_query="",
        mood_labels=["emotional", "melancholic"]
    )
    print(f"輸入: NL='', Moods=['emotional', 'melancholic']")
    print(f"情境: {result4['scenario']}")
    print(f"查詢文本: {result4['query']}")
    print(f"Mood 關係: {result4['mood_relationship']['type']}")
    
    # 測試案例 5: 兩者皆有（無衝突）
    print("\n【情境 3: NL + Mood - 無衝突】")
    result5 = generate_embedding_query(
        natural_query="溫暖治癒的故事",
        mood_labels=["heartwarming", "uplifting"]
    )
    print(f"輸入: NL='溫暖治癒的故事', Moods=['heartwarming', 'uplifting']")
    print(f"情境: {result5['scenario']}")
    print(f"查詢文本: {result5['query']}")
    print(f"衝突: {result5['conflict_detected']}")
    
    # 測試案例 6: 兩者皆有（有衝突）
    print("\n【情境 3: NL + Mood - 有衝突】")
    result6 = generate_embedding_query(
        natural_query="溫暖治癒的故事",
        mood_labels=["dark", "gritty"]
    )
    print(f"輸入: NL='溫暖治癒的故事', Moods=['dark', 'gritty']")
    print(f"情境: {result6['scenario']}")
    print(f"查詢文本: {result6['query']} (NL 優先)")
    print(f"衝突: {result6['conflict_detected']} ⚠️")
    print(f"說明: Mood 保留用於 Feature Filtering")
    
    # 測試案例 7: 無輸入
    print("\n【情境 4: 無輸入】")
    result7 = generate_embedding_query(
        natural_query="",
        mood_labels=[]
    )
    print(f"輸入: NL='', Moods=[]")
    print(f"情境: {result7['scenario']}")
    print(f"查詢文本: {result7['query']}")
