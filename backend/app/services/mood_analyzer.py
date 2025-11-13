# backend/app/services/mood_analyzer.py
"""
Mood 組合分析器 - Phase 3.6
識別 Mood Labels 之間的語義關係

作用：
- 分析使用者選擇的多個 Mood Labels 之間的關係
- 生成 Relationship-aware Embedding Query Template
- 支援 4 種關係類型：Journey / Paradox / Intensification / Multi-faceted

數據來源：
- 基於實際 Database 中使用的 mood_tags 和 keywords
- 參考 mapping_tables.py 中的 MOOD_LABEL_TO_DB_TAGS
- 包含 51 個精心設計的 mood 關係配對

使用場景：
- Phase 3.6 Embedding Query Generation
- 情境 2: 僅 Mood Labels（無自然語言）
- 情境 3: NL + Mood（衝突檢測）

範例：
    >>> analyze_mood_combination(["emotional", "heartwarming"])
    {
        "type": "journey",
        "template": "A heartwarming story about emotional healing...",
        "confidence": "high",
        "source": "matrix"
    }
"""

from typing import List, Dict, Optional, Tuple

# ============================================================================
# MOOD_RELATIONSHIP_MATRIX - 基於 DB 實際數據
# ============================================================================
# 從 MOOD_LABEL_TO_DB_TAGS 中提取常見組合，建立語義關係
# 
# DB 中常見的 mood_tags：
# - emotional, melancholic, bittersweet, romantic (情感類)
# - cheerful, lighthearted, feel-good, funny, uplifting (正面類)
# - dark, gritty, mysterious, suspenseful, thrilling (黑暗類)
# - heartwarming, comforting, cozy, inspiring (溫暖類)
# - thought-provoking, philosophical, contemplative (深度類)
# - action-packed, exciting, intense, fast-paced (動作類)
# - fantastical, whimsical, magical, imaginative, dreamy (奇幻類)

MOOD_RELATIONSHIP_MATRIX: Dict[Tuple[str, str], Dict] = {
    
    # ========================================================================
    # Journey (轉變) - 情感旅程，從 A 狀態轉變到 B 狀態
    # ========================================================================
    
    # 悲傷 → 治癒
    ("emotional", "heartwarming"): {
        "type": "journey",
        "description": "Emotional transformation from sadness to warmth",
        "template": "A heartwarming story about emotional healing and finding comfort, a journey from pain to hope",
        "zh_description": "從悲傷到溫暖的情感轉變"
    },
    ("melancholic", "uplifting"): {
        "type": "journey",
        "description": "Rising from melancholy to inspiration",
        "template": "An uplifting narrative about overcoming melancholy, finding strength and hope",
        "zh_description": "從憂鬱中振作、找到力量"
    },
    ("bittersweet", "inspiring"): {
        "type": "journey",
        "description": "Bittersweet journey to inspiration",
        "template": "A bittersweet yet inspiring story of growth and resilience",
        "zh_description": "苦澀中的成長與啟發"
    },
    
    # 黑暗 → 光明
    ("dark", "uplifting"): {
        "type": "journey",
        "description": "Journey from darkness to light",
        "template": "A powerful narrative moving from dark themes towards uplifting moments, finding light in darkness",
        "zh_description": "從黑暗走向光明"
    },
    ("dark", "heartwarming"): {
        "type": "journey",
        "description": "Dark to heartwarming transformation",
        "template": "A story that transforms dark experiences into heartwarming moments of humanity",
        "zh_description": "在黑暗中發現溫暖人性"
    },
    ("gritty", "hopeful"): {
        "type": "journey",
        "description": "Hope emerging from harsh reality",
        "template": "A gritty yet hopeful story about finding hope in harsh circumstances",
        "zh_description": "殘酷現實中萌芽的希望"
    },
    
    # 失落 → 找到
    ("melancholic", "feel-good"): {
        "type": "journey",
        "description": "From melancholy to feeling good",
        "template": "A feel-good story about moving past melancholy and rediscovering joy",
        "zh_description": "走出憂鬱、重拾快樂"
    },
    
    # 孤獨 → 連結
    ("contemplative", "heartwarming"): {
        "type": "journey",
        "description": "From solitary contemplation to human warmth",
        "template": "A contemplative journey leading to heartwarming connections",
        "zh_description": "從孤獨沉思到溫暖連結"
    },
    
    # 迷失 → 成長
    ("mysterious", "inspiring"): {
        "type": "journey",
        "description": "Mystery leading to self-discovery",
        "template": "A mysterious journey of self-discovery and inspiration",
        "zh_description": "神秘旅程中的自我發現"
    },
    
    # ========================================================================
    # Paradox (矛盾) - 看似矛盾但共存的情緒，營造複雜氛圍
    # ========================================================================
    
    # 黑暗 + 輕鬆
    ("dark", "lighthearted"): {
        "type": "paradox",
        "description": "Contrasting blend of dark and light",
        "template": "A movie that skillfully blends dark themes with lighthearted moments, balancing humor and depth",
        "zh_description": "黑色幽默、在黑暗中保持輕鬆"
    },
    ("dark", "funny"): {
        "type": "paradox",
        "description": "Dark comedy paradox",
        "template": "A darkly funny film mixing serious themes with comedy",
        "zh_description": "黑色喜劇、嚴肅議題的幽默呈現"
    },
    
    # 悲傷 + 歡樂
    ("emotional", "cheerful"): {
        "type": "paradox",
        "description": "Bittersweet emotional mix",
        "template": "A bittersweet story mixing emotional depth with cheerful moments",
        "zh_description": "悲喜交織、情感豐富"
    },
    ("melancholic", "funny"): {
        "type": "paradox",
        "description": "Melancholic humor",
        "template": "A melancholic yet funny narrative about life's complexities",
        "zh_description": "憂鬱中的幽默、生活的複雜性"
    },
    
    # 殘酷 + 美麗
    ("gritty", "romantic"): {
        "type": "paradox",
        "description": "Gritty romance paradox",
        "template": "A gritty yet romantic story of love in harsh circumstances",
        "zh_description": "殘酷現實中的浪漫愛情"
    },
    ("intense", "heartwarming"): {
        "type": "paradox",
        "description": "Intense warmth",
        "template": "An intensely heartwarming story with emotional depth",
        "zh_description": "強烈而溫暖的情感衝擊"
    },
    
    # 神秘 + 溫馨
    ("mysterious", "cozy"): {
        "type": "paradox",
        "description": "Cozy mystery",
        "template": "A mysterious yet cozy narrative with intriguing comfort",
        "zh_description": "溫馨的神秘氛圍"
    },
    
    # 驚悚 + 浪漫
    ("suspenseful", "romantic"): {
        "type": "paradox",
        "description": "Romantic suspense",
        "template": "A suspenseful romantic story blending tension with passion",
        "zh_description": "懸疑浪漫、緊張與激情並存"
    },
    
    # 哲學 + 歡樂
    ("philosophical", "lighthearted"): {
        "type": "paradox",
        "description": "Light philosophical exploration",
        "template": "A lighthearted yet philosophical exploration of life's questions",
        "zh_description": "輕鬆探討深刻議題"
    },
    
    # ========================================================================
    # Intensification (強化) - 相似情緒疊加，強化氛圍
    # ========================================================================
    
    # 深度悲傷
    ("emotional", "melancholic"): {
        "type": "intensification",
        "description": "Deep emotional melancholy",
        "template": "A deeply emotional and melancholic story, profoundly moving and contemplative",
        "zh_description": "極致悲傷、深刻動人"
    },
    ("melancholic", "bittersweet"): {
        "type": "intensification",
        "description": "Intensified melancholic mood",
        "template": "A bittersweet and melancholic narrative of profound sadness",
        "zh_description": "濃烈的憂鬱與苦澀"
    },
    ("heartbreaking", "emotional"): {
        "type": "intensification",
        "description": "Intensely heartbreaking",
        "template": "A heartbreaking and emotional story that deeply moves the soul",
        "zh_description": "撕心裂肺的情感衝擊"
    },
    
    # 強化黑暗
    ("dark", "gritty"): {
        "type": "intensification",
        "description": "Intensely dark atmosphere",
        "template": "An intensely dark and gritty film, raw and unflinching in its portrayal",
        "zh_description": "極致黑暗、殘酷寫實"
    },
    ("dark", "disturbing"): {
        "type": "intensification",
        "description": "Deeply disturbing darkness",
        "template": "A dark and disturbing narrative that challenges comfort zones",
        "zh_description": "極度不安的黑暗氛圍"
    },
    ("mysterious", "suspenseful"): {
        "type": "intensification",
        "description": "Heightened mystery and suspense",
        "template": "A mysterious and suspenseful thriller keeping you on edge",
        "zh_description": "懸疑神秘、緊張感十足"
    },
    
    # 強化歡樂
    ("cheerful", "lighthearted"): {
        "type": "intensification",
        "description": "Pure joy and lightness",
        "template": "A cheerful and lighthearted film full of joy and laughter",
        "zh_description": "純粹的歡樂與輕鬆"
    },
    ("feel-good", "uplifting"): {
        "type": "intensification",
        "description": "Intensely uplifting",
        "template": "A feel-good and uplifting story that lifts your spirits",
        "zh_description": "極度振奮人心"
    },
    ("funny", "lighthearted"): {
        "type": "intensification",
        "description": "Comedy intensification",
        "template": "A funny and lighthearted comedy for pure entertainment",
        "zh_description": "純粹的喜劇娛樂"
    },
    
    # 強化溫暖
    ("heartwarming", "comforting"): {
        "type": "intensification",
        "description": "Deep warmth and comfort",
        "template": "A heartwarming and comforting story that soothes the soul",
        "zh_description": "極致溫暖、療癒心靈"
    },
    ("heartwarming", "cozy"): {
        "type": "intensification",
        "description": "Cozy heartwarming feeling",
        "template": "A cozy and heartwarming film perfect for comfort",
        "zh_description": "溫馨舒適、暖心治癒"
    },
    ("uplifting", "inspiring"): {
        "type": "intensification",
        "description": "Powerful inspiration",
        "template": "An uplifting and inspiring story of triumph and hope",
        "zh_description": "強大的激勵與啟發"
    },
    
    # 強化刺激
    ("action-packed", "exciting"): {
        "type": "intensification",
        "description": "Maximum excitement",
        "template": "An action-packed and exciting thrill ride from start to finish",
        "zh_description": "極致刺激、腎上腺素爆發"
    },
    ("thrilling", "intense"): {
        "type": "intensification",
        "description": "Intense thriller",
        "template": "A thrilling and intense experience that grips you tight",
        "zh_description": "強烈緊張、扣人心弦"
    },
    ("fast-paced", "exciting"): {
        "type": "intensification",
        "description": "High-speed excitement",
        "template": "A fast-paced and exciting adventure that never slows down",
        "zh_description": "快節奏、持續刺激"
    },
    
    # 強化深度
    ("thought-provoking", "philosophical"): {
        "type": "intensification",
        "description": "Deep philosophical exploration",
        "template": "A thought-provoking and philosophical film exploring profound questions",
        "zh_description": "深度哲學思考"
    },
    ("contemplative", "philosophical"): {
        "type": "intensification",
        "description": "Contemplative depth",
        "template": "A contemplative and philosophical meditation on existence",
        "zh_description": "深刻沉思、哲學冥想"
    },
    ("mind-bending", "thought-provoking"): {
        "type": "intensification",
        "description": "Cerebral complexity",
        "template": "A mind-bending and thought-provoking puzzle that challenges perception",
        "zh_description": "燒腦、挑戰思維"
    },
    
    # 強化奇幻
    ("fantastical", "whimsical"): {
        "type": "intensification",
        "description": "Pure fantasy",
        "template": "A fantastical and whimsical journey into imagination",
        "zh_description": "極致奇幻、天馬行空"
    },
    ("magical", "imaginative"): {
        "type": "intensification",
        "description": "Magical imagination",
        "template": "A magical and imaginative world of wonder",
        "zh_description": "魔幻想像、奇妙世界"
    },
    ("dreamy", "atmospheric"): {
        "type": "intensification",
        "description": "Dreamlike atmosphere",
        "template": "A dreamy and atmospheric film with poetic visuals",
        "zh_description": "夢幻意境、詩意氛圍"
    },
    
    # ========================================================================
    # Multi-faceted (多面向) - 複雜組合，展現多元面向
    # ========================================================================
    
    # 情感複雜
    ("emotional", "thought-provoking"): {
        "type": "multi-faceted",
        "description": "Emotionally and intellectually engaging",
        "template": "An emotional and thought-provoking film that touches both heart and mind",
        "zh_description": "情感與思想的雙重衝擊"
    },
    ("romantic", "thought-provoking"): {
        "type": "multi-faceted",
        "description": "Romantic depth",
        "template": "A romantic and thought-provoking exploration of love and relationships",
        "zh_description": "深度浪漫、探討愛情本質"
    },
    
    # 刺激與深度
    ("thrilling", "thought-provoking"): {
        "type": "multi-faceted",
        "description": "Intelligent thriller",
        "template": "A thrilling and thought-provoking narrative that entertains and challenges",
        "zh_description": "智慧型驚悚、娛樂與深度並存"
    },
    ("action-packed", "emotional"): {
        "type": "multi-faceted",
        "description": "Emotional action",
        "template": "An action-packed film with emotional depth and character development",
        "zh_description": "動作與情感並重"
    },
    
    # 奇幻與深度
    ("fantastical", "thought-provoking"): {
        "type": "multi-faceted",
        "description": "Philosophical fantasy",
        "template": "A fantastical yet thought-provoking journey with deeper meaning",
        "zh_description": "富含哲理的奇幻旅程"
    },
    ("whimsical", "emotional"): {
        "type": "multi-faceted",
        "description": "Whimsical emotion",
        "template": "A whimsical and emotional story that charms and moves",
        "zh_description": "奇妙又動人的情感故事"
    },
    
    # 溫暖與深度
    ("heartwarming", "thought-provoking"): {
        "type": "multi-faceted",
        "description": "Warm and meaningful",
        "template": "A heartwarming and thought-provoking film about humanity",
        "zh_description": "溫暖而有深度的人性探討"
    },
    
    # 冒險與情感
    ("adventurous", "emotional"): {
        "type": "multi-faceted",
        "description": "Emotional adventure",
        "template": "An adventurous journey filled with emotional moments",
        "zh_description": "充滿情感的冒險旅程"
    },
    ("adventurous", "inspiring"): {
        "type": "multi-faceted",
        "description": "Inspiring adventure",
        "template": "An adventurous and inspiring tale of courage and discovery",
        "zh_description": "激勵人心的冒險故事"
    },
    
    # 神秘與情感
    ("mysterious", "emotional"): {
        "type": "multi-faceted",
        "description": "Emotional mystery",
        "template": "A mysterious and emotional narrative with layered storytelling",
        "zh_description": "情感豐富的神秘故事"
    },
    
    # 史詩與情感
    ("epic", "emotional"): {
        "type": "multi-faceted",
        "description": "Epic emotion",
        "template": "An epic and emotional saga spanning great scope and intimate moments",
        "zh_description": "史詩格局、情感細膩"
    },
    ("epic", "inspiring"): {
        "type": "multi-faceted",
        "description": "Epic inspiration",
        "template": "An epic and inspiring story of heroism and triumph",
        "zh_description": "史詩般的激勵故事"
    },
}


# ============================================================================
# 核心函數
# ============================================================================

def analyze_mood_combination(mood_labels: List[str]) -> Dict:
    """
    混合方法：Matrix 優先，Vector 補充
    
    Args:
        mood_labels: ["emotional", "heartwarming"] (英文 mood tags)
    
    Returns:
        {
            "type": "journey" | "paradox" | "intensification" | "multi-faceted",
            "template": str,
            "description": str,
            "zh_description": str,
            "confidence": "high" | "medium" | "low",
            "source": "matrix" | "vector" | "default"
        }
    
    Example:
        >>> analyze_mood_combination(["emotional", "heartwarming"])
        {
            "type": "journey",
            "template": "A heartwarming story about emotional healing...",
            "confidence": "high",
            "source": "matrix"
        }
    """
    # 單一 Mood
    if len(mood_labels) <= 1:
        return {
            "type": "simple",
            "template": "simple",
            "description": "Single mood",
            "zh_description": "單一情緒",
            "confidence": "high",
            "source": "default"
        }
    
    # Phase 1: Matrix 查詢（優先）
    # 嘗試所有可能的兩兩組合
    for i, mood1 in enumerate(mood_labels):
        for mood2 in mood_labels[i+1:]:
            # 嘗試正序
            if (mood1, mood2) in MOOD_RELATIONSHIP_MATRIX:
                relationship = MOOD_RELATIONSHIP_MATRIX[(mood1, mood2)]
                return {
                    "type": relationship["type"],
                    "template": relationship["template"],
                    "description": relationship["description"],
                    "zh_description": relationship.get("zh_description", ""),
                    "confidence": "high",
                    "source": "matrix"
                }
            # 嘗試反序
            elif (mood2, mood1) in MOOD_RELATIONSHIP_MATRIX:
                relationship = MOOD_RELATIONSHIP_MATRIX[(mood2, mood1)]
                return {
                    "type": relationship["type"],
                    "template": relationship["template"],
                    "description": relationship["description"],
                    "zh_description": relationship.get("zh_description", ""),
                    "confidence": "high",
                    "source": "matrix"
                }
    
    # Phase 2: 啟發式判斷（基於 mood 語義）
    heuristic_result = analyze_by_heuristics(mood_labels)
    if heuristic_result:
        return heuristic_result
    
    # Phase 3: Vector 補充（TODO: 未來實現）
    # vector_result = analyze_by_semantic_vector(mood_labels)
    # if vector_result["confidence"] > 0.7:
    #     return vector_result
    
    # Fallback
    return {
        "type": "multi-faceted",
        "template": f"A {' and '.join(mood_labels)} film with complex emotional layers",
        "description": "Complex multi-faceted mood combination",
        "zh_description": "複雜多面向的情緒組合",
        "confidence": "low",
        "source": "default"
    }


def analyze_by_heuristics(mood_labels: List[str]) -> Optional[Dict]:
    """
    基於啟發式規則判斷關係類型
    
    規則：
    1. 如果包含相反情緒（dark + light, sad + happy）→ Paradox
    2. 如果包含相似情緒（sad + melancholic）→ Intensification
    3. 如果包含轉變關係（sad + healing）→ Journey
    """
    # 定義情緒分組
    POSITIVE_MOODS = {
        "cheerful", "lighthearted", "feel-good", "funny", "uplifting",
        "heartwarming", "comforting", "cozy", "inspiring", "hopeful"
    }
    
    NEGATIVE_MOODS = {
        "dark", "gritty", "disturbing", "melancholic", "bittersweet",
        "emotional", "heartbreaking", "intense", "suspenseful"
    }
    
    ENERGETIC_MOODS = {
        "action-packed", "exciting", "thrilling", "fast-paced", "intense"
    }
    
    CALM_MOODS = {
        "contemplative", "philosophical", "dreamy", "atmospheric", "cozy"
    }
    
    mood_set = set(mood_labels)
    
    # 檢測矛盾關係
    has_positive = bool(mood_set & POSITIVE_MOODS)
    has_negative = bool(mood_set & NEGATIVE_MOODS)
    has_energetic = bool(mood_set & ENERGETIC_MOODS)
    has_calm = bool(mood_set & CALM_MOODS)
    
    if (has_positive and has_negative) or (has_energetic and has_calm):
        return {
            "type": "paradox",
            "template": f"A complex film blending {' and '.join(mood_labels[:2])} elements",
            "description": "Contrasting mood combination",
            "zh_description": "矛盾情緒的複雜融合",
            "confidence": "medium",
            "source": "heuristic"
        }
    
    # 檢測強化關係（相似情緒）
    if (len(mood_set & POSITIVE_MOODS) >= 2 or 
        len(mood_set & NEGATIVE_MOODS) >= 2):
        return {
            "type": "intensification",
            "template": f"A deeply {mood_labels[0]} film with intensified {mood_labels[1]} atmosphere",
            "description": "Intensified similar moods",
            "zh_description": "相似情緒的強化",
            "confidence": "medium",
            "source": "heuristic"
        }
    
    return None


# TODO: 未來擴展
def analyze_by_semantic_vector(mood_labels: List[str]) -> Dict:
    """
    使用 Embedding 計算 Mood 之間的語義距離
    自動識別關係類型
    
    實現方向：
    1. 為每個 mood tag 生成 Embedding
    2. 計算 pairwise similarity
    3. 基於相似度判斷關係：
       - similarity > 0.7 → intensification
       - similarity < 0.3 → paradox
       - 其他 → multi-faceted 或 journey
    """
    pass


# ============================================================================
# 輔助函數
# ============================================================================

def get_relationship_stats() -> Dict:
    """
    獲取 MOOD_RELATIONSHIP_MATRIX 統計資訊
    """
    stats = {
        "total": len(MOOD_RELATIONSHIP_MATRIX),
        "by_type": {
            "journey": 0,
            "paradox": 0,
            "intensification": 0,
            "multi-faceted": 0
        }
    }
    
    for relationship in MOOD_RELATIONSHIP_MATRIX.values():
        rel_type = relationship["type"]
        stats["by_type"][rel_type] += 1
    
    return stats


def search_relationships_by_mood(mood: str) -> List[Dict]:
    """
    搜尋包含特定 mood 的所有關係
    
    Args:
        mood: "emotional"
    
    Returns:
        包含該 mood 的所有關係列表
    """
    results = []
    for (mood1, mood2), relationship in MOOD_RELATIONSHIP_MATRIX.items():
        if mood == mood1 or mood == mood2:
            results.append({
                "moods": (mood1, mood2),
                "type": relationship["type"],
                "description": relationship["description"]
            })
    return results


# ============================================================================
# 測試與驗證
# ============================================================================

if __name__ == "__main__":
    # 統計資訊
    stats = get_relationship_stats()
    print(f"MOOD_RELATIONSHIP_MATRIX 統計：")
    print(f"總關係數：{stats['total']}")
    print(f"Journey: {stats['by_type']['journey']}")
    print(f"Paradox: {stats['by_type']['paradox']}")
    print(f"Intensification: {stats['by_type']['intensification']}")
    print(f"Multi-faceted: {stats['by_type']['multi-faceted']}")
    print()
    
    # 測試案例
    test_cases = [
        (["emotional", "heartwarming"], "Journey: 悲傷→溫暖"),
        (["dark", "lighthearted"], "Paradox: 黑色幽默"),
        (["emotional", "melancholic"], "Intensification: 深度悲傷"),
        (["emotional", "thought-provoking"], "Multi-faceted: 情感與思想"),
        (["cheerful"], "Simple: 單一情緒"),
    ]
    
    print("測試案例：")
    for mood_labels, expected in test_cases:
        result = analyze_mood_combination(mood_labels)
        print(f"\n輸入: {mood_labels}")
        print(f"預期: {expected}")
        print(f"結果: {result['type']} - {result.get('zh_description', 'N/A')}")
        print(f"信心: {result['confidence']} ({result['source']})")
