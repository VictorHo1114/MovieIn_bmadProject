# backend/app/services/mapping_tables.py
"""
中英文映射表集合
用於支援雙語 Feature Extraction
"""

# ============================================================================
# 中文  英文 Mood Tags 映射表
# ============================================================================
# 涵蓋 29 個 DB mood_tags，每個 mood 平均 4-7 個中文變體
# 總計: 141 條映射

ZH_TO_EN_MOOD = {
    # action-packed (動作充沛)
    "動作": "action-packed",
    "動作片": "action-packed",
    "動作場面": "action-packed",
    "動作戲": "action-packed",
    "爽片": "action-packed",
    
    # adventurous (冒險)
    "冒險": "adventurous",
    "探險": "adventurous",
    "歷險": "adventurous",
    "冒險片": "adventurous",
    
    # bittersweet (苦樂參半)
    "苦甜": "bittersweet",
    "苦樂參半": "bittersweet",
    "悲喜交加": "bittersweet",
    "百感交集": "bittersweet",
    
    # cheerful (歡樂)
    "歡樂": "cheerful",
    "愉快": "cheerful",
    "歡快": "cheerful",
    "開朗": "cheerful",
    "快樂": "cheerful",
    
    # cozy (溫馨)
    "溫馨": "cozy",
    "溫暖": "cozy",
    "舒適": "cozy",
    "溫馨感": "cozy",
    "療癒": "cozy",
    
    # creepy (詭異)
    "詭異": "creepy",
    "陰森": "creepy",
    "毛骨悚然": "creepy",
    "恐怖": "creepy",
    "驚悚": "creepy",
    
    # dark (黑暗)
    "黑暗": "dark",
    "陰暗": "dark",
    "暗黑": "dark",
    "沉重": "dark",
    "灰暗": "dark",
    "陰鬱": "dark",
    
    # disturbing (不安)
    "不安": "disturbing",
    "令人不安": "disturbing",
    "不適": "disturbing",
    "不舒服": "disturbing",
    "驚悚": "disturbing",
    
    # eerie (詭譎)
    "詭譎": "eerie",
    "詭祕": "eerie",
    "神祕": "eerie",
    "怪異": "eerie",
    "詭異": "eerie",
    
    # emotional (感性)
    "感動": "emotional",
    "感性": "emotional",
    "情感": "emotional",
    "情緒": "emotional",
    "動人": "emotional",
    "情感豐富": "emotional",
    "催淚": "emotional",
    
    # epic (史詩)
    "史詩": "epic",
    "壯闊": "epic",
    "宏大": "epic",
    "磅礴": "epic",
    "史詩級": "epic",
    "恢弘": "epic",
    
    # exciting (興奮)
    "興奮": "exciting",
    "刺激": "exciting",
    "激動": "exciting",
    "令人興奮": "exciting",
    "精彩": "exciting",
    
    # feel-good (療癒)
    "療癒": "feel-good",
    "治癒": "feel-good",
    "舒心": "feel-good",
    "正能量": "feel-good",
    "暖心": "feel-good",
    "愉悅": "feel-good",
    
    # funny (搞笑)
    "搞笑": "funny",
    "幽默": "funny",
    "好笑": "funny",
    "爆笑": "funny",
    "有趣": "funny",
    "喜劇": "funny",
    "詼諧": "funny",
    
    # heartwarming (暖心)
    "暖心": "heartwarming",
    "溫馨": "heartwarming",
    "感人": "heartwarming",
    "溫暖": "heartwarming",
    "窩心": "heartwarming",
    
    # hopeful (希望)
    "希望": "hopeful",
    "充滿希望": "hopeful",
    "樂觀": "hopeful",
    "光明": "hopeful",
    "正向": "hopeful",
    
    # inspiring (激勵)
    "激勵": "inspiring",
    "勵志": "inspiring",
    "啟發": "inspiring",
    "鼓舞": "inspiring",
    "振奮": "inspiring",
    "感召": "inspiring",
    
    # intense (緊張)
    "緊張": "intense",
    "強烈": "intense",
    "激烈": "intense",
    "緊湊": "intense",
    "張力": "intense",
    
    # lighthearted (輕鬆)
    "輕鬆": "lighthearted",
    "輕快": "lighthearted",
    "輕鬆愉快": "lighthearted",
    "無壓力": "lighthearted",
    "休閒": "lighthearted",
    
    # melancholic (憂鬱)
    "憂鬱": "melancholic",
    "悲傷": "melancholic",
    "哀傷": "melancholic",
    "傷心": "melancholic",
    "憂傷": "melancholic",
    "悲涼": "melancholic",
    "難過": "melancholic",
    "憂愁": "melancholic",
    
    # mysterious (神秘)
    "神秘": "mysterious",
    "神祕": "mysterious",
    "謎樣": "mysterious",
    "懸疑": "mysterious",
    "玄妙": "mysterious",
    
    # passionate (熱情)
    "熱情": "passionate",
    "激情": "passionate",
    "狂熱": "passionate",
    "熱烈": "passionate",
    "澎湃": "passionate",
    
    # romantic (浪漫)
    "浪漫": "romantic",
    "愛情": "romantic",
    "戀愛": "romantic",
    "浪漫愛情": "romantic",
    "羅曼蒂克": "romantic",
    
    # suspenseful (懸疑)
    "懸疑": "suspenseful",
    "懸念": "suspenseful",
    "吊人胃口": "suspenseful",
    "懸疑感": "suspenseful",
    
    # terrifying (恐怖)
    "恐怖": "terrifying",
    "可怕": "terrifying",
    "驚嚇": "terrifying",
    "嚇人": "terrifying",
    "驚悚": "terrifying",
    
    # thought-provoking (發人深省)
    "發人深省": "thought-provoking",
    "深刻": "thought-provoking",
    "引人思考": "thought-provoking",
    "有深度": "thought-provoking",
    "深度": "thought-provoking",
    "省思": "thought-provoking",
    
    # thrilling (驚險)
    "驚險": "thrilling",
    "刺激": "thrilling",
    "驚心動魄": "thrilling",
    "緊張刺激": "thrilling",
    
    # uplifting (振奮)
    "振奮": "uplifting",
    "提升": "uplifting",
    "昂揚": "uplifting",
    "激昂": "uplifting",
    "提振": "uplifting",
    
    # whimsical (異想天開)
    "異想天開": "whimsical",
    "奇幻": "whimsical",
    "夢幻": "whimsical",
    "奇異": "whimsical",
    "想像力": "whimsical",
}

# ============================================================================
# 中文  英文 Keywords 映射表
# ============================================================================
# 涵蓋常用主題詞、角色、場景、事件
# 總計: 67 條映射

ZH_TO_EN_KEYWORDS = {
    # 時間相關
    "時間旅行": "time travel",
    "穿越": "time travel",
    "時空旅行": "time travel",
    "時光倒流": "time travel",
    "未來": "future",
    "過去": "past",
    
    # 角色類型
    "超級英雄": "superhero",
    "英雄": "hero",
    "反派": "villain",
    "機器人": "robot",
    "AI": "artificial intelligence",
    "人工智慧": "artificial intelligence",
    "外星人": "alien",
    "殭屍": "zombie",
    "吸血鬼": "vampire",
    "怪物": "monster",
    "魔法": "magic",
    "巫師": "wizard",
    "間諜": "spy",
    "特工": "spy",
    "偵探": "detective",
    "殺手": "assassin",
    
    # 主題
    "末日": "apocalypse",
    "世界末日": "apocalypse",
    "災難": "disaster",
    "戰爭": "war",
    "革命": "revolution",
    "反抗": "rebellion",
    "愛情": "love",
    "友情": "friendship",
    "家庭": "family",
    "復仇": "revenge",
    "救贖": "redemption",
    "背叛": "betrayal",
    "陰謀": "conspiracy",
    
    # 場景/設定
    "太空": "space",
    "外太空": "outer space",
    "宇宙": "universe",
    "星際": "space",
    "海底": "underwater",
    "沙漠": "desert",
    "叢林": "jungle",
    "城市": "urban",
    "鄉村": "rural",
    
    # 動作/事件
    "追逐": "chase",
    "逃亡": "escape",
    "調查": "investigation",
    "謀殺": "murder",
    "犯罪": "crime",
    "搶劫": "heist",
    "冒險": "adventure",
    "探險": "exploration",
    "求生": "survival",
    "生存": "survival",
    
    # 情感/關係
    "失戀": "heartbreak",
    "分手": "breakup",
    "結婚": "wedding",
    "離婚": "divorce",
    "成長": "coming-of-age",
    "青春": "youth",
    "校園": "school",
    
    # 類型特定
    "喜劇": "comedy",
    "懸疑": "mystery",
    "驚悚": "thriller",
    "恐怖": "horror",
    "科幻": "science fiction",
    "奇幻": "fantasy",
}

# ============================================================================
# Mood Label → DB Mood Tags 映射表 (優化版)
# ============================================================================
# 職責: 純情感/氛圍標籤，不包含 genres/year_range (由 Hard Filter 處理)
# exclude_genres 只在用戶沒有選擇類型時才生效

MOOD_LABEL_TO_DB_TAGS = {
    # === 情緒相關 ===
    "失戀": {
        "db_mood_tags": ["emotional", "melancholic", "bittersweet", "romantic"],
        "db_keywords": ["heartbreak", "love", "breakup", "loss", "romance"],
        "category": "情緒",
        "description": "心碎、需要療癒"
    },
    "開心": {
        "db_mood_tags": ["cheerful", "lighthearted", "feel-good", "funny", "uplifting"],
        "db_keywords": ["fun", "happy", "comedy", "joy", "laughter"],
        "category": "情緒",
        "description": "想要歡笑、輕鬆愉快"
    },
    "憂鬱": {
        "db_mood_tags": ["melancholic", "dark", "emotional", "thought-provoking"],
        "db_keywords": ["depression", "sadness", "melancholy", "despair"],
        "category": "情緒",
        "description": "情緒低落、需要共鳴"
    },
    "想哭": {
        "db_mood_tags": ["emotional", "heartwarming", "bittersweet", "inspiring"],
        "db_keywords": ["tearjerker", "touching", "moving", "emotional"],
        "category": "情緒",
        "description": "需要情緒宣洩"
    },
    "興奮": {
        "db_mood_tags": ["exciting", "thrilling", "action-packed", "intense", "epic"],
        "db_keywords": ["adrenaline", "excitement", "action", "thriller"],
        "category": "情緒",
        "description": "想要刺激、腎上腺素"
    },
    
    # === 情境相關 ===
    "派對": {
        "db_mood_tags": ["exciting", "funny", "lighthearted", "action-packed"],
        "db_keywords": ["entertaining", "crowd-pleasing", "fun", "party"],
        "category": "情境",
        "description": "與朋友一起看、氣氛熱鬧"
    },
    "獨自一人": {
        "db_mood_tags": ["thought-provoking", "mysterious", "emotional", "dark"],
        "db_keywords": ["introspective", "contemplative", "solo", "reflection"],
        "category": "情境",
        "description": "一個人安靜觀賞"
    },
    "約會": {
        "db_mood_tags": ["romantic", "heartwarming", "passionate", "feel-good"],
        "db_keywords": ["romance", "love", "date", "charming", "sweet"],
        "category": "情境",
        "description": "浪漫氛圍、適合情侶"
    },
    "家庭時光": {
        "db_mood_tags": ["heartwarming", "feel-good", "uplifting", "whimsical"],
        "db_keywords": ["family", "wholesome", "kids", "children"],
        "category": "情境",
        "description": "全家一起看、老少咸宜"
    },
    
    # === 觀影目的 ===
    "認真觀影": {
        "db_mood_tags": ["thought-provoking", "emotional", "inspiring", "dark"],
        "db_keywords": ["masterpiece", "artistic", "profound", "critically acclaimed"],
        "category": "觀影目的",
        "description": "想要深度、藝術性",
        "min_rating": 7.5
    },
    "感受經典": {
        "db_mood_tags": ["epic", "inspiring", "thought-provoking", "emotional"],
        "db_keywords": ["classic", "timeless", "iconic", "legendary"],
        "category": "觀影目的",
        "description": "經典名作、影史地位",
        "min_rating": 8.0
    },
    "放鬆腦袋": {
        "db_mood_tags": ["lighthearted", "funny", "feel-good", "cheerful"],
        "db_keywords": ["entertainment", "easy", "relax", "light"],
        "category": "觀影目的",
        "description": "不用思考、純娛樂"
    },
    "週末早晨": {
        "db_mood_tags": ["heartwarming", "uplifting", "feel-good", "cozy"],
        "db_keywords": ["morning", "breakfast", "relaxing", "cozy"],
        "category": "氛圍",
        "description": "輕鬆愉快的早晨"
    },
    "深夜觀影": {
        "db_mood_tags": ["mysterious", "dark", "suspenseful", "thrilling"],
        "db_keywords": ["mystery", "suspense", "thriller", "night"],
        "category": "氛圍",
        "description": "深夜觀影、神秘氛圍"
    },
    "視覺饗宴": {
        "db_mood_tags": ["epic", "exciting", "action-packed"],
        "db_keywords": ["visual effects", "spectacle", "cinematic", "stunning"],
        "category": "體驗",
        "description": "震撼視覺、特效大片"
    },
    "動作冒險": {
        "db_mood_tags": ["action-packed", "thrilling", "adventurous", "exciting"],
        "db_keywords": ["action", "adventure", "hero", "quest"],
        "category": "體驗",
        "description": "刺激冒險、熱血沸騰"
    },
    "腦洞大開": {
        "db_mood_tags": ["thought-provoking", "mysterious", "whimsical"],
        "db_keywords": ["mind-bending", "surreal", "creative", "imaginative"],
        "category": "體驗",
        "description": "天馬行空、腦洞大開"
    }
}

# ============================================================================
# 輔助函數
# ============================================================================

def get_mood_label_list():
    """
    獲取所有 Mood Labels 的列表（用於前端顯示）
    從 MOOD_LABEL_TO_DB_TAGS 自動生成
    """
    result = []
    for mood_id, mood_data in MOOD_LABEL_TO_DB_TAGS.items():
        result.append({
            "id": mood_id,
            "description": mood_data.get("description", ""),
            "category": mood_data.get("category", "其他")
        })
    return result
