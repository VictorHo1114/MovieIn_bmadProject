# backend/app/routers/simple_recommend_router.py
"""
智能混合推薦 Router (Feature + Embedding)
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.orm import Session
from db.database import SessionLocal, get_db
from app.services.simple_recommend import recommend_movies_embedding_first
from app.services.mapping_tables import get_mood_label_list  # 修改導入 ⭐

router = APIRouter(prefix="/api/recommend/v2", tags=["recommend-v2"])

class SimpleRecommendRequest(BaseModel):
    query: str
    selected_genres: Optional[List[str]] = None  # 類型標籤 (繁體中文)
    selected_moods: Optional[List[str]] = None   # 心情/情境標籤
    selected_eras: Optional[List[str]] = None    # 年代標籤 (如 ["90s", "00s"])

@router.post("/movies")
async def get_simple_recommendations(
    request: SimpleRecommendRequest,
    db: Session = Depends(get_db)
):
    """
    Phase 3.6 Embedding-First 推薦 API
    
    架構流程：
    1. Embedding Query Generation: 智能生成查詢文本
    2. Embedding Similarity Search: 全庫語義搜索 (Top 300)
    3. Tiered Feature Filtering: 三層漸進式過濾 (→150)
    4. 3-Quadrant Classification: Q1完美/Q2發現/Q4候補
    5. Dynamic Scoring: 動態權重計算
    6. Mixed Sorting: 象限優先 + 分數排序
    7. Smart Selection: Top N 保證 + 隨機池多樣性
    
    參數：
    - query: 自然語言查詢（如 "難過的時候適合看什麼電影"）
    - selected_moods: 心情/情境標籤（如 ["heartwarming", "uplifting"]）
    - selected_genres: 類型標籤（如 ["劇情", "愛情"]）
    - selected_eras: 年代標籤（如 ["90s", "00s"]）
    
    返回：
    - movies: 推薦電影列表（包含 embedding_score, match_ratio, quadrant）
    - strategy: "Phase36-EmbeddingFirst"
    - version: "3.6"
    """
    try:
        # Phase 3.6: Embedding-First 架構（唯一推薦引擎）
        from app.services.mapping_tables import ERA_RANGE_MAP
        
        # 將 selected_eras 轉換為 year_ranges
        year_ranges = None
        if request.selected_eras:
            year_ranges = [ERA_RANGE_MAP.get(era, [2000, 2009]) for era in request.selected_eras]
        
        results = await recommend_movies_embedding_first(
            natural_query=request.query or "",
            mood_labels=request.selected_moods or [],
            genres=request.selected_genres or [],
            year_ranges=year_ranges,
            db_session=db,
            count=10
        )
        
        return {
            "success": True,
            "query": request.query,
            "count": len(results),
            "movies": results,
            "strategy": "Phase36-EmbeddingFirst",
            "version": "3.6",
            "config": {
                "architecture": "Embedding-First",
                "primary_engine": "Embedding Similarity Search",
                "secondary_engine": "Feature Filtering",
                "quadrants": 3
            }
        }
        
    except Exception as e:
        print(f"[Error] 推薦失敗: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/mood-labels")
async def get_mood_labels():
    """
    獲取所有可用的 Mood Labels
    
    返回格式：
    [
        {"id": "失戀", "description": "心碎、需要療癒", "category": "情緒"},
        {"id": "派對", "description": "與朋友一起看、氣氛熱鬧", "category": "情境"},
        ...
    ]
    """
    try:
        labels = get_mood_label_list()
        return {
            "success": True,
            "count": len(labels),
            "labels": labels
        }
    except Exception as e:
        print(f"[Error] 獲取 Mood Labels 失敗: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/system-info")
async def get_system_info():
    """
    獲取混合推薦系統資訊
    
    返回系統配置、評分權重、閾值等資訊
    """
    from app.services.simple_recommend import HYBRID_CONFIG
    from app.services.mapping_tables import (
        ERA_RANGE_MAP,
        GENRE_SIMPLIFIED_TO_TRADITIONAL
    )
    
    return {
        "success": True,
        "system": "Hybrid Recommendation System (Feature + Embedding)",
        "version": "2.0",
        "config": HYBRID_CONFIG,
        "filter_options": {
            "eras": [
                {"id": "60s", "label": "60年代", "range": [1960, 1969]},
                {"id": "70s", "label": "70年代", "range": [1970, 1979]},
                {"id": "80s", "label": "80年代", "range": [1980, 1989]},
                {"id": "90s", "label": "90年代", "range": [1990, 1999]},
                {"id": "00s", "label": "00年代", "range": [2000, 2009]},
                {"id": "10s", "label": "10年代", "range": [2010, 2019]},
                {"id": "20s", "label": "20年代", "range": [2020, 2029]},
            ],
            "genres": list(GENRE_SIMPLIFIED_TO_TRADITIONAL.values()),  # 繁體中文
            "max_selections": {
                "eras": 3,
                "genres": 3
            }
        },
        "scoring_dimensions": {
            "keywords_coverage": {"weight": "-30/-15/0", "description": "Keywords 覆蓋度"},
            "mood_tags_coverage": {"weight": "-20/-10/0", "description": "Mood Tags 覆蓋度"},
            "feature_buttons": {"weight": "-25/-15/0", "description": "Feature Buttons 明確度"},
            "abstract_words": {"weight": "-20/-5/+10", "description": "抽象詞檢測"},
            "feature_match_score": {"weight": "-15/-10/0", "description": "Feature 匹配分數"},
            "candidate_count": {"weight": "-15/-10/0", "description": "候選數量"}
        },
        "decision_logic": {
            "threshold": 40,
            "above_threshold": "Embedding (語義理解)",
            "below_threshold": "Feature (快速精準)",
            "total_score_range": 125
        }
    }
