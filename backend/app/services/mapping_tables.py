# backend/app/services/mapping_tables.py
"""
中英文映射表集合
用於支援雙語 Feature Extraction
"""

# ============================================================================
# 中文 → 英文 Mood Tags 映射表
# ============================================================================
# 涵蓋 44 個 DB mood_tags（包含 GPT 生成的 15 個新 tags）
# 每個 mood 平均 4-7 個中文變體
# 總計: 230+ 條映射

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
    
    # === 新增: GPT 生成的 Mood Tags ===
    
    # atmospheric (氛圍感)
    "氛圍": "atmospheric",
    "氛圍感": "atmospheric",
    "有氛圍": "atmospheric",
    "意境": "atmospheric",
    "氣氛": "atmospheric",
    
    # comforting (安慰)
    "安慰": "comforting",
    "慰藉": "comforting",
    "撫慰": "comforting",
    "安撫": "comforting",
    
    # contemplative (沉思)
    "沉思": "contemplative",
    "思考": "contemplative",
    "反思": "contemplative",
    "冥想": "contemplative",
    
    # dreamy (夢幻)
    "夢幻": "dreamy",
    "如夢": "dreamy",
    "夢境": "dreamy",
    "迷幻": "dreamy",
    
    # empowering (賦權)
    "賦權": "empowering",
    "充滿力量": "empowering",
    "力量感": "empowering",
    "增強信心": "empowering",
    
    # engaging (吸引人)
    "吸引人": "engaging",
    "引人入勝": "engaging",
    "扣人心弦": "engaging",
    "投入": "engaging",
    
    # fantastical (幻想)
    "奇幻": "fantastical",
    "幻想": "fantastical",
    "奇異世界": "fantastical",
    
    # fast-paced (節奏快)
    "節奏快": "fast-paced",
    "快節奏": "fast-paced",
    "緊湊": "fast-paced",
    "節奏明快": "fast-paced",
    
    # gritty (粗獷)
    "粗獷": "gritty",
    "寫實": "gritty",
    "殘酷": "gritty",
    "硬派": "gritty",
    "黑暗寫實": "gritty",
    
    # heartbreaking (心碎)
    "心碎": "heartbreaking",
    "令人心碎": "heartbreaking",
    "撕心裂肺": "heartbreaking",
    "虐心": "heartbreaking",
    
    # imaginative (富想像力)
    "富想像力": "imaginative",
    "創意": "imaginative",
    "創新": "imaginative",
    "有創意": "imaginative",
    
    # magical (魔幻)
    "魔幻": "magical",
    "魔法般": "magical",
    "神奇": "magical",
    "奇蹟": "magical",
    
    # mind-bending (燒腦)
    "燒腦": "mind-bending",
    "腦洞": "mind-bending",
    "顛覆": "mind-bending",
    "反轉": "mind-bending",
    
    # philosophical (哲學)
    "哲學": "philosophical",
    "哲理": "philosophical",
    "哲思": "philosophical",
    "人生": "philosophical",
    
    # realistic (寫實)
    "寫實": "realistic",
    "真實": "realistic",
    "紀實": "realistic",
    "現實": "realistic",
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
        "db_mood_tags": ["thought-provoking", "mysterious", "whimsical", "mind-bending", "imaginative"],
        "db_keywords": ["mind-bending", "surreal", "creative", "imaginative"],
        "category": "體驗",
        "description": "天馬行空、腦洞大開"
    },
    "燒腦懸疑": {
        "db_mood_tags": ["mind-bending", "mysterious", "suspenseful", "philosophical", "contemplative"],
        "db_keywords": ["mind-bending", "mystery", "plot twist", "complex"],
        "category": "體驗",
        "description": "複雜劇情、需要動腦"
    },
    "溫暖治癒": {
        "db_mood_tags": ["heartwarming", "comforting", "feel-good", "uplifting", "cozy"],
        "db_keywords": ["heartwarming", "wholesome", "comforting", "touching"],
        "category": "體驗",
        "description": "溫暖人心、療癒心靈"
    },
    "快節奏刺激": {
        "db_mood_tags": ["fast-paced", "thrilling", "action-packed", "exciting", "intense"],
        "db_keywords": ["fast-paced", "adrenaline", "action", "thriller"],
        "category": "體驗",
        "description": "節奏明快、緊張刺激"
    },
    "奇幻冒險": {
        "db_mood_tags": ["fantastical", "adventurous", "magical", "imaginative", "whimsical"],
        "db_keywords": ["fantasy", "magic", "adventure", "magical"],
        "category": "體驗",
        "description": "魔幻世界、冒險旅程"
    },
    "寫實殘酷": {
        "db_mood_tags": ["gritty", "realistic", "dark", "intense", "thought-provoking"],
        "db_keywords": ["realistic", "gritty", "harsh reality", "social"],
        "category": "體驗",
        "description": "殘酷現實、寫實刻劃"
    },
    "夢幻意境": {
        "db_mood_tags": ["dreamy", "atmospheric", "contemplative", "whimsical", "magical"],
        "db_keywords": ["surreal", "dreamlike", "atmospheric", "poetic"],
        "category": "氛圍",
        "description": "夢幻氛圍、詩意畫面"
    },
    "力量滿滿": {
        "db_mood_tags": ["empowering", "inspiring", "uplifting", "hopeful", "intense"],
        "db_keywords": ["empowerment", "strength", "courage", "inspiration"],
        "category": "情緒",
        "description": "充滿力量、激勵人心"
    },
    "扣人心弦": {
        "db_mood_tags": ["engaging", "suspenseful", "thrilling", "intense", "emotional"],
        "db_keywords": ["gripping", "engaging", "captivating", "compelling"],
        "category": "體驗",
        "description": "引人入勝、難以移開目光"
    },
    "心碎虐心": {
        "db_mood_tags": ["heartbreaking", "emotional", "melancholic", "bittersweet", "dark"],
        "db_keywords": ["heartbreaking", "tragic", "sad", "tear-jerking"],
        "category": "情緒",
        "description": "虐心催淚、情感強烈"
    }
}

# ============================================================================
# 年代與類型映射表（從 enhanced_feature_extraction.py 遷移）
# ============================================================================

# 年代映射表 (前端顯示 ID → 年份範圍)
# 使用位置: simple_recommend_router.py - 將 "90s" 轉換為 [1990, 1999]
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
# 使用位置: simple_recommend_router.py - /system-info API 顯示前端選項
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
# 使用位置: simple_recommend.py - tiered_feature_filtering() 轉換類型查詢
GENRE_TRADITIONAL_TO_SIMPLIFIED = {v: k for k, v in GENRE_SIMPLIFIED_TO_TRADITIONAL.items()}

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
